"""
rcode.reporting - APA-compliant LaTeX report generation.

Ports of R functions: ``reportNPAV``, ``reportNPAVChi``, ``reportART``,
``reportNparLD``, ``reportMeanAndSD``, ``reportDunnTest``,
``reportDunnTestTable``, ``rFromWilcox``, ``rFromNPAV``,
``reportggstatsplot``, ``reportggstatsplotPostHoc``, ``latexify_report``.
"""

from __future__ import annotations

import io
import re
import warnings
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from rcode.utils import not_empty


# ── Helpers ─────────────────────────────────────────────────────────────── #

def _fmt_p(p: float) -> str:
    """Format a p-value as LaTeX ``\\p{...}`` or ``\\pminor{0.001}``."""
    if p < 0.001:
        return r"\pminor{0.001}"
    return rf"\p{{{p:.3f}}}"


def _fmt_padj(p: float) -> str:
    """Format an adjusted p-value for post-hoc LaTeX output."""
    if p < 0.001:
        return r"\padjminor{0.001}"
    return rf"\padj{{{p:.3f}}}"


def _eta2_from_f(f_val: float, df: float, df_error: float) -> Optional[Dict[str, float]]:
    """Compute partial eta-squared (and 90 % CI) from an F statistic.

    Uses the formula: eta2_p = (F * df) / (F * df + df_error).
    """
    if df_error <= 0 or not np.isfinite(df_error):
        return None
    eta2 = (f_val * df) / (f_val * df + df_error)
    # Approximate CI via non-central F
    try:
        lambda_obs = f_val * df
        ci_low = max(0.0, 1 - (1 / (1 + sp_stats.ncf.ppf(0.05, df, df_error, lambda_obs) * df / df_error)))
        ci_high = 1 - (1 / (1 + sp_stats.ncf.ppf(0.95, df, df_error, lambda_obs) * df / df_error))
    except Exception:
        ci_low, ci_high = None, None
    return {"eta2": eta2, "ci_low": ci_low, "ci_high": ci_high}


def _cohens_w(chi: float, n: int) -> float:
    """Compute Cohen's *w* from a chi-square statistic."""
    return np.sqrt(chi / n)


def _asterisks(p: float) -> Optional[str]:
    """Return significance asterisks, or None if not significant."""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return None


def _detect_effect_type(desc: str) -> str:
    """Return 'interaction' if description contains 'X', else 'main'."""
    return "interaction" if "X" in desc else "main"


def _latexify_interaction(text: str) -> str:
    r"""Replace `` X`` with ``$\times$ \`` for LaTeX formatting."""
    return re.sub(r"(?<=\s)X", r"$\\times$ \\", text)


# ── Effect size helpers ─────────────────────────────────────────────────── #

def r_from_wilcox(p_value: float, n: int, data_name: str = "Sample") -> str:
    """Compute effect size *r* from a Wilcoxon test (Rosenthal 1994).

    Parameters
    ----------
    p_value : float
        P-value of the Wilcoxon test.
    n : int
        Total number of measurements.
    data_name : str
        Label for the data (printed in output).

    Returns
    -------
    str
        Formatted effect-size string.
    """
    z = sp_stats.norm.ppf(p_value / 2)
    r = z / np.sqrt(n)
    result = f"{data_name} Effect Size, r= {r:.3f} z= {z:.4f}"
    print(result)
    return result


def r_from_wilcox_adjusted(p_value: float, n: int, adjust_factor: float, data_name: str = "Sample") -> str:
    """Compute adjusted effect size *r* from a Wilcoxon test."""
    z = sp_stats.norm.ppf(p_value * adjust_factor / 2)
    r = z / np.sqrt(n)
    result = f"{data_name} Effect Size, r= {r:.3f} z= {z:.4f}"
    print(result)
    return result


def r_from_npav(p_value: float, n: int) -> str:
    r"""Compute effect size *r* from a non-parametric ANOVA p-value.

    Returns LaTeX: ``\effectsize{r}, Z=z``
    """
    z = sp_stats.norm.ppf(p_value / 2)
    r = z / np.sqrt(n)
    result = rf"\effectsize{{{r:.3f}}}, Z={z:.2f}"
    print(result)
    return result


# ── NPAV (F-based) reporting ────────────────────────────────────────────── #

def report_npav(
    model: pd.DataFrame,
    dv: str = "Testdependentvariable",
    write_to_clipboard: bool = False,
) -> str:
    r"""Generate LaTeX text from a non-parametric ANOVA (F-based) result.

    The *model* DataFrame must contain columns ``Df``, ``F value``, and
    ``Pr(>F)`` with row names as effect descriptions.

    Required LaTeX commands::

        \newcommand{\F}[3]{$F({#1},{#2})={#3}$}
        \newcommand{\p}{\textit{p=}}
        \newcommand{\pminor}{\textit{p$<$}}

    Parameters
    ----------
    model : DataFrame
        ANOVA table (rows = effects, must contain ``Pr(>F)``).
    dv : str
        Dependent variable name for the report text.
    write_to_clipboard : bool
        If True, copies result to clipboard.

    Returns
    -------
    str
        The LaTeX-formatted report text.
    """
    warnings.warn("report_npav is deprecated; prefer ARTool-based reporting.", DeprecationWarning, stacklevel=2)
    not_empty(model, "model")
    not_empty(dv, "dv")

    if "Pr(>F)" not in model.columns:
        msg = "No column 'Pr(>F)' was found. Most likely, you want to use report_npav_chi."
        print(msg)
        return msg

    p_col = model["Pr(>F)"]
    if not p_col.dropna().lt(0.05).any():
        msg = f"The NPAV found no significant effects on {dv}. "
        print(msg)
        _maybe_clip(msg, write_to_clipboard)
        return msg

    # Prepare descriptions
    model = model.copy()
    model["descriptions"] = model.index.astype(str)
    model["descriptions"] = model["descriptions"].str.replace(":", " X", regex=False)

    parts: list[str] = []
    rows = model.reset_index(drop=True)
    for i in range(len(rows)):
        p_val = rows.loc[i, "Pr(>F)"]
        if pd.isna(p_val) or p_val >= 0.05:
            continue

        f_val = round(rows.loc[i, "F value"], 2)
        num_df = rows.loc[i, "Df"]

        # Find denominator df (next row with NA p-value)
        den_df = np.nan
        for k in range(i, len(rows)):
            if pd.isna(rows.loc[k, "Pr(>F)"]):
                den_df = rows.loc[k, "Df"]
                break

        p_str = _fmt_p(p_val)
        desc = rows.loc[i, "descriptions"]
        effect_type = _detect_effect_type(desc)
        s = (
            f"The NPAV found a significant {effect_type} effect of "
            f"\\{desc.strip()} on {dv} "
            f"(\\F{{{int(num_df)}}}{{{int(den_df)}}}{{{f_val:.2f}}}, {p_str})"
        )

        # Effect size
        es = _eta2_from_f(f_val, num_df, den_df)
        if es and es["eta2"] is not None:
            s += f", $\\eta_{{p}}^{{2}}$={es['eta2']:.2f}"
            if es["ci_low"] is not None and es["ci_high"] is not None:
                s += f" [{es['ci_low']:.2f}, {es['ci_high']:.2f}]"

        s += ". "
        s = _latexify_interaction(s)
        parts.append(s)

    result = "".join(parts)
    print(result)
    _maybe_clip(result, write_to_clipboard)
    return result


# ── NPAV (Chi-square-based) reporting ──────────────────────────────────── #

def report_npav_chi(
    model: pd.DataFrame,
    dv: str = "Testdependentvariable",
    write_to_clipboard: bool = False,
    sample_size: Optional[int] = None,
) -> str:
    r"""Generate LaTeX text from a non-parametric ANOVA (chi-square-based).

    The *model* DataFrame must contain ``Df``, `` Chi Sq``, `` Pr(>Chi)``.

    Returns
    -------
    str
        The LaTeX-formatted report text.
    """
    warnings.warn("report_npav_chi is deprecated; prefer ARTool-based reporting.", DeprecationWarning, stacklevel=2)
    not_empty(model, "model")
    not_empty(dv, "dv")

    model = model.dropna()

    chi_col = " Chi Sq" if " Chi Sq" in model.columns else "Chi Sq"
    p_chi_col = " Pr(>Chi)" if " Pr(>Chi)" in model.columns else "Pr(>Chi)"

    if not model[p_chi_col].lt(0.05).any():
        msg = f"The NPAV found no significant effects on {dv}. "
        print(msg)
        _maybe_clip(msg, write_to_clipboard)
        return msg

    model = model.copy()
    model["descriptions"] = model.index.astype(str).str.replace(":", " X", regex=False)

    parts: list[str] = []
    for i in range(len(model)):
        row = model.iloc[i]
        p_val = row[p_chi_col]
        if pd.isna(p_val) or p_val >= 0.05:
            continue

        chi_val = round(row[chi_col], 2)
        num_df = int(row["Df"])
        p_str = _fmt_p(p_val)
        desc = row["descriptions"]
        effect_type = _detect_effect_type(desc)

        s = (
            f"The NPAV found a significant {effect_type} effect of "
            f"\\{desc.strip()} on {dv} "
            f"(\\chisq~(1)={chi_val}, {p_str})"
        )

        # Effect size: Cohen's w
        if sample_size is not None and sample_size > 0:
            w = _cohens_w(chi_val, sample_size)
            s += f", $w={w:.2f}"

        s += ". "
        s = _latexify_interaction(s)
        parts.append(s)

    result = "".join(parts)
    print(result)
    _maybe_clip(result, write_to_clipboard)
    return result


# ── ART reporting ───────────────────────────────────────────────────────── #

def report_art(
    model: pd.DataFrame,
    dv: str = "Testdependentvariable",
    write_to_clipboard: bool = False,
) -> str:
    r"""Generate LaTeX text from an ART (Aligned Rank Transform) ANOVA.

    The *model* DataFrame must contain columns ``Effect`` (or use index),
    ``Df``, ``F value``, ``Pr(>F)``, and ``Df.res``.

    Returns
    -------
    str
        The LaTeX-formatted report text.
    """
    not_empty(model, "model")
    not_empty(dv, "dv")

    if "Pr(>F)" not in model.columns:
        msg = "No column 'Pr(>F)' was found."
        print(msg)
        return msg

    if not model["Pr(>F)"].dropna().lt(0.05).any():
        msg = f"The ART found no significant effects on {dv}. "
        print(msg)
        _maybe_clip(msg, write_to_clipboard)
        return msg

    model = model.copy()
    if "Effect" in model.columns:
        model["descriptions"] = model["Effect"].astype(str).str.replace(":", " X", regex=False)
    else:
        model["descriptions"] = model.index.astype(str).str.replace(":", " X", regex=False)

    parts: list[str] = []
    for i in range(len(model)):
        row = model.iloc[i]
        p_val = row["Pr(>F)"]
        if pd.isna(p_val) or p_val >= 0.05:
            continue

        f_val = round(row["F value"], 2)
        num_df = int(row["Df"])
        den_df = int(row["Df.res"])
        p_str = _fmt_p(p_val)
        desc = row["descriptions"]
        effect_type = _detect_effect_type(desc)

        s = (
            f"The ART found a significant {effect_type} effect of "
            f"\\{desc.strip()} on {dv} "
            f"(\\F{{{num_df}}}{{{den_df}}}{{{f_val:.2f}}}, {p_str}"
        )

        # Effect size
        es = _eta2_from_f(f_val, num_df, den_df)
        if es and es["eta2"] is not None:
            s += f", $\\eta_{{p}}^{{2}}$ = {es['eta2']:.2f}"
            if es["ci_low"] is not None and es["ci_high"] is not None:
                s += f", 95\\% CI: [{es['ci_low']:.2f}, {es['ci_high']:.2f}]"

        s += "). "
        s = _latexify_interaction(s)
        parts.append(s)

    result = "".join(parts)
    print(result)
    _maybe_clip(result, write_to_clipboard)
    return result


# ── nparLD reporting ────────────────────────────────────────────────────── #

def report_npar_ld(
    model: dict,
    dv: str = "Testdependentvariable",
    write_to_clipboard: bool = False,
) -> str:
    r"""Generate LaTeX text from an nparLD result.

    *model* should be a dict with key ``"ANOVA.test"`` holding a DataFrame
    with columns ``Statistic``, ``df``, ``p-value``, and optionally ``RTE``.

    Returns
    -------
    str
        The LaTeX-formatted report text.
    """
    not_empty(model, "model")
    not_empty(dv, "dv")

    anova_df = model["ANOVA.test"]
    if isinstance(anova_df, dict):
        anova_df = pd.DataFrame(anova_df)

    if not anova_df["p-value"].dropna().lt(0.05).any():
        msg = f"The NPAV found no significant effects on {dv}. "
        print(msg)
        return msg

    anova_df = anova_df.copy()
    anova_df["descriptions"] = anova_df.index.astype(str).str.replace(":", " X", regex=False)

    parts: list[str] = []
    for i in range(len(anova_df)):
        row = anova_df.iloc[i]
        p_val = row["p-value"]
        if pd.isna(p_val) or p_val >= 0.05:
            continue

        f_val = round(row["Statistic"], 2)
        num_df = round(row["df"])
        p_str = _fmt_p(p_val)
        desc = row["descriptions"]
        effect_type = _detect_effect_type(desc)

        s = (
            f"The NPVA found a significant {effect_type} effect of "
            f"\\{desc.strip()} on {dv} "
            f"(\\F{{{f_val:.2f}}}, \\df{{{int(num_df)}}}, {p_str})"
        )

        if "RTE" in row.index and pd.notna(row.get("RTE")):
            s += f", $RTE={row['RTE']:.2f}"

        s += ". "
        s = _latexify_interaction(s)
        parts.append(s)

    result = "".join(parts)
    print(result)
    _maybe_clip(result, write_to_clipboard)
    return result


# ── Mean & SD reporting ─────────────────────────────────────────────────── #

def report_mean_and_sd(
    data: pd.DataFrame,
    iv: str = "testiv",
    dv: str = "testdv",
) -> str:
    r"""Report mean and SD per level of *iv* in LaTeX format.

    Produces lines like: ``%LevelA: \m{2.50}, \sd{0.78}``

    Returns
    -------
    str
        The full formatted output.
    """
    not_empty(data, "data")
    not_empty(iv, "iv")
    not_empty(dv, "dv")

    grouped = data.dropna(subset=[iv, dv]).groupby(iv)[dv]
    lines: list[str] = []
    for level, vals in grouped:
        m = vals.mean()
        sd = vals.std()
        line = f"%{level}: \\m{{{m:.2f}}}, \\sd{{{sd:.2f}}}"
        lines.append(line)

    result = "\n".join(lines)
    print(result)
    return result


# ── Dunn test reporting ─────────────────────────────────────────────────── #

def report_dunn_test(
    dunn_result: pd.DataFrame,
    data: pd.DataFrame,
    iv: str = "testiv",
    dv: str = "testdv",
) -> str:
    r"""Report significant Dunn test pairwise comparisons as text.

    Parameters
    ----------
    dunn_result : DataFrame
        Must contain columns ``Comparison`` (e.g. "A - B"), ``Z``, and ``P.adj``.
    data : DataFrame
        The original dataset (used for mean/SD calculations).
    iv, dv : str
        Independent / dependent variable column names.

    Returns
    -------
    str
        The formatted report.
    """
    not_empty(dunn_result, "dunn_result")
    not_empty(data, "data")

    if not dunn_result["P.adj"].dropna().lt(0.05).any():
        msg = f"A post-hoc test found no significant differences for {dv}. "
        print(msg)
        return msg

    findings: list[dict] = []
    for _, row in dunn_result.iterrows():
        if pd.isna(row["P.adj"]) or row["P.adj"] >= 0.05:
            continue

        p_str = _fmt_padj(row["P.adj"])
        parts = [p.strip() for p in row["Comparison"].split(" - ")]
        cond_a, cond_b = parts[0], parts[1]

        # Effect size: rank-biserial correlation
        es_str = ""
        try:
            grp_a = data.loc[data[iv] == cond_a, dv].dropna().values
            grp_b = data.loc[data[iv] == cond_b, dv].dropna().values
            u_stat, _ = sp_stats.mannwhitneyu(grp_a, grp_b, alternative="two-sided")
            n1, n2 = len(grp_a), len(grp_b)
            r_rb = 1 - (2 * u_stat) / (n1 * n2)
            es_str = rf", \rankbiserial{{{abs(r_rb):.2f}}}"
        except Exception:
            pass

        stats_a = data.loc[data[iv] == cond_a, dv]
        stats_b = data.loc[data[iv] == cond_b, dv]
        m_a, sd_a = stats_a.mean(), stats_a.std()
        m_b, sd_b = stats_b.mean(), stats_b.std()

        fmt_a = rf"(\m{{{m_a:.2f}}}, \sd{{{sd_a:.2f}}})"
        fmt_b = rf"(\m{{{m_b:.2f}}}, \sd{{{sd_b:.2f}}})"

        if m_a >= m_b:
            winner, winner_stats = cond_a.strip(), fmt_a
            loser_string = f"{cond_b.strip()} (\\m{{{m_b:.2f}}}, \\sd{{{sd_b:.2f}}}; {p_str}{es_str})"
        else:
            winner, winner_stats = cond_b.strip(), fmt_b
            loser_string = f"{cond_a.strip()} (\\m{{{m_a:.2f}}}, \\sd{{{sd_a:.2f}}}; {p_str}{es_str})"

        findings.append({"winner": winner, "winner_stats": winner_stats, "loser_string": loser_string})

    # Group by winner
    result_parts: list[str] = []
    df_findings = pd.DataFrame(findings)
    for winner in df_findings["winner"].unique():
        subset = df_findings[df_findings["winner"] == winner]
        losers = subset["loser_string"].tolist()
        if len(losers) == 1:
            joined = losers[0]
        elif len(losers) == 2:
            joined = " and ".join(losers)
        else:
            joined = ", ".join(losers[:-1]) + ", and " + losers[-1]

        winner_stats = subset.iloc[0]["winner_stats"]
        s = (
            f"A post-hoc test found that {dv} for the \\{iv} {winner} "
            f"was significantly higher {winner_stats} than for {joined}. "
        )
        result_parts.append(s)

    result = "".join(result_parts)
    print(result)
    return result


def report_dunn_test_table(
    dunn_result: pd.DataFrame,
    data: pd.DataFrame,
    iv: str = "testiv",
    dv: str = "testdv",
    order_by_p: bool = False,
    n_digits_p: int = 4,
) -> Optional[pd.DataFrame]:
    r"""Report significant Dunn test results as a formatted table.

    Parameters
    ----------
    dunn_result : DataFrame
        Must contain ``Comparison``, ``Z``, ``P.adj``.
    data : DataFrame
        Original dataset.
    iv, dv : str
        Independent / dependent variable column names.
    order_by_p : bool
        Sort by p-value.
    n_digits_p : int
        Decimal digits for p-value display.

    Returns
    -------
    DataFrame or None
        The formatted table, or None if nothing significant.
    """
    not_empty(data, "data")

    table = dunn_result[dunn_result["P.adj"] < 0.05].copy()
    if len(table) == 0:
        msg = f"A post-hoc test found no significant differences for {dv}. "
        print(msg)
        return None

    # Compute rank-biserial effect sizes
    effect_sizes = []
    for _, row in table.iterrows():
        parts = [p.strip() for p in row["Comparison"].split(" - ")]
        try:
            grp_a = data.loc[data[iv] == parts[0], dv].dropna().values
            grp_b = data.loc[data[iv] == parts[1], dv].dropna().values
            u_stat, _ = sp_stats.mannwhitneyu(grp_a, grp_b, alternative="two-sided")
            r_rb = 1 - (2 * u_stat) / (len(grp_a) * len(grp_b))
            effect_sizes.append(abs(r_rb))
        except Exception:
            effect_sizes.append(np.nan)

    table["r"] = effect_sizes

    if order_by_p:
        table = table.sort_values("P.adj")
    else:
        table = table.sort_values("Comparison")

    # Format p-values
    table["p-adjusted"] = table["P.adj"].apply(
        lambda p: "<0.001" if p < 0.001 else f"{p:.{n_digits_p}f}"
    )
    table["r"] = table["r"].apply(lambda v: f"{v:.2f}" if pd.notna(v) else "NA")

    result = table[["Comparison", "Z", "p-adjusted", "r"]].reset_index(drop=True)
    caption = (
        f"Post-hoc comparisons for independent variable \\{iv} and dependent variable \\{dv}. "
        f"Positive Z-values mean that the first-named level is sig. higher than the second-named. "
        f"Effect size reported as rank-biserial correlation (r)."
    )
    print(caption)
    print(result.to_string(index=False))
    return result


# ── ggstatsplot-style reporting ─────────────────────────────────────────── #

def report_ggstatsplot(
    stats: dict,
    iv: str = "independent",
    dv: str = "Testdependentvariable",
    write_to_clipboard: bool = False,
) -> str:
    r"""Report statistical details in APA LaTeX format.

    Parameters
    ----------
    stats : dict
        Should contain keys: ``method``, ``statistic``, ``p.value``,
        ``estimate`` (effect size), ``df``, ``df.error``.
    iv, dv : str
        Variable names for the report text.

    Returns
    -------
    str
        The formatted report.
    """
    not_empty(stats, "stats")

    effect_size = round(stats["estimate"], 2)
    p_val = round(stats["p.value"], 3)
    p_str = _fmt_p(p_val)
    statistic = round(stats["statistic"], 2)
    method = stats["method"]

    if method in ("Kruskal-Wallis rank sum test", "Friedman rank sum test"):
        result_str = f"(\\chisq({stats['df.error']})={statistic}, {p_str}, r={effect_size})"
    elif method == "Paired t-test":
        result_str = f"(t({stats['df.error']})={statistic}, {p_str}, r={effect_size})"
    elif method == "Wilcoxon signed rank test":
        result_str = f"(V={statistic}, {p_str}, r={effect_size})"
    else:
        result_str = f"(\\F{{{stats['df']}}}{{{stats['df.error']}}}{{{statistic}}}, {p_str}, r={effect_size})"

    if p_val >= 0.05:
        msg = f"A {method} found no significant effects on {dv} {result_str}. "
    else:
        msg = f"A {method} found a significant effect of \\{iv} on {dv} {result_str}. "

    print(msg)
    _maybe_clip(msg, write_to_clipboard)
    return msg


def report_ggstatsplot_posthoc(
    data: pd.DataFrame,
    pairwise_results: pd.DataFrame,
    iv: str = "testiv",
    dv: str = "testdv",
    label_mappings: Optional[Dict[str, str]] = None,
) -> str:
    r"""Report ggstatsplot-style post-hoc pairwise results.

    Parameters
    ----------
    data : DataFrame
        Original data.
    pairwise_results : DataFrame
        Must have ``group1``, ``group2``, ``p.value``.
    iv, dv : str
        Variable names.
    label_mappings : dict, optional
        Map condition codes to display labels.

    Returns
    -------
    str
        The formatted report.
    """
    not_empty(data, "data")
    not_empty(pairwise_results, "pairwise_results")

    if not pairwise_results["p.value"].dropna().lt(0.05).any():
        msg = f"A post-hoc test found no significant differences for {dv}. "
        print(msg)
        return msg

    parts: list[str] = []
    for _, row in pairwise_results.iterrows():
        if pd.isna(row["p.value"]) or row["p.value"] >= 0.05:
            continue

        p_str = _fmt_padj(row["p.value"])
        c1, c2 = str(row["group1"]), str(row["group2"])
        l1 = label_mappings.get(c1, c1) if label_mappings else c1
        l2 = label_mappings.get(c2, c2) if label_mappings else c2

        v1 = data.loc[data[iv] == c1, dv]
        v2 = data.loc[data[iv] == c2, dv]
        m1, sd1 = v1.mean(), v1.std()
        m2, sd2 = v2.mean(), v2.std()

        s1 = rf" (\m{{{m1:.2f}}}, \sd{{{sd1:.2f}}})"
        s2 = rf" (\m{{{m2:.2f}}}, \sd{{{sd2:.2f}}})"

        if m1 > m2:
            s = f"A post-hoc test found that {l1} was significantly higher{s1} in terms of \\{dv} compared to {l2}{s2}; {p_str}). "
        else:
            s = f"A post-hoc test found that {l2} was significantly higher{s2} in terms of \\{dv} compared to {l1}{s1}; {p_str}). "
        parts.append(s)

    result = "".join(parts)
    print(result)
    return result


# ── latexify_report ─────────────────────────────────────────────────────── #

def latexify_report(
    text: str,
    only_sig: bool = False,
    remove_std: bool = False,
    itemize: bool = True,
    print_result: bool = True,
) -> str:
    r"""Transform ``report``-style text into LaTeX-friendly output.

    Substitutions performed:
    - ``R2`` → ``$R^2$``
    - ``%`` → ``\%``
    - ``~`` → ``$\sim$``
    - ``Rhat`` → ``$\hat{R}$``
    - Bullet items (``- ...``) wrapped in ``\begin{itemize}`` / ``\end{itemize}``
    - Optionally filters to only significant items, removes standardized note.
    """
    # Basic substitutions
    out = text
    out = out.replace("R2", "$R^2$")
    out = out.replace("%", "\\%")
    out = out.replace("~", "$\\sim$")
    out = out.replace("Rhat", "$\\hat{R}$")

    std_pattern = "Standardized parameters were obtained by fitting the model"

    lines = out.split("\n")
    new_lines: list[str] = []
    bullet_block: list[str] = []
    in_bullet = False

    for line in lines:
        if remove_std and std_pattern in line:
            continue

        if re.match(r"^\s*-\s+", line):
            if only_sig and "non-significant" in line:
                continue
            if itemize:
                item = re.sub(r"^\s*-\s+", r"\\item ", line)
                bullet_block.append(item)
                in_bullet = True
            else:
                new_lines.append(re.sub(r"^\s*-\s+", "", line))
        else:
            if in_bullet and itemize:
                new_lines.extend(["\\begin{itemize}"] + bullet_block + ["\\end{itemize}"])
                bullet_block = []
                in_bullet = False
            new_lines.append(line)

    if in_bullet and itemize:
        new_lines.extend(["\\begin{itemize}"] + bullet_block + ["\\end{itemize}"])

    out = "\n".join(new_lines)

    if print_result:
        print(out)

    return out


# ── Clipboard helper ────────────────────────────────────────────────────── #

def _maybe_clip(text: str, do_clip: bool) -> None:
    if do_clip:
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception:
            pass
