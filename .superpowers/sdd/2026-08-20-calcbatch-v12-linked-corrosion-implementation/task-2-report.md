# Task 2 Report — Current and Legacy Workbook Schemas

## Scope completed

- Added immutable legacy main input/output header contracts and derived the
  current main inputs by inserting `Defect Length Basis` and `Repair Group ID`
  after `Defect Length [mm]`.
- Added the six current linked-corrosion main output headers, the 2,000-row
  detail limit, and the controlled detail input/output schemas.
- Added conditional external-corrosion main-row validation for the three exact
  defect-length bases, manual group IDs, and the mode-specific main remaining
  wall rule.
- Added individual-detail validation, including exact uploaded `Yes`
  confirmation before conversion to `True`.
- Added deterministic manual group linking with trimmed IDs, source-row order,
  duplicate main-group detection, orphan/ambiguous links, duplicate detail IDs,
  linked span/wall bounds, and row-local issues.

## RED/GREEN evidence

### Schema and main-row conditional validation

- RED: `python3 -m pytest -q tests/test_batch_schema.py tests/test_batch_validation.py`
  produced 4 failures: the detail-row maximum was absent, nonmanual repair
  group IDs were not rejected, and manual rows still required a main remaining
  wall.
- GREEN: the same command passed with `31 passed in 0.27s` after adding the
  schema contracts and conditional validation.

### Current output contract

- RED: `python3 -m pytest -q tests/test_batch_schema.py::test_current_outputs_keep_legacy_outputs_and_add_linked_corrosion_results`
  failed because the six linked-corrosion outputs were absent.
- GREEN: included in the later focused run below.

### Detail validation and group linking

- RED: `python3 -m pytest -q tests/test_batch_schema.py tests/test_batch_validation.py tests/test_batch_corrosion.py`
  stopped during collection with `ModuleNotFoundError: No module named 'batch_corrosion'`.
- GREEN: `python3 -m pytest -q tests/test_batch_schema.py tests/test_batch_validation.py tests/test_batch_corrosion.py`
  passed with `38 passed in 0.45s`.

## Full suite

- `python3 -m pytest -q` completed with `155 passed, 96 failed in 2.04s`.
- All failures are downstream legacy template/processor assumptions now exposed
  by the current v1.2 schemas. The first error is the expected
  `KeyError: 'Defect Length Basis'` in `workbook_template.py`'s legacy header
  guidance map; the remaining failures cascade from that template path or from
  fixed legacy column positions. Updating those rendering/processing paths is
  intentionally assigned to Tasks 4–6 and was excluded from this task.

## Files changed

- `batch_schema.py`
- `batch_validation.py`
- `batch_corrosion.py`
- `tests/helpers.py`
- `tests/test_batch_schema.py`
- `tests/test_batch_validation.py`
- `tests/test_batch_corrosion.py`

## Self-review

- Legacy headers remain materialized as untouched tuples; current input headers
  are built through a semantic insertion helper, rather than a positional
  rewrite.
- Group and defect IDs are normalized by trimming before linking; linked detail
  rows retain input tuple order rather than being sorted by ID.
- A detail error remains local to its source row and also invalidates only its
  unambiguous owning manual main row.
- The focused tests exercise real validators and linker behavior without mocks.

## Concerns / follow-up

- The planned template, processing, and cost-mapping tasks must consume the
  new headers before the full suite can return green. No rendering or processor
  code was changed here.
- Invalid partial detail rows are preserved as row-level validation issues;
  Task 5 must retain their raw Repair Group ID while parsing so that it can
  associate an invalid linked detail row with its manual main row whenever the
  association is unambiguous.
