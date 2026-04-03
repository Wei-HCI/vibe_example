# rcode — API Reference

Python port of [rCode](https://github.com/) by Mark Colley — a statistical helper library for HCI, VR, and questionnaire-based experimental research.

For installation and general usage, see the main [README.md](README.md).

## Quick Example

```python
import pandas as pd
from rcode import setup, check_assumptions_for_anova, report_mean_and_sd

setup()

df = pd.read_csv("data.csv")
print(check_assumptions_for_anova(df, y="score", factors=["group", "condition"]))
print(report_mean_and_sd(df, iv="group", dv="score"))
```

## Questionnaire Scoring

| Function | Questionnaire |
|----------|---------------|
| `process_ipq()` | Igroup Presence Questionnaire |
| `process_ssq()` | Simulator Sickness Questionnaire |
| `process_sus()` | System Usability Scale |

All three assume standard item layouts by default but accept explicit column mapping when the file structure differs.

## Assumption Checks

- `check_normality_by_group()` — Shapiro-Wilk per group
- `check_assumptions_for_anova()` — normality + sphericity + homogeneity screening for ANOVA workflows

## Reporting

Helpers for publication-ready output, often LaTeX-friendly:

- `report_mean_and_sd()` — descriptive statistics
- `report_npav()` / `report_npav_chi()` — non-parametric results
- `report_art()` — Aligned Rank Transform results
- `report_npar_ld()` — non-parametric longitudinal data
- `report_dunn_test()` / `report_dunn_test_table()` — Dunn's post-hoc tests
- `report_pairwise_paper_style()` — pairwise comparisons in paper format
- `latexify_report()` — convert reports to LaTeX

## Visualization

- `gg_withinstats_with_normality_check()` — within-subjects plot with stats overlay
- `gg_betweenstats_with_normality_check()` — between-subjects plot with stats overlay
- `generate_effect_plot()` — effect size visualization
- `generate_mobo_plot()` — multi-objective optimization plot

## Data Processing

- `replace_values()` — recode values
- `reshape_data()` — wide/long transforms
- `add_pareto_column()` — Pareto optimality labels
- `remove_outliers_rei()` — outlier removal

## Package Structure

```
rcode/
├── __init__.py                  # public re-exports
├── setup.py
├── assumptions.py
├── reporting.py
├── visualization.py
├── data_processing.py
├── questionnaire_processing.py
└── utils.py
```

## Implementation Note

The Python port covers all major workflows from the original R version. Some statistical operations (e.g., repeated-measures ANOVA, Friedman, Kruskal-Wallis) delegate to established libraries (`pingouin`, `scipy`, `statsmodels`) rather than reimplementing them from scratch.

## Citation

If you use `rcode` or the original rCode in research, please cite the upstream work by Mark Colley.
