# CalcBatch v1.2 Compact Output, Commercial Quantity, and 150-Row Design

## Status and authority

This design implements the user's 2026-08-20 instruction to revise only the
public CalcBatch v1.2 product. The instruction explicitly grants execution and
publication authority without another design question. The existing v1.1
calculator and earlier CalcBatch deployment remain outside scope.

## Goal

Make the controlled workbook easier to use by reducing the visible output area
on **Batch Input & Results**, adding quantity-based totals to **Cost
Calculation**, and limiting both main repair rows and linked individual-defect
rows to 150 records.

## Controlled workbook contract

### Batch Input & Results

The 20 current input columns remain unchanged and in their current order. The
only output columns in both a newly downloaded template and a processed result
are, in this exact order:

1. `Wall Loss [%]`
2. `Required Structural Thickness [mm]`
3. `Installed Plies`
4. `Total Repair Length [mm]`
5. `Cloth Band Count`
6. `Procurement Axial Length [mm]`
7. `Fabric Area [m2]`
8. `Epoxy Mass [kg]`
9. `Repair Zone Length [mm]`

The current table therefore has 29 columns and 151 rows including its header,
ending at `AC151`. Removed diagnostic values are not written as additional,
hidden, or appended columns on this sheet.

The calculation engine continues to produce its complete internal result. The
processor uses that internal result to populate Summary status totals, route
counts, engineering-review counts, and the Warnings register. The Streamlit
preview continues to show row status and correction messages before the user
calculates. No engineering equation or status-classification rule changes.

### Individual Defects

The existing five input columns and nineteen scalar B31G audit output columns
remain unchanged. The table accepts 150 populated detail rows, Excel rows 2
through 151. A populated input cell at row 152 or later is a workbook-level
`DETAIL_ROW_OUT_OF_RANGE` error.

### Cost Calculation

The existing twenty engineering columns, `Cost`, and `Price` remain unchanged.
Append two columns:

- `Quantity` in column W: blank by default, unlocked and visibly highlighted,
  protected by decimal-greater-than-or-equal-to-zero validation.
- `Total Amount` in column X: locked controlled formula.

For cost row `r`, the exact formula is:

```excel
=IF(OR(Vr="",Wr=""),"",Vr*Wr)
```

Thus blank Price or Quantity gives blank Total Amount, while Quantity zero
gives a numeric zero. Cost, Price, and Total Amount formulas are the only
formulas allowed in a processed workbook. Quantity formulas, negative values,
Booleans, text, NaN, and infinity are rejected. On safe re-upload, valid
Quantity values are preserved by compact cost-row position; all engineering
fields and formulas are rebuilt from trusted calculations.

The Cost table spans `A5:X...`; the input template contains no formulas. A
processed 150-row workbook may contain formulas only in `U6:U155`, `V6:V155`,
and `X6:X155` for populated compact rows.

## Limits and compatibility

- Main repair rows: maximum 150 populated rows, Excel rows 2 through 151.
- Individual Defects rows: maximum 150 populated rows, Excel rows 2 through
  151.
- Cost rows: maximum 150 compact rows, Excel rows 6 through 155.
- Upload byte, ZIP entry, compression, and macro/formula safety controls remain
  active. The parsed worksheet-cell ceiling is recalibrated to the smaller
  controlled workbook with conservative headroom.

The supported release contract is the current 150/150 template and a processed
workbook produced from that template. Older 500/2,000-row, five-, six-,
seven-sheet, and historical-wide templates are not supported or guaranteed;
users must download the current v1.2 template before calculation.

## User interface and documentation

The app title, repository, branch, and public URL remain the CalcBatch v1.2
identity. App guidance, workbook Instructions, README, and deployment checklist
state the 150/150 limits, nine main outputs, Quantity input, and Total Amount
formula. Download names remain the v1.2 names.

## Verification and release

The release must demonstrate:

- exact main header order and `A1:AC151` table/filter;
- exact detail `A1:X151` table/filter;
- exact Cost `A5:X...` table/filter and protected/unlocked behavior;
- formulas restricted to exact U/V/X formulas;
- valid Quantity preservation through processed-workbook re-upload;
- 150-row success and first-excess-row rejection for both input sheets;
- Summary and Warnings parity after removing main diagnostic columns;
- current-template re-upload without changing linked-corrosion inputs;
- a full automated regression pass and visual inspection of every final sheet;
- a scoped commit and push to the existing public
  `feature/linked-corrosion-v12` branch; and
- live verification at
  `https://iso24817calcbatch-prowrapv12.streamlit.app/`.

No v1.1 repository, older CalcBatch repository, branch, settings, or deployment
may be changed.
