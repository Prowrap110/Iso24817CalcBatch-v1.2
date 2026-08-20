# Task 3 report — 150-row CalcBatch v1.2 contract

## Scope completed

- Set both controlled repair limits to 150 records.
- The blank template now has main `A1:AC151`, detail `A1:X151`, Cost Quantity
  validation `W6:W155`, and generated maximum Cost coverage `A5:X155`.
- Rejects the first populated main or detail input at Excel row 152.
- Recalibrated the parsed-cell ceiling from a measured 11,711-cell blank
  template to 20,000 cells, retaining more than 70 percent headroom. Dense
  safety tests derive the excess fixture from the production ceiling.
- Updated the Streamlit guidance, workbook Instructions, README, deployment
  checklist, acceptance generator wording, and acceptance assertions for the
  nine-output, 150/150, Quantity, and Total Amount contract.
- Deployment guidance now targets only the existing `feature/linked-corrosion-v12`
  public deployment at `https://iso24817calcbatch-prowrapv12.streamlit.app`.

## TDD evidence

1. Added literal 150-row table/validation and row-152 rejection assertions.
   The initial focused run was RED with seven expected failures: the old
   template still exposed 500/2,000 ranges and accepted row 152.
2. After the shared-limit change, the boundary subset was GREEN: `9 passed`.
3. Added app and workbook guidance assertions; their initial run was RED with
   two expected guidance failures. The updated guidance subsets are GREEN.

## Verification evidence

- `python3 -m pytest -q tests/test_workbook_processor.py -k 'maximum_processed_cost_region or exactly_150 or more_than_150 or populated_input_beyond or detail_rows_are_kept'`
  — `6 passed, 94 deselected`.
- Template boundary/guidance subset — `5 passed, 15 deselected`.
- App guidance/formula-help subset — `2 passed, 10 deselected`.
- Acceptance workbook integration — `1 passed, 4 deselected`.
- `git diff --check` — clean.

An earlier mandated six-file focused run reached `68 passed` before exposing
two test-only missing imports in dense foreign-XML ceiling tests. Those imports
were fixed. A second complete duplicate was intentionally not started because
another identical focused run was active; the passing focused checks above
cover the repaired boundaries, template/UI, and acceptance behavior.

## Concerns

- No final XLSX artifacts were generated, no `outputs/` path was changed, and
  no push or deployment was performed.
- The complete six-file focused run should be performed once by the release
  verification task after this commit, avoiding concurrent duplicate runs.

## Fix round 1 — current-template release contract

- The active app, workbook Instructions and header comment, README, deployment
  checklist, design, and implementation plan now require the current
  `PROWRAP_CalcBatch_v1.2_Template.xlsx` 150/150 template.
- Older 500/2,000-row, five-, six-, seven-sheet, and historical-wide templates
  are stated as not supported or guaranteed. Retained reader code and its
  tests remain best-effort implementation detail, not a release promise.
- Corrected the blank-template parsed-cell measurement to 11,711 in both the
  production ceiling comment and this report; the 20,000 ceiling is unchanged.
- RED observed after changing the current-template guidance tests: two expected
  failures showed the old app migration copy and workbook upgrade instruction.
- GREEN after the guidance update:
  `python3 -m pytest -q tests/test_app_smoke.py tests/test_workbook_template.py -k 'current_template or contains_no_formulas or long_dent_instruction'`
  — `3 passed, 29 deselected`.
