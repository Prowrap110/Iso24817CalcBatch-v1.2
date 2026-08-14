# PROWRAP Warning Codes, Approved Cloth Widths, and Tg 110 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce compact permanent warning codes plus a dedicated warning register in batch workbooks, approve 300 mm and 500 mm cloth, and set Tg to 110 degC in both the batch engine and the separate v1.1 calculator.

**Architecture:** Add a strict batch-only warning catalogue that translates every existing engineering warning to one permanent code while preserving the engine's full warning text internally. Build the visible `Warnings` worksheet from the codes after row processing, and accept only the previous five-sheet or current six-sheet controlled workbook layouts. Change the material Tg once per repository and derive the 90 degC and 80 degC limits from it.

**Tech Stack:** Python 3.11, Streamlit, openpyxl, pytest/unittest, Git worktrees, Microsoft Excel or LibreOffice for final visual verification.

## Global Constraints

- Keep `https://iso24817calc-prowrapv11.streamlit.app` and the batch Streamlit app as separate deployments.
- Keep the existing `Compliance Warnings` column heading for old-template compatibility; processed cells contain codes only.
- Use permanent codes `W001` through `W020` exactly as defined in the approved design.
- New workbooks contain a visible `Warnings` sheet immediately after `Batch Input & Results`.
- Accept only the old controlled five-sheet layout or the new controlled six-sheet layout; continue rejecting all other sheet sets/orders.
- Treat exactly 300 mm and 500 mm as approved Prowrap CF cloth widths; retain the 50 mm stitch overlap.
- Set Tg to 110 degC and derive the general limit as Tg - 20 = 90 degC and long-life Class 3 Type B limit as Tg - 30 = 80 degC.
- Preserve formula-free, macro-free, fresh-template output and all current upload hardening.
- Use test-driven development: each production behavior must have a test observed failing first.

---

### Task 1: Permanent Warning Catalogue and Compact Row Codes

**Files:**
- Create: `warning_catalog.py`
- Modify: `batch_adapter.py`
- Modify: `workbook_processor.py`
- Test: `tests/test_warning_catalog.py`
- Test: `tests/test_batch_adapter.py`

**Interfaces:**
- Consumes: the existing ordered `tuple[str, ...]` of full warning messages assembled by `batch_adapter.calculate_row`.
- Produces: `WarningDefinition(code: str, meaning: str, matches: Callable[[str], bool])`, `warning_codes(messages: Iterable[str]) -> tuple[str, ...]`, and `warning_meaning(code: str) -> str`.

- [ ] **Step 1: Write failing catalogue and adapter tests**

```python
def representative_warning_messages():
    return (
        'Design temperature 91.0 degC exceeds the qualified Prowrap limit of 90.00 degC.',
        'NOT REPAIRABLE PER ISO 24817 FORMULA 12: no thickness can satisfy the case.',
        'Type B service life is capped at 2 years for PRW110.',
        'Design temperature 81.0 degC exceeds the Type B upper service limit of 80.0 degC.',
        'Type B defect at zero design pressure: Formula 12 is non-controlling.',
        'Type B design assumes a circular/near-circular defect of size 15 mm.',
        'Formula 12 validity exceeded: defect size 100 mm exceeds the limit.',
        'B31G: d/t > 0.80: beyond B31G applicability.',
        'B31G: d/t <= 0.10: metal loss is not limited as to length.',
        'B31G: Safety factor < 1.25 is below the minimum.',
        'B31G: SMYS > 483 MPa: falling back to Original B31G.',
        'B31G: Flow stress capped at SMTS.',
        'B31G Level 1: the corroded pipe alone is NOT acceptable at design pressure.',
        'Internal corrosion projected at 0.10 mm/yr to end of design life.',
        'Internal corrosion with corrosion rate = 0 mm/yr requires review.',
        'Axial load case 1 selected with a Type B defect.',
        'Repair thickness exceeds D/12.',
        'Prowrap CF cloth width 250 mm is not an approved configuration.',
        'Type A / Class 3 check was not run at zero design pressure.',
        'Type A / Class 3 check was not run above the qualified Prowrap temperature limit.',
    )

def test_each_defined_warning_message_maps_to_one_permanent_code():
    samples = representative_warning_messages()
    assert warning_codes(samples) == tuple(f'W{i:03d}' for i in range(1, 21))

def test_unknown_warning_is_rejected_instead_of_getting_an_improvised_code():
    with pytest.raises(UnmappedWarningError, match='Unmapped compliance warning'):
        warning_codes(('new unregistered warning',))

def test_adapter_writes_codes_but_warning_still_requires_review():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Prowrap CF Cloth Width [mm]': 250.0,
    }))
    assert outcome.status.value == 'REVIEW REQUIRED'
    assert outcome.outputs['Compliance Warnings'] == ('W018',)
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `pytest -q tests/test_warning_catalog.py tests/test_batch_adapter.py`

Expected: collection fails because `warning_catalog` does not exist, then the adapter assertion fails because it still returns full warning sentences.

- [ ] **Step 3: Implement the strict catalogue and adapter conversion**

Create one ordered `WARNING_DEFINITIONS` tuple containing codes `W001` through `W020`, their approved permanent meanings, and narrowly scoped message-prefix or semantic matchers. Implement:

```python
class UnmappedWarningError(ValueError):
    pass

def warning_codes(messages):
    resolved = []
    for message in messages:
        matches = [item.code for item in WARNING_DEFINITIONS if item.matches(message)]
        if len(matches) != 1:
            raise UnmappedWarningError(f'Unmapped compliance warning: {message}')
        if matches[0] not in resolved:
            resolved.append(matches[0])
    return tuple(resolved)
```

In `batch_adapter.calculate_row`, classify status using the full warnings first, then replace only the workbook-facing `Compliance Warnings` output with `warning_codes(warnings)`. Change `_output_value` to serialize the code tuple as `', '.join(value)`.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run: `pytest -q tests/test_warning_catalog.py tests/test_batch_adapter.py tests/test_batch_status.py`

Expected: all selected tests pass; an unknown warning raises rather than receiving a new number.

- [ ] **Step 5: Commit the catalogue**

```bash
git add warning_catalog.py batch_adapter.py workbook_processor.py tests/test_warning_catalog.py tests/test_batch_adapter.py
git commit -m "feat: add permanent batch warning codes"
```

---

### Task 2: Dedicated Warnings Worksheet and Legacy Template Compatibility

**Files:**
- Modify: `workbook_template.py`
- Modify: `workbook_processor.py`
- Modify: `workbook_formatting.py`
- Modify: `tests/test_workbook_template.py`
- Modify: `tests/test_workbook_processor.py`
- Modify: `tests/test_full_batch_acceptance.py`

**Interfaces:**
- Consumes: processed row cells containing comma-separated permanent codes and `warning_meaning(code)` from Task 1.
- Produces: `_write_warnings_sheet(workbook) -> None`, a six-sheet current template, and validation of either exact controlled sheet layout.

- [ ] **Step 1: Write failing template and processor tests**

```python
def test_template_has_visible_blank_warnings_sheet_after_results():
    workbook = _template_workbook()
    assert workbook.sheetnames == [
        'Batch Information', 'Batch Input & Results', 'Warnings',
        'Summary', 'Instructions', 'Lists',
    ]
    warnings = workbook['Warnings']
    assert warnings['A1'].value == 'Compliance Warning Register'
    assert [warnings.cell(3, col).value for col in range(1, 4)] == [
        'Warning Code', 'Warning Meaning / Required Action', 'Affected Excel Rows',
    ]
    assert warnings['A4'].value == 'No compliance warnings were generated.'

def test_processed_warning_sheet_consolidates_codes_and_rows():
    source = workbook_bytes_with_rows([
        valid_row_values(**{'Prowrap CF Cloth Width [mm]': 250.0}),
        valid_row_values(**{'Prowrap CF Cloth Width [mm]': 250.0}),
    ])
    workbook = _workbook(process_workbook(source, FIXED_TIME).workbook_bytes)
    assert workbook['Batch Input & Results']['W2'].value == 'W018'
    assert workbook['Warnings']['A4'].value == 'W018'
    assert workbook['Warnings']['C4'].value == '2, 3'

def test_previous_five_sheet_template_is_accepted_and_upgraded():
    old_workbook = _template_workbook()
    del old_workbook['Warnings']
    result = process_workbook(_saved(old_workbook), FIXED_TIME)
    assert 'Warnings' in _workbook(result.workbook_bytes).sheetnames
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `pytest -q tests/test_workbook_template.py tests/test_workbook_processor.py tests/test_full_batch_acceptance.py`

Expected: failures show the missing `Warnings` sheet, long row text, and rejection or absence of the six-sheet layout.

- [ ] **Step 3: Build and populate the controlled sheet**

In `create_template_workbook`, create `Warnings` immediately after the results sheet. Add title, explanatory subtitle, headers at row 3, the no-warning message at row 4, wrapped description width, frozen pane `A4`, output-cell protection, and no formulas.

Replace the single required-sheet tuple with:

```python
_LEGACY_SHEETS = (
    'Batch Information', 'Batch Input & Results', 'Summary', 'Instructions', 'Lists',
)
_CURRENT_SHEETS = (
    'Batch Information', 'Batch Input & Results', 'Warnings',
    'Summary', 'Instructions', 'Lists',
)
```

Validation accepts only either exact tuple. After processing all rows, parse the row code cells, aggregate source rows by code, and write sorted warning rows starting at row 4. Add an Excel table named `WarningRegister` only when at least one warning is present. Preserve the no-warning message otherwise.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `pytest -q tests/test_workbook_template.py tests/test_workbook_processor.py tests/test_full_batch_acceptance.py`

Expected: all selected tests pass, including formulas/protection/extra-sheet regressions.

- [ ] **Step 5: Commit workbook presentation**

```bash
git add workbook_template.py workbook_processor.py workbook_formatting.py tests/test_workbook_template.py tests/test_workbook_processor.py tests/test_full_batch_acceptance.py
git commit -m "feat: add separate warning register worksheet"
```

---

### Task 3: Approve 500 mm Cloth and Set Batch Tg to 110 degC

**Files:**
- Modify: `batch_schema.py`
- Modify: `batch_adapter.py`
- Modify: `engine/prowrap_materials.py`
- Modify: `tests/test_batch_adapter.py`
- Modify: `tests/engine/test_material_specs.py`
- Modify: `tests/engine/test_input_validation.py`
- Modify: `tests/engine/test_type_b_formula12.py`
- Modify: `tests/test_engine_snapshot.py`
- Modify: `ENGINE_SOURCE.md`

**Interfaces:**
- Consumes: `APPROVED_CLOTH_WIDTHS_MM` and `PROWRAP` material constants.
- Produces: approved widths `(300.0, 500.0)`, `glass_transition_temp == 110.0`, `max_temp == 90.0`, and long-life Type B `service_temp_limit_c == 80.0`.

- [ ] **Step 1: Write failing boundary and cloth tests**

```python
@pytest.mark.parametrize('width', [300.0, 500.0])
def test_approved_cloth_widths_do_not_create_warning(width):
    outcome = calculate_row(batch_info(), validated_row(**{
        'Prowrap CF Cloth Width [mm]': width,
    }))
    assert outcome.status.value == 'OK'
    assert outcome.outputs['Compliance Warnings'] == ()

def test_tg_110_derives_qualification_limits():
    assert PROWRAP['glass_transition_temp'] == 110.0
    assert PROWRAP['max_temp'] == 90.0

def test_temperature_boundary_accepts_90_and_rejects_above_90():
    calculate_repair(**default_inputs(temp=90.0))
    with pytest.raises(ValueError):
        calculate_repair(**default_inputs(temp=90.01))
```

Also change the Type B reference assertion to `service_temp_limit_c == 80.0` for design life greater than two years and `90.0` at the two-year cap.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `pytest -q tests/test_batch_adapter.py tests/engine/test_material_specs.py tests/engine/test_input_validation.py tests/engine/test_type_b_formula12.py`

Expected: 500 mm still maps to `W018`; Tg and temperature-boundary assertions fail against 78.18/58.18/48.18.

- [ ] **Step 3: Implement derived material constants and approved widths**

```python
APPROVED_CLOTH_WIDTHS_MM = (300.0, 500.0)

_GLASS_TRANSITION_TEMP_C = 110.0
PROWRAP = {
    # existing properties unchanged
    'glass_transition_temp': _GLASS_TRANSITION_TEMP_C,
    'max_temp': _GLASS_TRANSITION_TEMP_C - 20.0,
}
```

Update the unapproved-width warning meaning to say `300 mm or 500 mm configuration`. Keep band procurement driven by the entered row width and the 50 mm overlap. Record the new user-approved material-basis correction in `ENGINE_SOURCE.md`.

- [ ] **Step 4: Run batch engine and snapshot tests, validating changes rather than blindly accepting them**

Run: `pytest -q tests/engine tests/test_batch_adapter.py tests/test_engine_snapshot.py`

Expected: temperature tests pass. If numerical snapshots change, recompute the affected formula from Tg 110 and update only expectations directly caused by the new thermal factor; unrelated outputs must remain unchanged.

- [ ] **Step 5: Commit batch engineering changes**

```bash
git add batch_schema.py batch_adapter.py engine/prowrap_materials.py tests/test_batch_adapter.py tests/engine/test_material_specs.py tests/engine/test_input_validation.py tests/engine/test_type_b_formula12.py tests/test_engine_snapshot.py ENGINE_SOURCE.md
git commit -m "feat: approve 500 mm cloth and set batch Tg to 110"
```

---

### Task 4: Set Tg to 110 degC in the Separate v1.1 Calculator

**Files:**
- Modify: `/Users/can/Documents/GitHub/Iso24817Calc/prowrap_materials.py`
- Modify: `/Users/can/Documents/GitHub/Iso24817Calc/test_material_specs.py`
- Modify: `/Users/can/Documents/GitHub/Iso24817Calc/test_input_validation.py`
- Modify: `/Users/can/Documents/GitHub/Iso24817Calc/test_type_b_formula12.py`
- Modify: `/Users/can/Documents/GitHub/Iso24817Calc/test_current_calculation_baseline.py` only for formula-proven thermal-output changes.

**Interfaces:**
- Consumes: the v1.1 `PROWRAP` dictionary and existing temperature validation paths.
- Produces: the same exact 110/90/80 limits as the batch engine, without adding batch workbook behavior to v1.1.

- [ ] **Step 1: Create an isolated v1.1 worktree and verify its baseline**

Use `superpowers:using-git-worktrees`. Create branch `feature/tg110` from clean v1.1 `main`, install only declared requirements if needed, and run `python -m pytest -q`.

Expected: the existing suite passes before edits.

- [ ] **Step 2: Write the same failing material and boundary tests in v1.1**

Use the Task 3 assertions with v1.1 imports. Update Type B expected service limits to 80.0 and 90.0.

- [ ] **Step 3: Run focused v1.1 tests and verify RED**

Run: `python -m pytest -q test_material_specs.py test_input_validation.py test_type_b_formula12.py`

Expected: failures report the old 78.18, 58.18, and 48.18 values.

- [ ] **Step 4: Implement the single-source Tg change**

Define `_GLASS_TRANSITION_TEMP_C = 110.0`, set `glass_transition_temp` from it, and calculate `max_temp` as `_GLASS_TRANSITION_TEMP_C - 20.0`. Do not add a cloth selector, warning worksheet, or batch code to v1.1.

- [ ] **Step 5: Run the full v1.1 suite and commit**

Run: `python -m pytest -q`

Expected: all tests pass. Update only reference outputs proven to change because of the new thermal factor.

```bash
git add prowrap_materials.py test_material_specs.py test_input_validation.py test_type_b_formula12.py test_current_calculation_baseline.py
git commit -m "feat: set PROWRAP Tg to 110 degrees"
```

---

### Task 5: End-to-End Workbook, Visual, Security, and Deployment Verification

**Files:**
- Modify: `scripts/create_acceptance_workbook.py` if needed to include repeated and distinct warning examples.
- Modify: `tests/test_full_batch_acceptance.py`
- Modify: `README.md`
- Modify: `DEPLOYMENT.md`
- Create output: `/Users/can/Documents/Codex/2026-08-14/i/outputs/PROWRAP_Batch_Warning_Codes_Acceptance.xlsx`

**Interfaces:**
- Consumes: all batch tasks plus the committed v1.1 Tg branch.
- Produces: a visually verified acceptance workbook and two independently verified deployments.

- [ ] **Step 1: Write the failing end-to-end acceptance assertions**

Assert that the acceptance workbook produces at least two warning codes, reuses one code across multiple rows, includes a 500 mm no-warning row, contains the six controlled sheets in order, contains no formulas, and preserves status totals.

- [ ] **Step 2: Run acceptance and full batch suites**

Run: `pytest -q tests/test_full_batch_acceptance.py`

Expected before any needed generator adjustment: the new acceptance assertion fails for missing repeated warning coverage.

After the minimal generator/test-fixture adjustment, run: `pytest -q`

Expected: the complete batch suite passes with no warnings or errors from pytest.

- [ ] **Step 3: Generate and inspect the final workbook**

Generate the acceptance input, process it at a fixed UTC timestamp, and save the one user-facing workbook at the exact output path above. Inspect key values and formula absence programmatically. Render and visually inspect every visible sheet, checking especially that row warnings contain codes only and the `Warnings` sheet has readable descriptions and row references.

- [ ] **Step 4: Run release integrity checks**

Run in both repositories:

```bash
git diff --check
git status --short --branch
```

Confirm the original v1.1 repository contains no batch workbook files, the batch repository retains its own app identity, and neither workbook contains macros or formulas.

- [ ] **Step 5: Update documentation and commit acceptance evidence**

Document the Warnings sheet, codes-only row output, 300/500 mm approved widths, Tg 110, 90 degC general limit, 80 degC long-life Type B limit, legacy-template upgrade, and separate deployment URLs.

```bash
git add scripts/create_acceptance_workbook.py tests/test_full_batch_acceptance.py README.md DEPLOYMENT.md
git commit -m "docs: document warning register and Tg 110 release"
```

- [ ] **Step 6: Publish and verify each application independently**

Push `feature/warning-codes-tg110` to `Prowrap110/Iso24817CalcBatch`, open and merge its pull request, then wait for the batch Streamlit app to redeploy. Push `feature/tg110` to `Prowrap110/Iso24817Calc`, open and merge its pull request, then wait for `https://iso24817calc-prowrapv11.streamlit.app` to redeploy.

Verify the batch app downloads the new six-sheet workbook. Verify v1.1 visibly reports a 90 degC Prowrap temperature limit. Do not declare either deployment complete from local tests or GitHub state alone.
