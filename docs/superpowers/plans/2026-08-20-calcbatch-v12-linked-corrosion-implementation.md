# PROWRAP CalcBatch v1.2 Linked Corrosion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separate CalcBatch-v1.2 application that supports Actual, Independent, and linked Manual external-corrosion assessments while preserving one continuous-repair result and commercial row per main Excel row.

**Architecture:** Fork the verified current CalcBatch baseline into an isolated repository, port the verified v1.2 corrosion-domain model into the pinned engine, and extend the controlled workbook with a normalized `Individual Defects` table linked by `Repair Group ID`. Keep workbook parsing, row linking, calculation, result writing, commercial formulas, and Streamlit display in separate units so legacy seven-sheet uploads can be upgraded safely into the new trusted eight-sheet output.

**Tech Stack:** Python 3.12+, Streamlit, openpyxl, pytest, Streamlit AppTest, the existing pure-Python PROWRAP engine, LibreOffice for independent formula recalculation, and the spreadsheet artifact tooling for final visual inspection.

**Spec:** `docs/superpowers/specs/2026-08-20-calcbatch-v12-linked-corrosion-design.md`

## Global Constraints

- Work only in `Iso24817CalcBatch-v1.2`; do not edit, push, redeploy, or reconfigure current CalcBatch, v1.1, or either existing live application.
- Start execution in an isolated worktree on branch `feature/linked-corrosion-v12` created from committed `main` revision `6e1596d169ccb3574abfb6a8fb5a7e71fb4aaee7`.
- Port calculation behavior from verified `Iso24817Calcv1.2` revision `91b68d64508a4786934f0e17f2aea0dbebf745a7` while retaining every documented batch-only correction.
- Keep Customer, Project Location, and Report No common to the batch; keep Pipe OD in every main repair row.
- Keep one main row, one cost row, and one final status per continuous repair.
- Keep maximums of 500 main rows, 2,000 individual-defect rows, and 10 MB uploaded workbook size.
- Blank templates contain no formulas. Processed workbooks contain only the existing controlled Cost and Price formulas.
- All production behavior changes use strict RED-GREEN-REFACTOR test-driven development.
- Do not deploy Streamlit or publish GitHub content during implementation; those remain separately approved release actions.

---

### Task 1: Port the Verified v1.2 Corrosion Engine

**Files:**
- Create: `engine/corrosion_defects.py`
- Create: `tests/test_engine_corrosion_v12.py`
- Modify: `engine/prowrap_calculations.py`
- Modify: `engine/__init__.py`
- Modify: `tests/test_engine_snapshot.py`
- Modify: `ENGINE_SOURCE.md`

**Interfaces:**
- Consumes: current batch `calculate_repair(...)`, B31G, material, dent, temperature-review, and Type A / Class 3 behavior.
- Produces: `ACTUAL_DEFECT_LENGTH`, `INDEPENDENT_DEFECTS`, `ENTER_MANUALLY`, `DEFECT_LENGTH_BASES`, `IndividualCorrosionDefect`, `CorrosionAssessmentPlan`, and `build_corrosion_assessment_plan(...)`; extends `calculate_repair(..., defect_length_basis=ACTUAL_DEFECT_LENGTH, individual_defects=())` and returns the verified v1.2 corrosion trace fields.

- [ ] **Step 1: Write failing engine acceptance and compatibility tests**

```python
def test_three_modes_match_verified_v12_and_keep_the_full_repair_zone():
    base = dict(
        customer="PROTAP", location="Turkey", report_no="BATCH-V12",
        od=1016.0, wall=12.0, pressure=104.9, temp=40.0,
        defect_type="Corrosion", defect_loc="External", length=1000.0,
        rem_wall=9.652, yield_strength=450.0, design_factor=0.72,
        design_life=20, cloth_width_mm=500.0,
        allow_unqualified_temperature=True,
    )
    actual = calculate_repair(**base, defect_length_basis=ACTUAL_DEFECT_LENGTH)
    independent = calculate_repair(**base, defect_length_basis=INDEPENDENT_DEFECTS)
    manual = calculate_repair(
        **base,
        defect_length_basis=ENTER_MANUALLY,
        individual_defects=(
            IndividualCorrosionDefect("D-01", 10.0, 9.652, True),
            IndividualCorrosionDefect("D-02", 35.0, 10.0, True),
        ),
    )
    assert actual["p_steel_capacity"] == pytest.approx(7.571542406120033)
    assert independent["p_steel_capacity"] == pytest.approx(8.82257484144555)
    assert manual["p_steel_capacity"] == pytest.approx(8.783461911867068)
    assert (actual["num_plies"], independent["num_plies"], manual["num_plies"]) == (12, 7, 7)
    assert manual["governing_defect_id"] == "D-02"
    assert manual["governing_b31g_length_mm"] == 35.0
    for result in (actual, independent, manual):
        covered = result["iso_length"] - 2 * result["overlap_length"] - 2 * result["taper_length"]
        assert covered == pytest.approx(1000.0)


def test_actual_default_preserves_existing_batch_result():
    implicit = calculate_repair(**valid_engine_inputs())
    explicit = calculate_repair(
        **valid_engine_inputs(), defect_length_basis=ACTUAL_DEFECT_LENGTH,
    )
    assert explicit == implicit
```

- [ ] **Step 2: Run the new tests and confirm the missing-domain RED**

Run: `pytest -q tests/test_engine_corrosion_v12.py`

Expected: collection fails because `engine.corrosion_defects` and the two new `calculate_repair` arguments do not exist.

- [ ] **Step 3: Add the v1.2 domain model and merge the verified engine route**

```python
@dataclass(frozen=True)
class IndividualCorrosionDefect:
    defect_id: str
    longitudinal_length_mm: float
    remaining_wall_mm: float
    separation_exceeds_3t: bool


@dataclass(frozen=True)
class CorrosionAssessmentPlan:
    basis: str
    repair_zone_length_mm: float
    interaction_distance_mm: float
    candidates: tuple[IndividualCorrosionDefect, ...]
    minimum_remaining_wall_mm: float
    assumptions: tuple[str, ...]
```

Copy the verified validation and candidate-construction semantics from v1.2, then merge its B31G candidate loop and returned trace fields into the package-relative batch engine. Preserve `allow_unqualified_temperature=False` in the engine signature and the current batch high-temperature warning route; do not replace the current batch module wholesale.

- [ ] **Step 4: Add governing, pairing, applicability, high-SMYS, and noncorrosion tests**

```python
def test_manual_never_pairs_length_and_wall_from_different_defects():
    result = calculate_repair(
        **valid_engine_inputs(wall=12.0, length=500.0),
        defect_length_basis=ENTER_MANUALLY,
        individual_defects=(
            IndividualCorrosionDefect("LONG", 300.0, 11.0, True),
            IndividualCorrosionDefect("DEEP", 10.0, 9.0, True),
        ),
    )
    pairs = {
        item["defect_id"]: (item["length_mm"], item["remaining_wall_mm"])
        for item in result["b31g_assessments"]
    }
    assert pairs == {"LONG": (300.0, 11.0), "DEEP": (10.0, 9.0)}


def test_nonexternal_corrosion_ignores_the_new_basis_route():
    baseline = calculate_repair(**valid_engine_inputs(defect_loc="Internal"))
    changed = calculate_repair(
        **valid_engine_inputs(defect_loc="Internal"),
        defect_length_basis=INDEPENDENT_DEFECTS,
    )
    assert changed == baseline
```

- [ ] **Step 5: Run engine and inherited batch regression tests**

Run: `pytest -q tests/test_engine_corrosion_v12.py tests/test_engine_batch_hardening.py tests/test_batch_status.py tests/test_warning_catalog.py`

Expected: all pass, including 110 degC, 500 mm cloth, dent, zero-pressure, and high-SMYS warning behavior.

- [ ] **Step 6: Record exact provenance and commit**

Update `ENGINE_SOURCE.md` with source revision `91b68d64508a4786934f0e17f2aea0dbebf745a7`, source files `corrosion_defects.py` and `prowrap_calculations.py`, and retained batch-only differences. Set `SOURCE_ENGINE_REVISION = '91b68d6'` in the later processor task; leave the current workbook version unchanged until that task.

Run: `git add engine tests/test_engine_corrosion_v12.py tests/test_engine_snapshot.py ENGINE_SOURCE.md && git commit -m "feat: port verified v1.2 corrosion engine"`

---

### Task 2: Define Current and Legacy Workbook Schemas

**Files:**
- Create: `batch_corrosion.py`
- Create: `tests/test_batch_corrosion.py`
- Modify: `batch_schema.py`
- Modify: `batch_validation.py`
- Modify: `tests/helpers.py`
- Modify: `tests/test_batch_schema.py`
- Modify: `tests/test_batch_validation.py`

**Interfaces:**
- Consumes: Task 1 `IndividualCorrosionDefect` and exact basis constants.
- Produces: `MAX_DETAIL_ROWS = 2000`, `LEGACY_INPUT_HEADERS`, `LEGACY_OUTPUT_HEADERS`, `DETAIL_INPUT_HEADERS`, `DETAIL_OUTPUT_HEADERS`, `ValidatedIndividualDefectRow`, `validate_individual_defect_row(...)`, `ManualGroupLinks`, and `link_manual_groups(...)`.

- [ ] **Step 1: Write failing schema-order and mode-dependent validation tests**

```python
def test_v12_inputs_insert_basis_and_group_after_defect_length():
    start = INPUT_HEADERS.index("Defect Length [mm]")
    assert INPUT_HEADERS[start:start + 4] == (
        "Defect Length [mm]", "Defect Length Basis",
        "Repair Group ID", "Remaining Wall [mm]",
    )
    assert MAX_ROWS == 500
    assert MAX_DETAIL_ROWS == 2000


@pytest.mark.parametrize("basis", [ACTUAL_DEFECT_LENGTH, INDEPENDENT_DEFECTS])
def test_nonmanual_external_requires_wall_and_rejects_group_id(basis):
    row, issues = validate_row(2, valid_row_values(**{
        "Defect Length Basis": basis,
        "Repair Group ID": "R-001",
        "Remaining Wall [mm]": None,
    }))
    assert row is None
    assert [issue.code for issue in issues] == [
        "REPAIR_GROUP_NOT_ALLOWED", "REQUIRED_VALUE",
    ]


def test_manual_external_requires_group_and_blank_main_wall():
    row, issues = validate_row(2, valid_row_values(**{
        "Defect Length Basis": ENTER_MANUALLY,
        "Repair Group ID": "R-001",
        "Remaining Wall [mm]": None,
    }))
    assert issues == ()
    assert row.values["Repair Group ID"] == "R-001"
```

- [ ] **Step 2: Run schema/validation tests and confirm RED**

Run: `pytest -q tests/test_batch_schema.py tests/test_batch_validation.py`

Expected: assertions fail because the v1.2 headers, constants, and conditional validation do not exist.

- [ ] **Step 3: Add explicit current/legacy header contracts and row types**

```python
MAX_DETAIL_ROWS = 2000
DETAIL_INPUT_HEADERS = (
    "Repair Group ID", "Defect ID",
    "Individual longitudinal length [mm]", "Remaining wall [mm]",
    "Separation exceeds 3t",
)
DETAIL_OUTPUT_HEADERS = (
    "Source Excel Row", "Calculation Status", "Error Code", "Error Message",
    "B31G Method", "B31G Applicable", "B31G Acceptable",
    "Credited Safe Pressure [bar]", "Governing Defect",
    "Assessment Warning Codes",
)


@dataclass(frozen=True)
class ValidatedIndividualDefectRow:
    source_excel_row: int
    repair_group_id: str
    defect_id: str
    longitudinal_length_mm: float
    remaining_wall_mm: float
    separation_exceeds_3t: bool
```

Freeze the exact pre-v1.2 main input/output tuples in `LEGACY_INPUT_HEADERS` and `LEGACY_OUTPUT_HEADERS`; build the new `INPUT_HEADERS` by semantic insertion, not positional renaming.

- [ ] **Step 4: Write failing detail-row and linking tests**

```python
def test_linker_preserves_detail_order_and_reports_orphans():
    main = (validated_row(**{
        "Defect Length Basis": ENTER_MANUALLY,
        "Repair Group ID": "R-001", "Remaining Wall [mm]": None,
    }),)
    linked = link_manual_groups(
        main,
        (
            valid_detail_row(2, group="R-001", defect="D-02", length=35, wall=10),
            valid_detail_row(3, group="R-001", defect="D-01", length=10, wall=9.652),
            valid_detail_row(4, group="ORPHAN", defect="D-X", length=10, wall=9),
        ),
        detail_issues={},
    )
    assert [item.defect_id for item in linked.detail_rows_by_main_excel_row[2]] == ["D-02", "D-01"]
    assert linked.detail_issues[4][0].code == "ORPHAN_REPAIR_GROUP"


def test_duplicate_main_group_marks_both_main_rows_input_error():
    links = link_manual_groups((manual_main(2, "R-001"), manual_main(3, "R-001")), (), {})
    assert links.main_issues[2][0].code == "DUPLICATE_REPAIR_GROUP"
    assert links.main_issues[3][0].code == "DUPLICATE_REPAIR_GROUP"
```

- [ ] **Step 5: Implement detail validation and deterministic linking**

```python
@dataclass(frozen=True)
class ManualGroupLinks:
    defects_by_main_excel_row: dict[int, tuple[IndividualCorrosionDefect, ...]]
    detail_rows_by_main_excel_row: dict[int, tuple[ValidatedIndividualDefectRow, ...]]
    main_issues: dict[int, tuple[ValidationIssue, ...]]
    detail_issues: dict[int, tuple[ValidationIssue, ...]]


def link_manual_groups(
    main_rows: tuple[ValidatedRow, ...],
    detail_rows: tuple[ValidatedIndividualDefectRow, ...],
    detail_issues: dict[int, tuple[ValidationIssue, ...]],
) -> ManualGroupLinks:
    """Link exact trimmed IDs, retain worksheet order, and localize ambiguity."""
```

Perform linked length and wall bounds against the main row here. Require exact `Yes` in uploaded detail cells and convert it to `True` only after validation.

- [ ] **Step 6: Run validation/linking tests and commit**

Run: `pytest -q tests/test_batch_schema.py tests/test_batch_validation.py tests/test_batch_corrosion.py`

Expected: all pass with issue ordering matching workbook column order.

Run: `git add batch_schema.py batch_validation.py batch_corrosion.py tests && git commit -m "feat: define linked corrosion workbook data"`

---

### Task 3: Adapt One Main Row and Its Candidate Results

**Files:**
- Modify: `batch_adapter.py`
- Modify: `tests/test_batch_adapter.py`
- Modify: `warning_catalog.py`
- Modify: `tests/test_warning_catalog.py`

**Interfaces:**
- Consumes: Task 1 engine and Task 2 validated/linking types.
- Produces: `CandidateCalculation`, `RowCalculation.candidate_calculations`, and `calculate_row(batch_info, row, individual_defects=())`.

- [ ] **Step 1: Write failing adapter tests for all three modes**

```python
def test_manual_adapter_returns_main_and_candidate_outputs():
    outcome = calculate_row(
        batch_info(),
        validated_row(**{
            "Pipe OD [mm]": 1016.0, "Nominal Wall [mm]": 12.0,
            "Pipe Yield [MPa]": 450.0, "Design Pressure [bar]": 104.9,
            "Defect Length [mm]": 1000.0,
            "Defect Length Basis": ENTER_MANUALLY,
            "Repair Group ID": "R-001", "Remaining Wall [mm]": None,
            "Prowrap CF Cloth Width [mm]": 500.0,
        }),
        individual_defects=(
            IndividualCorrosionDefect("D-01", 10.0, 9.652, True),
            IndividualCorrosionDefect("D-02", 35.0, 10.0, True),
        ),
    )
    assert outcome.status.value == "REVIEW REQUIRED"
    assert outcome.outputs["Repair Zone Length [mm]"] == 1000.0
    assert outcome.outputs["B31G Candidate Count"] == 2
    assert outcome.outputs["Governing Defect ID"] == "D-02"
    assert outcome.outputs["Governing B31G Length [mm]"] == 35.0
    assert [item.defect_id for item in outcome.candidate_calculations] == ["D-01", "D-02"]
```

- [ ] **Step 2: Run adapter tests and confirm RED**

Run: `pytest -q tests/test_batch_adapter.py -k 'manual or independent or actual'`

Expected: failures show the adapter does not pass basis/defects or expose candidate outputs.

- [ ] **Step 3: Add candidate result type and map engine trace fields**

```python
@dataclass(frozen=True)
class CandidateCalculation:
    defect_id: str
    method: str
    applicable: bool
    acceptable: bool
    credited_safe_pressure_bar: float
    governing: bool
    warning_codes: tuple[str, ...]


@dataclass(frozen=True)
class RowCalculation:
    source_excel_row: int
    status: CalculationStatus
    outputs: dict[str, object]
    error_code: str = ""
    error_message: str = ""
    candidate_calculations: tuple[CandidateCalculation, ...] = ()
```

Pass `defect_length_basis`, manual candidates, governing substrate pressure, and conservative minimum wall to the same engine and optional Type A path used by v1.2. Preserve installable-output blanking for `NOT REPAIRABLE`.

- [ ] **Step 4: Verify warnings resolve at both main and candidate levels**

Add tests proving a candidate-prefixed W011 Original B31G fallback and W013 structural warning resolve to the existing permanent codes, without adding assumption-only warnings.

Run: `pytest -q tests/test_batch_adapter.py tests/test_warning_catalog.py tests/test_batch_status.py`

Expected: all pass, and candidate warning order follows candidate worksheet order.

- [ ] **Step 5: Commit the adapter boundary**

Run: `git add batch_adapter.py warning_catalog.py tests/test_batch_adapter.py tests/test_warning_catalog.py && git commit -m "feat: calculate linked corrosion repair rows"`

---

### Task 4: Build the Eight-Sheet Controlled Template

**Files:**
- Modify: `workbook_template.py`
- Modify: `workbook_formatting.py`
- Modify: `tests/test_workbook_template.py`

**Interfaces:**
- Consumes: Task 2 schema constants and current workbook formatting helpers.
- Produces: `create_template_workbook()` with exact eight-sheet order and `IndividualDefects` table covering rows 2 through 2001.

- [ ] **Step 1: Write failing structure, controls, and guidance tests**

```python
def test_v12_template_has_linked_detail_sheet_in_controlled_order():
    workbook = _template_workbook()
    assert workbook.sheetnames == [
        "Batch Information", "Batch Input & Results", "Individual Defects",
        "Cost Calculation", "Warnings", "Summary", "Instructions", "Lists",
    ]
    detail = workbook["Individual Defects"]
    assert tuple(cell.value for cell in detail[1]) == DETAIL_INPUT_HEADERS + DETAIL_OUTPUT_HEADERS
    assert detail.freeze_panes == "B2"
    assert detail.tables["IndividualDefects"].ref.endswith(str(MAX_DETAIL_ROWS + 1))
    assert detail.protection.sheet is True
    assert detail.protection.autoFilter is False
    assert detail["A2"].protection.locked is False
    assert detail.cell(2, len(DETAIL_INPUT_HEADERS) + 1).protection.locked is True


def test_v12_template_has_exact_basis_and_yes_dropdowns():
    workbook = _template_workbook()
    main = workbook["Batch Input & Results"]
    detail = workbook["Individual Defects"]
    validations = {item.formula1: str(item.sqref) for item in main.data_validations.dataValidation}
    assert validations["=DefectLengthBasisChoices"] == "I2:I501"
    detail_validations = {item.formula1: str(item.sqref) for item in detail.data_validations.dataValidation}
    assert detail_validations["=SeparationChoices"] == "E2:E2001"
```

- [ ] **Step 2: Run template tests and confirm RED**

Run: `pytest -q tests/test_workbook_template.py`

Expected: sheet-order, header, dropdown, and instruction assertions fail.

- [ ] **Step 3: Add the detail table and semantic dropdown routing**

Create `_build_individual_defects(worksheet)` using existing header, border, width, protection, and conditional-format helpers. Unlock only the five input columns. Add defined names for exact basis choices and `Yes`/blank separation input. Update main dropdown columns from header lookup rather than hardcoded letters.

- [ ] **Step 4: Add concise mode and linking instructions**

The rendered instruction text must contain these exact concepts:

```text
Actual defect length = continuous or interacting B31G length.
Independent defects = 10 x 10 mm, each separated by more than 3t.
t means nominal pipe wall thickness.
Enter manually = leave main Remaining Wall blank and link detail rows with Repair Group ID.
Defect Length remains the complete outer-to-outer continuous repair-zone span.
```

- [ ] **Step 5: Verify the template remains formula-free and commit**

Run: `pytest -q tests/test_workbook_template.py tests/test_cost_calculation.py`

Expected: all pass; every formula scan of the blank template returns an empty list.

Run: `git add workbook_template.py workbook_formatting.py tests/test_workbook_template.py && git commit -m "feat: add linked individual defects worksheet"`

---

### Task 5: Inspect, Upgrade, Calculate, and Rebuild Workbooks

**Files:**
- Modify: `workbook_processor.py`
- Modify: `tests/helpers.py`
- Modify: `tests/test_workbook_processor.py`
- Create: `tests/test_legacy_v12_upgrade.py`

**Interfaces:**
- Consumes: Tasks 2-4 schemas, validation/linking, adapter, and trusted template.
- Produces: extended `WorkbookInspection`, exact legacy/current contract recognition, linked preview/calculation, protected detail outputs, and current eight-sheet processed workbooks.

- [ ] **Step 1: Write failing current-workbook inspection tests**

```python
def test_inspection_reports_main_detail_and_manual_group_counts():
    source = workbook_bytes_with_rows(
        [manual_row(group="R-001")],
        detail_rows=[
            detail_values(group="R-001", defect="D-01", length=10, wall=9.652),
            detail_values(group="R-001", defect="D-02", length=35, wall=10.0),
        ],
    )
    inspection = inspect_workbook(source)
    assert inspection.workbook_errors == ()
    assert inspection.populated_rows == 1
    assert inspection.populated_detail_rows == 2
    assert inspection.manual_groups == 1
    assert inspection.recognized_detail_input_headers == DETAIL_INPUT_HEADERS
```

- [ ] **Step 2: Write failing legacy-upgrade tests before changing parsing**

Build a seven-sheet fixture from the frozen legacy headers and current baseline values. Assert:

```python
processed = process_workbook(legacy_bytes, FIXED_TIME, "legacy.xlsx")
workbook = load_workbook(BytesIO(processed.workbook_bytes), data_only=False)
assert workbook.sheetnames == CURRENT_SHEETS
main = workbook["Batch Input & Results"]
assert main.cell(2, column("Defect Length Basis")).value == ACTUAL_DEFECT_LENGTH
assert main.cell(2, column("Repair Group ID")).value is None
assert main.cell(2, column("Installed Plies")).value == legacy_expected_plies
assert not populated_detail_rows(workbook["Individual Defects"])
```

- [ ] **Step 3: Run processor tests and confirm RED**

Run: `pytest -q tests/test_workbook_processor.py tests/test_legacy_v12_upgrade.py`

Expected: current sheet/header validation rejects the new sheet and cannot classify legacy versus v1.2 headers.

- [ ] **Step 4: Implement exact contract classification and header-based copying**

```python
@dataclass(frozen=True)
class WorkbookContract:
    sheet_order: tuple[str, ...]
    input_headers: tuple[str, ...]
    output_headers: tuple[str, ...]
    has_individual_defects: bool
    is_legacy: bool
```

Accept only the frozen legacy seven-sheet order/header contract and the new current eight-sheet order/header contract. Rebuild every processed download from `create_template_workbook()`. Copy main inputs by exact heading map; for legacy external corrosion set Actual explicitly and leave Repair Group ID blank. Copy only controlled commercial assumptions and never copy uploaded result cells or formulas.

- [ ] **Step 5: Implement linked preparation and row-local calculation**

Parse main and detail rows only through their controlled maximums, validate each table, call `link_manual_groups`, then calculate each valid main row with its ordered defect tuple. Merge link issues into only the affected main result. Write orphan and invalid detail statuses even when no main row can be calculated.

Map `RowCalculation.candidate_calculations` back to linked detail rows by stable tuple order and write `Yes` to exactly the governing detail row.

- [ ] **Step 6: Extend inspection/header summaries without relaxing structure**

Add these fields to `WorkbookInspection`:

```python
populated_detail_rows: int
manual_groups: int
recognized_detail_input_headers: tuple[str, ...]
missing_detail_input_headers: tuple[str, ...]
unexpected_detail_headers: tuple[str, ...]
```

Preview each main row with Repair Group ID and basis. Report detail headings separately. Keep formulas, macros, sparse-cell, ZIP expansion, and out-of-range checks ahead of openpyxl-intensive processing; adjust the aggregate parsed-cell ceiling only to the measured current template maximum plus at least 25 percent headroom.

- [ ] **Step 7: Add processed re-upload, stale-output, and maximum-row tests**

```python
def test_processed_manual_workbook_reuploads_without_changing_results():
    first = process_workbook(manual_source(), FIXED_TIME, "manual.xlsx")
    second = process_workbook(first.workbook_bytes, FIXED_TIME, "manual-processed.xlsx")
    assert result_signature(second.workbook_bytes) == result_signature(first.workbook_bytes)


def test_exact_maximum_rows_are_kept_and_first_out_of_range_rows_reject():
    assert inspect_workbook(source_with_500_main_and_2000_details()).workbook_errors == ()
    assert issue_code(source_with_main_row_502()) == "INPUT_ROW_OUT_OF_RANGE"
    assert issue_code(source_with_detail_row_2002()) == "DETAIL_ROW_OUT_OF_RANGE"
```

- [ ] **Step 8: Run processor boundary suites and commit**

Run: `pytest -q tests/test_workbook_processor.py tests/test_legacy_v12_upgrade.py tests/test_engine_batch_hardening.py`

Expected: all pass, including formula objects, far-dimension cells, exact limits, processed re-upload, and row-local continuation.

Run: `git add workbook_processor.py tests && git commit -m "feat: process linked corrosion workbooks"`

---

### Task 6: Preserve Cost, Warning, Summary, and Formula Contracts

**Files:**
- Modify: `cost_calculation.py`
- Modify: `workbook_processor.py`
- Modify: `warning_catalog.py`
- Modify: `tests/test_cost_calculation.py`
- Modify: `tests/test_warning_catalog.py`
- Modify: `tests/test_full_batch_acceptance.py`

**Interfaces:**
- Consumes: current main/detail result headers from Tasks 2-5.
- Produces: semantic cost mapping, detail-aware warning affected-row text, updated source revision metadata, and exact controlled formula output.

- [ ] **Step 1: Write failing semantic commercial mapping tests**

```python
def test_cost_source_headers_survive_inserted_v12_columns():
    assert COST_SOURCE_HEADERS == (
        "Pipe OD [mm]", "Nominal Wall [mm]", "Pipe Yield [MPa]",
        "Design Pressure [bar]", "Operating Temperature [degC]",
        "Mechanism", "Defect Location", "Defect Length [mm]",
        "Remaining Wall [mm]", "Design Life [years]", "Design Factor",
        "Prowrap CF Cloth Width [mm]", "Wall Loss [%]",
        "Required Structural Thickness [mm]", "Installed Plies",
        "Total Repair Length [mm]", "Cloth Band Count",
        "Procurement Axial Length [mm]", "Fabric Area [m2]", "Epoxy Mass [kg]",
    )
```

- [ ] **Step 2: Replace positional cost selection with explicit header names**

Define the tuple exactly as asserted above. Continue resolving source columns from `INPUT_HEADERS + OUTPUT_HEADERS` at runtime. Do not change `CostRows`, assumption cells B3/E3/H3, or U/V formulas.

- [ ] **Step 3: Add detail-aware warning and summary tests**

```python
def test_warning_register_identifies_main_and_detail_rows():
    workbook = processed_manual_warning_workbook()
    warning_rows = warning_register(workbook)
    assert warning_rows["W013"] == "Main 2; Individual Defects 2, 3"
    assert workbook["Summary"]["B24"].value == "1.2.0"
    assert workbook["Summary"]["B25"].value == "91b68d6"
```

Only include a detail row under a warning code it actually emitted. Main warnings remain linked to main Excel rows.

- [ ] **Step 4: Verify formula allowlist and commercial recalculation**

Run: `pytest -q tests/test_cost_calculation.py tests/test_warning_catalog.py tests/test_full_batch_acceptance.py`

Expected: formulas exist only in processed `Cost Calculation!U:V`, table and auto-filter refs match, invalid/no-solution material cells stay blank, and 500 mm cloth adds no warning.

- [ ] **Step 5: Commit the commercial and audit boundary**

Run: `git add cost_calculation.py workbook_processor.py warning_catalog.py tests && git commit -m "feat: preserve v1.2 batch commercial audit"`

---

### Task 7: Update the Streamlit Workflow and Product Identity

**Files:**
- Modify: `app.py`
- Modify: `.streamlit/config.toml`
- Modify: `tests/test_app_smoke.py`

**Interfaces:**
- Consumes: Task 5 extended `WorkbookInspection` and processed workbook.
- Produces: v1.2 template/download names, two-table header inspection, main/detail/manual metrics, and unchanged session-bound safe download behavior.

- [ ] **Step 1: Write failing AppTest assertions**

```python
def test_app_identifies_itself_as_separate_v12_and_previews_linked_counts():
    app = AppTest.from_file(ROOT / "app.py").run()
    assert any("PROWRAP CalcBatch v1.2" in title.value for title in app.title)
    assert app.download_button[0].file_name == "PROWRAP_CalcBatch_v1.2_Template.xlsx"
    app.file_uploader[0].upload(
        "linked.xlsx", manual_source(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ).run()
    rendered = "\n".join(item.value for item in app.markdown)
    assert "1 populated repair row" in rendered
    assert "2 populated individual-defect rows" in rendered
    assert "1 manual repair group" in rendered
    assert "Recognized Individual Defects input columns (5)" in rendered
```

- [ ] **Step 2: Run AppTest and confirm RED**

Run: `pytest -q tests/test_app_smoke.py`

Expected: product-title, filename, detail-header, and linked-count assertions fail.

- [ ] **Step 3: Implement v1.2 guidance and detail inspection**

Use title `PROWRAP CalcBatch v1.2`, template filename `PROWRAP_CalcBatch_v1.2_Template.xlsx`, and processed filename prefix `PROWRAP_CalcBatch_v1.2_Results_`. Explain that Manual mode requires Repair Group IDs and the Individual Defects sheet. Display separate recognized/missing/unexpected lists for both tables.

- [ ] **Step 4: Preserve cache identity and safe failure behavior**

Keep source identity bound to both workbook bytes and exact filename. Keep calculate enabled for structurally valid workbooks with row-level errors. Do not display internal exception messages or customer inputs.

- [ ] **Step 5: Run AppTest and commit**

Run: `pytest -q tests/test_app_smoke.py tests/test_workbook_processor.py -k 'inspection or preview or source_identity or upload'`

Expected: all pass with no Streamlit exceptions.

Run: `git add app.py .streamlit/config.toml tests/test_app_smoke.py && git commit -m "feat: guide linked CalcBatch v1.2 uploads"`

---

### Task 8: Document, Generate, and Test the Release Acceptance Workbook

**Files:**
- Modify: `README.md`
- Modify: `DEPLOYMENT.md`
- Modify: `ENGINE_SOURCE.md`
- Modify: `scripts/create_acceptance_workbook.py`
- Modify: `tests/test_full_batch_acceptance.py`
- Create: `docs/superpowers/reports/2026-08-20-calcbatch-v12-verification.md`

**Interfaces:**
- Consumes: complete Tasks 1-7 application.
- Produces: reproducible acceptance input, end-to-end assertions, operator instructions, separate-release guidance, and verification evidence.

- [ ] **Step 1: Write the failing eight-sheet acceptance test**

The generated source shall contain:

```python
expected_rows = (
    ("Actual defect length", None, "Corrosion", "External"),
    ("Independent defects", None, "Corrosion", "External"),
    ("Enter manually", "R-001", "Corrosion", "External"),
    ("Enter manually", "R-BAD", "Corrosion", "External"),
    (None, None, "Dent no-crack", "External"),
    (None, None, "Dent w/crack", "External"),
)
```

Rows 2-4 use the same 1016 mm pipe, 12 mm wall, 104.9 bar pressure, 1,000 mm repair span, and 500 mm cloth. `R-001` has D-01 `(10, 9.652, Yes)` and D-02 `(35, 10.0, Yes)`. `R-BAD` contains at least one `No` separation confirmation.

- [ ] **Step 2: Run acceptance test and confirm RED**

Run: `pytest -q tests/test_full_batch_acceptance.py`

Expected: the old generator lacks basis/group/detail data and seven-sheet assertions fail.

- [ ] **Step 3: Update generator and end-to-end assertions**

Assert exact sheet order, three common fields, semantic cost mapping, expected statuses, candidate results, warning references, exact cost formulas, legacy upgrade, and re-upload identity. Reconcile engine values:

```python
assert actual_safe_pressure_mpa == pytest.approx(7.571542406120033)
assert independent_safe_pressure_mpa == pytest.approx(8.82257484144555)
assert manual_safe_pressure_mpa == pytest.approx(8.783461911867068)
assert (actual_plies, independent_plies, manual_plies) == (12, 7, 7)
```

- [ ] **Step 4: Update operator and release documentation**

Document both tables, exact mode rules, nominal-wall meaning of `t`, legacy upgrade, cost inputs, statuses, 500/2,000 row limits, and the separate deployment boundary. `DEPLOYMENT.md` must stop if the target repository or Streamlit app is the current CalcBatch or v1.1 target.

- [ ] **Step 5: Run complete automated verification**

Run: `pytest -q`

Expected: the entire inherited and new suite passes with no failures, errors, or unexpected warnings.

Run: `git diff --check main...HEAD`

Expected: no whitespace errors.

- [ ] **Step 6: Commit acceptance and documentation**

Run: `git add README.md DEPLOYMENT.md ENGINE_SOURCE.md scripts tests/test_full_batch_acceptance.py docs/superpowers/reports && git commit -m "docs: verify CalcBatch v1.2 release workflow"`

---

### Task 9: Produce and Visually Verify Final Workbook Artifacts

**Files:**
- Generate: `outputs/PROWRAP_CalcBatch_v1.2_Acceptance_Input.xlsx`
- Generate: `outputs/PROWRAP_CalcBatch_v1.2_Acceptance_Processed.xlsx`
- Modify: `docs/superpowers/reports/2026-08-20-calcbatch-v12-verification.md`

**Interfaces:**
- Consumes: Task 8 generator and real `process_workbook` path.
- Produces: two final acceptance workbooks plus structural, numerical, formula, recalculation, and visual evidence.

- [ ] **Step 1: Run the full suite from the exact final HEAD**

Run: `pytest -q`

Expected: every test passes immediately before artifact generation.

- [ ] **Step 2: Mark the spreadsheet operation exactly once**

Immediately before generating either workbook, load the bundled workspace
dependencies and run:

`node container_tools/mark_artifact_operation_started.mjs --operation-kind create --expected-output-count 2 --output-format xlsx`

Do not run the marker again during fixes or regeneration.

- [ ] **Step 3: Generate input and processed workbooks through production code**

Run: `python scripts/create_acceptance_workbook.py outputs/PROWRAP_CalcBatch_v1.2_Acceptance_Input.xlsx`

Then call `process_workbook` with a fixed UTC timestamp to create `outputs/PROWRAP_CalcBatch_v1.2_Acceptance_Processed.xlsx`. Do not hand-edit calculated output cells.

- [ ] **Step 4: Use the spreadsheet workflow for final artifact editing and inspection**

Use artifact tooling only for the approved commercial assumptions or visual inspection; after any tool export, reprocess through the real application path so protection, tables, hidden sheets, and controlled formulas are restored.

- [ ] **Step 5: Inspect structure and numerical results**

Verify:

```text
8 sheets in exact order; Lists hidden
500 main rows and 2,000 detail rows available
all input cells unlocked/selectable/filterable; all outputs locked
main and detail table refs equal their autoFilter refs
Actual/Independent/Manual safe pressures reconcile to direct engine calls
continuous repair-zone span remains 1,000 mm in all three comparison rows
manual D-02 is governing and every detail result stays on its source row
only controlled Cost U/V formulas exist
processed re-upload returns the same statuses and engineering results
```

- [ ] **Step 6: Recalculate commercially in LibreOffice and inspect all eight rendered sheets**

Populate B3/E3/H3 only with temporary acceptance values, recalculate a copy in LibreOffice, and reconcile Cost/Price against the displayed Fabric Area and Epoxy Mass. Render every sheet and visually check clipped headers, wrapped instructions, frozen rows, input highlighting, warning legibility, detail-table readability, and empty-state presentation.

- [ ] **Step 7: Record hashes, evidence, and repository isolation**

Append test totals, workbook sizes, SHA-256 hashes, formula counts, reconciliation values, render results, and any environment-only limitation to the verification report. Confirm:

```bash
git status --short --branch
git -C /Users/can/Documents/Codex/2026-08-14/i/outputs/Iso24817CalcBatch/.worktrees/feature-batch-calculator status --short --branch
git -C /Users/can/Documents/Codex/2026-08-14/i/work/Iso24817Calcv11-dent-split status --short --branch
```

The new feature worktree must be clean after committing report changes; current CalcBatch and v1.1 must show no new tracked changes.

- [ ] **Step 8: Request independent final review and apply only evidence-backed fixes**

Use `superpowers:requesting-code-review` against `main...HEAD`. If a reviewer identifies a defect, invoke `superpowers:receiving-code-review` and `superpowers:systematic-debugging`, reproduce it with a failing test, fix minimally, rerun the full suite, regenerate affected artifacts, and re-review. Do not publish or deploy as part of this task.
