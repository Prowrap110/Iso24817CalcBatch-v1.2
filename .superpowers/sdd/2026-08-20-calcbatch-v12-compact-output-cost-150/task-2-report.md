# Task 2 report — Quantity and Total Amount

## Scope delivered

- Extended the protected Cost Calculation table through column X with editable,
  highlighted Quantity (W) and locked Total Amount (X).
- Added the exact controlled Total Amount formula
  `=IF(OR(Vr="",Wr=""),"",Vr*Wr)` and expanded the formula allowlist to U, V,
  and X only.
- Added non-negative decimal validation across the current intermediate
  `W6:W505` range, derived from `COST_FIRST_DATA_ROW` and
  `COST_LAST_DATA_ROW` so Task 3 can atomically reduce the range with its
  limits change.
- Rejects negative, Boolean, text, non-finite, formula, and out-of-range
  Quantity values; whitespace-only Quantity is rebuilt as blank.
- Preserves valid Quantity by compact Cost row ordinal during a trusted
  re-upload; all engineering cells and controlled formulas are regenerated.

## TDD evidence

Initial formula/template contract test run was RED as required:

```text
python3 -m pytest -q tests/test_cost_calculation.py tests/test_workbook_template.py -k 'cost or commercial'
4 failed, 2 passed, 17 deselected
```

The failures were the missing Quantity/Total Amount headers, missing Total
Amount formula helper, missing X allowlist entry, and missing W template
protection/highlight/validation.

Focused GREEN checks completed:

```text
python3 -m pytest -q tests/test_cost_calculation.py tests/test_workbook_template.py -k 'cost or commercial'
6 passed, 17 deselected

python3 -m pytest -q tests/test_workbook_processor.py -k 'cost_quantity or processed_cost_quantity'
11 passed, 87 deselected

python3 -m pytest -q tests/test_workbook_processor.py::test_whitespace_only_cost_quantity_rebuilds_as_a_true_blank
1 passed

python3 -m pytest -q tests/test_workbook_processor.py::test_processed_cost_sheet_maps_requested_values_and_formulas tests/test_workbook_processor.py::test_processed_cost_sheet_uses_one_compact_row_per_populated_defect tests/test_workbook_processor.py::test_processed_cost_table_filter_covers_every_compact_row tests/test_workbook_processor.py::test_cleared_processed_defect_ignores_stale_exact_cost_formulas
4 passed

python3 -m pytest -q tests/test_full_batch_acceptance.py
5 passed
```

`git diff --check` passed.

## Concern

The local terminal wrapper detached long processor-suite executions after its
30-second output window, so the complete combined four-file command was not
recorded as one final result. The focused Cost/Quantity/re-upload checks,
affected existing processor checks, and full batch acceptance test are green.

## Fix round 1 — former A:V Cost contract compatibility

Reviewer reproduction showed that the former exact Cost header contract
(`20 engineering fields`, `Cost`, `Price`) was rejected as
`INVALID_COST_HEADERS` even when paired with a legitimate historical wide
eight-sheet v1.2 source or a legitimate legacy seven-sheet-with-Cost source.

Added faithful fixtures that freeze the old Cost shape: `A1:V1`, `A5:V6`, the
former 22 headers, and exact previously generated U/V formulas. The initial
regression run was RED as expected:

```text
python3 -m pytest -q tests/test_legacy_v12_upgrade.py::test_former_cost_contract_upgrades_only_recognized_historical_sources
2 failed
```

Both failures were the expected `INVALID_COST_HEADERS` rejection.

The minimal fix accepts only that exact former header tuple when the recognized
upload contract is either the historical wide eight-sheet v1.2 contract or the
legacy seven-sheet-with-Cost contract. Current compact sources remain strict
A:X, and arbitrary headings still fail. Every accepted former contract rebuilds
into the trusted A:X sheet with blank Quantity and regenerated U/V/X formulas.

GREEN evidence:

```text
python3 -m pytest -q tests/test_legacy_v12_upgrade.py::test_former_cost_contract_upgrades_only_recognized_historical_sources tests/test_legacy_v12_upgrade.py::test_current_compact_source_rejects_former_cost_contract
3 passed

python3 -m pytest -q tests/test_workbook_processor.py::test_changed_cost_heading_is_a_workbook_error tests/test_workbook_processor.py::test_processed_cost_formulas_and_commercial_inputs_are_safe_to_reupload
2 passed
```
