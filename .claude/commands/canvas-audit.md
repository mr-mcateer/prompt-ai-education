# Canvas Audit

Run a full audit of Canvas course(s) to check for issues.

## Instructions

1. Load credentials via `tools/env_loader.py`.
2. For each target course, check:
   - Unpublished assignments that should be published
   - Missing rubrics on graded assignments
   - Duplicate module items
   - Assignments without due dates
   - Empty modules
3. Output a summary report to the terminal.
4. If `--fix` is passed in $ARGUMENTS, auto-fix simple issues (duplicates, publish state).

## Arguments
- $ARGUMENTS: Optional flags like `--fix` or specific course IDs
