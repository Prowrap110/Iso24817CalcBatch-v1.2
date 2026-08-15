# PROWRAP Batch Cost Calculation Sheet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a protected, formula-driven `Cost Calculation` worksheet with blank editable commercial inputs, selected engineering columns, dynamic Cost and Price, safe re-upload, and live Streamlit deployment.

**Architecture:** Keep the engineering engine and main result schema unchanged. Add a focused `cost_calculation.py` contract for mappings, cells, and deterministic formulas; use the existing template module for presentation and the processor for controlled validation, regeneration, and value copying. Continue rebuilding every result from a trusted template, preserve five- and six-sheet backward compatibility, and allow only exact app-generated Cost/Price formulas in the controlled cost range.

**Tech Stack:** Python 3.11, Streamlit, openpyxl 3.1.5, pytest, `@oai/artifact-tool` for final workbook inspection/rendering, GitHub, Streamlit Community Cloud.

## Global Constraints

- The new sheet is named exactly `Cost Calculation` and appears immediately after `Batch Input & Results`.
- The three editable commercial cells are `B3` (CF Cost / m2), `E3` (Epoxy Cost / kg), and `H3` (Price Multiplier); all start blank.
- Cost is `Fabric Area * CF Cost/m2 + Epoxy Mass * Epoxy Cost/kg`.
- Price is `Cost * Price Multiplier`.
- Cost and Price remain blank until their required commercial inputs and material quantities exist.
- Cost and Price use neutral `#,##0.00` formatting with no hard-coded currency.
- All twenty requested source columns are copied as protected values in the specified order; engineering calculations and existing main-sheet columns do not change.
- Newly generated workbooks have seven sheets; controlled five- and six-sheet predecessors remain accepted and are upgraded.
- Formula validation remains deny-by-default. Only exact generated formulas in `Cost Calculation!U6:V505` are permitted on re-upload.
- Commercial source-table values are never trusted on re-upload; only the three validated commercial inputs are retained.
- The existing v1.1 repository and Streamlit application are not modified.
- Deployment targets only `Prowrap110/Iso24817CalcBatch` and `https://prowrap-batch-calculator.streamlit.app/`.

---

### Task 1: Define the Cost Contract and Blank Controlled Worksheet

**Files:**
- Create: `cost_calculation.py`
- Modify: `workbook_template.py:1-340`
- Modify: `tests/test_workbook_template.py:1-180`
- Create: `tests/test_cost_calculation.py`

**Interfaces:**
- Produces: `COST_INPUTS: tuple[tuple[str, str], ...]`
- Produces: `COST_SOURCE_HEADERS: tuple[str, ...]`
- Produces: `COST_TABLE_HEADERS: tuple[str, ...]`
- Produces: `COST_TABLE_HEADER_ROW = 5`, `COST_FIRST_DATA_ROW = 6`, `COST_LAST_DATA_ROW = 505`
- Produces: `cost_formula(row: int) -> str`, `price_formula(row: int) -> str`
- Produces: `is_allowed_cost_formula(cell) -> bool`
- Consumes: `INPUT_HEADERS`, `OUTPUT_HEADERS`, and `MAX_ROWS` from `batch_schema.py`

- [ ] **Step 1: Write failing contract and template tests**

Create `tests/test_cost_calculation.py` with direct formula and mapping assertions:

```python
from cost_calculation import (
    COST_FIRST_DATA_ROW,
    COST_SOURCE_HEADERS,
    COST_TABLE_HEADERS,
    cost_formula,
    price_formula,
)


def test_cost_contract_uses_the_requested_source_columns_in_order():
    assert COST_SOURCE_HEADERS == (
        'Pipe OD [mm]', 'Nominal Wall [mm]', 'Pipe Yield [MPa]',
        'Design Pressure [bar]', 'Operating Temperature [degC]',
        'Mechanism', 'Defect Location', 'Defect Length [mm]',
        'Remaining Wall [mm]', 'Design Life [years]', 'Design Factor',
        'Prowrap CF Cloth Width [mm]', 'Wall Loss [%]',
        'Required Structural Thickness [mm]', 'Installed Plies',
        'Total Repair Length [mm]', 'Cloth Band Count',
        'Procurement Axial Length [mm]', 'Fabric Area [m2]',
        'Epoxy Mass [kg]',
    )
    assert COST_TABLE_HEADERS == COST_SOURCE_HEADERS + ('Cost', 'Price')


def test_cost_formulas_use_absolute_inputs_and_relative_rows():
    assert cost_formula(COST_FIRST_DATA_ROW) == (
        '=IF(OR($B$3="",$E$3="",S6="",T6=""),"",'
        'S6*$B$3+T6*$E$3)'
    )
    assert price_formula(COST_FIRST_DATA_ROW) == (
        '=IF(OR(U6="",$H$3=""),"",U6*$H$3)'
    )
```

Extend `tests/test_workbook_template.py`:

```python
def test_template_has_blank_editable_cost_sheet_in_new_controlled_order():
    workbook = _template_workbook()
    assert workbook.sheetnames == [
        'Batch Information', 'Batch Input & Results', 'Cost Calculation',
        'Warnings', 'Summary', 'Instructions', 'Lists',
    ]
    cost = workbook['Cost Calculation']
    assert [cost[address].value for address in ('B3', 'E3', 'H3')] == [None, None, None]
    assert all(cost[address].protection.locked is False for address in ('B3', 'E3', 'H3'))
    assert [cost.cell(5, column).value for column in range(1, 23)][-2:] == ['Cost', 'Price']
    assert cost.freeze_panes == 'A6'
    assert cost.protection.sheet is True
```

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m pytest -q tests/test_cost_calculation.py tests/test_workbook_template.py
```

Expected: collection fails because `cost_calculation` does not exist, or the template sheet-order test fails because `Cost Calculation` is absent.

- [ ] **Step 3: Implement the focused cost contract**

Create `cost_calculation.py` with no workbook I/O:

```python
from batch_schema import MAX_ROWS

COST_INPUTS = (
    ('B3', 'CF Cost / m2'),
    ('E3', 'Epoxy Cost / kg'),
    ('H3', 'Price Multiplier'),
)
COST_SOURCE_HEADERS = (
    'Pipe OD [mm]', 'Nominal Wall [mm]', 'Pipe Yield [MPa]',
    'Design Pressure [bar]', 'Operating Temperature [degC]',
    'Mechanism', 'Defect Location', 'Defect Length [mm]',
    'Remaining Wall [mm]', 'Design Life [years]', 'Design Factor',
    'Prowrap CF Cloth Width [mm]', 'Wall Loss [%]',
    'Required Structural Thickness [mm]', 'Installed Plies',
    'Total Repair Length [mm]', 'Cloth Band Count',
    'Procurement Axial Length [mm]', 'Fabric Area [m2]',
    'Epoxy Mass [kg]',
)
COST_TABLE_HEADERS = COST_SOURCE_HEADERS + ('Cost', 'Price')
COST_TABLE_HEADER_ROW = 5
COST_FIRST_DATA_ROW = 6
COST_LAST_DATA_ROW = COST_FIRST_DATA_ROW + MAX_ROWS - 1


def cost_formula(row: int) -> str:
    return (
        f'=IF(OR($B$3="",$E$3="",S{row}="",T{row}=""),"",'
        f'S{row}*$B$3+T{row}*$E$3)'
    )


def price_formula(row: int) -> str:
    return f'=IF(OR(U{row}="",$H$3=""),"",U{row}*$H$3)'


def is_allowed_cost_formula(cell) -> bool:
    if not (COST_FIRST_DATA_ROW <= cell.row <= COST_LAST_DATA_ROW):
        return False
    if cell.column == 21:
        return cell.value == cost_formula(cell.row)
    if cell.column == 22:
        return cell.value == price_formula(cell.row)
    return False
```

- [ ] **Step 4: Build the blank Cost Calculation worksheet**

In `create_template_workbook()`, create `Cost Calculation` after `Batch Input & Results` and call `_build_cost_calculation(cost)`. Implement that builder to:

- write the title and three labels;
- apply the existing input style to the three value cells and leave them blank;
- add decimal `>= 0` data validation with `allow_blank=True` to `B3`, `E3`, and `H3`;
- write `COST_TABLE_HEADERS` in row 5 using `OUTPUT_HEADER_COLOR`;
- create table `CostRows` initially covering `A5:V6`;
- lock the sheet except the three inputs;
- allow filtering while protected;
- apply capped widths, `A6` freeze panes, neutral numeric formats, and hidden gridlines;
- leave all cells formula-free.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
python3 -m pytest -q tests/test_cost_calculation.py tests/test_workbook_template.py
```

Expected: all focused tests pass.

- [ ] **Step 6: Commit the controlled worksheet**

```bash
git add cost_calculation.py workbook_template.py tests/test_cost_calculation.py tests/test_workbook_template.py
git commit -m "feat: add blank controlled cost worksheet"
```

---

### Task 2: Populate Costs and Preserve Safe Re-upload

**Files:**
- Modify: `workbook_processor.py:35-575`
- Modify: `tests/test_workbook_processor.py:1-520`

**Interfaces:**
- Consumes: contract constants and formula functions from `cost_calculation.py`
- Produces: `_commercial_input_errors(workbook) -> tuple[ValidationIssue, ...]`
- Produces: `_write_cost_sheet(workbook) -> None`
- Produces: seven-sheet processed workbooks with deterministic U/V formulas

- [ ] **Step 1: Write failing structure, formula-safety, and mapping tests**

Add tests covering the new current order and old layouts:

```python
def test_previous_six_sheet_template_is_accepted_and_upgraded():
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    del workbook['Cost Calculation']
    result = process_workbook(_saved(workbook), processed_at=FIXED_TIME)
    assert _workbook(result.workbook_bytes).sheetnames == [
        'Batch Information', 'Batch Input & Results', 'Cost Calculation',
        'Warnings', 'Summary', 'Instructions', 'Lists',
    ]


def test_processed_cost_sheet_maps_requested_values_and_formulas():
    result = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]),
        processed_at=FIXED_TIME,
    )
    workbook = _workbook(result.workbook_bytes)
    source = workbook['Batch Input & Results']
    cost = workbook['Cost Calculation']
    expected_source_columns = ('A','B','C','D','E','F','G','H','I','K','L','R',
                               'AC','AJ','AK','AR','AS','AT','AU','AV')
    assert [cost.cell(6, column).value for column in range(1, 21)] == [
        source[f'{column}2'].value for column in expected_source_columns
    ]
    assert cost['U6'].value == cost_formula(6)
    assert cost['V6'].value == price_formula(6)
```

Add re-upload and tampering tests:

```python
def test_processed_cost_formulas_and_commercial_inputs_are_safe_to_reupload():
    first = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]), processed_at=FIXED_TIME,
    )
    workbook = _workbook(first.workbook_bytes)
    cost = workbook['Cost Calculation']
    cost['B3'], cost['E3'], cost['H3'] = 50.0, 20.0, 1.5
    second = process_workbook(_saved(workbook), processed_at=FIXED_TIME)
    regenerated = _workbook(second.workbook_bytes)['Cost Calculation']
    assert [regenerated[address].value for address in ('B3','E3','H3')] == [50.0,20.0,1.5]


def test_altered_cost_formula_is_rejected():
    result = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]), processed_at=FIXED_TIME,
    )
    workbook = _workbook(result.workbook_bytes)
    workbook['Cost Calculation']['U6'] = '=1+1'
    inspection = inspect_workbook(_saved(workbook))
    assert [issue.code for issue in inspection.workbook_errors] == ['FORMULA_NOT_ALLOWED']
```

Add a regression that clears the only main input row in a processed workbook while old exact U/V formulas remain, then verifies reprocessing returns zero cost rows without a workbook error.

- [ ] **Step 2: Run processor tests and verify RED**

Run:

```bash
python3 -m pytest -q tests/test_workbook_processor.py
```

Expected: failures show unsupported seven-sheet structure, disallowed generated formulas, and missing cost population.

- [ ] **Step 3: Extend controlled sheet-order validation**

In `workbook_processor.py`:

- keep `_LEGACY_SHEETS` as the five-sheet order;
- rename the present six-sheet tuple to `_PREVIOUS_SHEETS`;
- define `_CURRENT_SHEETS` as the seven-sheet order;
- validate order against `{_LEGACY_SHEETS, _PREVIOUS_SHEETS, _CURRENT_SHEETS}`;
- validate row-5 cost headings when `Cost Calculation` exists;
- reject unexpected sheets as before.

- [ ] **Step 4: Validate commercial values and exact formulas**

Implement `_commercial_input_errors(workbook)` so each present commercial cell is either blank or a finite, non-Boolean number `>= 0`. Return `INVALID_COST_INPUT` with the label and coordinate for invalid values.

Change `_formula_errors(workbook)` so:

```python
if (
    worksheet.title == 'Cost Calculation'
    and getattr(cell, 'data_type', None) == 'f'
    and isinstance(cell.value, str)
    and is_allowed_cost_formula(cell)
):
    continue
```

All other string formulas, array formulas, data-table formulas, formulas outside `U6:V505`, and altered commercial formulas retain `FORMULA_NOT_ALLOWED`. Call commercial validation and formula validation during inspection without weakening formula-error priority over row-range errors.

- [ ] **Step 5: Preserve only commercial assumptions during fresh rebuild**

Extend `_copy_controlled_inputs(source_workbook, output_workbook)` to copy `B3`, `E3`, and `H3` only when the source has `Cost Calculation`. Never copy source cost-table cells, table definitions, styles, or formulas.

- [ ] **Step 6: Populate the commercial table and calculation settings**

Implement `_write_cost_sheet(workbook)`:

```python
def _write_cost_sheet(workbook) -> None:
    source = workbook['Batch Input & Results']
    cost = workbook['Cost Calculation']
    all_headers = INPUT_HEADERS + OUTPUT_HEADERS
    source_columns = {
        header: all_headers.index(header) + 1 for header in COST_SOURCE_HEADERS
    }
    populated = _populated_rows(source)
    for output_row, (source_row, _) in enumerate(populated, start=COST_FIRST_DATA_ROW):
        for destination_column, header in enumerate(COST_SOURCE_HEADERS, start=1):
            cost.cell(output_row, destination_column).value = source.cell(
                source_row, source_columns[header]
            ).value
        cost.cell(output_row, 21).value = cost_formula(output_row)
        cost.cell(output_row, 22).value = price_formula(output_row)
    cost.tables['CostRows'].ref = f'A5:V{max(COST_FIRST_DATA_ROW, 5 + len(populated))}'
```

Apply row border/alignment/number formats, call `_write_cost_sheet` after all engineering result rows and before saving, and set:

```python
output_workbook.calculation.calcMode = 'auto'
output_workbook.calculation.fullCalcOnLoad = True
output_workbook.calculation.forceFullCalc = True
```

- [ ] **Step 7: Run processor tests and verify GREEN**

Run:

```bash
python3 -m pytest -q tests/test_workbook_processor.py tests/test_cost_calculation.py
```

Expected: all focused tests pass, including formula injection, sparse scanning, old-template, cleared-row, and re-upload regressions.

- [ ] **Step 8: Commit safe cost processing**

```bash
git add workbook_processor.py tests/test_workbook_processor.py
git commit -m "feat: calculate protected batch costs and prices"
```

---

### Task 3: Update Acceptance Coverage and User Guidance

**Files:**
- Modify: `tests/test_full_batch_acceptance.py:1-120`
- Modify: `README.md:1-90`
- Modify: `workbook_template.py:220-255`
- Modify: `DEPLOYMENT.md`

**Interfaces:**
- Consumes: seven-sheet output and exact formulas from Tasks 1-2
- Produces: updated acceptance contract and non-technical operating instructions

- [ ] **Step 1: Write failing acceptance assertions**

Update the full acceptance test to require the seven-sheet order, blank commercial inputs, twenty mapped columns, six cost rows aligned with the six status rows, and only the exact twelve generated formulas `U6:V11`. Assert that the 500 mm OK row has fabric/epoxy quantities and corresponding Cost/Price formulas, while the invalid and no-solution rows have blank material quantities and formula results remain blank when commercial inputs are blank.

- [ ] **Step 2: Run acceptance test and verify RED**

Run:

```bash
python3 -m pytest -q tests/test_full_batch_acceptance.py
```

Expected: failure until the acceptance contract and generated workbook agree on the new sheet and controlled formulas.

- [ ] **Step 3: Update workbook and repository instructions**

Change the template instructions to state:

- the input template itself contains no formulas;
- processed workbooks contain controlled Cost and Price formulas only;
- `B3`, `E3`, and `H3` on `Cost Calculation` are blank and editable;
- Cost and Price definitions match the approved formulas;
- no currency symbol is fixed;
- previous five- and six-sheet templates remain accepted and upgrade to seven sheets.

Make the same workflow explicit in `README.md` and keep the preliminary-engineering disclaimer unchanged. Update `DEPLOYMENT.md` sheet-count/live-smoke instructions without changing the isolation rule for v1.1.

- [ ] **Step 4: Run acceptance and documentation-adjacent tests**

Run:

```bash
python3 -m pytest -q tests/test_full_batch_acceptance.py tests/test_workbook_template.py tests/test_app_smoke.py
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit acceptance and documentation**

```bash
git add tests/test_full_batch_acceptance.py README.md workbook_template.py DEPLOYMENT.md
git commit -m "docs: explain editable batch cost calculations"
```

---

### Task 4: Full Regression and Visual Workbook Verification

**Files:**
- Create output: `/Users/can/Documents/Codex/2026-08-14/i/outputs/PROWRAP_Batch_Cost_Calculation_Acceptance.xlsx`
- Modify if required by findings: `workbook_template.py`, `workbook_processor.py`, `cost_calculation.py`, relevant tests

**Interfaces:**
- Consumes: complete implementation from Tasks 1-3
- Produces: verified acceptance workbook and release evidence

- [ ] **Step 1: Run the complete automated test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

Expected: all tests pass with zero failures.

- [ ] **Step 2: Generate a processed acceptance workbook**

Run the existing acceptance generator to create an input workbook, process it through `process_workbook`, and save the processed bytes as `PROWRAP_Batch_Cost_Calculation_Acceptance.xlsx` in the conversation output directory. Enter representative commercial values through `@oai/artifact-tool`: CF Cost/m2 `50.00`, Epoxy Cost/kg `20.00`, Price Multiplier `1.50`.

- [ ] **Step 3: Inspect formulas, values, and errors with artifact-tool**

Inspect `Cost Calculation!A1:V12` including values and formulas. Verify:

- the three commercial values are present and editable;
- source values match the main report;
- formula references are correct in every populated row;
- representative Cost equals `Fabric Area * 50 + Epoxy Mass * 20`;
- representative Price equals `Cost * 1.5` after recalculation;
- no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, or `#N/A` is present.

- [ ] **Step 4: Render and visually inspect all seven sheets**

Render each sheet, with a focused full-width render of `Cost Calculation!A1:V12`. Confirm the title, highlighted commercial inputs, table headers, engineering values, Cost, and Price are legible; no severe clipping or broken layout exists; Warnings remains separate; Lists remains hidden.

- [ ] **Step 5: Fix only verified defects and rerun affected tests**

If the inspection exposes a defect, first add or tighten the focused failing regression, verify RED, make the smallest implementation change, rerun the focused test to GREEN, then rerun the complete suite and visual inspection.

- [ ] **Step 6: Commit any verification-driven fixes**

If files changed during visual verification:

```bash
git add cost_calculation.py workbook_template.py workbook_processor.py tests
git commit -m "fix: polish batch cost workbook output"
```

---

### Task 5: Publish to GitHub and Verify Live Streamlit

**Files:**
- No new source files unless live verification exposes a tested defect

**Interfaces:**
- Consumes: clean, fully tested feature branch and acceptance workbook
- Produces: merged GitHub change and verified live batch calculator

- [ ] **Step 1: Perform final branch verification**

Run:

```bash
git status --short --branch
git diff --check origin/main...HEAD
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

Expected: clean worktree, no whitespace errors, and zero test failures.

- [ ] **Step 2: Review the complete branch diff**

Use `superpowers:requesting-code-review` and resolve every Critical or Important finding with a regression test. Repeat review until clean.

- [ ] **Step 3: Publish through the GitHub workflow**

Use `github:yeet` to confirm repository and branch scope, push `feature/cost-calculation-sheet`, and open a pull request titled:

```text
Add editable cost and price calculation worksheet
```

The PR body shall summarize editable blank assumptions, requested source-column mapping, formulas, safe re-upload, backward compatibility, full test count, visual verification, and explicit v1.1 isolation.

- [ ] **Step 4: Merge the approved batch pull request**

After the PR is clean and mergeable, merge it into `main` without deleting the feature branch unless the user asks. Record the merge commit.

- [ ] **Step 5: Verify Streamlit pulled the new main branch**

Open `https://prowrap-batch-calculator.streamlit.app/`, confirm Manage app still points to `prowrap110/iso24817calcbatch/main/app.py`, and reboot only if the live session remains stale after the repository update.

- [ ] **Step 6: Exercise the live workbook workflow**

Download the live template and verify seven sheets including blank editable `Cost Calculation`. Upload a non-sensitive one-row acceptance input, calculate, download the processed result, and verify with artifact-tool that:

- the processed report contains the mapped commercial row;
- `B3`, `E3`, and `H3` are blank/unlocked;
- U/V contain exact Cost/Price formulas;
- the workbook opens without formula errors;
- the existing Warnings sheet and engineering results still work.

- [ ] **Step 7: Deliver the release handoff**

Report the GitHub PR and merge commit, live batch URL, automated test result, live template/result evidence, and the acceptance workbook. State explicitly that the v1.1 app was not changed.
