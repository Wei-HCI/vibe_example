# rCode (Python Edition)

> Python port of [rCode](https://github.com/M-Colley/rCode) by [Mark Colley](https://m-colley.github.io/)

`rcode` is a Python package that streamlines statistical analysis and APA-compliant result reporting. It is a port of the original R package, built on top of `scipy`, `pingouin`, `statsmodels`, `matplotlib`, and `seaborn`.

## What Was Changed in This Python Port

Compared to Mark Colley's original `rCode` (R), this Python edition mainly introduces:

- A modular Python package layout (`rcode.setup`, `rcode.assumptions`, `rcode.reporting`, `rcode.visualization`, `rcode.data_processing`, `rcode.utils`) for reusable workflow-based analysis.
- Python-native statistical integration based on `scipy`, `pingouin`, `statsmodels`, and `scikit-posthocs` to reproduce and extend core inferential workflows.
- Automated APA-oriented reporting helpers that generate publication-ready LaTeX strings (e.g., NPAV, ART, Dunn, pairwise paper-style results with effect sizes).
- Expanded plotting utilities for within/between-subject comparisons and multi-factor effect visualization using matplotlib/seaborn objects (`Figure`, `Axes`) for downstream customization.
- Extra data-processing helpers (normalization, reshaping, value replacement, Pareto sorting, REI outlier detection) to support end-to-end analysis pipelines in Python.

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

## Installation

> **⚠️ It is strongly recommended to create a dedicated virtual environment** to avoid dependency conflicts.

### Step 1: Create a virtual environment

```bash
python -m venv myenv
```

### Step 2: Activate the environment

**Windows:**

```bash
myenv\Scripts\activate
```

**macOS / Linux:**

```bash
source myenv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

## Qwen Code Setup

This project can be used with [Qwen Code](https://github.com/QwenLM/qwen-code), an open-source AI coding agent for the terminal. Follow the steps below to set it up.

### Step 1: Install Qwen Code

**Linux / macOS:**

```bash
curl -fsSL https://qwen-code-assets.oss-cn-hangzhou.aliyuncs.com/installation/install-qwen.sh | bash
```

**Windows (Run as Administrator CMD):**

```cmd
curl -fsSL -o %TEMP%\install-qwen.bat https://qwen-code-assets.oss-cn-hangzhou.aliyuncs.com/installation/install-qwen.bat && %TEMP%\install-qwen.bat
```

Or install manually via npm (requires [Node.js](https://nodejs.org/en/download) v20+):

```bash
npm install -g @qwen-code/qwen-code@latest
```

### Step 2: Configure API Key

Add the API key in the qwen code, and select the MiniMax-M2.5 model.

```json
  "env": {
    "DASHSCOPE_API_KEY": "sk-sp-92cfc7ad460242aeac574fa8e7163384"
  },
  "model": {
    "name": "MiniMax-M2.5"
  }
```

### Step 3: Launch Qwen Code

```bash
cd path/to/your_project
qwen
```

Use `/stats` to verify the current session information and model configuration.

### Useful Commands

| Command | Description |
|---|---|
| `/help` | Display available commands |
| `/model <name>` | Switch model (e.g. `/model MiniMax-M2.5`) |
| `/stats` | Show current session information |
| `/clear` | Clear conversation history |
| `/compress` | Compress history to save tokens |

For more details, see the [Qwen Code documentation](https://qwenlm.github.io/qwen-code-docs/en/users/overview) and the [GitHub repository](https://github.com/QwenLM/qwen-code).

## Key Features

- **Automated Assumption Checking**: Verify normality (Shapiro-Wilk) and homogeneity of variance (Levene's test) for ANOVA models.
- **APA-Compliant LaTeX Reporting**: Generate copy-paste-ready LaTeX strings for NPAV, ART, Dunn tests, mean/SD, and more.
- **Enhanced Visualizations**: Box/violin plots with automatic parametric/non-parametric test selection and significance annotations.
- **Data Processing Utilities**: Normalize, replace values, Pareto front classification, REI-based outlier detection.

## Visualization Example

Below is an exploratory data analysis produced with `rcode.visualization`, demonstrating histogram, scatter plot with regression line, correlation matrix, and box plot outputs:

![Exploratory Data Analysis — WHO Life Expectancy Dataset](figures/eda_example.png)

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



## Prompt Example: Generate Custom Violin Plots

The following prompts were used with an AI coding assistant to generate violin plots from the dataset in this project.

**Prompt 1** — Generate violin plot script:

> Based on the CSV file in my text_dataset directory, write a script to generate violin plots by calling the functions from this project, and run this script in "myenv" environment.

**Prompt 2** — Customize colors and style:

> Change the colors of the three groups to match the reference image (green, orange, purple), remove all scatter points from the violin plot, and keep only the mean.

### Sample Output

The script generates both violin plots and paper-style LaTeX text for each dependent variable. Example output:

```latex
\textit{FVR} ($M = 23.23$, $SD = 4.01$) did not differ significantly from
\textit{Remote} ($M = 23.03$, $SD = 2.76$) in spatial presence (sp)
($t(29) = 0.30$, $p = .766$).

\textit{LocoScooter} ($M = 6.07$, $SD = 0.62$) was rated significantly higher
than \textit{Joystick} ($M = 3.36$, $SD = 1.69$) in physical demand
($W = 91$, $p = .001$, $r = 0.64$).
```

The function `report_pairwise_paper_style()` automatically:
1. Checks normality of paired differences (Shapiro-Wilk)
2. Selects the appropriate test (paired *t*-test or Wilcoxon signed-rank)
3. Reports *M*, *SD*, test statistic, *p*-value
4. Includes effect size (Cohen's *d* or rank-biserial *r*) for significant results

