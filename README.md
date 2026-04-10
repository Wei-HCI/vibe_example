# Super Analyze

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-Active-2ea44f.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20WSL2%20%7C%20Linux-6A6A6A)

`Super Analyze` is a **human-in-the-loop** assistant for statistical analysis of experimental datasets.

It turns raw data into a reproducible analysis workflow with automatic detection, explicit review gates, and traceable output artifacts.

<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a>
</p>

---

## Table of contents

- [What is Super Analyze?](#what-is-super-analyze)
- [Feature cards](#feature-cards)
- [Install](#install)
- [How to use](#how-to-use)
- [Workflow](#workflow)
- [Method mapping](#method-mapping)
- [Outputs](#outputs)
- [Supported questionnaires](#supported-questionnaires)
- [About rcode](#about-rcode)
- [Contributing](#contributing)
- [License](#license)

---

## What is Super Analyze?

Super Analyze helps research teams move from raw study files to reproducible analysis with better control.

- Detect questionnaire type and design structure from a dataset.
- Keep humans in the loop with required confirmation checkpoints.
- Recommend methods with rationale and alternatives.
- Generate rerunnable scripts and a clean artifact set.

The core value is simple: **fewer manual steps, clear decision traces, and lower reproducibility risk**.

---

## Feature cards

| Feature | What you get |
|---|---|
| **Smart intake** | Detects `IPQ`, `SSQ`, `SUS`, `NASA-TLX`, or generic experimental datasets, plus subject/condition/DV columns. |
| **Two confirmation gates** | Mandatory user confirmation on detection and method choice for every analysis path. |
| **Method suggestions** | Recommends parametric and non-parametric alternatives per dependent variable. |
| **Traceable script generation** | Produces a readable `analyze_<dataset>.py` with source labels (`rcode` vs fallback). |
| **Claude-first command flow** | Integrated slash-command flow for conversational execution. |
| **One command output pack** | Exports cleaned data, summary, and figure files together with the script. |

---

## Install

```bash
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### Register plugin in Claude Code

```bash
/plugin marketplace add <YOUR_REPO_PATH>
/plugin install super-analysis@vibe-example-local
```

Example:

```bash
/plugin marketplace add C:/Users/adminroot/Documents/GitHub/vibe_example
/plugin install super-analysis@vibe-example-local
```

---

## How to use

### Recommended (Claude command)

```bash
/super-analysis:run text_dataset/ipq.csv
# or shorthand
/super-analysis text_dataset/ipq.csv
```

### Direct CLI usage

```bash
python .\scripts\super_analyze.py scan path/to/dataset.csv
python .\scripts\super_analyze.py recommend path/to/dataset.csv
```

Use the virtual environment interpreter when available:

```bash
.\myenv\Scripts\python.exe .\scripts\super_analyze.py scan path/to/dataset.csv
```

---

## Workflow

```text
Data file → Detect → Confirm → Preprocess → Assumption checks → Confirm → Generate analysis → Export outputs
```

### Phase 1 — Detection (automatic)

- Detect questionnaire type and detected fields.
- Infer design pattern (within/between, single-factor or multi-factor).
- Produce an initial structured report.

### Phase 2 — Confirmation 1

- User confirms or corrects the detection report before moving forward.

### Phase 3 — Preprocessing

- Apply questionnaire scoring and data cleanup when supported.
- Keep intermediate files deterministic and auditable.

### Phase 4 — Assumption checks + recommendation (automatic)

- Compute condition-wise summaries and assumption checks.
- Suggest an analysis method and a fallback for each dependent variable.

### Phase 5 — Confirmation 2

- User accepts or replaces the suggested method per dependent variable.

### Phase 6 — Script and artifacts

- Generate `analyze_<dataset>.py` and result files after confirmations pass.

---

## Method mapping

| Design | Parametric option | Non-parametric option |
|---|---|---|
| 2 conditions, within-subject | Paired t-test | Wilcoxon signed-rank |
| 2 conditions, between-subject | Independent t-test | Mann–Whitney U |
| >2 conditions, within-subject | Repeated-measures ANOVA | Friedman |
| >2 conditions, between-subject | One-way ANOVA | Kruskal-Wallis |
| Multi-factor | Two-way ANOVA (or equivalent) | ART or non-parametric alternative |

---

## Outputs

| File | Purpose |
|---|---|
| `analyze_<dataset>.py` | Traceable analysis script, ready to rerun |
| `<dataset_stem>_cleaned_scored.csv` | Cleaned/scored data table |
| `<dataset_stem>_analysis_summary.txt` | Condensed run summary |
| `figures/*.png` | Auto-generated figures |

---

## Supported questionnaires

- `IPQ`, `SSQ`, `SUS`: processed through `rcode` when available.
- `NASA-TLX`: processed via local fallback when repository wrapper is not available.
- Generic datasets: skip questionnaire scoring and proceed directly to analysis checks and generation.

---

## About rcode

`Super Analyze` is an orchestration layer, while `rcode` is the underlying statistical library that handles scoring, checks, and reporting utilities.

See [README-rcode.md](README-rcode.md) for function-level documentation.

---

## Contributing

- Keep plugin behavior consistent with `.claude-plugin/` and `commands/`.
- Add tests or sample cases when changing workflow behavior.
- Update this README together with any command, output, or confirmation changes.

---

## License

MIT.

---
