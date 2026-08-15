# PROWRAP Batch Cost Calculation Sheet Design

**Date:** 2026-08-14
**Status:** Approved design, pending implementation plan
**Scope:** PROWRAP batch calculator only

## 1. Goal

Add a protected, user-editable `Cost Calculation` worksheet to the controlled
batch workbook. The worksheet shall present selected engineering inputs and
results in a compact commercial table, calculate material cost from fabric and
epoxy consumption, and calculate price from a user-controlled multiplier.

The existing `Batch Input & Results` worksheet and calculation engine remain
unchanged. The existing v1.1 calculator is outside this change.

## 2. User Workflow

1. The downloaded input template contains the blank `Cost Calculation` sheet.
2. The user completes and uploads the batch input in the existing manner.
3. The processed workbook contains one commercial row for every populated
   defect row, in the same order as `Batch Input & Results`.
4. The following three cells are blank, visibly highlighted, and unlocked:
   - `B3`: CF Cost / m2
   - `E3`: Epoxy Cost / kg
   - `H3`: Price Multiplier
5. The user may enter, change, or clear these three values after downloading
   the processed workbook. Cost and Price update automatically in Excel.
6. Cost and Price remain blank until their required commercial inputs exist.
7. A processed workbook may be uploaded again. The three commercial values are
   retained, and the controlled commercial table and formulas are regenerated.

## 3. Workbook Structure

The new current workbook sheet order is:

1. `Batch Information`
2. `Batch Input & Results`
3. `Cost Calculation`
4. `Warnings`
5. `Summary`
6. `Instructions`
7. `Lists` (hidden)

For backward compatibility, the processor continues accepting the prior exact
five-sheet and six-sheet controlled layouts. All newly generated templates and
processed workbooks use the seven-sheet layout above.

## 4. Worksheet Layout

- `A1:V1`: title area, `PROWRAP Cost Calculation`
- `A3`: `CF Cost / m2`; `B3`: blank editable numeric value
- `D3`: `Epoxy Cost / kg`; `E3`: blank editable numeric value
- `G3`: `Price Multiplier`; `H3`: blank editable numeric value
- Row 5: commercial table headers
- Row 6 onward: one row per populated defect
- Freeze panes at `A6`
- Gridlines hidden
- AutoFilter enabled on the commercial table

The three editable cells use the existing input color convention, a two-decimal
number format, and unlocked cell protection. Labels, copied engineering data,
table headers, and formula cells are locked. No currency symbol is fixed; Cost
and Price use a neutral `#,##0.00` number format.

Blank or non-negative numeric values are accepted in the three commercial
cells. Excel data validation provides a user-facing entry guard. Server-side
validation applies when a workbook containing values is uploaded again.

## 5. Commercial Table Mapping

The selected columns are copied as values from `Batch Input & Results` in the
exact order requested. Source column letters refer to the controlled main
report; destination letters refer to `Cost Calculation`.

| Destination | Source | Heading |
|---|---|---|
| A | A | Pipe OD [mm] |
| B | B | Nominal Wall [mm] |
| C | C | Pipe Yield [MPa] |
| D | D | Design Pressure [bar] |
| E | E | Operating Temperature [degC] |
| F | F | Mechanism |
| G | G | Defect Location |
| H | H | Defect Length [mm] |
| I | I | Remaining Wall [mm] |
| J | K | Design Life [years] |
| K | L | Design Factor |
| L | R | Prowrap CF Cloth Width [mm] |
| M | AC | Wall Loss [%] |
| N | AJ | Required Structural Thickness [mm] |
| O | AK | Installed Plies |
| P | AR | Total Repair Length [mm] |
| Q | AS | Cloth Band Count |
| R | AT | Procurement Axial Length [mm] |
| S | AU | Fabric Area [m2] |
| T | AV | Epoxy Mass [kg] |
| U | Calculated | Cost |
| V | Calculated | Price |

Rows with `INPUT ERROR`, `SYSTEM ERROR`, or no installable solution remain in
the commercial table so the table stays aligned with the populated batch. Their
unavailable engineering results remain blank, and Cost and Price remain blank.

## 6. Formulas

For the first commercial data row at row 6:

```excel
=IF(OR($B$3="",$E$3="",S6="",T6=""),"",S6*$B$3+T6*$E$3)
```

```excel
=IF(OR(U6="",$H$3=""),"",U6*$H$3)
```

These formulas fill down through the populated commercial rows using relative
row references and absolute assumption-cell references. The workbook requests
automatic/full recalculation on opening so changing a commercial input updates
all affected rows immediately.

## 7. Controlled Workbook and Formula Safety

The input template remains free of formulas. Cost and Price formulas are added
only by the batch processor to the processed workbook.

Formula validation remains deny-by-default. On re-upload, the processor accepts
only the exact generated Cost and Price formulas in `U6:V505`, the controlled
commercial-row range. This also permits a user to clear a defect input row in a
previously processed workbook without stale, but still exact, commercial
formulas blocking re-upload. Formulas in any other cell, or altered Cost or
Price formulas, remain a workbook-level error. The processor rebuilds every
output from a trusted template and copies only controlled batch inputs plus the
three commercial values; it never trusts uploaded commercial-table values.

Old five-sheet and six-sheet controlled templates remain valid. Unexpected
sheets, missing required sheets, changed headings, or unsafe formulas remain
invalid.

## 8. Processing Flow

1. Inspect the uploaded workbook and determine whether it is a supported legacy
   or current controlled layout.
2. Validate normal batch inputs and the three optional commercial values.
3. Permit only exact previously generated Cost and Price formulas, when present.
4. Create a fresh seven-sheet controlled workbook.
5. Copy common batch information and controlled defect inputs.
6. Retain valid commercial values from `B3`, `E3`, and `H3` when the source has
   the Cost Calculation sheet; otherwise leave them blank.
7. Calculate the engineering rows as before.
8. Populate the compact commercial table from the finished main report.
9. Add the controlled Cost and Price formulas and request Excel recalculation.

## 9. Error Handling

- Blank commercial inputs are valid and produce blank Cost or Price results.
- Negative, non-numeric, non-finite, or formula-based commercial inputs are
  rejected on upload with a plain-language workbook error.
- A missing Cost Calculation sheet is accepted only for a recognized legacy
  layout; the processed result upgrades it to the seven-sheet format.
- A changed commercial-table heading or unexpected formula is rejected.
- Commercial-sheet errors never change engineering row classification or
  silently alter the calculated repair design.

## 10. Testing and Acceptance

Automated tests shall verify:

- New templates contain the exact seven-sheet order.
- The new sheet has blank/unlocked `B3`, `E3`, and `H3`; protected headings,
  copied values, and formulas; freeze pane `A6`; and the expected table style.
- All twenty requested source columns map to the correct commercial headings and
  values in the correct order.
- Cost and Price formulas use the correct absolute and relative references.
- Blank commercial inputs yield blank formula results when recalculated.
- Representative rates and multiplier produce the expected Cost and Price.
- Error and no-solution rows retain row alignment and blank commercial results.
- A processed workbook with unchanged generated formulas can be re-uploaded,
  retains the three commercial values, and regenerates a clean result.
- Clearing a defect input row before re-upload removes its regenerated
  commercial row without treating its old exact Cost and Price formulas as
  unsafe.
- Altered formulas, extra formulas, negative rates, and invalid multiplier values
  are rejected deterministically.
- Existing five-sheet and six-sheet templates remain accepted.
- The 500-row limit, warning register, formula-injection protections, and all
  existing engineering calculations remain unchanged.

Visual acceptance shall render the Cost Calculation sheet with both empty and
populated commercial inputs. Headers, assumption cells, Cost, and Price must be
fully visible without clipped text, and the wide table must remain filterable
and usable at normal Excel zoom.

## 11. Documentation and Deployment

Update the template instructions and README to explain the blank commercial
inputs, formula definitions, neutral currency treatment, and safe re-upload
behavior. Deploy only to the separate PROWRAP batch calculator repository and
Streamlit application. Do not replace or combine it with the existing v1.1 app.
