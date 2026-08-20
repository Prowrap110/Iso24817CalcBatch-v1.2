# Task 1 report — compact CalcBatch v1.2 results

## Scope completed

- Replaced the public main-sheet output tuple with the exact nine requested headers.
- Preserved the former wide eight-sheet v1.2 tuple as
  `HISTORICAL_V12_OUTPUT_HEADERS` and accepts it only with the exact eight-sheet
  order and headings.  The historical contract has `is_legacy=False`, so its
  linked-corrosion fields are retained rather than legacy-normalized.
- Kept five-, six-, and seven-sheet legacy uploads accepted.
- Rebuilt results into the narrow controlled template.  Rich calculation output
  remains in the in-memory `RowCalculation` objects.
- Changed warning aggregation and Summary status/method/review counts to read
  those in-memory calculations.  Individual Defects warnings continue to be
  collected from their scalar detail cells.
- Removed main-sheet status conditional formatting and wide diagnostic-only
  styling.

## TDD evidence

RED:

- `python3 -m pytest -q tests/test_batch_schema.py -x` failed because the old
  wide `OUTPUT_HEADERS` began with `Source Excel Row`.
- `python3 -m pytest -q tests/test_workbook_template.py -x` failed because the
  old template retained diagnostic headers.
- The new in-memory warning/Summary parity test failed with the intentionally
  absent main warning aggregation: `Warnings!A4` remained the no-warning
  message instead of `W018`.

GREEN / verification:

- `python3 -m pytest -q tests/test_batch_schema.py` — 5 passed.
- `python3 -m pytest -q tests/test_legacy_v12_upgrade.py` — 5 passed.
- `python3 -m pytest -q tests/test_workbook_template.py -k 'compact_output_columns_do_not_include_diagnostic_json or canonical_headings_and_a_filterable_compact_table'` — 2 passed.
- `python3 -m pytest -q tests/test_workbook_processor.py -k compact_main_sheet_keeps_warning_and_summary_aggregation_in_memory` — 1 passed.
- `python3 -m py_compile ...` for all Task 1 production and test modules — passed.
- `python3 -m pytest --collect-only -q tests/test_workbook_processor.py` — 87 tests collected.
- `git diff --check` — passed.

## Scope boundary / concern

The Task 1 plan's illustrative `A1:AC151` assertion conflicts with Task 3's
explicit ownership of the 150-row limit.  Task 1 retains the existing 500-row
extent, so its compact main table is `A1:AC501`; Task 3 changes it to
`A1:AC151`.  This avoids partially applying the separate 150/150 release task.

The complete required focused command includes existing large 501/2,000-row
processor cases and exceeded the environment's 30-second command window here;
the focused new/changed tests and import/compile/collection checks above were
run successfully.  Task 3 must update the out-of-scope acceptance assertions
that intentionally still inspect removed main diagnostic columns.

## Fix round 1 — reviewer findings

RED:

- `python3 -m pytest -q tests/test_workbook_processor.py -k formula_anywhere_in_the_controlled_workbook_is_rejected -x` failed for `Batch Input & Results!AY501`: expected `FORMULA_NOT_ALLOWED`, actual `INVALID_INPUT_HEADERS`.

Changes:

- Moved formula scanning ahead of header/structure validation in
  `inspect_workbook`, preserving formula-anywhere safety priority even when a
  sparse off-table formula expands the sheet dimension.
- Replaced the stale main status-formatting test: the main sheet now asserts no
  `containsText` status rules, while Individual Defects retains all five status
  rules.
- Removed the unused `linked_detail_rows` assignment.

GREEN / verification:

- Formula-anywhere regression parametrization — 2 passed.
- Individual Defects-only status-formatting regression — 1 passed.
- `py_compile` for changed production/test modules — passed.
- `git diff --check` — passed.
- A full `tests/test_workbook_template.py` invocation was started as requested
  but again crossed the environment's 30-second command limit before a final
  summary could be returned; the targeted regression passed independently.
