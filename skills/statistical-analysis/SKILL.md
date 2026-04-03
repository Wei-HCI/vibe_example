---
name: statistical-analysis
description: Use when user invokes /statistical-analysis with a data file path (CSV/Excel). Orchestrates a complete statistical analysis workflow for rCode questionnaire data (IPQ, SSQ, NASA-TLX, etc.) with auto-detection, human confirmation at key nodes, and traceable script generation.
---

# Super Analyze — Statistical Analysis Workflow

A workflow orchestrator for experimental data analysis using rCode. Scans data, recommends methods, asks for confirmation at critical decision points, and generates a fully traceable analysis script.

**This is NOT an auto-analyzer.** It detects, recommends, and asks — the human decides.

## Invocation

```
/statistical-analysis path/to/data.csv
```

## Checklist

You MUST create a task for each phase and complete them in order:

1. **Data scan & identification** — read file, detect questionnaire/design/variables
2. **User confirmation 1** — present structured detection report, get approval
3. **Preprocessing & descriptive stats** — score questionnaire, export cleaned CSV, summarize
4. **Assumption checks & method recommendation** — normality/sphericity/homogeneity, output recommendation cards
5. **User confirmation 2** — user confirms or overrides method per DV
6. **Main analysis & post-hoc** — run omnibus + pairwise if significant
7. **User confirmation 3** — user reviews results, decides to proceed
8. **Generate outputs** — script, cleaned CSV, summary, figures

## Phase 1: Data Scan & Identification

Read the user-provided file. Output a **structured detection report**:

```
Detected questionnaire: [IPQ / SSQ / NASA-TLX / Unknown]
Confidence: [HIGH / MEDIUM / LOW]
Evidence:
  - [list concrete evidence: column names, item text, scoring patterns]
Detected:
  - Subject ID column: [column name]
  - Condition column: [column name]
  - Conditions found: [list]
  - Participants: [N]
  - Design: [within / between / mixed], [2-condition / 3-condition / NxM]
  - Dependent variables: [list]
```

### Stop Conditions — MUST stop and ask user when:

- Questionnaire identification confidence is LOW
- Cannot find a clear subject ID column
- Cannot find a condition column
- Participants have incomplete condition coverage
- Column mapping does not match scoring function defaults
- Inferred design is ambiguous
- Multi-factor design exceeds current rule coverage

**Never guess past a stop condition. Ask.**

## Confirmation Node 1

Present the detection report. User confirms or corrects:
- Questionnaire type
- Subject ID column
- Condition column
- Dependent variables
- Experimental design (within/between, factor structure)

Use AskUserQuestion with the detected values as recommended options.

## Phase 2-3: Preprocessing & Descriptive Statistics

After confirmation:

1. Call the appropriate rCode scoring function:
   - IPQ → `process_ipq()`
   - SSQ → `process_ssq()`
   - SUS → `process_sus()`
   - NASA-TLX → manual composite scoring (no rCode function)
   - Unknown → skip scoring, use raw columns
2. Export `cleaned_scored.csv`
3. Call `report_mean_and_sd(data, iv=condition_col, dv=dv)` for each DV
4. Display summary table

## Phase 4: Assumption Checks & Method Recommendation

Run assumption checks:
- **Normality:** `pg.normality(data, dv=dv, group=condition)` per DV
- **Sphericity:** `pg.sphericity()` when >= 3 within-subjects conditions
- **Homogeneity:** `scipy.stats.levene()` for between-subjects designs

Also call `check_assumptions_for_anova()` from rCode as a coarse screen.

Output one **recommendation card per DV**:

```
┌─────────────────────────────────────────────┐
│ DV: [name]                                  │
│ Recommended method: [method name]           │
│ Rationale:                                  │
│   · [reason 1]                              │
│   · [reason 2]                              │
│ Alternative: [fallback method]              │
│ Risk note: [when to consider the alternative]│
└─────────────────────────────────────────────┘
```

## Confirmation Node 2

Present all recommendation cards. User confirms or overrides the method for each DV.

This is the **most critical** human-in-the-loop point. Use AskUserQuestion per DV
with the recommended method as the first option.

## Phase 5-6: Main Analysis & Post-hoc

Execute the confirmed methods:

| Design | Parametric | Non-parametric |
|--------|-----------|----------------|
| 2 conditions, within | Paired t-test | Wilcoxon signed-rank |
| 2 conditions, between | Independent t-test | Mann-Whitney U |
| >= 3 conditions, within | rm ANOVA | Friedman |
| >= 3 conditions, between | One-way ANOVA | Kruskal-Wallis |
| Multi-factor | Two-way ANOVA | ART |

If omnibus p < .05:
- Run Holm-corrected pairwise comparisons
- Compute effect sizes (Cohen's d or rank-biserial r)

## Confirmation Node 3

Present omnibus results (and post-hoc if run). User decides whether to proceed
with visualization and report generation.

## Phase 7: Generate Outputs

Output priority — **script is the auditable core**:

### 1. `analyze_xxx.py` (primary output)

Every code block MUST have a traceability comment:

```python
# Repository function(s): rcode.process_ipq()
# Statistical method: deterministic questionnaire scoring
# Why appropriate: repository defines IPQ scoring rules
# Fallback rule: none; direct repository function
```

```python
# Repository function(s): none
# Statistical method: repeated-measures ANOVA (pingouin.rm_anova)
# Why appropriate: 3+ within-subjects conditions, normality and sphericity OK
# Fallback rule: local implementation; rCode does not expose rm_anova wrapper
```

### 2. `cleaned_scored.csv`
### 3. `summary.txt` — includes method traceability per DV
### 4. `figures/*.png` — via `gg_withinstats_with_normality_check()` or `gg_betweenstats_with_normality_check()`

## Red Flags - STOP

- You are about to run an analysis without user confirming the method → STOP
- You detected the questionnaire type but confidence is LOW and you didn't ask → STOP
- You are writing the script without traceability comments → STOP
- You chose parametric when assumption checks failed and user didn't override → STOP
- You are running post-hoc without a significant omnibus result → STOP

All of these mean: go back to the relevant confirmation node.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Treating auto-detection as ground truth | Always present as recommendation, let user confirm |
| Running rm ANOVA when normality violated | Check per-group normality, not just overall |
| Forgetting sphericity check | Required for >= 3 within-subjects conditions |
| Skipping traceability comments | Every block needs repository-backed vs fallback annotation |
| Generating report without script | Script is primary output; report is secondary |
