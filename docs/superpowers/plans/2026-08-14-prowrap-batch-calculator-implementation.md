# PROWRAP Batch Repair Calculator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separate Streamlit application that accepts the controlled PROWRAP Excel template, applies three common batch fields to up to 500 defect rows beginning with Pipe OD, and returns a user-friendly processed workbook with row-level engineering results and statuses.

**Architecture:** The new `Iso24817CalcBatch` repository vendors the calculation modules from `Iso24817Calcv1.1` commit `68e5409` into an isolated `engine` package. Workbook parsing, validation, status classification, calculation adaptation, formatting, and Streamlit presentation remain separate modules. The existing v1.1 repository and deployment are read-only references and receive no changes.

**Tech Stack:** Python 3.11, Streamlit, openpyxl, pytest, standard-library dataclasses and enums.

## Global Constraints

- Do not modify, commit to, merge into, redirect, or redeploy `Iso24817Calcv1.1` or `https://iso24817calc-prowrapv11.streamlit.app`.
- Work only in the separate `Iso24817CalcBatch` repository and deploy it to a separate Streamlit application and URL.
- Pin the engine source to `Iso24817Calcv1.1` commit `68e5409` and record provenance in code and every output workbook.
- Enter `Customer`, `Project Location`, and `Report No` once on `Batch Information`; do not repeat them in defect rows.
- The first defect-row input column is `Pipe OD [mm]`.
- Accept only controlled `.xlsx` workbooks, no macros or formulas, at most 10 MB and 500 populated defect rows.
- Preserve row order and input-cell values; write results only to appended output columns in a new workbook.
- One bad row must not stop valid rows.
- Supported statuses are exactly `OK`, `REVIEW REQUIRED`, `NOT REPAIRABLE`, `INPUT ERROR`, and `SYSTEM ERROR`.
- `NOT REPAIRABLE` rows must not contain installable ply, thickness, material, or procurement quantities.
- The fixed stitch overlap remains 50 mm. Version 1 recognizes 300 mm as approved; other widths greater than 50 mm require review.
- Type B PRW110 service-life wording must use the configured 2-year limit.
- Uploaded and generated files are temporary and are not retained after the Streamlit session.

---

## Planned File Structure

```text
Iso24817CalcBatch/
├── .gitignore
├── .streamlit/config.toml
├── ENGINE_SOURCE.md
├── README.md
├── DEPLOYMENT.md
├── app.py
├── batch_adapter.py
├── batch_schema.py
├── batch_status.py
├── batch_validation.py
├── requirements.txt
├── requirements-dev.txt
├── runtime.txt
├── workbook_formatting.py
├── workbook_processor.py
├── workbook_template.py
├── engine/
│   ├── __init__.py
│   ├── b31g.py
│   ├── iso24817_typea_class3.py
│   ├── prowrap_calculations.py
│   └── prowrap_materials.py
├── scripts/
│   └── create_acceptance_workbook.py
└── tests/
    ├── __init__.py
    ├── engine/
    ├── helpers.py
    ├── test_app_smoke.py
    ├── test_batch_adapter.py
    ├── test_batch_schema.py
    ├── test_batch_status.py
    ├── test_batch_validation.py
    ├── test_engine_batch_hardening.py
    ├── test_full_batch_acceptance.py
    ├── test_workbook_processor.py
    └── test_workbook_template.py
```

## Task 1: Pin and Import the Existing Calculation Engine

**Files:**

- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `runtime.txt`
- Create: `ENGINE_SOURCE.md`
- Create: `engine/__init__.py`
- Create: `engine/b31g.py`
- Create: `engine/iso24817_typea_class3.py`
- Create: `engine/prowrap_calculations.py`
- Create: `engine/prowrap_materials.py`
- Create: `tests/__init__.py`
- Create: `tests/engine/test_b31g.py`
- Create: `tests/engine/test_cloth_width.py`
- Create: `tests/engine/test_current_calculation_baseline.py`
- Create: `tests/engine/test_input_validation.py`
- Create: `tests/engine/test_iso24817_typea_class3.py`
- Create: `tests/engine/test_long_term_overlap.py`
- Create: `tests/engine/test_material_specs.py`
- Create: `tests/engine/test_type_b_formula12.py`
- Create: `tests/engine/test_typea_baseline_matches_rigorous.py`
- Create: `tests/engine/test_typea_class3_adapter.py`
- Create: `tests/test_engine_snapshot.py`

**Interfaces:**

- Consumes: `Iso24817Calcv1.1` commit `68e5409` as a read-only source.
- Produces: importable `engine.prowrap_calculations.calculate_repair`, `calculate_type_a_class3_prowrap_check`, and `apply_type_a_class3_result_to_repair` functions.

- [ ] **Step 1: Write the failing snapshot/provenance test**

```python
# tests/test_engine_snapshot.py
from pathlib import Path


def test_pinned_engine_is_importable_and_documented():
    from engine.prowrap_calculations import calculate_repair

    assert callable(calculate_repair)
    provenance = Path('ENGINE_SOURCE.md').read_text(encoding='utf-8')
    assert 'Prowrap110/Iso24817Calcv1.1' in provenance
    assert '68e5409' in provenance
```

- [ ] **Step 2: Run the test and verify the engine is absent**

Run: `python3 -m pytest tests/test_engine_snapshot.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'engine'`.

- [ ] **Step 3: Add runtime files and the pinned source record**

Use these dependency files:

```text
# requirements.txt
streamlit>=1.40,<2
openpyxl>=3.1,<4

# requirements-dev.txt
-r requirements.txt
pytest>=8,<9

# runtime.txt
python-3.11
```

`ENGINE_SOURCE.md` must state the source repository, exact commit `68e5409`, import date `2026-08-14`, the four copied engine modules, and that all later corrections are batch-repository-only.

- [ ] **Step 4: Copy the four modules and inherited engine tests from the pinned revision**

Copy only the approved calculation modules and calculation tests. Change their internal imports from root-level imports to package-relative imports, for example:

```python
from .b31g import assess_b31g
from .iso24817_typea_class3 import TypeAClass3Inputs, calculate_type_a_class3
from .prowrap_materials import PROWRAP
```

Update copied tests to import from `engine.*`. Do not copy the original Streamlit UI, desktop launcher, packaging files, or form module.

- [ ] **Step 5: Install dependencies and verify the pinned engine**

Run: `python3 -m pip install -r requirements-dev.txt`

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_engine_snapshot.py tests/engine -v`

Expected: snapshot test PASS and all inherited engine tests PASS.

- [ ] **Step 6: Commit the isolated engine baseline**

```bash
git add .gitignore requirements.txt requirements-dev.txt runtime.txt ENGINE_SOURCE.md engine tests
git commit -m 'chore: pin PROWRAP v1.1 calculation engine'
```

## Task 2: Harden the Engine for Batch-Safe Inputs

**Files:**

- Create: `tests/helpers.py`
- Create: `tests/test_engine_batch_hardening.py`
- Modify: `engine/prowrap_calculations.py`

**Interfaces:**

- Consumes: `engine.prowrap_calculations.calculate_repair(**kwargs)`.
- Produces: the same return dictionary for valid v1.1 inputs, plus deterministic zero-pressure Type B warnings and strict enumeration errors.

- [ ] **Step 1: Add a reusable valid-input fixture and failing edge-case tests**

```python
# tests/helpers.py
def valid_engine_inputs(**overrides):
    values = dict(
        customer='Batch Customer', location='Batch Location', report_no='B-001',
        od=457.2, wall=9.53, pressure=50.0, temp=40.0,
        defect_type='Corrosion', defect_loc='External', length=100.0,
        rem_wall=4.5, yield_strength=359.0, design_factor=0.72,
        design_life=20, internal_corrosion_rate=0.0,
        installation_temp=20.0, component_type='Straight',
        cyclic_derating_factor=1.0, axial_load_case=0,
        cloth_width_mm=300.0,
    )
    values.update(overrides)
    return values
```

```python
# tests/test_engine_batch_hardening.py
import pytest

from engine.prowrap_calculations import calculate_repair
from tests.helpers import valid_engine_inputs


def test_zero_pressure_type_b_returns_three_ply_review_warning():
    result = calculate_repair(**valid_engine_inputs(
        pressure=0.0, defect_type='Leak', defect_loc='External'
    ))
    assert result['num_plies'] == 3
    assert any('zero design pressure' in warning.lower()
               for warning in result['compliance_warnings'])


@pytest.mark.parametrize(('field', 'value'), [
    ('defect_type', 'Erosion'),
    ('defect_loc', 'Outside'),
    ('axial_load_case', 2),
])
def test_invalid_route_enumeration_is_rejected(field, value):
    with pytest.raises(ValueError, match='Unsupported'):
        calculate_repair(**valid_engine_inputs(**{field: value}))


def test_type_b_life_warning_uses_two_year_limit():
    result = calculate_repair(**valid_engine_inputs(defect_type='Leak'))
    assert any('2 years' in warning for warning in result['compliance_warnings'])
```

- [ ] **Step 2: Run the new tests and verify the known failures**

Run: `python3 -m pytest tests/test_engine_batch_hardening.py -v`

Expected: zero-pressure Type B crashes or lacks the warning; invalid enumerations are not rejected; the life-limit wording test exposes the stale comment/message if present.

- [ ] **Step 3: Add strict engine validation and zero-pressure guards**

At the start of `calculate_repair`, reject values outside these sets:

```python
allowed_mechanisms = {'Corrosion', 'Dent', 'Leak', 'Crack'}
allowed_locations = {'External', 'Internal'}
allowed_axial_cases = {0, 1}
if defect_type not in allowed_mechanisms:
    raise ValueError(f'Unsupported mechanism: {defect_type}')
if defect_loc not in allowed_locations:
    raise ValueError(f'Unsupported defect location: {defect_loc}')
if axial_load_case not in allowed_axial_cases:
    raise ValueError(f'Unsupported axial load case: {axial_load_case}')
```

When a Type B case has zero pressure and therefore no Formula 12 detail dictionary, skip all detail dereferences, retain the three-ply impact minimum, and append this warning:

```python
('Type B defect at zero design pressure: Formula 12 is non-controlling; '
 'the impact-qualified three-ply minimum is shown and engineering review '
 'of the Type B defect classification is required.')
```

Change the Type B service-life source comment and visible wording to the configured 2-year limit.

- [ ] **Step 4: Run edge-case and inherited engine regression tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_engine_batch_hardening.py tests/engine -v`

Expected: all tests PASS and the inherited baseline values remain unchanged.

- [ ] **Step 5: Commit the batch-safe engine corrections**

```bash
git add engine/prowrap_calculations.py tests/helpers.py tests/test_engine_batch_hardening.py
git commit -m 'fix: harden calculation engine for batch inputs'
```

## Task 3: Define the Batch Schema and Row Validation

**Files:**

- Create: `batch_schema.py`
- Create: `batch_validation.py`
- Modify: `tests/helpers.py`
- Create: `tests/test_batch_schema.py`
- Create: `tests/test_batch_validation.py`

**Interfaces:**

- Produces: `BatchInfo`, `ValidationIssue`, `ValidatedRow`, `INPUT_HEADERS`, `OUTPUT_HEADERS`, `validate_batch_info(values)`, and `validate_row(excel_row, values)`.
- Consumed by: workbook template, workbook processor, and batch adapter.

- [ ] **Step 1: Write failing schema tests**

```python
# tests/test_batch_schema.py
from batch_schema import INPUT_HEADERS, MAX_ROWS, BatchInfo


def test_row_inputs_begin_with_pipe_od_and_exclude_common_fields():
    assert INPUT_HEADERS[0] == 'Pipe OD [mm]'
    assert 'Customer' not in INPUT_HEADERS
    assert 'Project Location' not in INPUT_HEADERS
    assert 'Report No' not in INPUT_HEADERS
    assert MAX_ROWS == 500


def test_batch_info_holds_three_common_values():
    info = BatchInfo('ACME', 'Station 4', 'R-100')
    assert info.customer == 'ACME'
    assert info.project_location == 'Station 4'
    assert info.report_no == 'R-100'
```

- [ ] **Step 2: Create the schema dataclasses and exact header tuples**

```python
# batch_schema.py
from dataclasses import dataclass
from typing import Any

MAX_ROWS = 500
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
STITCH_OVERLAP_MM = 50.0
APPROVED_CLOTH_WIDTHS_MM = (300.0,)

@dataclass(frozen=True)
class BatchInfo:
    customer: str
    project_location: str
    report_no: str

@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str

@dataclass(frozen=True)
class ValidatedRow:
    source_excel_row: int
    values: dict[str, Any]
```

Define `INPUT_HEADERS` in the exact order from the design specification, beginning with `Pipe OD [mm]`. Define `OUTPUT_HEADERS` in the exact order from Section 8 of the design specification.

- [ ] **Step 3: Write failing row-validation tests**

First add this human-header helper to `tests/helpers.py`:

```python
def valid_row_values(**overrides):
    values = {
        'Pipe OD [mm]': 457.2,
        'Nominal Wall [mm]': 9.53,
        'Pipe Yield [MPa]': 359.0,
        'Design Pressure [bar]': 50.0,
        'Operating Temperature [degC]': 40.0,
        'Mechanism': 'Corrosion',
        'Defect Location': 'External',
        'Defect Length [mm]': 100.0,
        'Remaining Wall [mm]': 4.5,
        'Internal Corrosion Rate [mm/year]': None,
        'Design Life [years]': 20,
        'Design Factor': 0.72,
        'Run Type A / Class 3 Check': 'No',
        'Installation Temperature [degC]': 20.0,
        'Component Type': 'Straight',
        'Cyclic Derating Factor': 1.0,
        'Axial Load Case': 0,
        'Prowrap CF Cloth Width [mm]': 300.0,
    }
    values.update(overrides)
    return values
```

Test a valid row, missing common information, remaining wall greater than nominal wall, invalid selections, a formula cell marker, missing internal corrosion rate, cloth width at 50 mm, and an alternate 250 mm width that validates but later requires review.

```python
def test_internal_corrosion_requires_rate():
    values = valid_row_values(**{
        'Mechanism': 'Corrosion',
        'Defect Location': 'Internal',
        'Internal Corrosion Rate [mm/year]': None,
    })
    row, issues = validate_row(2, values)
    assert row is None
    assert [issue.code for issue in issues] == ['INTERNAL_CORROSION_RATE_REQUIRED']
```

- [ ] **Step 4: Implement deterministic validation**

`validate_batch_info` strips surrounding whitespace and requires all three common values. `validate_row` converts finite numeric values, validates the exact selection sets, rejects formulas, requires whole-number design life, enforces `remaining wall <= nominal wall`, and returns all detected issues in input-column order.

Use stable error codes such as `REQUIRED_VALUE`, `INVALID_NUMBER`, `OUT_OF_RANGE`, `INVALID_SELECTION`, `FORMULA_NOT_ALLOWED`, and `INTERNAL_CORROSION_RATE_REQUIRED`.

- [ ] **Step 5: Run schema and validation tests**

Run: `python3 -m pytest tests/test_batch_schema.py tests/test_batch_validation.py -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit the batch contract**

```bash
git add batch_schema.py batch_validation.py tests/test_batch_schema.py tests/test_batch_validation.py
git commit -m 'feat: define batch workbook input contract'
```

## Task 4: Build Row Calculation and Status Classification

**Files:**

- Create: `batch_status.py`
- Create: `batch_adapter.py`
- Modify: `tests/helpers.py`
- Create: `tests/test_batch_status.py`
- Create: `tests/test_batch_adapter.py`

**Interfaces:**

- Consumes: `BatchInfo`, `ValidatedRow`, and the pure engine functions.
- Produces: `CalculationStatus`, `RowCalculation`, `classify_result(result, extra_warnings)`, and `calculate_row(batch_info, row)`.

- [ ] **Step 1: Write failing status-priority tests**

```python
# tests/test_batch_status.py
from batch_status import CalculationStatus, classify_result


def test_not_repairable_has_priority_over_review_warning():
    result = {'type_b_details': {'repairable_formula12': False},
              'compliance_warnings': ['outside validity']}
    assert classify_result(result, ()) is CalculationStatus.NOT_REPAIRABLE


def test_warning_produces_review_required():
    result = {'type_b_details': None, 'compliance_warnings': ['check required']}
    assert classify_result(result, ()) is CalculationStatus.REVIEW_REQUIRED
```

- [ ] **Step 2: Implement the status enum and priority function**

```python
class CalculationStatus(str, Enum):
    OK = 'OK'
    REVIEW_REQUIRED = 'REVIEW REQUIRED'
    NOT_REPAIRABLE = 'NOT REPAIRABLE'
    INPUT_ERROR = 'INPUT ERROR'
    SYSTEM_ERROR = 'SYSTEM ERROR'
```

`classify_result` first detects `repairable_formula12 is False`, then any compliance or adapter warning, and otherwise returns `OK`. Input and system errors are created by the processor, not inferred from engine results.

- [ ] **Step 3: Write failing adapter parity and safety tests**

Add these helpers to `tests/helpers.py`:

```python
from batch_schema import BatchInfo
from batch_validation import validate_row


def batch_info():
    return BatchInfo('Batch Customer', 'Batch Location', 'B-001')


def validated_row(**overrides):
    row, issues = validate_row(2, valid_row_values(**overrides))
    assert not issues
    assert row is not None
    return row
```

```python
def test_adapter_applies_common_info_and_matches_baseline():
    outcome = calculate_row(batch_info(), validated_row())
    assert outcome.status.value == 'OK'
    assert outcome.outputs['Installed Plies'] == 3
    assert outcome.outputs['Installed Thickness [mm]'] == 2.49
    assert outcome.outputs['Total Repair Length [mm]'] == pytest.approx(388.934, rel=1e-3)


def test_not_repairable_blanks_installable_quantities():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Mechanism': 'Leak',
        'Design Pressure [bar]': 100.0,
    }))
    assert outcome.status.value == 'NOT REPAIRABLE'
    for heading in ('Installed Plies', 'Installed Thickness [mm]',
                    'Fabric Area [m2]', 'Epoxy Mass [kg]'):
        assert outcome.outputs[heading] is None
```

- [ ] **Step 4: Implement the adapter**

Define:

```python
@dataclass(frozen=True)
class RowCalculation:
    source_excel_row: int
    status: CalculationStatus
    outputs: dict[str, object]
    error_code: str = ''
    error_message: str = ''
```

Map the common fields to `customer`, `location`, and `report_no`; map each row header to the engine arguments. Run the optional Type A/Class 3 check only when `Run Type A / Class 3 Check` is `Yes` and the route is applicable. Convert MPa pressure outputs to bar with `* 10.0`. Add a review warning for cloth widths not in `(300.0,)`.

Catch only expected `ValueError` as `INPUT ERROR`. Allow unexpected exceptions to reach the processor, which converts them to `SYSTEM ERROR` without exposing a traceback.

- [ ] **Step 5: Run adapter and status tests**

Run: `python3 -m pytest tests/test_batch_status.py tests/test_batch_adapter.py -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit row calculation behavior**

```bash
git add batch_status.py batch_adapter.py tests/test_batch_status.py tests/test_batch_adapter.py
git commit -m 'feat: calculate and classify individual defect rows'
```

## Task 5: Generate the User-Friendly Excel Template

**Files:**

- Create: `workbook_formatting.py`
- Create: `workbook_template.py`
- Modify: `tests/helpers.py`
- Create: `tests/test_workbook_template.py`

**Interfaces:**

- Consumes: schema headers, allowed selections, units, and limits.
- Produces: `create_template_workbook() -> bytes` and reusable formatting helpers.

- [ ] **Step 1: Write failing workbook-structure tests**

```python
def test_template_has_common_info_and_row_table():
    workbook = load_workbook(BytesIO(create_template_workbook()))
    assert workbook.sheetnames == [
        'Batch Information', 'Batch Input & Results',
        'Summary', 'Instructions', 'Lists',
    ]
    info = workbook['Batch Information']
    assert [info['A3'].value, info['A4'].value, info['A5'].value] == [
        'Customer', 'Project Location', 'Report No'
    ]
    data = workbook['Batch Input & Results']
    assert data['A1'].value == 'Pipe OD [mm]'
    assert data.freeze_panes == 'A2'
    assert workbook['Lists'].sheet_state == 'hidden'
```

Also test all input/output headings, dropdown validations, 500-row validation ranges, filter/table presence, comments, input/output colors, and that the workbook contains no formulas.

- [ ] **Step 2: Implement shared formatting primitives**

Create named colors for input headers, output headers, common fields, `OK`, `REVIEW REQUIRED`, `NOT REPAIRABLE`, `INPUT ERROR`, and `SYSTEM ERROR`. Implement header styling, automatic widths with caps, wrapped text, and unlocked input cells.

- [ ] **Step 3: Implement the five-sheet template**

Use `openpyxl.Workbook`. Put common labels in `A3:A5` and blank editable values in `B3:B5`. Place row headings in row 1 of `Batch Input & Results`, with `Pipe OD [mm]` in `A1`. Add Excel list validation for all selections from the hidden `Lists` sheet through row 501. Add instructions and the preliminary-screening disclaimer.

- [ ] **Step 4: Run template tests and open a rendered smoke copy**

Add a reusable filled-workbook helper to `tests/helpers.py`:

```python
from io import BytesIO
from openpyxl import load_workbook

from batch_schema import INPUT_HEADERS
from workbook_template import create_template_workbook


def workbook_bytes_with_rows(rows):
    workbook = load_workbook(BytesIO(create_template_workbook()))
    info = workbook['Batch Information']
    info['B3'] = 'Batch Customer'
    info['B4'] = 'Batch Location'
    info['B5'] = 'B-001'
    data = workbook['Batch Input & Results']
    for excel_row, values in enumerate(rows, start=2):
        for column, header in enumerate(INPUT_HEADERS, start=1):
            data.cell(excel_row, column, values.get(header))
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
```

Run: `python3 -m pytest tests/test_workbook_template.py -v`

Create: `python3 -c "from pathlib import Path; from workbook_template import create_template_workbook; Path('/tmp/PROWRAP_Batch_Template.xlsx').write_bytes(create_template_workbook())"`

Expected: tests PASS and Excel opens the temporary workbook without a repair warning.

- [ ] **Step 5: Commit the template generator**

```bash
git add workbook_formatting.py workbook_template.py tests/test_workbook_template.py
git commit -m 'feat: generate PROWRAP batch Excel template'
```

## Task 6: Parse and Process Complete Workbooks

**Files:**

- Create: `workbook_processor.py`
- Create: `tests/test_workbook_processor.py`

**Interfaces:**

- Consumes: uploaded workbook bytes, schema validation, and `calculate_row`.
- Produces: `inspect_workbook(data) -> WorkbookInspection` and `process_workbook(data, processed_at) -> ProcessedBatch`.

- [ ] **Step 1: Write failing workbook-level tests**

Cover a valid template, missing batch information, missing worksheets, missing/duplicate headings, files over 10 MB, more than 500 populated rows, macros, formulas, and corrupt/password-protected data.

```python
from datetime import UTC, datetime

from tests.helpers import valid_row_values, workbook_bytes_with_rows

FIXED_TIME = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)


def test_one_invalid_row_does_not_stop_valid_rows():
    source = workbook_bytes_with_rows([
        valid_row_values(),
        valid_row_values(**{'Remaining Wall [mm]': 12.0}),
        valid_row_values(),
    ])
    result = process_workbook(source, processed_at=FIXED_TIME)
    assert result.status_counts == {'OK': 2, 'INPUT ERROR': 1}
```

- [ ] **Step 2: Define processor result models**

```python
@dataclass(frozen=True)
class WorkbookInspection:
    batch_info: BatchInfo | None
    populated_rows: int
    valid_rows: int
    invalid_rows: int
    workbook_errors: tuple[ValidationIssue, ...]
    preview: tuple[dict[str, object], ...]

@dataclass(frozen=True)
class ProcessedBatch:
    workbook_bytes: bytes
    status_counts: dict[str, int]
    populated_rows: int
```

- [ ] **Step 3: Implement safe workbook inspection**

Reject data over 10 MB before parsing. Verify the OOXML ZIP does not contain `vbaProject.bin`. Load with `data_only=False`; reject formula cells in common inputs or populated row inputs. Require the exact common labels and exact row headers. Count a row as populated when any input cell is nonblank. Stop with a workbook error above 500 rows.

- [ ] **Step 4: Implement independent row processing and output writing**

Copy the workbook in memory, preserve input cells, calculate each row, and write only the output headings. Convert row-validation issues to `INPUT ERROR` and unexpected adapter exceptions to `SYSTEM ERROR`. Update `Summary` from actual row statuses and serialize diagnostic dictionaries as stable JSON with sorted keys.

- [ ] **Step 5: Run processor tests**

Run: `python3 -m pytest tests/test_workbook_processor.py -v`

Expected: all tests PASS, including mixed-row continuation and input preservation.

- [ ] **Step 6: Commit workbook processing**

```bash
git add workbook_processor.py tests/test_workbook_processor.py
git commit -m 'feat: process batch workbooks row by row'
```

## Task 7: Build the Separate Streamlit User Interface

**Files:**

- Create: `app.py`
- Create: `.streamlit/config.toml`
- Create: `tests/test_app_smoke.py`

**Interfaces:**

- Consumes: `create_template_workbook`, `inspect_workbook`, and `process_workbook`.
- Produces: the four-stage browser workflow and a downloadable processed workbook.

- [ ] **Step 1: Write a failing Streamlit smoke test**

```python
from streamlit.testing.v1 import AppTest


def test_app_starts_with_template_and_upload_actions():
    app = AppTest.from_file('app.py').run()
    assert not app.exception
    assert any('PROWRAP Batch Repair Calculator' in title.value
               for title in app.title)
    assert any('Download Excel Template' in button.label
               for button in app.download_button)
```

- [ ] **Step 2: Implement the four visible stages**

Build a single page with:

1. title, purpose, and isolation note;
2. template download button;
3. `.xlsx` uploader with 10 MB guidance;
4. inspection summary and first-20-row preview;
5. calculate button;
6. status-count cards and processed-workbook download.

Use plain-language messages. Do not display stack traces, retain files, or call the existing v1.1 website.

- [ ] **Step 3: Keep calculations explicit and repeat-safe**

Store the processed bytes and source-file hash in `st.session_state`. Clear the processed result when a different upload arrives. Name the output `PROWRAP_Batch_Results_<YYYYMMDD_HHMMSS>.xlsx` and disable calculation only for workbook-level errors, not invalid rows.

- [ ] **Step 4: Run UI smoke and processor tests**

Run: `python3 -m pytest tests/test_app_smoke.py tests/test_workbook_processor.py -v`

Run: `streamlit run app.py --server.headless true`

Expected: tests PASS and the local page loads with no exception.

- [ ] **Step 5: Commit the separate batch UI**

```bash
git add app.py .streamlit/config.toml tests/test_app_smoke.py
git commit -m 'feat: add user-friendly Streamlit batch workflow'
```

## Task 8: Add End-to-End Acceptance Coverage and Deployment Handoff

**Files:**

- Create: `scripts/create_acceptance_workbook.py`
- Create: `tests/test_full_batch_acceptance.py`
- Create: `README.md`
- Create: `DEPLOYMENT.md`
- Modify: `ENGINE_SOURCE.md`

**Interfaces:**

- Consumes: the complete application stack.
- Produces: a repeatable acceptance workbook, full regression evidence, and instructions for a separate Streamlit deployment.

- [ ] **Step 1: Write the failing end-to-end acceptance test**

Generate a workbook containing:

1. baseline external corrosion;
2. a valid alternate cloth width that requires review;
3. a Formula 12 case that is not repairable;
4. remaining wall greater than nominal wall;
5. a zero-pressure leak.

Assert statuses in row order:

```python
assert statuses == [
    'OK', 'REVIEW REQUIRED', 'NOT REPAIRABLE',
    'INPUT ERROR', 'REVIEW REQUIRED',
]
```

Assert all rows contain common Customer, Project Location, and Report No values in their engine invocation evidence without repeating those values in the defect table.

- [ ] **Step 2: Implement the acceptance-workbook generator**

The script starts from `create_template_workbook()`, fills the three common cells and five controlled rows, and writes only to a caller-supplied path. It must not write into the repository during tests; tests use a temporary directory.

- [ ] **Step 3: Write operating and deployment documentation**

`README.md` covers setup, template use, statuses, row limit, privacy, and test commands. `DEPLOYMENT.md` requires a new GitHub repository and a new Streamlit application, explicitly prohibits selecting the existing v1.1 app during deployment, and includes a rollback procedure that affects only the batch app.

Update `ENGINE_SOURCE.md` with the final list of intentional batch-only corrections and the release version `1.0.0`.

- [ ] **Step 4: Run the complete verification suite**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q`

Expected: all inherited engine, batch, workbook, UI, and end-to-end tests PASS.

Run: `python3 scripts/create_acceptance_workbook.py /tmp/PROWRAP_Batch_Acceptance.xlsx`

Run the local app, upload the acceptance workbook, and verify the downloaded workbook opens in Excel with the five expected statuses and no repair warning.

- [ ] **Step 5: Verify the existing calculator remains untouched**

Run: `git -C /Users/can/Documents/GitHub/Iso24817Calcv1.1 status --short --branch`

Expected: the same clean local state observed before implementation; no files or commits from this project appear there.

Open `https://iso24817calc-prowrapv11.streamlit.app` read-only and verify the existing single-case calculator still loads independently.

- [ ] **Step 6: Commit the acceptance and deployment package**

```bash
git add scripts/create_acceptance_workbook.py tests/test_full_batch_acceptance.py README.md DEPLOYMENT.md ENGINE_SOURCE.md
git commit -m 'docs: add batch acceptance and deployment handoff'
```

## Final Verification Gate

Before declaring implementation complete:

1. Run `git status --short --branch` in `Iso24817CalcBatch`; expected result is a clean working tree.
2. Run `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q`; record the exact pass count.
3. Generate and process the acceptance workbook; record all five row statuses.
4. Open the processed workbook in Excel and confirm filters, frozen panes, dropdowns, colors, common information, appended row outputs, and no repair warning.
5. Confirm `Iso24817Calcv1.1` is unchanged and its existing Streamlit URL still works.
6. Deploy only to a new staging application; do not connect the new repository to the existing v1.1 Streamlit application.
