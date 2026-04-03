---
description: Run the Super Analyze workflow with structured confirmation nodes
allowed-tools: Bash, Read, Write, AskUserQuestion
---

# Run Super Analyze

Treat the slash-command argument as the dataset path. If the user did not pass a
path, ask for it with `AskUserQuestion` before doing anything else.

## Goal

Guide one dataset through:
1. deterministic scan
2. structured human confirmation
3. deterministic method recommendation
4. structured method confirmation
5. traceable script generation

Use the repository helper CLI instead of re-detecting everything from scratch:

- `.\myenv\Scripts\python.exe .\scripts\super_analyze.py scan <path>`
- `.\myenv\Scripts\python.exe .\scripts\super_analyze.py recommend <path> ...`

If `.\myenv\Scripts\python.exe` does not exist, fall back to `python`.

## Phase 1

Run `scan` first and present:
- detected questionnaire
- confidence
- evidence
- subject ID column
- condition column
- design label
- dependent variables
- any stop conditions

## Confirmation Node 1

Use `AskUserQuestion` with structured options for:
- questionnaire type
- subject ID column
- condition column
- design acceptance

If the scan returned stop conditions, surface them clearly before asking.

## Phase 2

Run `recommend` with the user-confirmed values.

Present one card per dependent variable:
- descriptive statistics by condition
- normality outcome per condition
- sphericity or Levene result when applicable
- recommended method
- alternative method
- rationale
- risk note

## Confirmation Node 2

Use `AskUserQuestion` per dependent variable so the user can:
- accept the recommended method
- switch to the listed alternative

## Phase 3

After methods are confirmed:
- generate a traceable analysis script in the workspace root
- name it `analyze_<dataset_stem>.py`
- prefer repository functions when available
- use local fallback only where the repository has no wrapper

Every analysis block in the generated script must include:
- repository function(s)
- statistical method
- why the method is appropriate
- fallback rule

Also generate:
- `<dataset_stem>_cleaned_scored.csv` when preprocessing creates derived columns
- `<dataset_stem>_analysis_summary.txt`

## Guard Rails

- Do not skip the `scan` helper.
- Do not skip `AskUserQuestion` at either confirmation node.
- Do not run omnibus analysis without an explicit confirmed method per DV.
- If the design is ambiguous, stop and ask the user instead of guessing.
- If the repository lacks a wrapper, label the generated code as local fallback.
