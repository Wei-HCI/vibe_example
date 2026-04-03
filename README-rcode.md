# rcode (Python Edition)

> Python port of rCode for statistical analysis support, questionnaire scoring, reporting, and visualization

`rcode` is the library layer in this repository. It provides reusable statistical helpers for HCI, VR, and questionnaire-based experimental research workflows.

This package is a Python adaptation of the original R project by Mark Colley and focuses on:
- questionnaire scoring
- assumption checks
- APA-style reporting helpers
- within-subject and between-subject visualization helpers
- lightweight data processing utilities

## Package Layout

Core modules:
- `rcode.setup`
- `rcode.assumptions`
- `rcode.reporting`
- `rcode.visualization`
- `rcode.data_processing`
- `rcode.questionnaire_processing`
- `rcode.utils`

Public imports are re-exported in `rcode/__init__.py`.

## What `rcode` Currently Covers

### Questionnaire Processing

Implemented scoring helpers:
- `process_ipq()`
- `process_ssq()`
- `process_sus()`

These functions assume standard item layouts by default, but they also allow explicit column mapping when the file structure differs from the expected layout.

### Assumptions

Implemented helpers include:
- `check_normality_by_group()`
- `check_assumptions_for_anova()`

These support coarse screening for ANOVA-style workflows.

### Reporting

Implemented reporting helpers include:
- `report_mean_and_sd()`
- `report_npav()`
- `report_npav_chi()`
- `report_art()`
- `report_npar_ld()`
- `report_dunn_test()`
- `report_dunn_test_table()`
- `report_pairwise_paper_style()`
- `latexify_report()`

These are aimed at publication-ready or paper-style output, often in LaTeX-friendly form.

### Visualization

Implemented plotting helpers include:
- `gg_withinstats_with_normality_check()`
- `gg_betweenstats_with_normality_check()`
- `generate_effect_plot()`
- `generate_mobo_plot()`

### Data Processing

Implemented processing helpers include:
- `replace_values()`
- `reshape_data()`
- `add_pareto_column()`
- `remove_outliers_rei()`

## Current Limits

`rcode` does not yet fully wrap every analysis workflow that existed in the original R version.

In particular, the current Python package does not expose a single unified wrapper for:
- repeated-measures ANOVA omnibus workflows
- non-parametric omnibus workflows equivalent to the original `np.anova(...)`
- full ggstatsplot-object-based extraction/reporting workflows

So in generated analysis scripts, you may still see local fallback calls to:
- `pingouin.rm_anova()`
- `pingouin.friedman()`
- `pingouin.pairwise_tests()`
- `pingouin.sphericity()`

That does not mean the analysis is invalid. It means the orchestration layer is calling established external statistics libraries directly because the wrapper is not yet part of `rcode`.

## Installation

```bash
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Core Dependencies

| Package | Version |
|---|---|
| numpy | >= 1.24 |
| pandas | >= 2.0 |
| scipy | >= 1.10 |
| matplotlib | >= 3.7 |
| seaborn | >= 0.12 |
| statsmodels | >= 0.14 |
| pingouin | >= 0.5 |
| scikit-posthocs | >= 0.8 |
| pyperclip | >= 1.8 |
| openpyxl | >= 3.1 |

## Example Usage

```python
import pandas as pd
from rcode import setup, check_assumptions_for_anova, report_mean_and_sd

setup()

df = pd.read_csv("data.csv")
print(check_assumptions_for_anova(df, y="score", factors=["group", "condition"]))
print(report_mean_and_sd(df, iv="group", dv="score"))
```

## Prompting Guidance

If you are generating analysis scripts with an AI coding assistant, the safest pattern is:
- explicitly state the questionnaire type
- explicitly state the experimental design
- require repository functions when they exist
- require explicit fallback labeling when they do not

This repository's plugin-oriented Prompt 1 guidance lives in the main [README.md](C:\Users\adminroot\Documents\GitHub\vibe_example\README.md).

## Citation

If you use the original rCode concept or this Python adaptation in research, cite the upstream work by Mark Colley.
