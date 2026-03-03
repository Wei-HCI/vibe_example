"""
rcode.assumptions - ANOVA assumption checking.

Ports of R functions: ``check_normality_by_group``, ``checkAssumptionsForAnova``.
"""

from __future__ import annotations

from typing import List, Optional, Union

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from rcode.utils import not_empty


def check_normality_by_group(
    data: pd.DataFrame,
    x: str,
    y: str,
    alpha: float = 0.05,
) -> bool:
    """Check Shapiro-Wilk normality within each group of *x*.

    Parameters
    ----------
    data : DataFrame
        The dataset.
    x : str
        Column name for the grouping variable.
    y : str
        Column name for the numeric dependent variable.
    alpha : float
        Significance level (default 0.05).

    Returns
    -------
    bool
        ``True`` if **all** groups pass the normality test (p >= alpha).
    """
    not_empty(data, "data")
    not_empty(x, "x")
    not_empty(y, "y")

    if y not in data.columns:
        raise ValueError(f"Column '{y}' not found in data.")
    if x not in data.columns:
        raise ValueError(f"Column '{x}' not found in data.")

    values = pd.to_numeric(data[y], errors="coerce")
    if values.isna().all():
        return False

    groups = data[x].dropna().unique()
    for group in groups:
        group_vals = values[data[x] == group].dropna().values
        if len(group_vals) < 3:
            continue  # Cannot test with fewer than 3 observations
        if np.var(group_vals) == 0:
            continue  # Constant values — skip
        _, p_value = sp_stats.shapiro(group_vals)
        if p_value < alpha:
            return False

    return True


def check_assumptions_for_anova(
    data: pd.DataFrame,
    y: str,
    factors: List[str],
    alpha: float = 0.05,
) -> str:
    """Check normality and homogeneity of variance for an ANOVA model.

    Performs:
    1. Shapiro-Wilk on OLS residuals.
    2. Shapiro-Wilk per group combination.
    3. Levene's test for homogeneity.

    Parameters
    ----------
    data : DataFrame
    y : str
        Dependent variable column name.
    factors : list of str
        Independent variable column names.
    alpha : float
        Significance level (default 0.05).

    Returns
    -------
    str
        A message indicating whether parametric ANOVA is appropriate, or which
        assumption was violated.
    """
    not_empty(data, "data")
    not_empty(y, "y")
    not_empty(factors, "factors")

    import statsmodels.api as sm
    from statsmodels.formula.api import ols

    # Build formula string
    formula_str = f"{y} ~ {' * '.join(factors)}"

    try:
        model = ols(formula_str, data=data).fit()
    except Exception as e:
        return f"Could not fit OLS model: {e}"

    # 1. Shapiro-Wilk on residuals
    residuals = model.resid.dropna().values
    if len(residuals) >= 3:
        _, p_resid = sp_stats.shapiro(residuals)
        if p_resid < alpha:
            return "You must take the non-parametric ANOVA as model residuals are non-normal."

    # 2. Shapiro-Wilk per group combination
    group_col = data[factors].astype(str).agg("_".join, axis=1)
    for _, group_vals in data.groupby(group_col)[y]:
        vals = group_vals.dropna().values
        if len(vals) < 3:
            continue
        if np.var(vals) == 0:
            continue
        _, p_group = sp_stats.shapiro(vals)
        if p_group < alpha:
            return (
                "You must take the non-parametric ANOVA as normality assumption "
                "by groups is violated (one or more p < 0.05)."
            )

    # 3. Levene's test
    groups = [grp[y].dropna().values for _, grp in data.groupby(group_col)]
    groups = [g for g in groups if len(g) > 0]
    if len(groups) >= 2:
        _, p_levene = sp_stats.levene(*groups)
        if p_levene < alpha:
            return "You must take the non-parametric ANOVA as Levene's test is significant (p < 0.05)."

    return (
        "You may take parametric ANOVA. "
        "See https://www.datanovia.com/en/lessons/anova-in-r/#check-assumptions-1 for more information."
    )
