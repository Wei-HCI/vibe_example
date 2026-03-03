# rCode (Python Edition)

> Python port of [rCode](https://github.com/M-Colley/rCode) by [Mark Colley](https://m-colley.github.io/)

`rcode` is a Python package that streamlines statistical analysis and APA-compliant result reporting. It is a port of the original R package, built on top of `scipy`, `pingouin`, `statsmodels`, `matplotlib`, and `seaborn`.

## Requirements

- Python >= 3.10

### Core Dependencies

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

### Optional Dependencies

| Package | Version | Purpose |
|---|---|---|
| pygmo | >= 2.19 | Faster Pareto front computation |

### Dev Dependencies

| Package | Version |
|---|---|
| pytest | >= 7.0 |
| pytest-cov | >= 4.0 |

## Installation

**Option 1: Using requirements.txt (recommended for reproducible environments)**

```bash
pip install -r requirements.txt        # core dependencies
pip install -r requirements-dev.txt    # dev/test dependencies (optional)
pip install -e .                       # install the package itself
```

**Option 2: Using pyproject.toml (all-in-one)**

```bash
pip install -e ".[dev]"
```

**Option 3: Only install core dependencies without editable mode**

```bash
pip install .
```

## Running Tests

```bash
pytest tests/ -v
```

With coverage report:

```bash
pytest tests/ -v --cov=rcode --cov-report=term-missing
```

## Key Features

- **Automated Assumption Checking**: Verify normality (Shapiro-Wilk) and homogeneity of variance (Levene's test) for ANOVA models.
- **APA-Compliant LaTeX Reporting**: Generate copy-paste-ready LaTeX strings for NPAV, ART, Dunn tests, mean/SD, and more.
- **Enhanced Visualizations**: Box/violin plots with automatic parametric/non-parametric test selection and significance annotations.
- **Data Processing Utilities**: Normalize, replace values, Pareto front classification, REI-based outlier detection.

## Quick Start

```python
import pandas as pd
from rcode import setup, check_assumptions_for_anova, report_mean_and_sd

# Setup (sets matplotlib defaults, prints citation)
setup()

# Check ANOVA assumptions
df = pd.read_csv("data.csv")
result = check_assumptions_for_anova(df, y="score", factors=["group", "condition"])
print(result)

# Report mean and SD in LaTeX
report_mean_and_sd(df, iv="group", dv="score")
```

## Module Overview

| Module | Description |
|---|---|
| `rcode.setup` | Environment configuration, citation printing |
| `rcode.utils` | Utility functions (`normalize`, `na_zero`, `path_prep`, etc.) |
| `rcode.assumptions` | ANOVA assumption checking (normality, homogeneity) |
| `rcode.reporting` | APA-compliant LaTeX report generation |
| `rcode.visualization` | Statistical plots with automatic test selection |
| `rcode.data_processing` | Data reshaping, Pareto analysis, REI outlier detection |

## Citation

```bibtex
@misc{colley2024rcode,
  author       = {Mark Colley},
  title        = {rCode: Enhanced R Functions for Statistical Analysis and Reporting},
  year         = {2024},
  howpublished = {\url{https://github.com/M-Colley/rCode}},
  doi          = {10.5281/zenodo.16875755}
}
```
