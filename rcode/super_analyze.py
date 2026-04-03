"""
rcode.super_analyze - deterministic helpers for the Super Analyze plugin.

These utilities give the plugin a stable backend for:
1. Scanning CSV / Excel files
2. Detecting questionnaire type and experimental design
3. Applying repository-backed preprocessing where available
4. Producing method recommendations for common single-factor workflows
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd
import pingouin as pg
from scipy import stats as sp_stats

from rcode.assumptions import check_assumptions_for_anova
from rcode.questionnaire_processing import process_ipq, process_ssq, process_sus


def _canon(value: object) -> str:
    text = str(value).strip().lower()
    text = text.replace("_", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def read_table(path: str | Path) -> pd.DataFrame:
    """Read a CSV or Excel file into a DataFrame."""
    table_path = Path(path)
    suffix = table_path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(table_path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(table_path)

    raise ValueError(f"Unsupported file type: {table_path.suffix}")


def _columns_by_canonical_name(data: pd.DataFrame) -> Dict[str, str]:
    return {_canon(column): column for column in data.columns}


def _detect_questionnaire(data: pd.DataFrame) -> Dict[str, Any]:
    canonical = _columns_by_canonical_name(data)
    column_names = list(canonical.keys())

    scores: Dict[str, int] = {
        "IPQ": 0,
        "SSQ": 0,
        "NASA-TLX": 0,
        "SUS": 0,
    }
    evidence: Dict[str, List[str]] = {name: [] for name in scores}

    def has_all(names: Iterable[str]) -> bool:
        return all(name in canonical for name in names)

    if has_all(["ipq sp", "ipq inv", "ipq real"]):
        scores["IPQ"] += 5
        evidence["IPQ"].append("Found scored IPQ columns: IPQ_SP, IPQ_INV, IPQ_REAL.")
    elif has_all(["sp", "inv", "real"]):
        scores["IPQ"] += 4
        evidence["IPQ"].append("Found scored IPQ columns: SP, INV, REAL.")

    ipq_keywords = [
        "sense of being there",
        "virtual world surrounded me",
        "felt present in the virtual space",
        "real environment",
    ]
    for keyword in ipq_keywords:
        if any(keyword in name for name in column_names):
            scores["IPQ"] += 1
            evidence["IPQ"].append(f"Found typical IPQ item text containing '{keyword}'.")

    ssq_keywords = [
        "general discomfort",
        "nausea",
        "burping",
        "difficulty focusing",
        "stomach awareness",
    ]
    for keyword in ssq_keywords:
        if keyword in canonical:
            scores["SSQ"] += 1
            evidence["SSQ"].append(f"Found typical SSQ symptom column '{canonical[keyword]}'.")
    if has_all(["ssq n", "ssq o", "ssq d", "ssq ts"]):
        scores["SSQ"] += 4
        evidence["SSQ"].append("Found scored SSQ columns: SSQ_N, SSQ_O, SSQ_D, SSQ_TS.")
    elif has_all(["nausea", "oculomotor", "disorientation", "total score"]):
        scores["SSQ"] += 3
        evidence["SSQ"].append("Found scored SSQ columns: Nausea, Oculomotor, Disorientation, Total Score.")

    nasa_dims = [
        "mental demand",
        "physical demand",
        "temporal demand",
        "performance",
        "effort",
        "frustration",
    ]
    matched_nasa = [canonical[name] for name in nasa_dims if name in canonical]
    if matched_nasa:
        scores["NASA-TLX"] += len(matched_nasa)
        evidence["NASA-TLX"].append(
            "Found NASA-TLX dimensions: " + ", ".join(matched_nasa[:6]) + "."
        )

    if has_all(["sus total"]):
        scores["SUS"] += 4
        evidence["SUS"].append("Found SUS_TOTAL column.")
    sus_keywords = [
        "i think that i would like to use this system frequently",
        "i found the system unnecessarily complex",
        "i thought the system was easy to use",
    ]
    for keyword in sus_keywords:
        if any(keyword in name for name in column_names):
            scores["SUS"] += 1
            evidence["SUS"].append(f"Found typical SUS item text containing '{keyword}'.")

    best_name = max(scores, key=scores.get)
    best_score = scores[best_name]
    if best_score >= 5:
        confidence = "HIGH"
    elif best_score >= 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    if best_score == 0:
        return {
            "name": "Unknown",
            "confidence": "LOW",
            "evidence": ["No strong questionnaire signature matched known rules."],
        }

    return {
        "name": best_name,
        "confidence": confidence,
        "evidence": evidence[best_name],
    }


def _detect_subject_id(data: pd.DataFrame) -> Optional[str]:
    candidates: List[tuple[int, str]] = []

    for column in data.columns:
        name = _canon(column)
        unique = data[column].dropna().nunique()
        if unique == 0:
            continue

        score = 0
        if name in {"participant id", "participantid", "subject id", "subjectid", "pid"}:
            score += 6
        if "participant" in name or "subject" in name or name == "id" or name.endswith(" id"):
            score += 4
        if unique < len(data) and unique >= 2:
            score += 2
        if unique <= max(5, len(data) // 2):
            score += 1
        if "condition" in name or "group" in name:
            score -= 3

        if score > 0:
            candidates.append((score, column))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], str(item[1])))
    return candidates[0][1]


def _condition_repetition_score(
    data: pd.DataFrame,
    subject_col: Optional[str],
    condition_col: str,
) -> int:
    n_conditions = data[condition_col].dropna().nunique()
    if n_conditions < 2 or n_conditions > 8:
        return -5

    score = 0
    if subject_col and subject_col in data.columns:
        coverage = data.groupby(subject_col)[condition_col].nunique(dropna=True)
        if not coverage.empty:
            if (coverage == n_conditions).all():
                score += 4
            elif coverage.max() > 1:
                score += 2
            elif coverage.eq(1).all():
                score += 1

    return score


def _detect_condition_column(data: pd.DataFrame, subject_col: Optional[str]) -> Optional[str]:
    candidates: List[tuple[int, str]] = []

    for column in data.columns:
        if column == subject_col:
            continue

        name = _canon(column)
        unique = data[column].dropna().nunique()
        if unique < 2 or unique > min(12, max(3, len(data) // 2)):
            continue

        score = 0
        if "condition" in name:
            score += 6
        if "group" in name or "treatment" in name or "environment" in name:
            score += 3
        if unique <= 8:
            score += 1
        score += _condition_repetition_score(data, subject_col, column)

        if score > 0:
            candidates.append((score, column))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], str(item[1])))
    return candidates[0][1]


def _detect_wide_layout(data: pd.DataFrame) -> bool:
    bases: Dict[str, int] = {}
    for column in data.columns:
        base = re.sub(r"\.\d+$", "", str(column)).strip()
        bases[base] = bases.get(base, 0) + 1

    repeated_bases = any(count > 1 for count in bases.values())
    unnamed = any(str(column).lower().startswith("unnamed:") for column in data.columns)
    return repeated_bases or unnamed


def _infer_design(
    data: pd.DataFrame,
    subject_col: Optional[str],
    condition_col: Optional[str],
) -> Dict[str, Any]:
    if condition_col is None:
        return {
            "design_type": "ambiguous",
            "label": "Unknown design",
            "participants": 0,
            "conditions": [],
            "wide_layout": _detect_wide_layout(data),
            "stop_reasons": ["Could not infer design without a condition column."],
        }

    conditions = data[condition_col].dropna().astype(str).unique().tolist()
    n_conditions = len(conditions)
    participants = data[subject_col].dropna().nunique() if subject_col else 0
    stop_reasons: List[str] = []

    if _detect_wide_layout(data):
        stop_reasons.append("Detected a wide or multi-block spreadsheet layout that needs human confirmation.")

    if subject_col is None:
        label = f"{n_conditions}-condition design (subject ID unclear)"
        return {
            "design_type": "ambiguous",
            "label": label,
            "participants": participants,
            "conditions": conditions,
            "wide_layout": _detect_wide_layout(data),
            "stop_reasons": stop_reasons + ["Could not find a clear subject ID column."],
        }

    coverage = data.groupby(subject_col)[condition_col].nunique(dropna=True)
    if coverage.empty:
        design_type = "ambiguous"
    elif (coverage == n_conditions).all() and n_conditions >= 2:
        design_type = "within-subjects"
    elif coverage.eq(1).all():
        design_type = "between-subjects"
    else:
        design_type = "ambiguous"
        stop_reasons.append("Participants do not have consistent condition coverage.")

    label = f"{n_conditions}-condition {design_type}" if n_conditions else "Unknown design"
    return {
        "design_type": design_type,
        "label": label,
        "participants": int(participants),
        "conditions": conditions,
        "wide_layout": _detect_wide_layout(data),
        "stop_reasons": stop_reasons,
    }


def _detect_dvs(
    data: pd.DataFrame,
    questionnaire: str,
    exclude: Sequence[str] | None = None,
) -> List[str]:
    excluded = set(exclude or [])
    canonical = _columns_by_canonical_name(data)

    questionnaire_dvs: Dict[str, List[List[str]]] = {
        "IPQ": [["IPQ_SP", "IPQ_INV", "IPQ_REAL"], ["SP", "INV", "REAL"]],
        "SSQ": [
            ["SSQ_N", "SSQ_O", "SSQ_D", "SSQ_TS"],
            ["Nausea", "Oculomotor", "Disorientation", "Total Score"],
        ],
        "NASA-TLX": [
            ["NASA_TLX_RAW_SUM", "NASA_TLX_RAW_MEAN"],
            [
                "Mental Demand",
                "Physical Demand",
                "Temporal Demand",
                "Performance",
                "Effort",
                "Frustration",
            ],
        ],
        "SUS": [["SUS_TOTAL"]],
    }

    for candidate_group in questionnaire_dvs.get(questionnaire, []):
        result: List[str] = []
        for candidate in candidate_group:
            if candidate in data.columns and candidate not in excluded:
                result.append(candidate)
            else:
                key = _canon(candidate)
                if key in canonical and canonical[key] not in excluded:
                    result.append(canonical[key])
        if len(result) == len(candidate_group):
            return result

    numeric = data.select_dtypes(include=[np.number]).columns.tolist()
    return [column for column in numeric if column not in excluded]


def preprocess_questionnaire_data(
    data: pd.DataFrame,
    questionnaire: str,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Apply repository-backed scoring where possible."""
    processed = data.copy()
    metadata: Dict[str, Any] = {
        "questionnaire": questionnaire,
        "repository_function": None,
        "scoring_mode": "none",
        "derived_columns": [],
    }

    if questionnaire == "IPQ":
        if all(column in processed.columns for column in ["IPQ_SP", "IPQ_INV", "IPQ_REAL"]):
            metadata["scoring_mode"] = "already_scored"
            metadata["derived_columns"] = ["IPQ_SP", "IPQ_INV", "IPQ_REAL"]
            return processed, metadata
        if all(column in processed.columns for column in ["SP", "INV", "REAL"]):
            processed["IPQ_SP"] = pd.to_numeric(processed["SP"], errors="coerce")
            processed["IPQ_INV"] = pd.to_numeric(processed["INV"], errors="coerce")
            processed["IPQ_REAL"] = pd.to_numeric(processed["REAL"], errors="coerce")
            metadata["scoring_mode"] = "aliased_existing_scores"
            metadata["derived_columns"] = ["IPQ_SP", "IPQ_INV", "IPQ_REAL"]
            return processed, metadata

        processed = process_ipq(processed)
        metadata["repository_function"] = "process_ipq"
        metadata["scoring_mode"] = "repository"
        metadata["derived_columns"] = ["IPQ_SP", "IPQ_INV", "IPQ_REAL"]
        return processed, metadata

    if questionnaire == "SSQ":
        if all(column in processed.columns for column in ["SSQ_N", "SSQ_O", "SSQ_D", "SSQ_TS"]):
            metadata["scoring_mode"] = "already_scored"
            metadata["derived_columns"] = ["SSQ_N", "SSQ_O", "SSQ_D", "SSQ_TS"]
            return processed, metadata

        processed = process_ssq(processed)
        metadata["repository_function"] = "process_ssq"
        metadata["scoring_mode"] = "repository"
        metadata["derived_columns"] = ["SSQ_N", "SSQ_O", "SSQ_D", "SSQ_TS"]
        return processed, metadata

    if questionnaire == "SUS":
        if "SUS_TOTAL" in processed.columns:
            metadata["scoring_mode"] = "already_scored"
            metadata["derived_columns"] = ["SUS_TOTAL"]
            return processed, metadata

        processed = process_sus(processed)
        metadata["repository_function"] = "process_sus"
        metadata["scoring_mode"] = "repository"
        metadata["derived_columns"] = ["SUS_TOTAL"]
        return processed, metadata

    if questionnaire == "NASA-TLX":
        dims = [
            "Mental Demand",
            "Physical Demand",
            "Temporal Demand",
            "Performance",
            "Effort",
            "Frustration",
        ]
        if all(column in processed.columns for column in dims):
            numeric = processed[dims].apply(pd.to_numeric, errors="coerce")
            processed["NASA_TLX_RAW_SUM"] = numeric.sum(axis=1)
            processed["NASA_TLX_RAW_MEAN"] = numeric.mean(axis=1)
            metadata["scoring_mode"] = "local_fallback"
            metadata["derived_columns"] = ["NASA_TLX_RAW_SUM", "NASA_TLX_RAW_MEAN"]
        return processed, metadata

    return processed, metadata


def build_scan_report(path: str | Path) -> Dict[str, Any]:
    """Create a deterministic detection report for one dataset."""
    table_path = Path(path)
    data = read_table(table_path)
    questionnaire = _detect_questionnaire(data)
    subject_col = _detect_subject_id(data)
    condition_col = _detect_condition_column(data, subject_col)
    design = _infer_design(data, subject_col, condition_col)

    stop_conditions: List[str] = []
    if questionnaire["confidence"] == "LOW":
        stop_conditions.append("Questionnaire detection confidence is low.")
    if subject_col is None:
        stop_conditions.append("Could not find a clear subject ID column.")
    if condition_col is None:
        stop_conditions.append("Could not find a clear condition column.")
    stop_conditions.extend(design["stop_reasons"])

    dvs = _detect_dvs(
        data,
        questionnaire["name"],
        exclude=[column for column in [subject_col, condition_col] if column],
    )
    if not dvs:
        stop_conditions.append("Could not identify dependent variable columns.")

    seen = set()
    deduped_stops = [item for item in stop_conditions if not (item in seen or seen.add(item))]

    return {
        "path": str(table_path),
        "shape": [int(data.shape[0]), int(data.shape[1])],
        "questionnaire": questionnaire,
        "subject_id_column": subject_col,
        "condition_column": condition_col,
        "participants": design["participants"],
        "conditions": design["conditions"],
        "design": {
            "type": design["design_type"],
            "label": design["label"],
            "wide_layout": design["wide_layout"],
        },
        "dependent_variables": dvs,
        "stop_conditions": deduped_stops,
    }


def _safe_shapiro(values: pd.Series) -> Dict[str, Any]:
    cleaned = pd.to_numeric(values, errors="coerce").dropna()
    if len(cleaned) < 3:
        return {"ran": False, "reason": "fewer than 3 observations"}
    if np.isclose(cleaned.var(ddof=1), 0.0):
        return {"ran": False, "reason": "zero variance"}

    statistic, p_value = sp_stats.shapiro(cleaned)
    return {
        "ran": True,
        "W": float(statistic),
        "p": float(p_value),
        "passed": bool(p_value >= 0.05),
        "n": int(len(cleaned)),
    }


def _safe_levene(groups: List[pd.Series]) -> Optional[Dict[str, Any]]:
    prepared = [pd.to_numeric(group, errors="coerce").dropna() for group in groups]
    prepared = [group for group in prepared if len(group) > 0]
    if len(prepared) < 2:
        return None

    statistic, p_value = sp_stats.levene(*prepared)
    return {
        "W": float(statistic),
        "p": float(p_value),
        "passed": bool(p_value >= 0.05),
    }


def _safe_sphericity(
    data: pd.DataFrame,
    dv: str,
    subject_col: str,
    condition_col: str,
) -> Optional[Dict[str, Any]]:
    try:
        result = pg.sphericity(data, dv=dv, subject=subject_col, within=condition_col)
    except Exception as exc:
        return {"ran": False, "reason": str(exc)}

    return {
        "ran": True,
        "passed": bool(result.spher),
        "W": float(result.W),
        "chi2": float(result.chi2),
        "dof": int(result.dof),
        "p": float(result.pval),
    }


def _describe_by_condition(data: pd.DataFrame, condition_col: str, dv: str) -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    grouped = data.dropna(subset=[condition_col, dv]).groupby(condition_col)[dv]
    for condition, values in grouped:
        numeric = pd.to_numeric(values, errors="coerce").dropna()
        summaries.append(
            {
                "condition": str(condition),
                "n": int(len(numeric)),
                "mean": float(numeric.mean()) if len(numeric) else None,
                "sd": float(numeric.std(ddof=1)) if len(numeric) > 1 else 0.0,
            }
        )
    return summaries


def _recommend_method(
    design_type: str,
    n_conditions: int,
    all_groups_normal: bool,
    sphericity: Optional[Dict[str, Any]],
    homogeneity: Optional[Dict[str, Any]],
    coarse_screen: str,
) -> Dict[str, Any]:
    rationale: List[str] = []
    risk_notes: List[str] = []

    if design_type == "within-subjects":
        if n_conditions <= 2:
            parametric = "paired t-test"
            nonparametric = "Wilcoxon signed-rank test"
        else:
            parametric = "repeated-measures ANOVA"
            nonparametric = "Friedman test"

        rationale.append(f"{n_conditions}-condition within-subjects design.")
        if all_groups_normal:
            rationale.append("All condition-wise Shapiro-Wilk checks passed.")
        else:
            rationale.append("At least one condition failed Shapiro-Wilk normality.")
            risk_notes.append("Parametric inference may be sensitive to non-normal groups.")

        if n_conditions >= 3 and sphericity and sphericity.get("ran"):
            if sphericity["passed"]:
                rationale.append("Mauchly's sphericity test passed.")
            else:
                rationale.append("Mauchly's sphericity test failed.")
                risk_notes.append("If you still use rm ANOVA, apply a correction such as Greenhouse-Geisser.")

        use_parametric = all_groups_normal and (
            n_conditions < 3 or not sphericity or not sphericity.get("ran") or sphericity.get("passed", False)
        )
    elif design_type == "between-subjects":
        if n_conditions <= 2:
            parametric = "independent t-test"
            nonparametric = "Mann-Whitney U test"
        else:
            parametric = "one-way ANOVA"
            nonparametric = "Kruskal-Wallis test"

        rationale.append(f"{n_conditions}-condition between-subjects design.")
        if all_groups_normal:
            rationale.append("All group-wise Shapiro-Wilk checks passed.")
        else:
            rationale.append("At least one group failed Shapiro-Wilk normality.")
            risk_notes.append("Consider a rank-based alternative.")

        if homogeneity:
            if homogeneity["passed"]:
                rationale.append("Levene's test passed.")
            else:
                rationale.append("Levene's test failed.")
                risk_notes.append("Variance heterogeneity weakens the classical ANOVA assumption.")

        use_parametric = all_groups_normal and (homogeneity is None or homogeneity.get("passed", False))
    else:
        return {
            "recommended_method": "manual review required",
            "alternative_method": None,
            "rationale": ["The design is ambiguous or unsupported for automatic recommendation."],
            "risk_note": "Confirm the design manually before running any omnibus analysis.",
        }

    if coarse_screen.lower().startswith("you must take the non-parametric"):
        use_parametric = False
        risk_notes.append("Repository coarse screen recommends a non-parametric workflow.")

    return {
        "recommended_method": parametric if use_parametric else nonparametric,
        "alternative_method": nonparametric if use_parametric else parametric,
        "rationale": rationale,
        "risk_note": " ".join(dict.fromkeys(risk_notes)) if risk_notes else None,
    }


def _coarse_anova_screen(data: pd.DataFrame, dv: str, factor: str) -> str:
    subset = data.dropna(subset=[factor, dv])[[factor, dv]].copy()
    subset = subset.rename(columns={factor: "factor_1", dv: "dv_1"})
    return check_assumptions_for_anova(subset, "dv_1", ["factor_1"])


def build_method_recommendations(
    path: str | Path,
    questionnaire: Optional[str] = None,
    subject_col: Optional[str] = None,
    condition_col: Optional[str] = None,
    dvs: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Generate assumption summaries and recommended tests for each DV."""
    scan = build_scan_report(path)
    data = read_table(path)

    resolved_questionnaire = questionnaire or scan["questionnaire"]["name"]
    processed, scoring = preprocess_questionnaire_data(data, resolved_questionnaire)

    resolved_subject = subject_col or scan["subject_id_column"]
    resolved_condition = condition_col or scan["condition_column"]
    design = _infer_design(processed, resolved_subject, resolved_condition)
    resolved_dvs = list(dvs) if dvs else _detect_dvs(
        processed,
        resolved_questionnaire,
        exclude=[column for column in [resolved_subject, resolved_condition] if column],
    )

    stop_conditions = list(scan["stop_conditions"])
    if resolved_condition is None:
        stop_conditions.append("Cannot recommend a method without a condition column.")
    if not resolved_dvs:
        stop_conditions.append("Cannot recommend a method without dependent variables.")

    results: List[Dict[str, Any]] = []
    n_conditions = len(design["conditions"])

    for dv in resolved_dvs:
        if dv not in processed.columns or resolved_condition is None:
            continue

        normality: List[Dict[str, Any]] = []
        grouped = processed.groupby(resolved_condition)
        for condition_name, group in grouped:
            stats = _safe_shapiro(group[dv])
            stats["condition"] = str(condition_name)
            normality.append(stats)

        all_groups_normal = all(item.get("passed", True) for item in normality if item.get("ran"))
        coarse_screen = (
            _coarse_anova_screen(processed, dv, resolved_condition)
            if resolved_condition
            else "Could not run coarse assumption screen."
        )

        homogeneity = None
        sphericity = None
        if design["design_type"] == "between-subjects":
            homogeneity = _safe_levene([group[dv] for _, group in grouped])
        elif design["design_type"] == "within-subjects" and n_conditions >= 3 and resolved_subject:
            sphericity = _safe_sphericity(processed, dv, resolved_subject, resolved_condition)

        recommendation = _recommend_method(
            design["design_type"],
            n_conditions,
            all_groups_normal,
            sphericity,
            homogeneity,
            coarse_screen,
        )

        results.append(
            {
                "dv": dv,
                "descriptive_stats": _describe_by_condition(processed, resolved_condition, dv),
                "assumptions": {
                    "normality": normality,
                    "all_groups_normal": all_groups_normal,
                    "sphericity": sphericity,
                    "homogeneity": homogeneity,
                    "coarse_screen": coarse_screen,
                },
                **recommendation,
            }
        )

    deduped_stop_conditions = list(dict.fromkeys(stop_conditions))
    return {
        "path": str(Path(path)),
        "questionnaire": resolved_questionnaire,
        "subject_id_column": resolved_subject,
        "condition_column": resolved_condition,
        "design": {
            "type": design["design_type"],
            "label": design["label"],
            "conditions": design["conditions"],
            "participants": design["participants"],
        },
        "scoring": scoring,
        "dependent_variables": resolved_dvs,
        "stop_conditions": deduped_stop_conditions,
        "recommendations": results,
    }
