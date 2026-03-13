"""
rcode.questionnaire_processing - Questionnaire-specific preprocessing helpers.

Start with deterministic scoring utilities for standard questionnaires such as
the Simulator Sickness Questionnaire (SSQ).
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence

import pandas as pd

from rcode.utils import not_empty


_SSQ_LETTER_ORDER = tuple("CDEFGHIJKLMNOPQR")
_SUS_LETTER_ORDER = tuple("CDEFGHIJKL")
_IPQ_LETTER_ORDER = tuple("DEFGHIJKLMNOP")


def _resolve_ssq_columns(
    data: pd.DataFrame,
    symptom_columns: Optional[Sequence[str]] = None,
) -> Dict[str, str]:
    """Resolve SSQ symptom columns to Excel-style letters C..R.

    If ``symptom_columns`` is omitted, the function assumes the SSQ items are
    stored in columns 3..18 of ``data`` (Excel columns C..R).
    """
    if symptom_columns is None:
        if data.shape[1] < len(_SSQ_LETTER_ORDER) + 2:
            raise ValueError(
                "SSQ scoring needs 16 symptom columns. Pass 'symptom_columns' "
                "explicitly or provide a table with items in columns C:R."
            )
        symptom_columns = data.columns[2:18].tolist()

    if len(symptom_columns) != len(_SSQ_LETTER_ORDER):
        raise ValueError(
            "'symptom_columns' must contain exactly 16 columns, matching Excel "
            "positions C through R."
        )

    missing = [col for col in symptom_columns if col not in data.columns]
    if missing:
        raise ValueError(f"Columns not found in data: {missing}")

    return dict(zip(_SSQ_LETTER_ORDER, symptom_columns))


def process_ssq(
    data: pd.DataFrame,
    symptom_columns: Optional[Sequence[str]] = None,
    inplace: bool = False,
) -> pd.DataFrame:
    """Compute SSQ subscale and total scores.

    The expected SSQ item order follows Excel columns C..R. You can either:
    1. Leave ``symptom_columns`` empty and place the 16 SSQ items in columns C:R
    2. Pass the 16 item column names explicitly in C:R order

    Computed columns:
    - ``SSQ_A_RAW``: C + H + I + J + K + R + Q
    - ``SSQ_B_RAW``: C + D + E + F + G + K + M
    - ``SSQ_C_RAW``: G + J + L + M + N + O + P
    - ``SSQ_N``: ``SSQ_A_RAW * 9.54``
    - ``SSQ_O``: ``SSQ_B_RAW * 7.58``
    - ``SSQ_D``: ``SSQ_C_RAW * 13.92``
    - ``SSQ_TOTAL_RAW``: ``SSQ_A_RAW + SSQ_B_RAW + SSQ_C_RAW``
    - ``SSQ_TS``: ``SSQ_TOTAL_RAW * 3.74``
    """
    not_empty(data, "data")

    result = data if inplace else data.copy()
    col = _resolve_ssq_columns(result, symptom_columns)

    numeric = result[list(col.values())].apply(pd.to_numeric, errors="coerce")
    for name in numeric.columns:
        result[name] = numeric[name]

    result["SSQ_A_RAW"] = (
        result[col["C"]]
        + result[col["H"]]
        + result[col["I"]]
        + result[col["J"]]
        + result[col["K"]]
        + result[col["Q"]]
        + result[col["R"]]
    )
    result["SSQ_B_RAW"] = (
        result[col["C"]]
        + result[col["D"]]
        + result[col["E"]]
        + result[col["F"]]
        + result[col["G"]]
        + result[col["K"]]
        + result[col["M"]]
    )
    result["SSQ_C_RAW"] = (
        result[col["G"]]
        + result[col["J"]]
        + result[col["L"]]
        + result[col["M"]]
        + result[col["N"]]
        + result[col["O"]]
        + result[col["P"]]
    )

    result["SSQ_N"] = result["SSQ_A_RAW"] * 9.54
    result["SSQ_O"] = result["SSQ_B_RAW"] * 7.58
    result["SSQ_D"] = result["SSQ_C_RAW"] * 13.92
    result["SSQ_TOTAL_RAW"] = result["SSQ_A_RAW"] + result["SSQ_B_RAW"] + result["SSQ_C_RAW"]
    result["SSQ_TS"] = result["SSQ_TOTAL_RAW"] * 3.74
    result["Nausea"] = result["SSQ_N"]
    result["Oculomotor"] = result["SSQ_O"]
    result["Disorientation"] = result["SSQ_D"]
    result["Total Score"] = result["SSQ_TS"]

    return result


def _resolve_sus_columns(
    data: pd.DataFrame,
    item_columns: Optional[Sequence[str]] = None,
) -> Dict[str, str]:
    """Resolve SUS item columns to Excel-style letters C..L."""
    if item_columns is None:
        if data.shape[1] < len(_SUS_LETTER_ORDER) + 2:
            raise ValueError(
                "SUS scoring needs 10 item columns. Pass 'item_columns' "
                "explicitly or provide a table with items in columns C:L."
            )
        item_columns = data.columns[2:12].tolist()

    if len(item_columns) != len(_SUS_LETTER_ORDER):
        raise ValueError(
            "'item_columns' must contain exactly 10 columns, matching Excel "
            "positions C through L."
        )

    missing = [col for col in item_columns if col not in data.columns]
    if missing:
        raise ValueError(f"Columns not found in data: {missing}")

    return dict(zip(_SUS_LETTER_ORDER, item_columns))


def process_sus(
    data: pd.DataFrame,
    item_columns: Optional[Sequence[str]] = None,
    inplace: bool = False,
) -> pd.DataFrame:
    """Compute the SUS total score.

    The expected SUS item order follows Excel columns C..L. You can either:
    1. Leave ``item_columns`` empty and place the 10 SUS items in columns C:L
    2. Pass the 10 item column names explicitly in C:L order

    Computed column:
    - ``SUS_TOTAL``:
      ``((C + E + G + I + K) - 5 + 25 - D - F - H - J - L) * 2.5``
    """
    not_empty(data, "data")

    result = data if inplace else data.copy()
    col = _resolve_sus_columns(result, item_columns)

    numeric = result[list(col.values())].apply(pd.to_numeric, errors="coerce")
    for name in numeric.columns:
        result[name] = numeric[name]

    positive_sum = (
        result[col["C"]]
        + result[col["E"]]
        + result[col["G"]]
        + result[col["I"]]
        + result[col["K"]]
    )
    negative_sum = (
        result[col["D"]]
        + result[col["F"]]
        + result[col["H"]]
        + result[col["J"]]
        + result[col["L"]]
    )

    result["SUS_TOTAL"] = ((positive_sum - 5) + (25 - negative_sum)) * 2.5

    return result


def _resolve_ipq_columns(
    data: pd.DataFrame,
    item_columns: Optional[Sequence[str]] = None,
) -> Dict[str, str]:
    """Resolve IPQ item columns to Excel-style letters D..P."""
    if item_columns is None:
        if data.shape[1] < len(_IPQ_LETTER_ORDER) + 3:
            raise ValueError(
                "IPQ scoring needs 13 item columns. Pass 'item_columns' "
                "explicitly or provide a table with items in columns D:P."
            )
        item_columns = data.columns[3:16].tolist()

    if len(item_columns) != len(_IPQ_LETTER_ORDER):
        raise ValueError(
            "'item_columns' must contain exactly 13 columns, matching Excel "
            "positions D through P."
        )

    missing = [col for col in item_columns if col not in data.columns]
    if missing:
        raise ValueError(f"Columns not found in data: {missing}")

    return dict(zip(_IPQ_LETTER_ORDER, item_columns))


def process_ipq(
    data: pd.DataFrame,
    item_columns: Optional[Sequence[str]] = None,
    inplace: bool = False,
) -> pd.DataFrame:
    """Compute IPQ subscale scores.

    The expected IPQ item order follows Excel columns D..P. You can either:
    1. Leave ``item_columns`` empty and place the 13 IPQ items in columns D:P
    2. Pass the 13 item column names explicitly in D:P order

    Computed columns:
    - ``IPQ_SP``: D + ((-1) * E + 6) + F + G + H
    - ``IPQ_INV``: I + J + ((-1) * K + 6) + L
    - ``IPQ_REAL``: ((-1) * M + 6) + N + O + P
    """
    not_empty(data, "data")

    result = data if inplace else data.copy()
    col = _resolve_ipq_columns(result, item_columns)

    numeric = result[list(col.values())].apply(pd.to_numeric, errors="coerce")
    for name in numeric.columns:
        result[name] = numeric[name]

    result["IPQ_SP"] = (
        result[col["D"]]
        + ((-1) * result[col["E"]] + 6)
        + result[col["F"]]
        + result[col["G"]]
        + result[col["H"]]
    )
    result["IPQ_INV"] = (
        result[col["I"]]
        + result[col["J"]]
        + ((-1) * result[col["K"]] + 6)
        + result[col["L"]]
    )
    result["IPQ_REAL"] = (
        ((-1) * result[col["M"]] + 6)
        + result[col["N"]]
        + result[col["O"]]
        + result[col["P"]]
    )

    return result
