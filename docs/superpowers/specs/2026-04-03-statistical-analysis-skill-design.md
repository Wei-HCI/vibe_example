# Statistical Analysis Workflow Skill — Design Spec

**Date:** 2026-04-03
**Status:** Approved
**Scope:** rCode (vibe_example) project only

## Positioning

**Statistical analysis workflow orchestrator** — not an auto-analyzer.
Responsible for: scanning, recommending, asking, generating scripts, executing, summarizing.

## Target Users

Designed for both statistics-savvy researchers and newcomers. Defaults assume
statistical knowledge but provides brief explanations and recommendation rationale
so newcomers can follow along.

## Invocation

```
/statistical-analysis path/to/data.csv
```

User provides a data file path (CSV or Excel). The skill reads the file and begins
the workflow.

## Workflow Phases

### Phase 1: Data Scan & Identification (automatic)

Read the file and output a **structured detection report**:

```
Detected questionnaire: IPQ
Confidence: HIGH
Evidence:
  - Found columns SP/INV/REAL
  - Found typical IPQ item text patterns
  - Participants appear across 3 conditions (repeated)
Pending confirmation:
  - Questionnaire type
  - Subject ID column
  - Condition column
  - Dependent variables
  - Design type (within/between, 2x2 / 2x3 / one-way)
```

#### Stop Conditions

The skill MUST stop and ask the user (not proceed automatically) when:

- Questionnaire identification confidence is LOW
- Cannot find a clear subject ID column
- Cannot find a condition column
- Participants have incomplete condition coverage
- Column mapping does not match scoring function defaults
- Inferred design is ambiguous or not unique
- Multi-factor design exceeds current rule coverage

### -> Confirmation Node 1

User confirms or corrects: questionnaire type, subject ID, condition column,
dependent variables, and experimental design.

### Phase 2: Preprocessing (automatic)

- Call rCode scoring functions (`process_ipq`, `process_ssq`, `process_sus`, etc.)
- Handle missing values
- Export `cleaned_scored.csv`

### Phase 3: Descriptive Statistics (automatic)

- Call `report_mean_and_sd()` per condition
- Display summary table

### Phase 4: Assumption Checks (automatic)

Run and display results for:

- Normality: Shapiro-Wilk per group
- Sphericity: Mauchly (when >= 3 within-subjects conditions)
- Homogeneity of variance: Levene (for between-subjects designs)

Output a **structured recommendation card per DV**:

```
DV: IPQ_SP
Recommended method: Repeated-measures ANOVA
Rationale:
  - 3-condition within-subjects design
  - All groups pass normality (all p > .05)
  - Sphericity OK (W=0.94, p=.405)
Alternative: Friedman test
Risk note: If you prefer robust analysis, switch to Friedman
```

```
DV: IPQ_REAL
Recommended method: Friedman test
Rationale:
  - SVR group violates normality (p=.007)
Alternative: rm ANOVA (if ignoring violation)
```

### -> Confirmation Node 2

User reviews each DV's recommendation card and confirms or overrides the method
choice per DV. This is the most critical human-in-the-loop point.

### Phase 5: Main Analysis (automatic)

Method selection rules based on confirmed design:

| Design | Parametric | Non-parametric |
|--------|-----------|----------------|
| 2 conditions, within | Paired t-test | Wilcoxon signed-rank |
| 2 conditions, between | Independent t-test | Mann-Whitney U |
| >= 3 conditions, within | rm ANOVA | Friedman |
| >= 3 conditions, between | One-way ANOVA | Kruskal-Wallis |
| Multi-factor | Two-way ANOVA | ART (Aligned Rank Transform) |

### Phase 6: Post-hoc Analysis (automatic, if omnibus significant)

- Holm-corrected pairwise comparisons
- Effect size computation (Cohen's d / rank-biserial r)
- Only runs when omnibus p < .05

### -> Confirmation Node 3

User reviews omnibus results and decides whether to proceed with visualization
and report generation.

### Phase 7: Output (script-centric)

Output priority (script is the auditable core):

1. **`analyze_xxx.py`** — Complete analysis script with:
   - Prompt 1 style traceability comments per block
   - Each block annotates: repository function used, statistical method,
     why appropriate, fallback rule
   - Labels which steps are `repository-backed` vs `local fallback`
   - Records each DV's final method choice
2. **`cleaned_scored.csv`** — Preprocessed data
3. **`summary.txt`** — Statistical results with method traceability
4. **`figures/*.png`** — Publication-ready visualizations via rCode plot functions

## Confirmation Nodes Summary

| Node | When | What to confirm |
|------|------|-----------------|
| 1 | After data scan | Questionnaire type, ID col, condition col, DVs, design |
| 2 | After assumption checks | Recommended method per DV (structured cards, can override) |
| 3 | After main analysis | Omnibus results acceptable, proceed to plots/report |

## Dependencies

- **rCode functions used:** `process_ipq`, `process_ssq`, `process_sus`,
  `check_assumptions_for_anova`, `report_mean_and_sd`,
  `gg_withinstats_with_normality_check`, `gg_betweenstats_with_normality_check`
- **Local fallback (pingouin):** `pg.rm_anova`, `pg.friedman`, `pg.pairwise_tests`,
  `pg.sphericity`, `pg.normality`
- **Local fallback (scipy):** `scipy.stats.shapiro`, `scipy.stats.levene`,
  `scipy.stats.ttest_rel`, `scipy.stats.wilcoxon`, `scipy.stats.mannwhitneyu`

## Key Principles

1. **Script is the auditable core** — reports and figures can be regenerated from it
2. **Auto-detect, human-confirm** — never treat detection as ground truth
3. **Structured recommendations** — not just natural language, but card-format with
   rationale, alternative, and risk note
4. **3 confirmation nodes** — enough for control, not so many it's annoying
5. **Traceability** — every block in the output script documents what it does and why
