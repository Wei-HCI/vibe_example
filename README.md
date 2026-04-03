# Super Analyze

> Human-in-the-loop statistical analysis plugin for experimental research data

Super Analyze is a workflow layer on top of `rcode`. It helps you go from raw questionnaire data to an auditable analysis script, cleaned data export, summary text, and figures.

It is not a standalone statistics engine. It orchestrates:
- data scan and questionnaire/design detection
- user confirmation at key decision points
- questionnaire scoring through `rcode` when available
- method recommendation per dependent variable
- script generation with traceability comments

## What It Is

Super Analyze is designed for command-driven use inside Claude Code.

Typical flow:
1. You invoke `/statistical-analysis path/to/data.csv`
2. The workflow scans the file and proposes questionnaire type, design, ID column, condition column, and dependent variables
3. You confirm or correct the detection
4. The workflow scores the questionnaire, checks assumptions, recommends methods, and asks for confirmation again
5. It generates an auditable analysis script plus outputs

This is not "press one button and trust the result". The plugin recommends. You decide.

## How To Use

1. Install Python dependencies for this repository:

```bash
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

2. Install the plugin in Claude Code from this repository path:

```text
/plugin install /path/to/this/repository
```

3. Restart Claude Code.

4. Invoke the workflow with a data file:

```text
/statistical-analysis text_dataset/ipq.csv
```

## Workflow

The plugin is built around three confirmation nodes.

### Confirmation 1: Detection

The workflow scans the file and proposes:
- questionnaire type
- subject ID column
- condition column
- dependent variables
- design type

You confirm or correct the proposal before preprocessing starts.

### Confirmation 2: Method Choice

After scoring and assumption checks, the workflow recommends a method per dependent variable, for example:
- paired t-test vs Wilcoxon signed-rank
- repeated-measures ANOVA vs Friedman
- one-way ANOVA vs Kruskal-Wallis

You accept or override the recommendation.

### Confirmation 3: Output

After the main analysis, you review the omnibus results and decide whether to continue to post-hoc tests, figures, and reporting outputs.

## Outputs

The primary output is always the analysis script.

Expected outputs:
- `analyze_xxx.py`
- `cleaned_scored.csv`
- `summary.txt`
- `figures/*.png`

The script is the auditable core. Reports and figures can be regenerated from it.

## Supported Questionnaires

Current workflow support is centered on:
- IPQ
- SSQ
- SUS
- NASA-TLX

For `IPQ`, `SSQ`, and `SUS`, the workflow can reuse repository scoring functions when the file layout matches or when explicit column mapping is supplied.

For `NASA-TLX`, scoring is currently handled as a local fallback because `rcode` does not yet expose a dedicated `process_nasa_tlx()` function.

## Relationship To `rcode`

`Super Analyze` is the orchestration layer.

`rcode` is the statistical helper library underneath it.

In practice:
- `rcode` handles things like questionnaire scoring, descriptive reporting, assumption checks, and visualization helpers
- `Super Analyze` handles scanning, asking, selecting methods, and generating traceable scripts

When `rcode` does not yet expose a wrapper for a needed analysis step, the generated script may use a local fallback through established libraries such as `pingouin`, `scipy`, or `statsmodels`.

That fallback is still auditable because the generated script labels:
- which blocks are repository-backed
- which blocks are local fallback
- which statistical method is used
- why that method was chosen

## Plugin Scope

This repository contains both:
- the `rcode` Python package
- the `Super Analyze` plugin and workflow design

If you want the package-level documentation for `rcode` itself, see [README-rcode.md](C:\Users\adminroot\Documents\GitHub\vibe_example\README-rcode.md).

## Notes

- The plugin is intended for human-in-the-loop research workflows, not blind automation.
- Auto-detection is a recommendation, not ground truth.
- The most important review artifact is always the generated script.
