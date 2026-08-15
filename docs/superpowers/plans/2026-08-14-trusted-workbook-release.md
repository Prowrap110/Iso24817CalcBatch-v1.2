# PROWRAP Batch Trusted-Workbook Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Complete and publish the Cost Calculation batch release for controlled template and processed workbooks used by the user.

**Architecture:** Keep the existing practical workbook controls and trusted-template rebuild. Remove the unintegrated OPC experiment, fix filename-sensitive result identity and workbook guidance, rebuild the final acceptance file, then publish and live-test the batch app.

**Tech Stack:** Python 3.11, Streamlit 1.x, openpyxl 3.1.x, pytest, Excel XLSX, artifact-tool, GitHub, Streamlit Community Cloud.

## Global Constraints

- Modify and publish only `Prowrap110/Iso24817CalcBatch`.
- Never modify or redeploy the existing v1.1 repository or app.
- Support only the controlled template and previously processed batch workbooks.
- Keep 10 MB, 500-row, macro/encryption, ZIP expansion, exact-sheet/header, and controlled-formula safeguards.
- Keep all engineering calculations, warnings, 500 mm behavior, Tg 110 degC behavior, and Cost/Price formulas unchanged.
- Publish only after the full suite, final workbook review, and live batch URL test pass.

---

### Task 1: Remove the Unintegrated OPC Experiment

**Files:**
- Delete: `opc_package.py`
- Delete: `tests/opc_fixtures.py`
- Delete: `tests/test_opc_package.py`

**Interfaces:**
- Preserves the existing `workbook_processor.py` upload path and all currently integrated practical safeguards.
- Produces no replacement package API.

- [ ] Confirm `workbook_processor.py` does not import or call `opc_package`.
- [ ] Delete only the three unintegrated Task-1 experiment files.
- [ ] Run `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q` and require zero failures.
- [ ] Run `git diff --check` and confirm the original v1.1 repository was untouched.
- [ ] Commit with `chore: remove unused OPC resolver experiment`.

---

### Task 2: Finish Source Traceability and Workbook Guidance

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_smoke.py`
- Modify: `workbook_template.py`
- Modify: `tests/test_workbook_template.py`
- Modify: `requirements.txt`

**Interfaces:**
- Produces `_source_identity(data: bytes, filename: str) -> str`.
- Preserves the current Streamlit stages and session-local processed bytes.

- [ ] Add a failing unit test proving identity changes when either bytes or exact filename changes.
- [ ] Add a failing AppTest: calculate `first.xlsx`, upload identical bytes as `renamed-second.xlsx`, verify the old download disappears, recalculate, and verify `Summary!B7 == 'renamed-second.xlsx'`.
- [ ] Run the focused tests and confirm the expected RED against bytes-only identity.
- [ ] Implement `_source_identity` with SHA-256 over workbook bytes, a NUL separator, and UTF-8 filename bytes; use it for every current/processed upload comparison.
- [ ] Run the identity tests to GREEN.
- [ ] Add failing workbook/app assertions for accurate controlled-formula help, retained commercial values, and integer display formats in Design Life, Installed Plies, and Cloth Band Count.
- [ ] Change uploader help to state that macros and uncontrolled formulas are rejected while exact processed Cost and Price formulas are accepted on re-upload.
- [ ] Change Instructions to say commercial cells may be blank or may retain values from a previously processed workbook.
- [ ] Apply `#,##0` to Cost Calculation columns J, O, and Q without altering values.
- [ ] Change `requirements.txt` to `openpyxl>=3.1,<3.2`.
- [ ] Run app, template, full acceptance, and complete repository tests; require zero failures.
- [ ] Commit with `fix: bind batch results to source filename`.

---

### Task 3: Rebuild, Review, Publish, and Live-Test

**Files:**
- Regenerate: `/Users/can/Documents/Codex/2026-08-14/i/outputs/PROWRAP_Batch_Cost_Calculation_Acceptance.xlsx`

**Interfaces:**
- Produces the final acceptance workbook, merged GitHub batch release, and verified batch Streamlit workflow.

- [ ] Run the complete suite, diff check, and clean-worktree check.
- [ ] Generate the six-row controlled acceptance input and process it through real `process_workbook`.
- [ ] Set commercial values to CF `50.00`, epoxy `20.00`, and multiplier `1.50`; rebuild through the processor so controlled metadata is restored.
- [ ] Verify seven-sheet order, editable/filterable protected inputs, hidden Lists, matching Cost table/filter range, 120/120 mappings, exact controlled formulas, recalculated Cost/Price, separate Warnings, warning-free 500 mm row, and source filename.
- [ ] Render all sheets and visually inspect the Cost Calculation table and commercial inputs.
- [ ] Run one final whole-branch review focused on the supported controlled-workbook workflow, calculations, usability, privacy, regression, and v1.1 isolation.
- [ ] Push `feature/cost-calculation-sheet` to `Prowrap110/Iso24817CalcBatch`, open the batch-repository PR, pass checks, and merge.
- [ ] Verify `https://prowrap-batch-calculator.streamlit.app/`: template download, controlled upload, calculation, processed download, re-upload, Cost formulas, warnings sheet, and renamed-source clearing.
- [ ] Verify `https://iso24817calc-prowrapv11.streamlit.app/` remains available and unchanged.
- [ ] Report merged commit/PR, test count, workbook hash, live checks, and link the final workbook exactly once.
