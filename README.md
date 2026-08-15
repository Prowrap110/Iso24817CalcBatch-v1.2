# PROWRAP Batch Repair Calculator

Version 1.2.0 is a separate Excel batch calculator for preliminary PROWRAP repair screening. It processes up to 500 independent pipeline-defect rows and returns a new workbook with row-level results appended beside the inputs.

It is deliberately independent from the existing single-case PROWRAP v1.1 calculator. This repository, its deployment, and its URL must never replace, redirect, modify, or be deployed over the v1.1 application.

## Run locally

Use Python 3.11, then install the application dependencies:

```bash
python3 -m pip install -r requirements-dev.txt
streamlit run app.py
```

## Use the batch workbook

1. Download the controlled `PROWRAP_Batch_Template.xlsx` from the app.
2. On **Batch Information**, enter Customer, Project Location, and Report No once.
3. On **Batch Input & Results**, enter one defect per row, starting with `Pipe OD [mm]`. Do not add, remove, rename, or reorder columns.
4. Upload the `.xlsx`, review the first 20 rows, calculate, and download the new results workbook.
5. In the processed workbook, enter or change the three highlighted commercial assumptions on **Cost Calculation**: `B3` for CF Cost / m2, `E3` for Epoxy Cost / kg, and `H3` for Price Multiplier.

The template accepts at most 500 populated rows. Blank rows are ignored; partially completed rows are retained and marked individually. The input cells and their row order are preserved. Results are appended only in the output columns. The downloaded input template contains no formulas, macros, or VBA. A processed workbook contains only the controlled Cost and Price formulas described below.

The mechanism list distinguishes two dent calculation routes. **Dent w/crack** uses the conservative full-pressure laminate basis and claims no substrate pressure credit. For an eligible external defect with at least 1 mm remaining wall, **Dent no-crack** uses component-pipe substrate load sharing based on pipe yield strength, design factor, remaining wall, and outside diameter. Internal dents and external dents below 1 mm remaining wall stay on the Type B full-replacement route with no substrate credit. `Dent no-crack` selects the composite-repair calculation basis; it is not a complete dent integrity or fatigue acceptance assessment. Dent depth, local strain, ovalization, fatigue, gouge, and weld interaction remain outside this calculator and require competent engineering review.

Previously downloaded controlled batch workbooks containing the legacy generic `Dent` value remain accepted. During processing, that value is migrated conservatively to `Dent w/crack` and written with the canonical name in the regenerated result and Cost Calculation sheets. A legacy row never gains the `Dent no-crack` substrate credit automatically.

The **Cost Calculation** table contains the twenty requested engineering fields in the same compact row order as the populated defects. Cost is calculated as `Fabric Area x CF Cost / m2 + Epoxy Mass x Epoxy Cost / kg`; Price is `Cost x Price Multiplier`. Both remain blank until their required assumptions and material quantities exist. No currency symbol is fixed, so enter both material rates in one consistent currency. The three assumptions remain editable after download, and a processed workbook may be uploaded again: its assumptions are retained while the controlled table and formulas are rebuilt from the trusted engineering results.

Processed defect rows show only permanent references such as `W003, W006` in the `Compliance Warnings` column. The separate **Warnings** worksheet gives each code's full meaning, required action, and affected source-row numbers. Repeated warnings share one permanent code and one consolidated register entry.

Prowrap CF cloth widths of **300 mm and 500 mm** are approved configurations in this batch release; both continue to use the fixed 50 mm stitch overlap. The approved material basis is **Tg = 110 degC**, giving a general qualified design-temperature limit of **90 degC** and a long-life Class 3 Type B limit of **80 degC**.

Previously downloaded controlled five-sheet, six-sheet, and seven-sheet workbooks remain accepted under their existing structural validation rules. Processing upgrades older layouts to the current seven-sheet output containing **Cost Calculation** and the **Warnings** register.

## Statuses

- `OK` — a valid result with no review warning.
- `REVIEW REQUIRED` — a result exists, but engineering or product approval is needed.
- `NOT REPAIRABLE` — the Type B Formula 12 route has no repair solution; do not treat any diagnostic result as an installable design.
- `INPUT ERROR` — correct the row-level error and recalculate.
- `SYSTEM ERROR` — retain the workbook and contact PROTAP.

These are preliminary screening outputs. Competent engineering review is required before repair design, approval, procurement, or installation.

## Privacy and file handling

The app processes one controlled `.xlsx` workbook at a time (maximum 10 MB). Uploads and generated files are kept only in the active Streamlit session or temporary processing memory; the application does not create a calculation database or retain customer workbooks. Do not upload macro-enabled or password-protected workbooks. Unexpected or altered formulas are rejected; only the exact Cost and Price formulas produced by this calculator are accepted on re-upload.

## Verify

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 scripts/create_acceptance_workbook.py /tmp/PROWRAP_Batch_Acceptance.xlsx
```

The six-row acceptance workbook exercises `Dent w/crack` with zero substrate credit and `Dent no-crack` with component-pipe load sharing, plus `OK`, `REVIEW REQUIRED`, `NOT REPAIRABLE`, `INPUT ERROR`, a zero-pressure Type B `REVIEW REQUIRED` row, repeated permanent warning references, a warning-free 500 mm cloth row, the twenty-field commercial mapping, and controlled Cost and Price formulas.
