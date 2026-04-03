# Super Analyze

A Claude Code plugin for statistical analysis of experimental research data. It auto-detects questionnaire types and experimental designs, asks for your confirmation at key decision points, and generates a traceable analysis script.

Built on top of `rcode`, a statistical helper library in the same repository (see [README-rcode.md](README-rcode.md)).

## Quick Start

```bash
# 1. Install dependencies
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
pip install -e .

# 2. Register as a local plugin in Claude Code
/plugin marketplace add C:/Users/adminroot/Documents/GitHub/vibe_example
/plugin install super-analysis@vibe-example-local

# 3. Run
/super-analysis:run text_dataset/ipq.csv
# or shorthand
/super-analysis text_dataset/ipq.csv
```

## Workflow

```
Data file ──▶ Detect ──▶ Confirm ──▶ Preprocess ──▶ Assumptions ──▶ Confirm ──▶ Analyze ──▶ Output
                │          ▲                            │              ▲
                │          │                            │              │
            automatic   you decide                 auto-recommend   you decide
```

**Phase 1 — Detection (automatic)**
Scan the file and detect questionnaire type (IPQ / SSQ / SUS / NASA-TLX / generic), independent variables, dependent variables, subject ID, and experimental design (within/between-subjects, single/multi-factor).

**Confirmation 1 — You confirm or correct the detection results**

**Phase 2 — Preprocessing (automatic)**
Score questionnaires via `rcode` functions when available, clean data, and export `cleaned_scored.csv`.

**Phase 3 — Descriptive Statistics & Assumption Checks (automatic)**
Summarize by condition; run Shapiro-Wilk, Mauchly, Levene, etc. and recommend a statistical method per dependent variable.

**Confirmation 2 — You confirm or override the recommended methods**

**Phase 4 — Main Analysis (automatic)**

| Design | Parametric | Non-parametric |
|--------|-----------|----------------|
| 2 conditions, within | Paired t-test | Wilcoxon |
| 2 conditions, between | Independent t-test | Mann-Whitney U |
| ≥3 conditions, within | Repeated-measures ANOVA | Friedman |
| ≥3 conditions, between | One-way ANOVA | Kruskal-Wallis |
| Multi-factor | Two-way ANOVA | ART |

**Phase 5 — Output**

| File | Description |
|------|-------------|
| `analyze_xxx.py` | Traceable analysis script (the core artifact — each block is labeled with its source) |
| `cleaned_scored.csv` | Cleaned and scored data |
| `summary.txt` | Results summary |
| `figures/*.png` | Figures |

Every code block in the generated script is labeled as either `rcode`-backed or local fallback (using pingouin / scipy / statsmodels).

## Supported Questionnaires

- **IPQ / SSQ / SUS** — reuses scoring functions from `rcode`
- **NASA-TLX** — local fallback scoring (`rcode` does not yet expose a dedicated wrapper)
- **Generic data** — skips questionnaire scoring and goes straight to analysis

## The `rcode` Library

Super Analyze is the orchestration layer; `rcode` is the statistical library underneath it, handling questionnaire scoring, assumption checks, reporting, and plotting.

For the full list of available functions, see [README-rcode.md](README-rcode.md).
