# PROWRAP Batch Repair Calculator Design

**Date:** 2026-08-14  
**Status:** Approved direction; implementation requires review of this written specification  
**Product name:** PROWRAP Batch Repair Calculator  
**Repository name:** `Iso24817CalcBatch`

## 1. Objective

Build a separate, user-friendly Streamlit application that processes an Excel workbook containing one pipeline defect per row and returns a new Excel workbook with calculation results appended to the corresponding rows.

The application reuses a pinned snapshot of the verified Python calculation engine behind PROWRAP v1.1. It does not modify, replace, merge into, redirect, or redeploy the existing `Iso24817Calcv1.1` repository or the production application at `https://iso24817calc-prowrapv11.streamlit.app`.

## 2. Success Criteria

The first release is successful when:

1. The existing v1.1 application and URL remain unchanged and independently usable.
2. The new batch application has its own repository, Streamlit deployment, and URL.
3. A user can download the controlled Excel template, enter up to 500 independent defect rows, upload the workbook, and download a processed copy.
4. The application preserves input values and row order and appends results to the same row.
5. A bad row does not stop valid rows from being calculated.
6. Each row clearly reports `OK`, `REVIEW REQUIRED`, `NOT REPAIRABLE`, `INPUT ERROR`, or `SYSTEM ERROR`.
7. Valid-row engineering outputs match the single-case engine for the same inputs.
8. Every output workbook records the batch-engine version, pinned v1.1 source revision, and processing timestamp.

## 3. Scope Boundaries

### Included in version 1

- Separate Streamlit batch application.
- Controlled `.xlsx` template download.
- `.xlsx` upload, validation, calculation, preview, and processed-workbook download.
- One defect per row and a maximum of 500 populated rows.
- Row-level calculation status, errors, warnings, and engineering outputs.
- Summary and instructions worksheets.
- Regression parity with the valid calculations in the existing v1.1 engine.
- Fixes inside the new repository for batch-blocking engine edge cases.
- A separate staging deployment before production release.

### Not included in version 1

- Any modification or deployment change to `Iso24817Calcv1.1`.
- Google Sheets integration or live cell updates.
- Native Excel formulas, VBA, macros, Office Scripts, or an Excel add-in.
- Arbitrary customer workbook layouts.
- Per-defect PDF reports or a ZIP of reports.
- Accounts, persistent uploads, a calculation database, or approval signatures.
- A claim that the workbook alone constitutes engineering approval or certification.

## 4. Isolation and Source Provenance

The new application will be developed only in the new `Iso24817CalcBatch` repository. Implementation begins from a pinned copy of the calculation-related files at `Iso24817Calcv1.1` commit `68e5409`:

- `prowrap_calculations.py`
- `prowrap_materials.py`
- `iso24817_typea_class3.py`
- `b31g.py`
- the calculation-engine regression tests

The original Streamlit presentation module is used only as a behavioral reference. The batch application receives its own UI and orchestration modules.

The new repository contains an `ENGINE_SOURCE.md` record with:

- source repository name;
- source commit hash;
- import date;
- copied files;
- intentional batch-only corrections made after import.

The same source revision and batch release version are written into every processed workbook. Runtime calculation does not call the existing website or require a network connection to it.

## 5. User Experience

The application has one simple page with four visible stages.

### Stage 1: Download template

The page begins with a short explanation and a prominent **Download Excel Template** button. A compact unit legend and the supported choices appear below the button.

### Stage 2: Upload workbook

The user drags or selects one `.xlsx` file. The application rejects macro-enabled, password-protected, oversized, or structurally incompatible files with a plain-language message.

The application displays:

- file name;
- populated row count;
- recognized input columns;
- missing or unexpected columns;
- number of rows currently valid or requiring correction.

### Stage 3: Review preview

A preview shows the first 20 populated rows with only identity fields and validation status. The **Calculate Batch** button is enabled when the workbook structure is valid. Invalid data rows do not disable the button because they are reported individually.

### Stage 4: Calculate and download

After processing, the page shows a summary of all status counts and a **Download Processed Workbook** button. The returned file name is:

`PROWRAP_Batch_Results_<YYYYMMDD_HHMMSS>.xlsx`

Uploaded and generated workbooks remain in session memory or temporary storage only and are not retained after the session.

## 6. Workbook Design

The controlled workbook contains four worksheets.

### `Batch Input & Results`

This is the main worksheet. Each populated row represents one defect. Input columns appear first, followed by calculation outputs. The processor never sorts rows, deletes rows, renames user identifiers, or changes input values.

Formatting rules:

- freeze the header row and identity columns;
- enable Excel table filters;
- use blue headers for input columns and dark gray headers for output columns;
- mark conditional inputs with a note in the header;
- color statuses green, amber, red, or gray;
- wrap warning and error text;
- protect output cells without applying a password, allowing users to remove protection if necessary;
- include no formulas or macros.

### `Summary`

This worksheet contains:

- workbook name and processing time;
- total populated rows;
- counts by calculation status;
- counts by Type A/Type B route;
- count of rows with compliance warnings;
- count of rows requiring engineering review;
- engine version and pinned source revision;
- a disclaimer that results are preliminary screening outputs and require competent engineering review.

### `Instructions`

This worksheet explains the workflow, required fields, units, allowed selections, conditional internal-corrosion input, status meanings, and the rule that blank rows are ignored.

### `Lists`

This hidden worksheet supplies Excel data-validation lists. It contains no engineering formulas.

## 7. Canonical Input Columns

The template uses plain human-readable headings in row 1, with units included where applicable. The application maps these headings to internal machine-stable keys that are not exposed to the user. Header comments provide additional guidance.

| Column | Requirement | Unit or choices |
|---|---|---|
| `Defect ID` | Required; unique within workbook | Text |
| `Customer` | Required | Text |
| `Project Location` | Required | Text |
| `Report No` | Required | Text |
| `Pipe OD [mm]` | Required | mm; positive |
| `Nominal Wall [mm]` | Required | mm; positive |
| `Pipe Yield [MPa]` | Required | MPa; positive |
| `Design Pressure [bar]` | Required | bar; zero or positive |
| `Operating Temperature [degC]` | Required | degrees C |
| `Mechanism` | Required | `Corrosion`, `Dent`, `Leak`, `Crack` |
| `Defect Location` | Required | `External`, `Internal` |
| `Defect Length [mm]` | Required | mm; positive |
| `Remaining Wall [mm]` | Required | mm; zero or positive and not greater than nominal wall |
| `Internal Corrosion Rate [mm/year]` | Required only for internal corrosion | mm/year; zero or positive |
| `Design Life [years]` | Required | Whole years; minimum 1 |
| `Design Factor` | Required | Greater than or equal to 0.10 and no greater than 1.00 |
| `Run Type A / Class 3 Check` | Required | `Yes`, `No` |
| `Installation Temperature [degC]` | Required | degrees C |
| `Component Type` | Required | `Straight`, `Bend`, `Tee`, `Flange`, `Reducer` |
| `Cyclic Derating Factor` | Required | Greater than 0 and no greater than 1 |
| `Axial Load Case` | Required | `0`, `1` |
| `Prowrap CF Cloth Width [mm]` | Required | mm; greater than the fixed 50 mm stitch overlap |

Version 1 recognizes 300 mm as the configured approved PROWRAP cloth width. Any other value greater than 50 mm is calculated but receives `REVIEW REQUIRED` with an instruction to confirm product approval. Values of 50 mm or less are rejected.

Blank rows are ignored. Partially populated rows receive `INPUT ERROR`.

## 8. Canonical Output Columns

Outputs are appended to the same row in five groups.

### Traceability and status

- `Source Excel Row`
- `Calculation Status`
- `Error Code`
- `Error Message`
- `Compliance Warnings`
- `Batch Engine Version`
- `Source Engine Revision`
- `Processed At [UTC]`

### Classification and remaining wall

- `Thickness Calculation Method`
- `Overlap Calculation Method`
- `Wall Loss [%]`
- `End-of-Life Remaining Wall [mm]`
- `No Substrate Capacity`

### Pressure and structural results

- `B31G Applicable`
- `B31G Acceptable`
- `Effective Pipe Capacity [bar]`
- `Composite Pressure Deficit [bar]`
- `Required Structural Thickness [mm]`
- `Installed Plies`
- `Installed Thickness [mm]`
- `Thin-Wall Thickness Check OK`
- `Type A / Class 3 Check Run`
- `Type A / Class 3 Controls`

### Layout and materials

- `Required Overlap [mm]`
- `Taper Length [mm]`
- `Total Repair Length [mm]`
- `Cloth Band Count`
- `Procurement Axial Length [mm]`
- `Fabric Area [m2]`
- `Epoxy Mass [kg]`

### Diagnostic detail

- `B31G Detail`
- `Type A Detail`
- `Type B Detail`

Diagnostic dictionaries are serialized as compact readable text so the workbook remains flat and filterable.

## 9. Status Model

Statuses are assigned in this order:

1. `INPUT ERROR`: a required field, type, range, enumeration, or conditional field is invalid.
2. `SYSTEM ERROR`: an unexpected exception occurs after validation.
3. `NOT REPAIRABLE`: ISO Formula 12 reports no repair solution for the requested Type B case.
4. `REVIEW REQUIRED`: a numeric result exists but one or more engineering conditions require review, including formula validity limits, service-life or temperature qualification limits, axial-load limitations, thickness validity failure, unapproved cloth width, or another compliance warning.
5. `OK`: the row has a valid result and no review warning.

For `NOT REPAIRABLE`, the workbook retains diagnostic pressure and Formula 12 information but leaves `installed_plies`, `installed_thickness_mm`, material quantities, and procurement quantities blank. This prevents a diagnostic number from being mistaken for an acceptable repair design.

## 10. Calculation Flow

For each populated row:

1. Normalize Excel cell values without changing the displayed input cells.
2. Validate all required, conditional, numeric, and enumerated inputs.
3. Call the pure `calculate_repair()` engine.
4. If requested and applicable, call `calculate_type_a_class3_prowrap_check()` and merge it through `apply_type_a_class3_result_to_repair()`.
5. Classify the engineering outcome using the status model.
6. Flatten the selected engine outputs into output columns.
7. Continue to the next row even if the current row fails.

Shared engine calls are wrapped by a batch adapter. Streamlit, Excel formatting, and status presentation do not enter the engineering modules.

## 11. Required Batch-Only Engine Corrections

The following issues must be corrected and regression-tested in the new repository before batch release:

1. A zero-pressure Type B row must not dereference missing Type B details or crash. It returns the impact-qualified three-ply minimum and `REVIEW REQUIRED`, with a message that Formula 12 was not controlling at zero design pressure and the Type B defect classification still requires engineering review.
2. Formula 12 `not repairable` must be a first-class status, not merely a warning accompanying apparent repair quantities.
3. Mechanism, defect location, component type, axial-load case, and yes/no fields must use strict enumeration validation.
4. The Type B service-life wording must agree with the configured PRW110 material limit of 2 years.
5. Cloth width must be greater than the fixed 50 mm stitch overlap. Widths outside the configured approved list require review.

These corrections apply only to the new batch repository. They do not change the existing v1.1 application.

## 12. Component Boundaries

The new codebase uses focused modules:

- `app.py`: Streamlit page flow and user-facing messages.
- `batch_schema.py`: canonical column definitions, enumerations, units, and limits.
- `batch_validation.py`: workbook-level and row-level validation.
- `batch_adapter.py`: mapping between one spreadsheet row and the pure calculation engine.
- `batch_status.py`: deterministic status classification.
- `workbook_template.py`: generation of the controlled blank template.
- `workbook_processor.py`: workbook reading, row iteration, and result writing.
- `workbook_formatting.py`: tables, colors, filters, widths, protection, and summary formatting.
- `engine/`: pinned calculation modules copied from v1.1.
- `tests/`: inherited engine regressions plus batch-specific tests.

No module both calculates engineering results and controls the Streamlit UI.

## 13. Error Handling

Workbook-level errors stop processing and explain how to correct the file. Examples include wrong file type, missing primary worksheet, duplicate column names, missing required columns, password protection, files larger than 10 MB, or more than 500 populated rows.

Row-level errors do not stop the batch. Each affected row receives a stable error code and a plain-language explanation. Unexpected exceptions are recorded as `SYSTEM ERROR`; internal stack traces are logged for development but are not written into customer workbooks.

The processor always writes to a new in-memory workbook. It never overwrites the uploaded file.

## 14. Testing Strategy

### Engine regression

- Preserve the existing valid-input engine tests and reference vectors.
- Verify the current baseline vector produces 3 plies, 2.49 mm installed thickness, approximately 388.934 mm repair length, two 300 mm bands, approximately 2.5854 m2 fabric, and approximately 3.1025 kg epoxy.
- Preserve Type A closed-form/bisection cross-checks, B31G references, Type B Formula 12 cases, cloth-width behavior, and input validation tests.

### Batch behavior

- One valid row matches the single-case engine field by field.
- Multiple valid rows preserve order and defect IDs.
- A mixed workbook produces results for valid rows and errors only for invalid rows.
- Blank rows remain blank and do not count toward the 500-row limit.
- Duplicate defect IDs are rejected at row level.
- Conditional internal-corrosion rate behavior matches v1.1.
- Strict selection validation prevents silent route changes.
- `NOT REPAIRABLE` rows contain no installable repair quantities.
- Zero-pressure Type B rows do not crash.
- Input cells remain byte-for-byte equivalent where Excel representation permits.
- Output styles, filters, frozen panes, validation lists, status colors, and summary counts are verified.

### Deployment acceptance

- The existing v1.1 URL is verified before and after the new deployment.
- The new staging URL processes an acceptance workbook containing every route and status.
- The downloaded workbook opens without repair warnings in current Microsoft Excel.
- The application retains no uploaded workbook after the session.

## 15. Deployment

The deployment sequence is:

1. Implement and test locally in `Iso24817CalcBatch`.
2. Publish the new repository without changing the original repository.
3. Deploy a separate Streamlit staging application connected only to the new repository.
4. Complete engineering and usability acceptance with a controlled workbook.
5. Promote the separate batch application to its own production URL.

The existing production Streamlit application remains connected to its existing repository and deployment configuration throughout.

## 16. Future Extensions

After version 1 is accepted, independent enhancements may add:

- individual PDF reports packaged as a ZIP;
- a Google Sheets thin client backed by the same Python engine;
- an offline desktop or Excel add-in interface;
- configurable approved cloth widths;
- controlled audit storage and approval workflow.

Each extension must continue using one authoritative Python calculation engine and must not silently change existing calculations.
