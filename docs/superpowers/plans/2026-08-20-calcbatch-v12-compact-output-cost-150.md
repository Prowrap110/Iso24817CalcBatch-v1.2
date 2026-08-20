# CalcBatch v1.2 Compact Output, Commercial Quantity, and 150-Row Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a compact CalcBatch v1.2 workbook with exactly nine main outputs, quantity-based total amounts, and 150-row main/detail limits.

**Architecture:** Preserve the rich engine result internally while narrowing only the controlled main worksheet boundary. Summary and warning aggregation consume in-memory calculations instead of removed worksheet diagnostics. Historical workbook contracts are recognized explicitly and always rebuilt into the new narrow trusted template.

**Tech Stack:** Python 3.11, Streamlit, openpyxl, pytest, Git, GitHub, Streamlit Community Cloud.

**Spec:** `docs/superpowers/specs/2026-08-20-calcbatch-v12-compact-output-cost-150-design.md`

## Global Constraints

- Change only CalcBatch v1.2 on `feature/linked-corrosion-v12`.
- Do not change v1.1, the earlier CalcBatch repository, or their deployments.
- `Batch Input & Results` has the existing 20 inputs followed by exactly the nine outputs listed in the spec.
- Maximum populated main rows and Individual Defects rows are each 150.
- Quantity is an editable non-negative Cost input; Total Amount is `Quantity * Price`.
- No engineering equation or status-classification rule changes.
- Use tests first and observe each new test fail before production edits.
- Preserve controlled legacy uploads within the new row limits.

---

### Task 1: Narrow the main result boundary without losing warnings or Summary logic

**Files:**
- Modify: `batch_schema.py`
- Modify: `workbook_processor.py`
- Modify: `workbook_template.py`
- Modify: `tests/test_batch_schema.py`
- Modify: `tests/test_workbook_template.py`
- Modify: `tests/test_workbook_processor.py`
- Modify: `tests/test_legacy_v12_upgrade.py`
- Modify: `tests/helpers.py`

**Interfaces:**
- Consumes: rich `RowCalculation.outputs` from `batch_adapter.calculate_row`.
- Produces: exact nine-member `OUTPUT_HEADERS`; explicit historical wide-eight-sheet contract; `_write_warnings_sheet(workbook, calculations)` and `_write_summary(..., calculations)` behavior independent of removed main columns.

- [ ] **Step 1: Add exact failing schema and workbook tests**

```python
assert OUTPUT_HEADERS == (
    'Wall Loss [%]', 'Required Structural Thickness [mm]', 'Installed Plies',
    'Total Repair Length [mm]', 'Cloth Band Count',
    'Procurement Axial Length [mm]', 'Fabric Area [m2]',
    'Epoxy Mass [kg]', 'Repair Zone Length [mm]',
)
assert tuple(cell.value for cell in data[1]) == INPUT_HEADERS + OUTPUT_HEADERS
assert data.tables['BatchRows'].ref == 'A1:AC151'
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python3 -m pytest -q tests/test_batch_schema.py tests/test_workbook_template.py tests/test_legacy_v12_upgrade.py`

Expected: failures show the current wide output tuple/table and missing historical-wide contract.

- [ ] **Step 3: Implement the narrow schema and compatibility contract**

Freeze the pre-narrow wide v1.2 tuple under a historical name, set current
`OUTPUT_HEADERS` to the exact nine literals, select upload contracts by sheet
order plus exact headings, and preserve `is_legacy=False` for the historical
wide eight-sheet contract.

- [ ] **Step 4: Add failing warning/Summary parity tests**

Create a calculation that produces a warning and a review status; assert the
main header has no diagnostic columns while Warnings and Summary still contain
the expected warning row and status/method counts.

- [ ] **Step 5: Run the parity tests and verify RED**

Run the exact new tests in `tests/test_workbook_processor.py`; expect removed
header lookups in `_write_warnings_sheet` or `_write_summary` to fail.

- [ ] **Step 6: Refactor aggregation to in-memory calculations**

Pass the `calculations` mapping from `process_workbook` into warning and Summary
writers. Read status, method, and compliance warnings from each
`RowCalculation`, while retaining detail warning collection from scalar detail
rows. Remove main status conditional formatting and obsolete wide-column
styling.

- [ ] **Step 7: Run focused tests GREEN and commit**

Run: `python3 -m pytest -q tests/test_batch_schema.py tests/test_workbook_template.py tests/test_workbook_processor.py tests/test_legacy_v12_upgrade.py tests/test_warning_catalog.py`

Commit only Task 1 files with message: `feat: compact CalcBatch v1.2 result columns`.

### Task 2: Add Quantity and Total Amount to the protected Cost sheet

**Files:**
- Modify: `cost_calculation.py`
- Modify: `workbook_template.py`
- Modify: `workbook_processor.py`
- Modify: `tests/test_cost_calculation.py`
- Modify: `tests/test_workbook_template.py`
- Modify: `tests/test_workbook_processor.py`
- Modify: `tests/test_full_batch_acceptance.py`

**Interfaces:**
- Consumes: current compact populated-main-row order and Cost source mapping.
- Produces: `Quantity` column W, `Total Amount` column X, `total_amount_formula(row)`, strict U/V/X formula allowlist, and safe Quantity re-upload.

- [ ] **Step 1: Add failing formula and template tests**

```python
assert COST_TABLE_HEADERS[-4:] == ('Cost', 'Price', 'Quantity', 'Total Amount')
assert total_amount_formula(6) == '=IF(OR(V6="",W6=""),"",V6*W6)'
assert cost['W6'].protection.locked is False
assert cost['X6'].protection.locked is True
```

- [ ] **Step 2: Run the Cost tests and verify RED**

Run: `python3 -m pytest -q tests/test_cost_calculation.py tests/test_workbook_template.py -k 'cost or commercial'`.

- [ ] **Step 3: Implement the four-column commercial tail**

Use named Cost/Price/Quantity/Total column indexes. Extend the Cost table and
merged title through X, highlight and unlock W6:W155, add non-negative decimal
validation, and write the exact blank-safe Total Amount formula in X.

- [ ] **Step 4: Add failing validation and re-upload tests**

Test blank, zero, positive, negative, Boolean, text, NaN, infinity, formula
injection in W, exact formula allowlisting in X, and preservation of W values
through `process_workbook` re-upload.

- [ ] **Step 5: Run new processor tests and verify RED**

Run the exact new Cost tests in `tests/test_workbook_processor.py`; expect
Quantity not to persist and X not to contain an allowed formula.

- [ ] **Step 6: Implement strict Quantity processing**

Validate W values after formula validation, normalize whitespace to blank,
preserve valid W values by compact row position, regenerate A:V and X, and keep
all non-Quantity result cells locked.

- [ ] **Step 7: Run focused tests GREEN and commit**

Run: `python3 -m pytest -q tests/test_cost_calculation.py tests/test_workbook_template.py tests/test_workbook_processor.py tests/test_full_batch_acceptance.py`.

Commit only Task 2 files with message: `feat: add quantity totals to batch costs`.

### Task 3: Enforce 150/150 limits and update the user-facing contract

**Files:**
- Modify: `batch_schema.py`
- Modify: `workbook_processor.py`
- Modify: `workbook_template.py`
- Modify: `app.py`
- Modify: `README.md`
- Modify: `DEPLOYMENT.md`
- Modify: `scripts/create_acceptance_workbook.py`
- Modify: boundary and acceptance tests under `tests/`

**Interfaces:**
- Consumes: current schema/table/formula helpers from Tasks 1 and 2.
- Produces: 150-row main/detail tables and validations, 150-row Cost region, updated guidance, and a representative acceptance source workbook.

- [ ] **Step 1: Add literal boundary tests and verify RED**

Test exactly 150 populated main rows and detail rows as accepted, with the first
populated input at Excel row 152 rejected. Assert `A1:AC151`, `A1:X151`, Cost
row 155, and no validation or formula region beyond those limits.

Run the exact boundary tests; expect current 500/2000 extents.

- [ ] **Step 2: Change both controlled limits to 150**

Set `MAX_ROWS = 150` and `MAX_DETAIL_ROWS = 150`. Recalibrate the parsed-cell
ceiling with measured conservative headroom and update dense-package tests to
derive their excess case from the production ceiling.

- [ ] **Step 3: Update app, Instructions, README, deployment checklist, and acceptance generator**

State the exact nine main outputs, 150/150 limits, editable Quantity, and
controlled Total Amount formula. Keep all product names and v1.2 filenames.

- [ ] **Step 4: Run focused boundary/UI/acceptance tests GREEN**

Run: `python3 -m pytest -q tests/test_batch_schema.py tests/test_workbook_template.py tests/test_workbook_processor.py tests/test_app_smoke.py tests/test_full_batch_acceptance.py tests/test_legacy_v12_upgrade.py`.

- [ ] **Step 5: Commit**

Commit only Task 3 files with message: `feat: cap CalcBatch v1.2 at 150 repairs`.

### Task 4: Verify the workbook artifacts and public release

**Files:**
- Create: `outputs/PROWRAP_CalcBatch_v1.2_Template.xlsx`
- Create: `outputs/PROWRAP_CalcBatch_v1.2_Processed.xlsx`
- Create or update: `docs/superpowers/reports/2026-08-20-calcbatch-v12-compact-release.md`

**Interfaces:**
- Consumes: committed production generator and processor from Tasks 1-3.
- Produces: verified controlled artifacts, release evidence, pushed public branch, and a healthy live Streamlit app.

- [ ] **Step 1: Run complete automated verification**

Run: `python3 -m pytest -q`; require zero failures. Run `git diff --check` and
confirm only intended files plus untracked release outputs.

- [ ] **Step 2: Generate both workbooks through production paths**

Run the spreadsheet artifact-operation marker exactly once immediately before
generation. Generate the template and a processed representative workbook from
the production functions; do not hand-edit controlled metadata.

- [ ] **Step 3: Inspect calculations, formulas, controls, and every sheet**

Use the spreadsheet artifact runtime to inspect key ranges and render all eight
sheets. Confirm exact table/filter ranges, protection, Quantity validation,
U/V/X formulas only, no formula errors, correct Total Amount after a temporary
commercial recalculation, and clean processed-workbook re-upload.

- [ ] **Step 4: Independent review and final commit**

Dispatch a read-only whole-branch reviewer. Address any Critical or Important
finding with a failing regression first. Commit the release report and intended
code/docs only; never stage `outputs/` broadly.

- [ ] **Step 5: Push and verify Streamlit**

Push `feature/linked-corrosion-v12` to the existing public GitHub repository.
Verify the exact remote commit. Allow Streamlit Community Cloud to redeploy,
then verify the live title, template download, 150-row workbook contract, and a
representative upload/calculate/download workflow at the existing public URL.

- [ ] **Step 6: Confirm isolation**

Read-only check that the v1.1 and earlier CalcBatch repositories/deployments
were not changed. Report the public URL, commit, tests, and final workbook
paths/hashes.
