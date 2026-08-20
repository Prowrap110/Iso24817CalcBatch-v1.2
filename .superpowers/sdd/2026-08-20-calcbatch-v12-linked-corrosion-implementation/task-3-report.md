# Task 3 Report: Adapt One Main Row and Its Candidate Results

## Scope delivered

- Added `CandidateCalculation` and ordered `RowCalculation.candidate_calculations`.
- Extended `calculate_row()` with linked `individual_defects` input, all three
  external-corrosion length bases, conservative manual-mode remaining wall,
  governing B31G substrate credit, and the same optional Type A/Class 3 path.
- Mapped repair-zone, 3t interaction, candidate-count, and governing-candidate
  fields to the main output dictionary.
- Kept B31G candidate assessments available in the diagnostic output.
- Added behavior coverage for actual, independent, manual, Type A, and
  candidate-prefixed B31G warning paths.  Candidate warnings resolve through
  the existing permanent catalog entries; no assumption-only warning was added.

## TDD evidence

- RED: `pytest -q tests/test_batch_adapter.py -k 'manual or independent or actual'`
  produced 3 expected failures: missing repair-zone outputs for actual and
  independent modes, plus an unsupported `individual_defects` argument for
  manual mode.
- GREEN: the same focused adapter set passed after the adapter boundary change.
- Focused warning behavior: candidate-prefixed Original-B31G fallback and
  structural warnings resolve to `W011`, `W013` in candidate worksheet order.

## Verification

- `pytest -q tests/test_engine_corrosion_v12.py tests/test_engine_batch_hardening.py tests/test_batch_adapter.py tests/test_warning_catalog.py tests/test_batch_status.py`
  — 54 passed.
- `git diff --check` — passed.
- `PYTHONPATH=. pytest -q` — 160 passed, 96 failed outside Task 3 scope.

## Full-suite boundary

The canonical schema from Task 2 is ahead of the unmodified workbook/template
and processor consumers.  The first and dominant cause is
`workbook_template._HEADER_NOTES['Defect Length Basis']` raising `KeyError`
while it still renders the old main-row headers; that cascades to template,
processor, app-smoke, acceptance, and snapshot tests.  A separate preexisting
cost-contract expectation still assumes `Remaining Wall [mm]` immediately
follows `Defect Length [mm]`, rather than the new schema fields.  These 96
failures are intentionally left for Tasks 4-6.

Running plain `pytest -q` additionally has 11 collection errors for
`tests/engine/*` because its import path omits the repository root; the
`PYTHONPATH=.` run above is the complete executable suite result.
