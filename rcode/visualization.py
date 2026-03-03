"""
rcode.visualization - Statistical plots with automatic test selection.

Ports of R functions: ``ggwithinstatsWithPriorNormalityCheck``,
``ggbetweenstatsWithPriorNormalityCheck``, ``generateEffectPlot``,
``generateMoboPlot`` / ``generateMoboPlot2``.

All functions return a ``matplotlib.figure.Figure`` (and optionally an
``Axes``) so the caller can further customise or save the plot.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from rcode.assumptions import check_normality_by_group
from rcode.utils import not_empty


# ── Helpers ─────────────────────────────────────────────────────────────── #

def _asterisks(p: float) -> Optional[str]:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return None


def _pairwise_test(
    data: pd.DataFrame,
    x: str,
    y: str,
    paired: bool,
    p_adjust: str = "holm",
) -> pd.DataFrame:
    """Run pairwise comparisons between groups (Wilcoxon / Mann-Whitney).

    Returns a DataFrame with ``group1``, ``group2``, ``p.value``.
    """
    import itertools

    groups = sorted(data[x].dropna().unique())
    records: list[dict] = []

    for a, b in itertools.combinations(groups, 2):
        va = data.loc[data[x] == a, y].dropna().values
        vb = data.loc[data[x] == b, y].dropna().values
        if len(va) < 2 or len(vb) < 2:
            continue
        try:
            if paired:
                min_len = min(len(va), len(vb))
                _, p = sp_stats.wilcoxon(va[:min_len], vb[:min_len])
            else:
                _, p = sp_stats.mannwhitneyu(va, vb, alternative="two-sided")
        except Exception:
            p = 1.0
        records.append({"group1": a, "group2": b, "p.value": p})

    if not records:
        return pd.DataFrame(columns=["group1", "group2", "p.value"])

    df = pd.DataFrame(records)

    # Holm correction
    if p_adjust == "holm" and len(df) > 1:
        from statsmodels.stats.multitest import multipletests
        _, corrected, _, _ = multipletests(df["p.value"].values, method="holm")
        df["p.value"] = corrected

    return df


def _add_significance_brackets(
    ax: plt.Axes,
    data: pd.DataFrame,
    x: str,
    y: str,
    pairwise_df: pd.DataFrame,
    group_order: list,
) -> None:
    """Draw significance brackets with asterisks on *ax*."""
    sig = pairwise_df[pairwise_df["p.value"] < 0.05].copy()
    if sig.empty:
        return

    sig["asterisk"] = sig["p.value"].apply(_asterisks)
    y_max = data[y].max()
    y_step = (data[y].max() - data[y].min()) * 0.08
    y_pos = y_max + y_step

    for _, row in sig.iterrows():
        try:
            x1 = group_order.index(row["group1"])
            x2 = group_order.index(row["group2"])
        except ValueError:
            continue

        ax.plot([x1, x1, x2, x2], [y_pos, y_pos + y_step * 0.3, y_pos + y_step * 0.3, y_pos],
                color="black", linewidth=0.8)
        ax.text((x1 + x2) / 2, y_pos + y_step * 0.35, row["asterisk"],
                ha="center", va="bottom", fontsize=10, fontweight="bold")
        y_pos += y_step * 1.2


def _choose_test_type(data: pd.DataFrame, x: str, y: str) -> str:
    """Return 'parametric' or 'nonparametric' based on normality checks."""
    is_normal = check_normality_by_group(data, x, y)
    return "parametric" if is_normal else "nonparametric"


def _subtitle_test(
    data: pd.DataFrame,
    x: str,
    y: str,
    test_type: str,
    paired: bool,
) -> str:
    """Run the overall test and return a subtitle string."""
    groups = sorted(data[x].dropna().unique())
    group_vals = [data.loc[data[x] == g, y].dropna().values for g in groups]

    if len(groups) == 2:
        a, b = group_vals
        if paired:
            min_len = min(len(a), len(b))
            if test_type == "nonparametric":
                stat, p = sp_stats.wilcoxon(a[:min_len], b[:min_len])
                return f"Wilcoxon V={stat:.1f}, p={p:.3f}"
            else:
                stat, p = sp_stats.ttest_rel(a[:min_len], b[:min_len])
                return f"Paired t({min_len - 1})={stat:.2f}, p={p:.3f}"
        else:
            if test_type == "nonparametric":
                stat, p = sp_stats.mannwhitneyu(a, b, alternative="two-sided")
                return f"Mann-Whitney U={stat:.1f}, p={p:.3f}"
            else:
                stat, p = sp_stats.ttest_ind(a, b)
                return f"Welch t={stat:.2f}, p={p:.3f}"
    else:
        if test_type == "nonparametric":
            if paired:
                stat, p = sp_stats.friedmanchisquare(*group_vals)
                return f"Friedman χ²={stat:.2f}, p={p:.3f}"
            else:
                stat, p = sp_stats.kruskal(*group_vals)
                return f"Kruskal-Wallis H={stat:.2f}, p={p:.3f}"
        else:
            stat, p = sp_stats.f_oneway(*group_vals)
            return f"One-way ANOVA F={stat:.2f}, p={p:.3f}"


# ── Public API ──────────────────────────────────────────────────────────── #

def gg_withinstats_with_normality_check(
    data: pd.DataFrame,
    x: str,
    y: str,
    ylab: str,
    xlabels: Optional[List[str]] = None,
    show_pairwise: bool = True,
    plot_type: str = "boxviolin",
    show_asterisks: bool = False,
    figsize: Tuple[float, float] = (10, 7),
) -> Tuple[plt.Figure, plt.Axes]:
    """Box/violin within-subjects plot with normality-aware test subtitle.

    Automatically chooses parametric or non-parametric test based on
    Shapiro-Wilk normality check.

    Parameters
    ----------
    data : DataFrame
    x : str
        Grouping (within-subject factor) column name.
    y : str
        Numeric dependent variable column name.
    ylab : str
        Y-axis label.
    xlabels : list of str, optional
        Custom x-axis tick labels.
    show_pairwise : bool
        Whether to show pairwise significance brackets.
    plot_type : str
        ``"box"``, ``"violin"``, or ``"boxviolin"`` (default).
    show_asterisks : bool
        If True, show asterisk annotations instead of full p-values.
    figsize : tuple
        Figure size.

    Returns
    -------
    (Figure, Axes)
    """
    not_empty(data, "data")
    not_empty(x, "x")
    not_empty(y, "y")
    not_empty(ylab, "ylab")

    import seaborn as sns

    test_type = _choose_test_type(data, x, y)
    subtitle = _subtitle_test(data, x, y, test_type, paired=True)

    group_order = sorted(data[x].dropna().unique())
    fig, ax = plt.subplots(figsize=figsize)

    # Plot
    if plot_type in ("violin", "boxviolin"):
        sns.violinplot(data=data, x=x, y=y, order=group_order,
                       inner=None, alpha=0.3, ax=ax)
    if plot_type in ("box", "boxviolin"):
        sns.boxplot(data=data, x=x, y=y, order=group_order,
                    width=0.3, boxprops=dict(alpha=0.7), ax=ax)

    # Individual data points
    sns.stripplot(data=data, x=x, y=y, order=group_order,
                  color="black", alpha=0.3, size=3, jitter=True, ax=ax)

    # Centrality: mean
    means = data.groupby(x)[y].mean().reindex(group_order)
    ax.scatter(range(len(group_order)), means.values, color="darkblue",
               s=80, alpha=0.5, zorder=5, label="Mean")

    ax.set_ylabel(ylab)
    ax.set_xlabel("")
    ax.set_title(subtitle, fontsize=14, fontstyle="italic")

    if xlabels is not None and len(xlabels) == len(group_order):
        ax.set_xticklabels(xlabels)

    # Pairwise annotations
    if show_pairwise:
        pw = _pairwise_test(data, x, y, paired=True)
        _add_significance_brackets(ax, data, x, y, pw, group_order)

    fig.tight_layout()
    return fig, ax


def gg_betweenstats_with_normality_check(
    data: pd.DataFrame,
    x: str,
    y: str,
    ylab: str,
    xlabels: Optional[List[str]] = None,
    show_pairwise: bool = True,
    plot_type: str = "boxviolin",
    show_asterisks: bool = False,
    figsize: Tuple[float, float] = (10, 7),
) -> Tuple[plt.Figure, plt.Axes]:
    """Box/violin between-subjects plot with normality-aware test subtitle.

    Same interface as :func:`gg_withinstats_with_normality_check` but for
    independent (between-subject) comparisons.
    """
    not_empty(data, "data")
    not_empty(x, "x")
    not_empty(y, "y")
    not_empty(ylab, "ylab")

    import seaborn as sns

    test_type = _choose_test_type(data, x, y)
    subtitle = _subtitle_test(data, x, y, test_type, paired=False)

    group_order = sorted(data[x].dropna().unique())
    fig, ax = plt.subplots(figsize=figsize)

    if plot_type in ("violin", "boxviolin"):
        sns.violinplot(data=data, x=x, y=y, order=group_order,
                       inner=None, alpha=0.3, ax=ax)
    if plot_type in ("box", "boxviolin"):
        sns.boxplot(data=data, x=x, y=y, order=group_order,
                    width=0.3, boxprops=dict(alpha=0.7), ax=ax)

    sns.stripplot(data=data, x=x, y=y, order=group_order,
                  color="black", alpha=0.3, size=3, jitter=True, ax=ax)

    means = data.groupby(x)[y].mean().reindex(group_order)
    ax.scatter(range(len(group_order)), means.values, color="darkblue",
               s=80, alpha=0.5, zorder=5, label="Mean")

    ax.set_ylabel(ylab)
    ax.set_xlabel("")
    ax.set_title(subtitle, fontsize=14, fontstyle="italic")

    if xlabels is not None and len(xlabels) == len(group_order):
        ax.set_xticklabels(xlabels)

    if show_pairwise:
        pw = _pairwise_test(data, x, y, paired=False)
        _add_significance_brackets(ax, data, x, y, pw, group_order)

    fig.tight_layout()
    return fig, ax


def generate_effect_plot(
    data: pd.DataFrame,
    x: str,
    y: str,
    fill_colour_group: str,
    ytext: str = "testylab",
    xtext: str = "testxlab",
    legend_pos: str = "best",
    shown_effect: str = "main",
    effect_legend: bool = False,
    x_labels_overwrite: Optional[List[str]] = None,
    figsize: Tuple[float, float] = (10, 7),
) -> Tuple[plt.Figure, plt.Axes]:
    """Generate an effect plot emphasising main or interaction effects.

    Parameters
    ----------
    data : DataFrame
    x : str
        Factor on x-axis.
    y : str
        Dependent variable.
    fill_colour_group : str
        Column for colour grouping.
    ytext, xtext : str
        Axis labels.
    legend_pos : str
        Matplotlib legend location string (e.g. ``"best"``, ``"upper left"``).
    shown_effect : str
        ``"main"`` or ``"interaction"``.
    effect_legend : bool
        Show legend entry for the effect line.
    x_labels_overwrite : list of str, optional
        Custom x-axis tick labels.
    figsize : tuple
        Figure size.

    Returns
    -------
    (Figure, Axes)
    """
    not_empty(data, "data")
    not_empty(x, "x")
    not_empty(y, "y")
    not_empty(fill_colour_group, "fill_colour_group")

    import seaborn as sns

    if shown_effect not in ("main", "interaction"):
        raise ValueError("shown_effect must be 'main' or 'interaction'.")

    fig, ax = plt.subplots(figsize=figsize)

    x_groups = data[x].dropna().unique()
    fill_groups = data[fill_colour_group].dropna().unique()
    palette = sns.color_palette("deep", n_colors=len(fill_groups))

    # Per-group means and error bars
    for idx, fg in enumerate(fill_groups):
        subset = data[data[fill_colour_group] == fg]
        group_means = subset.groupby(x)[y].mean()
        group_ci = subset.groupby(x)[y].apply(
            lambda s: sp_stats.sem(s.dropna()) * sp_stats.t.ppf(0.975, max(1, len(s) - 1))
        )
        x_positions = range(len(group_means))

        ax.errorbar(
            x_positions, group_means.values, yerr=group_ci.values,
            fmt="o", color=palette[idx], markersize=8, capsize=4,
            label=str(fg), alpha=0.8,
        )

        # Interaction line (bold for interaction effect, dashed for main)
        ls = "-" if shown_effect == "interaction" else "--"
        lw = 2 if shown_effect == "interaction" else 1
        ax.plot(x_positions, group_means.values, linestyle=ls, linewidth=lw,
                color=palette[idx], alpha=0.7)

    # Grand-mean line (bold for main effect, dashed for interaction)
    grand_means = data.groupby(x)[y].mean()
    gm_ls = "-" if shown_effect == "main" else "--"
    gm_lw = 2.5 if shown_effect == "main" else 1
    label = f"Mean of {xtext}" if effect_legend else None
    ax.plot(range(len(grand_means)), grand_means.values, linestyle=gm_ls,
            linewidth=gm_lw, color="black", marker="o", markersize=9,
            zorder=5, label=label)

    ax.set_ylabel(ytext)
    ax.set_xlabel(xtext)
    ax.set_xticks(range(len(x_groups)))
    if x_labels_overwrite is not None:
        ax.set_xticklabels(x_labels_overwrite)
    else:
        ax.set_xticklabels(x_groups)

    ax.legend(loc=legend_pos)
    fig.tight_layout()
    return fig, ax


def generate_mobo_plot(
    data: pd.DataFrame,
    x: str,
    y: str,
    fill_colour_group: str = "ConditionID",
    ytext: Optional[str] = None,
    n_sampling_steps: int = 5,
    figsize: Tuple[float, float] = (10, 7),
    phase_col: Optional[str] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Generate a multi-objective Bayesian optimisation plot.

    Visualises sampling and optimisation phases with a vertical separator
    and per-group trend lines.

    Parameters
    ----------
    data : DataFrame
    x : str
        Iteration column.
    y : str
        Objective column.
    fill_colour_group : str
        Colour-grouping column.
    ytext : str, optional
        Y-axis label (defaults to title-cased *y*).
    n_sampling_steps : int
        Number of initial sampling iterations (used when *phase_col* is None).
    figsize : tuple
        Figure size.
    phase_col : str, optional
        Column indicating ``"sampling"`` / ``"optimization"`` phase
        (for ``generateMoboPlot2``-style usage).

    Returns
    -------
    (Figure, Axes)
    """
    not_empty(data, "data")
    not_empty(x, "x")
    not_empty(y, "y")

    import seaborn as sns

    if ytext is None:
        ytext = y.replace("_", " ").title()

    data = data.copy()
    data[x] = pd.to_numeric(data[x], errors="coerce")

    # Determine sampling / optimisation boundary
    if phase_col is not None and phase_col in data.columns:
        n_sampling_steps = int(data.loc[data[phase_col] == "sampling", x].max())

    max_iter = int(data[x].max())

    fig, ax = plt.subplots(figsize=figsize)

    # Per-group plots
    has_groups = fill_colour_group in data.columns
    if has_groups:
        groups = data[fill_colour_group].dropna().unique()
        palette = sns.color_palette("deep", n_colors=len(groups))
        for idx, grp in enumerate(groups):
            subset = data[data[fill_colour_group] == grp]
            grp_means = subset.groupby(x)[y].mean()
            grp_ci = subset.groupby(x)[y].apply(
                lambda s: sp_stats.sem(s.dropna()) * sp_stats.t.ppf(0.975, max(1, len(s) - 1))
            )
            iters = grp_means.index.values
            ax.errorbar(iters, grp_means.values, yerr=grp_ci.values,
                        fmt="o-", color=palette[idx], markersize=5,
                        capsize=3, label=str(grp), alpha=0.8)

            # Trend line (polynomial degree 2)
            if len(iters) >= 3:
                z = np.polyfit(iters.astype(float), grp_means.values, 2)
                poly = np.poly1d(z)
                xs = np.linspace(iters.min(), iters.max(), 100)
                ax.plot(xs, poly(xs), linestyle="--", color=palette[idx],
                        alpha=0.3, linewidth=0.8)
    else:
        grp_means = data.groupby(x)[y].mean()
        grp_ci = data.groupby(x)[y].apply(
            lambda s: sp_stats.sem(s.dropna()) * sp_stats.t.ppf(0.975, max(1, len(s) - 1))
        )
        iters = grp_means.index.values
        ax.errorbar(iters, grp_means.values, yerr=grp_ci.values,
                    fmt="o-", color="steelblue", markersize=5, capsize=3, alpha=0.8)

    # Phase separator
    ax.axvline(n_sampling_steps + 0.5, linestyle="--", color="black", alpha=0.5)

    y_range = ax.get_ylim()
    text_y = y_range[0] + (y_range[1] - y_range[0]) * 0.95
    ax.text(n_sampling_steps / 2, text_y, "Sampling", ha="center", fontsize=11)
    n_opt = max_iter - n_sampling_steps
    ax.text(n_sampling_steps + n_opt / 2, text_y, "Optimization", ha="center", fontsize=11)

    ax.set_xlabel("Iteration")
    ax.set_ylabel(ytext)
    if has_groups:
        ax.legend(loc="best")
    fig.tight_layout()
    return fig, ax
