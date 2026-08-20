# Task 4 report — Eight-sheet controlled template

## Delivered

- Added the controlled `Individual Defects` worksheet in the required third position, producing the exact eight-sheet order.
- Added protected `IndividualDefects` table `A1:O2001`, with only its five detail-input columns unlocked and frozen headers at `B2`.
- Added controlled named-list validations for all main selections, including `Defect Length Basis` through `I2:I501`, and the detail `Yes`/blank separation selection through `E2:E2001`.
- Routed dropdown ranges from semantic header lookup rather than fixed column letters.
- Added concise linked-corrosion instructions and retained existing blank-template, cost-sheet, protection, highlighting, Lists-hidden, 110 degC, 500 mm, and dent guidance behavior.

## Verification

- RED: `python3 -m pytest -q tests/test_workbook_template.py` failed before implementation because `Defect Length Basis` was missing template metadata and the linked-detail template did not exist.
- GREEN: `python3 -m pytest -q tests/test_workbook_template.py` — `18 passed`.
- Direct generated-workbook inspection: exact eight-sheet order; `IndividualDefects` is `A1:O2001`; detail input/output protection is `False`/`True`; validation ranges are `I2:I501` and `E2:E2001`; blank-template formula scan is empty.
- Rendered the generated workbook successfully with LibreOffice (36 pages); the renderer emitted font-cache warnings only.
- Broad regression: `python3 -m pytest -q` — `203 passed, 55 failed`. Failures are expected downstream pre-Task-5/6 consumers that reject `Individual Defects`, plus the Task-6 cost-source semantic mapping contract.

## Boundary retained

`tests/test_cost_calculation.py` still has one expected failure: it asserts the legacy cost-source order while `COST_SOURCE_HEADERS` currently follows positional slices after Task 2 inserted the new main inputs. Task 6 owns that semantic cost mapping; this Task 4 change does not modify it.
