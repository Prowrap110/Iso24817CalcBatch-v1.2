# PROWRAP CalcBatch v1.2

PROWRAP CalcBatch v1.2 is a separate Excel batch calculator for preliminary PROWRAP repair screening. It processes up to 150 continuous-repair rows and 150 linked individual-defect rows, then returns a new workbook with controlled results beside the inputs.

It is deliberately independent from the existing single-case PROWRAP v1.1 calculator. This repository, its deployment, and its URL must never replace, redirect, modify, or be deployed over the v1.1 application.

## Run locally

Use Python 3.11, then install the application dependencies:

```bash
python3 -m pip install -r requirements-dev.txt
streamlit run app.py
```

## Use the batch workbook

1. Download the controlled `PROWRAP_CalcBatch_v1.2_Template.xlsx` from the app.
2. On **Batch Information**, enter Customer, Project Location, and Report No once.
3. On **Batch Input & Results**, enter one continuous repair zone per row, starting with `Pipe OD [mm]`. Do not add, remove, rename, or reorder columns.
4. For external corrosion, select one **Defect Length Basis**:
   - **Actual defect length** assesses the entered length and remaining wall as one continuous/interacting B31G defect.
   - **Independent defects** assumes 10 mm x 10 mm defects, each separated by more than `3t`, using the entered remaining wall. The entered Defect Length is still the full continuous repair-zone span.
   - **Enter manually** leaves the main Remaining Wall blank and gives the row a unique Repair Group ID. Enter its individually paired lengths and remaining walls on **Individual Defects**; each row must confirm separation exceeds `3t`. The least creditable individual assessment governs, but the main Defect Length remains the full repair-zone span.
5. Here `t` means the **nominal pipe wall thickness**, not defect depth or remaining wall. Manual group ownership is exact: one Repair Group ID belongs to one manual main row, and orphan, duplicate, or incomplete detail records are reported locally.
6. Upload the `.xlsx`, review the first 20 rows, calculate, and download the new results workbook.
7. In the processed workbook, enter or change the three highlighted commercial assumptions on **Cost Calculation**: `B3` for CF Cost / m2, `E3` for Epoxy Cost / kg, and `H3` for Price Multiplier.
8. Enter an optional blank or non-negative **Quantity** for each compact Cost row. **Total Amount** is the locked controlled formula `Price x Quantity`.

The template accepts at most 150 populated main rows and 150 populated Individual Defects rows, and uploads cannot exceed 10 MB. Blank rows are ignored; partially completed rows are retained and marked individually. The input cells and their row order are preserved. The only main outputs are **Wall Loss [%]**, **Required Structural Thickness [mm]**, **Installed Plies**, **Total Repair Length [mm]**, **Cloth Band Count**, **Procurement Axial Length [mm]**, **Fabric Area [m2]**, **Epoxy Mass [kg]**, and **Repair Zone Length [mm]**. The downloaded input template contains no formulas, macros, or VBA. A processed workbook contains only the controlled Cost, Price, and Total Amount formulas described below.

The mechanism list distinguishes two dent calculation routes. **Dent w/crack** uses the conservative full-pressure laminate basis and claims no substrate pressure credit. For an eligible external defect with at least 1 mm remaining wall, **Dent no-crack** uses component-pipe substrate load sharing based on pipe yield strength, design factor, remaining wall, and outside diameter. Internal dents and external dents below 1 mm remaining wall stay on the Type B full-replacement route with no substrate credit. `Dent no-crack` selects the composite-repair calculation basis; it is not a complete dent integrity or fatigue acceptance assessment. Dent depth, local strain, ovalization, fatigue, gouge, and weld interaction remain outside this calculator and require competent engineering review.

Download and use the current `PROWRAP_CalcBatch_v1.2_Template.xlsx` with its 150 main-row and 150 Individual Defects-row limits. Older 500/2,000-row templates are not supported or guaranteed for this release; start again from the current template before calculation.

Quantity and Total Amount complete the Cost Calculation tail after Cost and Price. Quantity is blank by default, visibly highlighted, editable, and restricted to non-negative numbers; Total Amount is locked and formula-controlled as `Price x Quantity`. Valid Quantity values are retained on a safe re-upload while all controlled engineering values and formulas are rebuilt.

The **Cost Calculation** table contains the twenty requested engineering fields in the same compact row order as the populated defects. Cost is calculated as `Fabric Area x CF Cost / m2 + Epoxy Mass x Epoxy Cost / kg`; Price is `Cost x Price Multiplier`. Both remain blank until their required assumptions and material quantities exist. No currency symbol is fixed, so enter both material rates in one consistent currency. The three assumptions remain editable after download, and a processed workbook may be uploaded again: its assumptions are retained while the controlled table and formulas are rebuilt from the trusted engineering results.

Processed defect rows show only permanent references such as `W003, W006` in the `Compliance Warnings` column. The separate **Warnings** worksheet gives each code's full meaning, required action, and affected source-row numbers. Repeated warnings share one permanent code and one consolidated register entry.

Prowrap CF cloth widths of **300 mm and 500 mm** are approved configurations in this batch release; both continue to use the fixed 50 mm stitch overlap. The approved material basis is **Tg = 110 degC**, giving a general qualified design-temperature limit of **90 degC** and a long-life Class 3 Type B limit of **80 degC**.

Use only the current eight-sheet template and its processed-workbook contract for re-upload. The download contains **Batch Information**, **Batch Input & Results**, **Individual Defects**, **Cost Calculation**, **Warnings**, **Summary**, **Instructions**, and hidden **Lists**.

## Statuses

- `OK` — a valid screening result with no review warning.
- `REVIEW REQUIRED` — a result exists, but engineering or product approval is needed.
- `NOT REPAIRABLE` — the Type B Formula 12 route has no repair solution; do not treat any diagnostic result as an installable design.
- `INPUT ERROR` — correct the main or linked Individual Defects row and recalculate.
- `SYSTEM ERROR` — retain the workbook and contact PROTAP.

These are preliminary screening outputs. Competent engineering review is required before repair design, approval, procurement, or installation.

## Privacy and file handling

The app processes one controlled `.xlsx` workbook at a time (maximum 10 MB). Uploads and generated files are kept only in the active Streamlit session or temporary processing memory; the application does not create a calculation database or retain customer workbooks. Do not upload macro-enabled or password-protected workbooks. Unexpected or altered formulas are rejected; only the exact Cost, Price, and Total Amount formulas produced by this calculator are accepted on re-upload.

## Verify

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 scripts/create_acceptance_workbook.py /tmp/PROWRAP_Batch_Acceptance.xlsx
```

The six-row acceptance workbook exercises Actual, Independent, and linked Manual external corrosion; an invalid Manual group; `Dent no-crack`; and `Dent w/crack`. It reconciles the three corrosion safe pressures, plies, continuous repair span, governing manual detail, permanent warning references, the twenty-field commercial mapping, editable Quantity, controlled Cost/Price/Total Amount formulas, and current-template re-upload behavior. Batch release version is `1.2.0`; its verified external-corrosion engine source is `91b68d64508a4786934f0e17f2aea0dbebf745a7`.
