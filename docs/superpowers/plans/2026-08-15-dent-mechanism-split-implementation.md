# Dent Mechanism Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to execute this plan task by task. Use
> `superpowers:test-driven-development` for every behavior change,
> `superpowers:verification-before-completion` before any completion claim, and
> `superpowers:finishing-a-development-branch` for each repository release.

**Goal:** Replace the generic `Dent` choice with `Dent w/crack` and
`Dent no-crack`; preserve the existing full-pressure calculation for cracked
dents and apply the approved component-pipe substrate load-sharing formula to
eligible external uncracked dents in both the v1.1 and Calcbatch applications.

**Architecture:** Implement and release the engineering rule in v1.1 first.
Keep canonical mechanism names and the component-pipe pressure helper in the
calculation layer, with Streamlit and reporting consuming the calculation
result rather than recreating the rule. Then port the approved calculation
change into the isolated batch engine. The batch boundary alone accepts legacy
`Dent` and normalizes it to `Dent w/crack` before preview, calculation,
controlled-workbook regeneration, and Cost Calculation mapping.

**Tech stack:** Python 3.11, Streamlit, pytest/unittest, openpyxl, fpdf,
Git/GitHub, Streamlit Community Cloud.

## Global constraints

- The controlling design is
  `docs/superpowers/specs/2026-08-15-dent-mechanism-split-design.md`.
- v1.1 and Calcbatch remain separate repositories, branches, Streamlit apps,
  and URLs. Never deploy one repository over the other.
- Run v1.1 work before batch work. The batch provenance must reference the
  exact verified v1.1 dent-split commit.
- Use this approved load-sharing equation only for external
  `Dent no-crack` with end-of-life remaining wall at least 1 mm:

  ```text
  S_allow = SMYS * Design Factor
  p_s = 2 * S_allow * t_remaining / OD
  p_composite = max(0, p_design - p_s)
  ```

- `Dent w/crack` receives zero substrate credit. It must reproduce the current
  generic-dent numbers for the same input vector.
- Both dent choices stay Type B for internal defects or remaining wall below
  1 mm. B31G remains corrosion-only.
- No dent-depth, local-strain, fatigue, gouge, or weld-interaction acceptance
  calculation is added.
- Do not change Tg 110 degC, the derived 90 degC material limit, 300/500 mm
  approved cloth behavior, warning meanings/codes, Cost/Price equations,
  editable commercial inputs, seven-sheet order, or common batch fields.
- Keep all Excel input templates formula-free. Controlled Cost/Price formulas
  are allowed only in processed workbooks under the existing rules.
- Apply test-driven development literally: write the failing test, run it and
  observe the intended failure, make the smallest implementation, rerun to
  green, then commit.

## Repository roots and release targets

| Application | Worktree used for implementation | Release target |
| --- | --- | --- |
| v1.1 | `/Users/can/Documents/Codex/2026-08-14/i/work/Iso24817Calcv11-dent-split` | `Prowrap110/Iso24817Calcv1.1` and `https://iso24817calc-prowrapv11.streamlit.app` |
| Calcbatch | `/Users/can/Documents/Codex/2026-08-14/i/outputs/Iso24817CalcBatch/.worktrees/feature-batch-calculator` | `Prowrap110/Iso24817CalcBatch` and `https://prowrap-batch-calculator.streamlit.app` |

---

## Task 1: Establish isolated worktrees and capture clean baselines

**Files:**

- Verify only: v1.1 repository and batch repository Git state
- Create: v1.1 linked worktree at the path in the table above
- Verify only: all existing test files in both repositories

### Step 1: Confirm the exact v1.1 base revision

From `/Users/can/Documents/GitHub/Iso24817Calcv1.1`, fetch the remote and
verify that the intended base is the current deployed main revision. At plan
creation time this is `691b5fef556de4e752b6ffa651884ffbfd08ca3d`.

```bash
git fetch origin
git rev-parse origin/main
git status --short --branch
```

If `origin/main` moved, stop and reconcile the newer changes before creating
the worktree. Do not silently build from the stale hash.

### Step 2: Create the v1.1 feature worktree

Use the `superpowers:using-git-worktrees` skill. Create a dedicated branch and
worktree without altering the existing checkout:

```bash
git worktree add \
  /Users/can/Documents/Codex/2026-08-14/i/work/Iso24817Calcv11-dent-split \
  -b feature/dent-mechanism-split origin/main
```

Verify:

```bash
git -C /Users/can/Documents/Codex/2026-08-14/i/work/Iso24817Calcv11-dent-split status --short --branch
```

Expected: branch `feature/dent-mechanism-split` and a clean worktree.

### Step 3: Run clean v1.1 baseline tests

From the new v1.1 worktree:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

Expected: every existing v1.1 test passes before feature edits. Record the
count and exact base revision in the execution report.

### Step 4: Confirm the batch feature worktree is clean

From the Calcbatch worktree:

```bash
git status --short --branch
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

Expected: branch `feature/dent-mechanism-split`, only the already-approved
design/plan commits, and a fully green baseline.

No commit is created in this task.

---

## Task 2: Implement the v1.1 dent calculation split in the engine

**Files:**

- Create: `prowrap_mechanisms.py`
- Create: `test_dent_mechanism_split.py`
- Modify: `prowrap_calculations.py`
- Modify: `test_typea_baseline_matches_rigorous.py`
- Modify if exact result keys are asserted: `test_current_calculation_baseline.py`

### Step 1: Write failing canonical-name and formula tests

Create `test_dent_mechanism_split.py`. Use `default_inputs` from
`test_current_calculation_baseline.py` and add these assertions:

```python
import pytest

from prowrap_calculations import (
    calculate_repair,
    component_pipe_allowable_basis,
    substrate_credit_bar_for_iso_check,
)
from prowrap_mechanisms import MECHANISM_CHOICES, normalize_mechanism
from test_current_calculation_baseline import default_inputs


def test_canonical_mechanism_choices_replace_generic_dent():
    assert MECHANISM_CHOICES == (
        "Corrosion", "Dent w/crack", "Dent no-crack", "Leak", "Crack",
    )
    assert "Dent" not in MECHANISM_CHOICES
    assert normalize_mechanism(" Dent no-crack ") == "Dent no-crack"
    with pytest.raises(ValueError, match="Unsupported defect mechanism"):
        normalize_mechanism("Dent")


def test_component_pipe_allowable_basis_uses_approved_equation():
    basis = component_pipe_allowable_basis(
        od_mm=457.2,
        remaining_wall_mm=9.53,
        smys_mpa=359.0,
        design_factor=0.72,
    )
    expected_stress = 359.0 * 0.72
    expected_pressure = 2.0 * expected_stress * 9.53 / 457.2
    assert basis["allowable_stress_mpa"] == pytest.approx(expected_stress)
    assert basis["allowable_pressure_mpa"] == pytest.approx(expected_pressure)


def test_dent_with_crack_preserves_current_full_pressure_result():
    result = calculate_repair(**default_inputs(
        defect_type="Dent w/crack", rem_wall=9.53,
    ))
    assert result["calculation_basis"] == (
        "Dent w/crack - full-pressure laminate"
    )
    assert result["allowable_pipe_stress_mpa"] is None
    assert result["p_steel_capacity"] == 0.0
    assert result["p_composite_design"] == 5.0
    assert result["t_required"] == pytest.approx(7.4240889243)
    assert result["num_plies"] == 9
    assert result["final_thickness"] == pytest.approx(7.47)
    assert substrate_credit_bar_for_iso_check(result) == 0.0


def test_external_dent_no_crack_uses_component_pipe_load_sharing():
    result = calculate_repair(**default_inputs(
        defect_type="Dent no-crack", rem_wall=9.53,
    ))
    expected_stress = 359.0 * 0.72
    expected_pressure = 2.0 * expected_stress * 9.53 / 457.2
    assert result["calculation_basis"] == (
        "Dent no-crack - substrate load sharing"
    )
    assert result["allowable_pipe_stress_mpa"] == pytest.approx(expected_stress)
    assert result["p_steel_capacity"] == pytest.approx(expected_pressure)
    assert result["p_composite_design"] == 0.0
    assert result["typea_design"]["tmin_c_mm"] == 0.0
    assert result["num_plies"] == 3
    assert result["final_thickness"] == pytest.approx(2.49)
    assert substrate_credit_bar_for_iso_check(result) == pytest.approx(
        expected_pressure * 10.0
    )
```

### Step 2: Write failing route-limit tests

Add parameterized tests showing both canonical dents become Type B without
credit when internal or when the remaining wall is below 1 mm:

```python
@pytest.mark.parametrize("mechanism", ["Dent w/crack", "Dent no-crack"])
@pytest.mark.parametrize(
    ("location", "remaining_wall"),
    [("Internal", 9.53), ("External", 0.9)],
)
def test_dent_routes_without_eligible_substrate_are_type_b(
    mechanism, location, remaining_wall,
):
    result = calculate_repair(**default_inputs(
        defect_type=mechanism,
        defect_loc=location,
        rem_wall=remaining_wall,
    ))
    assert result["calc_method_thick"] == "Type B (Total Replacement)"
    assert result["p_steel_capacity"] == 0.0
    assert result["allowable_pipe_stress_mpa"] is None
```

Add a structural case where `p_s < p_design` and assert exact Formula 5
pressure deficit, not only the minimum-floor case:

```python
def test_dent_no_crack_formula5_receives_only_the_pressure_deficit():
    result = calculate_repair(**default_inputs(
        defect_type="Dent no-crack",
        rem_wall=3.0,
        pressure=120.0,
    ))
    expected_ps = 2.0 * (359.0 * 0.72) * 3.0 / 457.2
    assert result["p_steel_capacity"] == pytest.approx(expected_ps)
    assert result["p_composite_design"] == pytest.approx(12.0 - expected_ps)
    assert result["typea_design"]["substrate_pressure_mpa"] == pytest.approx(
        expected_ps
    )
    assert result["typea_design"]["tmin_c_mm"] > 0.0
```

### Step 3: Run the focused tests and confirm RED

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  test_dent_mechanism_split.py \
  test_typea_baseline_matches_rigorous.py
```

Expected RED: imports/choices/result fields do not exist and the current
generic `Dent` routing does not implement the new distinction.

### Step 4: Add the canonical mechanism module

Create `prowrap_mechanisms.py` with one source of truth:

```python
DENT_WITH_CRACK = "Dent w/crack"
DENT_NO_CRACK = "Dent no-crack"

MECHANISM_CHOICES = (
    "Corrosion",
    DENT_WITH_CRACK,
    DENT_NO_CRACK,
    "Leak",
    "Crack",
)


def normalize_mechanism(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if text not in MECHANISM_CHOICES:
        raise ValueError(f"Unsupported defect mechanism: {text or '(blank)'}")
    return text
```

Do not accept legacy generic `Dent` here. Legacy migration belongs only to the
Calcbatch workbook boundary.

### Step 5: Add the pure component-pipe helper

In `prowrap_calculations.py`, import the canonical dent constants and implement
a unit-explicit pure helper near the other baseline helpers:

```python
def component_pipe_allowable_basis(
    *, od_mm, remaining_wall_mm, smys_mpa, design_factor,
):
    allowable_stress_mpa = smys_mpa * design_factor
    allowable_pressure_mpa = max(
        0.0,
        2.0 * allowable_stress_mpa * remaining_wall_mm / od_mm,
    )
    return {
        "allowable_stress_mpa": allowable_stress_mpa,
        "allowable_pressure_mpa": allowable_pressure_mpa,
    }
```

The existing input validation protects division by zero and invalid material
values. Do not add an alternate dent formula or B31G call.

### Step 6: Route canonical dent mechanisms in `calculate_repair`

Normalize `defect_type` once immediately after input validation. Then:

- use Type A for either external dent with remaining wall at least 1 mm;
- label both routes `Type A (Dent Reinforcement)` for compatibility;
- set `p_steel_capacity = 0` for `Dent w/crack`;
- calculate and assign the approved basis only for eligible
  `Dent no-crack`;
- keep corrosion B31G logic unchanged and exclusive to corrosion;
- keep Type B dent routes at zero credit;
- set result fields `calculation_basis` and
  `allowable_pipe_stress_mpa` for reporting/audit;
- add `substrate_pressure_mpa` to the `baseline_type_a_design` result so the
  closed-form Formula 5 input is directly auditable;
- continue passing `p_steel_capacity` into `baseline_type_a_design` and
  `substrate_credit_bar_for_iso_check`.

Use these exact dent calculation-basis strings:

```python
"Dent w/crack - full-pressure laminate"
"Dent no-crack - substrate load sharing"
```

For non-dent routes, retain a clear existing basis such as the B31G method or
Type B full replacement, without altering their numbers.

### Step 7: Update parity and optional-check tests

In `test_typea_baseline_matches_rigorous.py`:

- replace generic `Dent` cases with `Dent w/crack`;
- add an external `Dent no-crack` structural case (`pressure=120`,
  `rem_wall=3.0`) to the baseline-vs-rigorous matrix;
- update the routing tests for both new names;
- assert the optional rigorous calculation receives the same dent-specific
  substrate credit as the baseline.

Do not weaken the existing strain, Formula 4, Formula 5, thickness, layer,
overlap, or taper parity assertions.

### Step 8: Run focused and full v1.1 tests

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  test_dent_mechanism_split.py \
  test_typea_baseline_matches_rigorous.py \
  test_typea_class3_adapter.py \
  test_current_calculation_baseline.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

Expected GREEN: all new route/formula/parity tests and every pre-existing test
pass.

### Step 9: Commit the engine change

```bash
git add prowrap_mechanisms.py prowrap_calculations.py \
  test_dent_mechanism_split.py test_typea_baseline_matches_rigorous.py \
  test_current_calculation_baseline.py test_typea_class3_adapter.py
git commit -m "feat: split dent repair calculation routes"
```

Record this commit hash; Task 5 uses it as the batch source revision.

---

## Task 3: Update the v1.1 interface, engineering display, and PDF report

**Files:**

- Modify: `PWR110Calculator.py`
- Modify: `test_streamlit_form_submission.py`
- Modify: `test_report_wording.py`
- Modify: `DESKTOP_BUILD.md` only if its user-facing mechanism list is present

### Step 1: Write failing Streamlit selector tests

Extend `test_streamlit_form_submission.py` with:

```python
def test_mechanism_selector_uses_the_two_canonical_dent_choices(self):
    app = AppTest.from_file("PWR110Calculator.py").run()
    mechanism = app.selectbox(key="type_")
    assert mechanism.options == [
        "Select…",
        "Corrosion",
        "Dent w/crack",
        "Dent no-crack",
        "Leak",
        "Crack",
    ]
    assert "Dent" not in mechanism.options
```

Add a complete-form test that selects each dent choice, calculates, and
asserts the rendered mechanism and basis text. For `Dent w/crack`, assert nine
plies for the approved representative vector; for `Dent no-crack`, assert
three plies and the displayed `S_allow` and `p_s` values.

### Step 2: Write failing PDF/report behavior tests

Replace the existing source-text assertion in `test_report_wording.py` with
behavioral tests. For each dent result, call the real `create_pdf()`, verify the
returned bytes start with `%PDF`, extract the page text with `pypdf.PdfReader`,
and assert the user-visible report contains:

- the applicable exact dent calculation-basis string;
- the applicable allowable-stress, substrate-pressure, and pressure-deficit
  values;
- no statement that B31G supplies dent substrate capacity;
- the existing preliminary-engineering disclaimer.

These tests must exercise the generated report. Do not search
`PWR110Calculator.py` source text or assert on an FPDF mock.

### Step 3: Run focused tests and confirm RED

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  test_streamlit_form_submission.py test_report_wording.py
```

Expected RED: the selector still contains generic `Dent`, and the display/PDF
does not expose the route-specific basis.

### Step 4: Update the v1.1 selector and explanatory text

In `PWR110Calculator.py`:

- import `MECHANISM_CHOICES` from `prowrap_mechanisms`;
- build the selectbox as `[NEUTRAL_CHOICE, *MECHANISM_CHOICES]`;
- replace the misleading generic corrosion/dent caption with text explaining
  that substrate credit is route-specific and shown in the result;
- do not change the optional Type A/Class 3 checkbox default.

### Step 5: Render the calculation basis from result data

Use `report_data["defect_type"]` and `report_data["calculation_basis"]` after
calculation; do not keep displaying the unnormalized function argument.

For external `Dent no-crack`, display:

- allowable pipe stress `S_allow` in MPa;
- substrate allowable pressure `p_s` in MPa/bar;
- composite pressure deficit;
- governing thickness/layer outcome already shown.

For `Dent w/crack`, display zero `p_s` and state that the full design pressure
is assigned to the laminate. Preserve the existing B31G details only for
corrosion.

### Step 6: Make the PDF basis dynamic

In `create_pdf(report_data)`:

- add Calculation Basis, allowable pipe stress when present, substrate
  allowable pressure, and composite pressure deficit to the calculation table;
- make the standards note route-aware rather than claiming B31G for all rows;
- preserve all existing numerical repair/procurement outputs and the
  preliminary-screening disclaimer.

### Step 7: Run focused, full, and local UI verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  test_streamlit_form_submission.py test_report_wording.py \
  test_dent_mechanism_split.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
streamlit run PWR110Calculator.py --server.headless true
```

Exercise both dent selections locally and confirm there are no Streamlit
exceptions. Stop the local server after the check.

### Step 8: Commit the v1.1 user-facing change

```bash
git add PWR110Calculator.py test_streamlit_form_submission.py \
  test_report_wording.py DESKTOP_BUILD.md
git commit -m "feat: expose dent repair basis in v1.1"
```

Do not add `DESKTOP_BUILD.md` if it was unchanged.

---

## Task 4: Verify, publish, and live-test v1.1 independently

**Files:**

- Verify only: all v1.1 source and test files
- GitHub: v1.1 feature branch and pull request
- Streamlit: existing v1.1 application only

### Step 1: Perform pre-publication verification

Use `superpowers:requesting-code-review`, address only evidence-backed
findings, then run:

```bash
git diff --check origin/main...HEAD
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
git status --short --branch
```

Run an explicit representative-vector probe and record exact unrounded values
for both dent mechanisms. Confirm:

- cracked dent retains nine plies and 7.47 mm installed thickness;
- no-crack dent calculates `S_allow=258.48 MPa` and the exact approved `p_s`;
- no-crack result is three plies when the minimum floor controls;
- internal and below-1-mm dent cases are Type B;
- Tg remains 110 degC.

### Step 2: Publish through the connected GitHub workflow

Use the GitHub publication skill/app. Push only the v1.1 feature branch and
open a draft PR against `Prowrap110/Iso24817Calcv1.1:main`. Include the formula,
route matrix, full test result, and explicit statement that Calcbatch has not
yet been changed in this release step.

After review, merge only with the user's authorization and verify the merge
commit is on v1.1 `main`.

### Step 3: Verify Streamlit v1.1 deployment

Wait for the existing v1.1 Streamlit app to deploy from its own repository.
At `https://iso24817calc-prowrapv11.streamlit.app` verify:

- selector contains both new names and not generic `Dent`;
- representative `Dent w/crack` and `Dent no-crack` calculations match local
  verified values;
- PDF download succeeds and shows the correct basis;
- normal corrosion still calculates;
- no batch upload/download UI appears.

Record the live revision/time and screenshots or visible evidence. If the app
has not redeployed, diagnose its repository/branch settings; do not deploy the
batch repository to this URL.

No code commit is expected in this task unless review finds a defect. Any fix
must repeat RED/GREEN/full verification and receive its own focused commit.

---

## Task 5: Add canonical and legacy mechanism handling at the batch boundary

**Files:**

- Create: `batch_mechanisms.py`
- Modify: `batch_validation.py`
- Modify: `workbook_processor.py`
- Modify: `tests/test_batch_validation.py`
- Modify: `tests/test_workbook_processor.py`
- Modify: `tests/helpers.py`

### Step 1: Write failing batch normalization tests

In `tests/test_batch_validation.py`, add:

```python
@pytest.mark.parametrize("mechanism", ["Dent w/crack", "Dent no-crack"])
def test_accepts_canonical_dent_mechanisms(mechanism):
    row, issues = validate_row(2, valid_row_values(Mechanism=mechanism))
    assert issues == ()
    assert row.values["Mechanism"] == mechanism


def test_legacy_dent_is_conservatively_normalized():
    row, issues = validate_row(2, valid_row_values(Mechanism=" Dent "))
    assert issues == ()
    assert row.values["Mechanism"] == "Dent w/crack"


@pytest.mark.parametrize("mechanism", ["dent", "Dent no crack", "Dent/crack"])
def test_ambiguous_dent_spellings_are_rejected(mechanism):
    row, issues = validate_row(2, valid_row_values(Mechanism=mechanism))
    assert row is None
    assert [issue.code for issue in issues] == ["INVALID_SELECTION"]
```

Use dictionary unpacking if `valid_row_values` cannot accept a header with a
space as a keyword.

### Step 2: Write failing preview/regeneration/re-upload tests

In `tests/test_workbook_processor.py`, create a prior controlled workbook with
`Mechanism='Dent'`, process it, and assert:

- inspection preview says `Dent w/crack`;
- engine receives `Dent w/crack`;
- regenerated `Batch Input & Results!F2` is `Dent w/crack`;
- Cost Calculation mechanism cell for the same row is `Dent w/crack`;
- re-upload remains valid and does not revert the value;
- all unrelated cells and commercial assumptions retain their existing
  behavior.

Also test a current `Dent no-crack` workbook remains unchanged through preview,
processing, Cost Calculation, and re-upload.

### Step 3: Run focused tests and confirm RED

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_batch_validation.py tests/test_workbook_processor.py \
  -k "dent or mechanism"
```

Expected RED: new names are rejected and legacy `Dent` remains unnormalized in
preview/output.

### Step 4: Implement the batch-boundary helper

Create `batch_mechanisms.py`:

```python
CANONICAL_MECHANISMS = (
    "Corrosion", "Dent w/crack", "Dent no-crack", "Leak", "Crack",
)
LEGACY_MECHANISM_ALIASES = {"Dent": "Dent w/crack"}
ACCEPTED_UPLOAD_MECHANISMS = (
    *CANONICAL_MECHANISMS,
    *LEGACY_MECHANISM_ALIASES,
)


def normalize_upload_mechanism(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return LEGACY_MECHANISM_ALIASES.get(text, text)
```

Do not use case-folding or fuzzy matching.

### Step 5: Normalize during validation and trusted output rebuilding

In `batch_validation.py`:

- validate mechanism text after trimming;
- accept only `ACCEPTED_UPLOAD_MECHANISMS`;
- store `normalize_upload_mechanism(text)` in `ValidatedRow.values`.

In `workbook_processor.py`:

- use the validated row's canonical value in the preview;
- in `_copy_controlled_inputs`, normalize the Mechanism cell as the trusted
  output workbook is rebuilt;
- leave every other copied input unchanged;
- rely on the regenerated canonical source cell so `_write_cost_sheet` maps the
  same name automatically.

The adapter should still normalize/assert canonically as a defense-in-depth
boundary in Task 6, but workbook regeneration is the authoritative migration.

### Step 6: Run focused and processor suites

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_batch_validation.py tests/test_workbook_processor.py
```

Expected GREEN: canonical names and conservative legacy migration pass; all
controlled-workbook security/integrity regressions stay green.

### Step 7: Commit the boundary migration

```bash
git add batch_mechanisms.py batch_validation.py workbook_processor.py \
  tests/test_batch_validation.py tests/test_workbook_processor.py tests/helpers.py
git commit -m "feat: normalize batch dent mechanisms"
```

---

## Task 6: Port the approved v1.1 dent calculation into the batch engine

**Files:**

- Create: `engine/prowrap_mechanisms.py`
- Modify: `engine/prowrap_calculations.py`
- Modify: `batch_adapter.py`
- Modify: `workbook_processor.py`
- Modify: `ENGINE_SOURCE.md`
- Modify: `tests/engine/test_typea_baseline_matches_rigorous.py`
- Create: `tests/engine/test_dent_mechanism_split.py`
- Modify: `tests/test_batch_adapter.py`
- Modify: `tests/test_engine_snapshot.py`

### Step 1: Pin the verified v1.1 source revision

Use the exact v1.1 commit verified and released in Tasks 2–4. Update
`SOURCE_ENGINE_REVISION` in `workbook_processor.py` to its short hash and bump
`BATCH_ENGINE_VERSION` from `1.1.0` to `1.2.0` because this is a new calculation
feature.

Update `ENGINE_SOURCE.md` to state:

- the exact source repository and commit;
- the addition of `prowrap_mechanisms.py` to the copied/ported engine modules;
- the approved dent split and exact formula;
- legacy aliasing is a batch-boundary behavior, not an engine formula;
- all existing batch-only zero-pressure, temperature-review, cloth-width, and
  logging corrections remain in force.

### Step 2: Write failing engine parity tests

Port the Task 2 dent tests into
`tests/engine/test_dent_mechanism_split.py`, changing imports to
`engine.prowrap_calculations` and `engine.prowrap_mechanisms`.

In `tests/engine/test_typea_baseline_matches_rigorous.py`, mirror the canonical
dent cases and baseline-vs-rigorous assertions used in the verified v1.1
revision.

Run and confirm RED:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/engine/test_dent_mechanism_split.py \
  tests/engine/test_typea_baseline_matches_rigorous.py
```

### Step 3: Write failing adapter/output-detail tests

In `tests/test_batch_adapter.py`, assert for both new mechanisms:

- canonical mechanism reaches `calculate_repair`;
- cracked dent produces zero Effective Pipe Capacity, 50 bar Composite Pressure
  Deficit, and nine plies for the representative vector;
- no-crack dent produces the exact allowable stress/pressure basis, zero
  deficit, and three plies;
- `Type A Detail` contains a stable baseline audit structure with
  `calculation_basis`, `allowable_pipe_stress_mpa`,
  `substrate_allowable_pressure_mpa`, `composite_pressure_deficit_mpa`, and
  `baseline_typea_design`;
- when the optional Class 3 check runs, its result is nested under a separate
  key rather than replacing the baseline audit values;
- invalid/no-solution rows retain blank installable outputs.

Do not add new worksheet columns. The existing Mechanism, Thickness Calculation
Method, Effective Pipe Capacity, Composite Pressure Deficit, and Type A Detail
fields provide the audit trail while preserving old controlled workbook
headers.

### Step 4: Port only the approved v1.1 engine changes

Copy `prowrap_mechanisms.py` from the verified v1.1 revision to
`engine/prowrap_mechanisms.py` and adjust imports to package-relative form.

Port the approved dent helper, routing, and result fields into
`engine/prowrap_calculations.py`. Do not overwrite the file wholesale: preserve
the documented batch-only `allow_unqualified_temperature` behavior and all
existing batch fixes.

Keep B31G corrosion-only and retain the exact same helper/formula/result keys as
v1.1 so parity tests compare directly.

### Step 5: Build a stable Type A audit detail in the adapter

In `batch_adapter._map_outputs`, emit `Type A Detail` as:

```python
{
    "calculation_basis": result["calculation_basis"],
    "allowable_pipe_stress_mpa": result["allowable_pipe_stress_mpa"],
    "substrate_allowable_pressure_mpa": result["p_steel_capacity"],
    "composite_pressure_deficit_mpa": result["p_composite_design"],
    "baseline_typea_design": result.get("typea_design"),
    "optional_class3_check": result.get("iso_typea_class3"),
}
```

Use this structure only when a Type A design exists; keep Type B Detail and B31G
Detail semantics unchanged. This exposes `S_allow` without changing the
controlled workbook header contract.

Normalize/assert the adapter's mechanism with `normalize_upload_mechanism`
before calling the engine so direct `calculate_row` callers cannot pass legacy
`Dent` downstream.

### Step 6: Run focused, engine, adapter, and provenance suites

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/engine/test_dent_mechanism_split.py \
  tests/engine/test_typea_baseline_matches_rigorous.py \
  tests/test_batch_adapter.py \
  tests/test_engine_snapshot.py
```

Expected GREEN: engine parity with released v1.1 plus batch-specific behavior
preserved.

### Step 7: Commit the batch engine port

```bash
git add engine/prowrap_mechanisms.py engine/prowrap_calculations.py \
  batch_adapter.py workbook_processor.py ENGINE_SOURCE.md \
  tests/engine/test_dent_mechanism_split.py \
  tests/engine/test_typea_baseline_matches_rigorous.py \
  tests/test_batch_adapter.py
git commit -m "feat: port approved dent load sharing to batch"
```

Include any actually modified provenance snapshot test in the commit.

---

## Task 7: Update the batch template, application text, acceptance workbook, and docs

**Files:**

- Modify: `workbook_template.py`
- Modify: `app.py`
- Modify: `scripts/create_acceptance_workbook.py`
- Modify: `tests/test_workbook_template.py`
- Modify: `tests/test_app_smoke.py`
- Modify: `tests/test_full_batch_acceptance.py`
- Modify: `tests/test_cost_calculation.py` only if an assertion needs canonical mechanism values
- Modify: `README.md`
- Modify: `DEPLOYMENT.md`

### Step 1: Write failing template and app tests

In `tests/test_workbook_template.py`, load the hidden `Lists` sheet and assert
the exact mechanism list and order:

```python
assert mechanism_values == [
    "Corrosion", "Dent w/crack", "Dent no-crack", "Leak", "Crack",
]
assert "Dent" not in mechanism_values
```

Keep the existing named-range/data-validation extent assertion (`F2:F501`).
Also assert the Mechanism cell comment and Instructions text explain:

- cracked dent = full-pressure laminate;
- no-crack external dent = component-pipe substrate load sharing;
- generic legacy `Dent` is accepted only when upgrading an older batch
  workbook and becomes `Dent w/crack`.

In `tests/test_app_smoke.py`, assert the app caption lists both new names and no
generic Dent entry.

Run and confirm RED:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_workbook_template.py tests/test_app_smoke.py
```

### Step 2: Update template choices and instructions

Import `CANONICAL_MECHANISMS` into `workbook_template.py` and use it for
`MechanismChoices`. Update `_HEADER_NOTES` and the Instructions worksheet with
the approved distinction and engineering-review limitation.

Do not put legacy generic `Dent` in the new dropdown. Do not change sheet order,
input columns, table extent, protection, filters, formula rules, or Cost sheet
commercial cells.

### Step 3: Update application text

In `app.py`, list the exact supported canonical names. Add one concise note that
old controlled batch workbooks containing generic `Dent` are interpreted
conservatively as `Dent w/crack`.

Do not change the separate-app notice, upload size, session behavior, or
download naming.

### Step 4: Make the six-row acceptance workbook exercise both dent routes

Keep six rows, the existing status order, warning coverage, 500 mm case, and 12
Cost/Price formulas. Change the existing first and sixth OK rows:

- row 1: `Dent w/crack`, external, remaining wall 9.53 mm, 300 mm cloth;
- row 6: `Dent no-crack`, external, remaining wall 9.53 mm, 500 mm cloth.

Leave rows 2–5 as the current unapproved-width review, Type B not-repairable,
invalid-input, and zero-pressure Type B review cases. This keeps expected
statuses:

```python
[
    "OK", "REVIEW REQUIRED", "NOT REPAIRABLE",
    "INPUT ERROR", "REVIEW REQUIRED", "OK",
]
```

### Step 5: Extend end-to-end acceptance assertions

In `tests/test_full_batch_acceptance.py`, additionally assert:

- source and processed rows contain the two canonical dent names;
- row 1 has zero capacity credit, 50 bar deficit, and nine plies;
- row 6 has exact approved component-pipe credit, zero deficit, and three
  plies;
- the Cost Calculation mechanism mappings contain the same names;
- Type A Detail for both rows records the route-specific basis;
- row 6 retains no cloth warning for 500 mm;
- all existing status, warning-register, 120-cell mapping, formula,
  protection, freeze-pane, table/filter, hidden Lists, and safe re-upload
  assertions remain active;
- after re-upload, dent names and commercial assumptions remain unchanged.

Do not reduce assertions to make the test pass. Update only values intentionally
changed by the approved mechanisms.

### Step 6: Update user and deployment documentation

In `README.md`:

- bump the release description to 1.2.0;
- document both dent choices and their routing in plain language;
- state that `Dent no-crack` selects a calculation basis, not a complete dent
  integrity/fatigue acceptance assessment;
- document conservative legacy `Dent` migration;
- retain all Cost, warning, Tg, cloth, privacy, and verification guidance.

In `DEPLOYMENT.md`:

- add both live dent smoke vectors;
- keep the batch repository/URL distinct from v1.1;
- require checking the source revision shown in Summary;
- retain existing rollback instructions, scoped only to the batch app.

### Step 7: Run focused and full batch tests

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_workbook_template.py \
  tests/test_app_smoke.py \
  tests/test_full_batch_acceptance.py \
  tests/test_cost_calculation.py \
  tests/test_workbook_processor.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

Expected GREEN: every test passes with the six-row acceptance contract and
all previous workbook integrity tests intact.

### Step 8: Commit the user-facing batch release

```bash
git add workbook_template.py app.py scripts/create_acceptance_workbook.py \
  tests/test_workbook_template.py tests/test_app_smoke.py \
  tests/test_full_batch_acceptance.py tests/test_cost_calculation.py \
  README.md DEPLOYMENT.md
git commit -m "docs: publish dent choices in batch workflow"
```

Do not add `tests/test_cost_calculation.py` if it was unchanged.

---

## Task 8: Generate and inspect the controlled batch acceptance artifacts

**Files:**

- Generate: `outputs/PROWRAP_Batch_Dent_Split_Acceptance_Input.xlsx`
- Generate: `outputs/PROWRAP_Batch_Dent_Split_Acceptance_Processed.xlsx`
- Verify only: both generated workbooks

### Step 1: Generate the controlled source workbook

Use `scripts/create_acceptance_workbook.py` and save only to the batch
worktree's `outputs/` folder. Confirm the input workbook has seven sheets, no
formulas, canonical dent dropdown values, and the two approved dent rows.

### Step 2: Process through the real product boundary

Call `process_workbook()` with a fixed UTC timestamp and the actual source
filename. Save the returned bytes as the processed acceptance workbook. Do not
construct a look-alike result workbook directly with openpyxl.

### Step 3: Inspect values and workbook controls

Using the spreadsheet verification skill/runtime, verify:

- exact seven-sheet order and hidden Lists;
- Batch Input & Results and Cost Calculation both show canonical names;
- row-specific `S_allow`, `p_s`, deficit, thickness, and plies match tests;
- 500 mm is warning-free;
- cost inputs B3/E3/H3 remain yellow, blank, unlocked, and data-validated;
- CostRows table and autoFilter have matching references;
- only the exact controlled Cost/Price formulas exist;
- input cells are editable, output cells protected, and filters usable;
- no formula or workbook error is present;
- processed workbook safely re-uploads.

### Step 4: Perform visual rendering checks

Render all seven sheets. Inspect the long mechanism labels for clipping in both
the result table and Cost Calculation. Increase only capped column width or
alignment if necessary; do not add wrapped long remarks to result rows.

Any visual or structural defect requires a failing regression test, the minimal
fix, focused/full green runs, and a separate commit.

### Step 5: Record artifact hashes

Record file sizes and SHA-256 hashes in the execution report. Generated
acceptance workbooks are verification deliverables; commit them only if the
repository already tracks acceptance artifacts and the deployment policy
requires it.

---

## Task 9: Final review, publish Calcbatch, and verify both live apps

**Files:**

- Verify only: complete Calcbatch repository and acceptance artifacts
- GitHub: batch feature branch and pull request
- Streamlit: batch application and final cross-app isolation check

### Step 1: Request final code review

Use `superpowers:requesting-code-review`. The reviewer must specifically check:

- exact formula and route matrix;
- generic `Dent` can only become `Dent w/crack`;
- no B31G dent credit;
- preview/result/Cost/re-upload consistency;
- v1.1 source provenance;
- no regression in workbook structure, formulas, protections, Cost inputs,
  warning codes, Tg110, or 300/500 mm cloth;
- no changes to v1.1 files from the batch worktree.

Address only confirmed findings with RED/GREEN evidence.

### Step 2: Run final batch release gates

```bash
git diff --check origin/main...HEAD
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
git status --short --branch
streamlit run app.py --server.headless true
```

Exercise template download, current workbook upload, legacy generic-Dent
upload, calculation, result download, Cost edit/re-upload, and both dent result
routes locally. Stop the server after verification.

### Step 3: Publish through the connected GitHub workflow

Push only `feature/dent-mechanism-split` in
`Prowrap110/Iso24817CalcBatch`. Open a draft PR against batch `main` with:

- approved formula and route matrix;
- conservative legacy migration;
- exact pinned v1.1 source revision;
- full test and acceptance-artifact evidence;
- explicit confirmation that v1.1 was released separately.

After review, merge only with user authorization.

### Step 4: Verify batch Streamlit deployment

At `https://prowrap-batch-calculator.streamlit.app` verify:

- new template contains both canonical dent choices;
- legacy generic-Dent workbook uploads and regenerates as `Dent w/crack`;
- six-row acceptance workbook returns the expected statuses and both dent
  results;
- processed workbook downloads and safely re-uploads;
- Cost Calculation remains editable and recalculates in Excel;
- Summary shows batch version 1.2.0 and the released v1.1 source revision;
- no single-case v1.1 form appears.

### Step 5: Perform final cross-application isolation check

Open both live URLs independently and verify:

- v1.1 is still the single-case calculator with its own PDF report;
- Calcbatch is still the Excel upload/download calculator;
- both show the two new dent names;
- the representative dent vectors agree numerically;
- neither URL redirects to or displays the other app.

### Step 6: Prepare the final handoff

Report:

- v1.1 merge commit and live verification time;
- batch merge commit and live verification time;
- complete test counts for both repositories;
- acceptance workbook paths and hashes;
- exact representative-vector results;
- the explicit engineering limitation that this change selects a repair
  load-sharing basis and does not replace a dedicated dent integrity/fatigue
  assessment.

Do not claim release completion until both URLs and both repository revisions
have been independently verified.
