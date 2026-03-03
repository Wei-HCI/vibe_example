"""
rcode.data_processing - Data wrangling, Pareto analysis, REI outlier detection.

Ports of R functions: ``replace_values``, ``reshape_data``,
``add_pareto_emoa_column``, ``remove_outliers_REI``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Sequence, Union

import numpy as np
import pandas as pd

from rcode.utils import not_empty


# ── replace_values ──────────────────────────────────────────────────────── #

def replace_values(
    data: pd.DataFrame,
    to_replace: Sequence[str],
    replace_with: Sequence[str],
) -> pd.DataFrame:
    """Replace specified values throughout a DataFrame.

    Parameters
    ----------
    data : DataFrame
        Input data.
    to_replace : sequence of str
        Values to find.
    replace_with : sequence of str
        Corresponding replacement values.

    Returns
    -------
    DataFrame
        A copy with substitutions applied.
    """
    if len(to_replace) != len(replace_with):
        raise ValueError("Length of 'to_replace' and 'replace_with' must be the same.")

    mapping = dict(zip(to_replace, replace_with))
    result = data.copy()
    result = result.replace(mapping)
    return result


# ── reshape_data ────────────────────────────────────────────────────────── #

def reshape_data(
    input_filepath: Union[str, Path],
    marker: str = "videoinfo",
    id_col: str = "ID",
    output_filepath: Optional[Union[str, Path]] = None,
    sheet_name: str = "Results",
) -> pd.DataFrame:
    """Reshape wide-format Excel data to long format based on column markers.

    Identifies sections of columns between markers that start with *marker*
    and stacks them under the first section.

    Parameters
    ----------
    input_filepath : str or Path
        Path to input Excel file.
    marker : str
        Column-name prefix that marks section boundaries.
    id_col : str
        Name of the ID column to repeat for each section.
    output_filepath : str or Path, optional
        If given, write the reshaped data to this Excel file.
    sheet_name : str
        Sheet name to read (falls back to first sheet if not found).

    Returns
    -------
    DataFrame
        The reshaped long-form data.
    """
    input_filepath = Path(input_filepath)

    # Read Excel — fall back to first sheet
    xls = pd.ExcelFile(input_filepath)
    sheet = sheet_name if sheet_name in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(xls, sheet_name=sheet)

    id_column = df[[id_col]]

    # Identify pre-marker columns (e.g. ID) and marker-delimited data sections.
    # Layout: [ID cols...] [marker_1] [data cols...] [marker_2] [data cols...] ...
    pre_marker_cols: list[str] = []
    sections: list[list[str]] = []
    current: list[str] = []
    seen_marker = False

    for col in df.columns:
        if col.startswith(marker):
            if seen_marker and current:
                sections.append(current)
            seen_marker = True
            current = []
        else:
            if seen_marker:
                current.append(col)
            else:
                pre_marker_cols.append(col)
    if current:
        sections.append(current)

    if not sections:
        return df

    # Build long DataFrame: first section includes pre-marker cols
    long_df = pd.concat([df[pre_marker_cols], df[sections[0]]], axis=1)
    base_columns = long_df.columns.tolist()

    for section in sections[1:]:
        sliced = pd.concat([id_column, df[section]], axis=1)
        sliced.columns = base_columns
        long_df = pd.concat([long_df, sliced], ignore_index=True)

    # Write output
    if output_filepath is not None:
        output_filepath = Path(output_filepath)
        counter = 0
        target = output_filepath
        while target.exists():
            counter += 1
            target = output_filepath.with_stem(f"{output_filepath.stem}_{counter}")
        long_df.to_excel(target, index=False)

    return long_df


# ── Pareto front classification ─────────────────────────────────────────── #

def _is_dominated(point: np.ndarray, others: np.ndarray) -> bool:
    """Return True if *point* is dominated by any row in *others*."""
    # A point is dominated if there exists another point that is >= in all
    # objectives and strictly > in at least one.
    for other in others:
        if np.all(other >= point) and np.any(other > point):
            return True
    return False


def add_pareto_column(
    data: pd.DataFrame,
    objectives: List[str],
) -> pd.DataFrame:
    """Add a ``PARETO`` boolean column indicating Pareto front membership.

    Parameters
    ----------
    data : DataFrame
    objectives : list of str
        Column names for the objectives (higher = better).

    Returns
    -------
    DataFrame
        A copy with a ``PARETO`` column.
    """
    not_empty(data, "data")
    not_empty(objectives, "objectives")

    result = data.copy()
    obj_vals = result[objectives].values.astype(float)

    if len(obj_vals) <= 1:
        result["PARETO"] = True
        return result

    # Try using pygmo if available
    try:
        import pygmo

        ndf, _, _, _ = pygmo.fast_non_dominated_sorting((-obj_vals).tolist())
        pareto_indices = set(ndf[0])
        result["PARETO"] = [i in pareto_indices for i in range(len(obj_vals))]
        return result
    except ImportError:
        pass

    # Pure-Python fallback
    is_pareto = np.ones(len(obj_vals), dtype=bool)
    for i in range(len(obj_vals)):
        if not is_pareto[i]:
            continue
        for j in range(len(obj_vals)):
            if i == j or not is_pareto[j]:
                continue
            if np.all(obj_vals[j] >= obj_vals[i]) and np.any(obj_vals[j] > obj_vals[i]):
                is_pareto[i] = False
                break

    result["PARETO"] = is_pareto
    return result


# ── REI outlier detection ───────────────────────────────────────────────── #

def remove_outliers_rei(
    data: pd.DataFrame,
    variables: Optional[List[str]] = None,
    likert_range: tuple = (1, 5),
) -> pd.DataFrame:
    """Calculate the Response Entropy Index and flag suspicious responses.

    Parameters
    ----------
    data : DataFrame
        Raw data (each row = one respondent).
    variables : list of str, optional
        Columns to analyse. If None, all numeric columns are used.
    likert_range : tuple of (int, int)
        Min and max of the Likert scale.

    Returns
    -------
    DataFrame
        Copy of *data* with added columns ``REI``, ``Percentile``, ``Suspicious``.
    """
    result = data.copy()

    if variables is not None and len(variables) > 0:
        cols = [c for c in variables if c in result.columns]
    else:
        cols = result.select_dtypes(include=[np.number]).columns.tolist()

    if len(cols) < 2:
        raise ValueError("Not enough columns found for REI computation.")

    subset = result[cols].values
    n_questions = subset.shape[1]

    # Count occurrences of each unique response per row
    unique_responses = np.unique(subset[~np.isnan(subset)])

    rei_values = np.zeros(len(result))
    for i in range(len(result)):
        row = subset[i]
        row_valid = row[~np.isnan(row)]
        if len(row_valid) == 0:
            continue
        counts = np.array([np.sum(row_valid == v) for v in unique_responses])
        proportions = counts / len(row_valid)
        # Shannon entropy in log10
        with np.errstate(divide="ignore", invalid="ignore"):
            log_terms = np.where(proportions > 0, proportions * np.log10(proportions), 0.0)
        rei_values[i] = -np.sum(log_terms)

    result["REI"] = rei_values

    # Percentile (based on normal distribution CDF)
    from scipy import stats as sp_stats

    mean_rei = np.nanmean(rei_values)
    std_rei = np.nanstd(rei_values, ddof=0)
    if std_rei > 0:
        result["Percentile"] = np.round(
            sp_stats.norm.cdf(rei_values, loc=mean_rei, scale=std_rei) * 100, 2
        )
    else:
        result["Percentile"] = 50.0

    result["Suspicious"] = "No"
    result.loc[(result["Percentile"] <= 10) | (result["Percentile"] >= 90), "Suspicious"] = "Maybe"
    result.loc[(result["Percentile"] <= 5) | (result["Percentile"] >= 95), "Suspicious"] = "Yes"

    return result
