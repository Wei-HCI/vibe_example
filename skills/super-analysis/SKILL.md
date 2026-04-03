---
name: super-analysis
description: Use when the user wants to analyze one CSV or Excel dataset with rcode-backed questionnaire scoring, assumption checks, method recommendation, and traceable script generation.
---

# Super Analyze

This skill is the short-form entry point for the Super Analyze workflow.

If the plugin command `/super-analysis:run` is available, prefer it because it
is written to use structured confirmation prompts. Use this skill when the user
calls `/super-analysis` directly.

## Invocation

```text
/super-analysis path/to/data.csv
```

If the user does not provide a dataset path, ask for one before continuing.

## Required Workflow

You must complete these phases in order:

1. Run the deterministic scan helper.
2. Present the scan report.
3. Get user confirmation on questionnaire, ID column, condition column, design,
   and dependent variables.
4. Run the deterministic recommendation helper.
5. Present the recommendation cards.
6. Get user confirmation on the method for each dependent variable.
7. Generate the analysis script and companion outputs.

## Helper Commands

Prefer the repository helpers over ad-hoc reasoning:

```powershell
.\myenv\Scripts\python.exe .\scripts\super_analyze.py scan <path>
```

```powershell
.\myenv\Scripts\python.exe .\scripts\super_analyze.py recommend <path>
```

If `.\myenv\Scripts\python.exe` does not exist, fall back to `python`.

## Phase 1: Scan

The scan report must include:

- detected questionnaire
- confidence
- concrete evidence
- subject ID column
- condition column
- design label
- dependent variables
- stop conditions

## Stop Conditions

Do not guess past these cases. Ask the user instead.

- Questionnaire confidence is low.
- Subject ID column is unclear.
- Condition column is unclear.
- The sheet looks like a wide or multi-block export.
- Participant condition coverage is inconsistent.
- The design is ambiguous.

## Phase 2: Recommendation

After the user confirms the scan, run the recommendation helper and present one
card per DV with:

- descriptive statistics by condition
- normality result per condition
- sphericity or Levene result when applicable
- recommended method
- alternative method
- rationale
- risk note

## Method Rules

Use these defaults unless the user overrides them:

| Design | Parametric | Non-parametric |
|--------|-----------|----------------|
| 2 conditions, within | Paired t-test | Wilcoxon signed-rank |
| 2 conditions, between | Independent t-test | Mann-Whitney U |
| >= 3 conditions, within | Repeated-measures ANOVA | Friedman |
| >= 3 conditions, between | One-way ANOVA | Kruskal-Wallis |
| Multi-factor | Two-way ANOVA | ART |

## Output Rules

The primary output is the script:

- `analyze_xxx.py`

Also generate when relevant:

- `cleaned_scored.csv`
- `summary.txt`
- `figures/*.png`

Every major code block in the generated script must label:

- repository function(s)
- statistical method
- why it is appropriate
- fallback rule

## Red Flags

Stop and correct the workflow if any of these happen:

- You are about to run omnibus analysis without user-confirmed methods.
- You are about to write the script without traceability comments.
- You are treating auto-detection as ground truth.
- You are using a parametric method after failed assumptions without user approval.
