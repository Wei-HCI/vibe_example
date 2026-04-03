# Super Analyze Workflow Design Spec

**Date:** 2026-04-03  
**Status:** Approved  
**Scope:** `rcode` / `vibe_example` only

## Positioning

Super Analyze is a workflow orchestrator, not a standalone statistics engine.

It is responsible for:

- scanning datasets
- detecting questionnaire and design hints
- asking for confirmation at decision nodes
- recommending methods
- generating traceable scripts and outputs

## Entry Points

Primary plugin command:

```text
/super-analysis:run path/to/data.csv
```

Skill alias:

```text
/super-analysis path/to/data.csv
```

## Workflow Phases

### Phase 1: Data Scan and Identification

The workflow reads the user-provided CSV or Excel file and outputs a structured
detection report containing:

- detected questionnaire
- confidence
- evidence
- subject ID column
- condition column
- conditions found
- participant count
- inferred design
- dependent variables
- stop conditions

### Confirmation Node 1

The user confirms or corrects:

- questionnaire type
- subject ID column
- condition column
- dependent variables
- experimental design

### Phase 2: Preprocessing

- Reuse `rcode` scoring helpers when available:
  - `process_ipq`
  - `process_ssq`
  - `process_sus`
- Use a local fallback only when the repository does not expose a wrapper.
- Export `cleaned_scored.csv` when derived columns are created.

### Phase 3: Descriptive Statistics

- Summarize each dependent variable by condition.

### Phase 4: Assumption Checks and Recommendation

Run and present:

- Shapiro-Wilk per group
- Mauchly when there are 3 or more within-subject conditions
- Levene for between-subject designs

Each dependent variable gets a recommendation card with:

- recommended method
- alternative method
- rationale
- risk note

### Confirmation Node 2

The user confirms or overrides the recommended method per dependent variable.

### Phase 5: Main Analysis

Default method mapping:

| Design | Parametric | Non-parametric |
|--------|-----------|----------------|
| 2 conditions, within | Paired t-test | Wilcoxon signed-rank |
| 2 conditions, between | Independent t-test | Mann-Whitney U |
| >= 3 conditions, within | Repeated-measures ANOVA | Friedman |
| >= 3 conditions, between | One-way ANOVA | Kruskal-Wallis |
| Multi-factor | Two-way ANOVA | ART |

### Phase 6: Output

Primary output:

- `analyze_xxx.py`

Secondary outputs:

- `cleaned_scored.csv`
- `summary.txt`
- `figures/*.png`

## Stop Conditions

The workflow must stop and ask the user when:

- questionnaire detection confidence is low
- subject ID is unclear
- condition column is unclear
- the sheet looks like a wide or multi-block export
- participant coverage is inconsistent
- the design is ambiguous

## Core Principle

The script is the auditable core. Everything else can be regenerated from it.
