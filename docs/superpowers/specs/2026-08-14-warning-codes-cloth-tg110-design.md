# PROWRAP Warning Codes, Approved Cloth Widths, and Tg 110 Design

## Objective

Improve the batch results workbook without changing any repair input or output
calculation columns, and update the PROWRAP temperature basis consistently.
The existing v1.1 Streamlit calculator and the separate batch Streamlit
calculator remain independent applications.

## Approved Requirements

1. Replace long warning text in each batch result row with permanent warning
   codes such as `W001` and `W018`.
2. Put the full warning register on a separate visible `Warnings` worksheet,
   not below the main defect table.
3. Treat both 300 mm and 500 mm Prowrap CF cloth as approved configurations.
   Neither width produces a cloth-approval warning in the batch calculator.
4. Set the Prowrap glass transition temperature, Tg, to 110 degC in both the
   batch calculation engine and the existing v1.1 calculator.
5. Retain the current ISO-derived temperature rules:
   - general qualified design-temperature limit = Tg - 20 degC = 90 degC;
   - Class 3 Type B limit for service longer than two years = Tg - 30 degC =
     80 degC.

## Workbook Design

### Main results worksheet

The `Batch Input & Results` table keeps its current columns and controlled
500-row extent. The existing `Compliance Warnings` column is retained so
previously downloaded templates remain recognizable. Its processed cells
contain only comma-separated permanent codes, for example `W001, W018`.
Long warning sentences are never written into defect rows.

The column width is reduced to suit codes, while the status, engineering
outputs, table filters, frozen panes, protection, and input values remain
unchanged.

### Warnings worksheet

Processed workbooks contain a visible `Warnings` worksheet immediately after
`Batch Input & Results`. It contains one row for each warning code present in
the processed batch, ordered by code. The columns are:

- `Warning Code`
- `Warning Meaning / Required Action`
- `Affected Excel Rows`

Repeated occurrences use the same permanent code and are consolidated. The
affected-row cell lists the source Excel row numbers in ascending order. If a
batch contains no warnings, the worksheet retains its title, headers, and a
plain-language `No compliance warnings were generated.` message.

The worksheet is formula-free, protected consistently with the other output
sheets, uses a filterable Excel table for populated warning rows, freezes the
header, wraps the warning description, and uses the established PROWRAP
header colors.

### Template compatibility

Newly downloaded templates include the blank `Warnings` worksheet. Upload
validation accepts exactly either:

- the previous controlled five-sheet layout; or
- the new controlled six-sheet layout with `Warnings` in its defined position.

No arbitrary extra worksheet is accepted. Processing always regenerates a
fresh current-version workbook, so an older valid template is upgraded to the
six-sheet output and user changes to controlled output content do not survive.

## Permanent Warning Catalogue

The catalogue uses one stable code per engineering condition. Dynamic values
remain visible in the associated defect input and result cells; the warning
register gives the stable meaning and required action.

| Code | Permanent meaning |
|---|---|
| W001 | Design temperature exceeds the general qualified Prowrap limit; engineering review is required before design or installation. |
| W002 | No Type B Formula 12 repair solution exists for the requested case; do not install without changing the design basis or repair method. |
| W003 | Requested Type B life exceeds the qualified PRW110 life; inspect, revalidate, or replace at the qualified limit. |
| W004 | Class 3 Type B design temperature exceeds the applicable Tg - 30 service limit. |
| W005 | Zero-pressure Type B Formula 12 is non-controlling; the impact-qualified minimum is shown and classification requires review. |
| W006 | Type B design uses the defined through-wall defect basis and Annex F impact-qualified minimum; assessor confirmation is required. |
| W007 | Type B Formula 12 defect-size validity limit is exceeded; an engineered assessment is required. |
| W008 | B31G d/t exceeds 0.80; B31G is not applicable and no substrate credit is taken. |
| W009 | B31G d/t is at or below 0.10; the section 3(a) length limitation note applies. |
| W010 | B31G safety factor is below the permitted minimum. |
| W011 | Modified B31G SMYS validity is exceeded and the calculation falls back to Original B31G. |
| W012 | B31G flow stress has been capped at SMTS. |
| W013 | B31G Level 1 finds the corroded pipe unacceptable at design pressure; the composite repair is structural. |
| W014 | Internal corrosion has been projected to end of design life; assessment uses the end-of-life remaining wall. |
| W015 | Internal corrosion rate is zero; enter a justified rate or perform engineering review. |
| W016 | Type B with axial load case 1 requires an engineered axial-load-path assessment. |
| W017 | Repair thickness exceeds D/12; the ISO thin-wall formulae are outside their validity range. |
| W018 | Entered Prowrap CF cloth width is not an approved 300 mm or 500 mm configuration; confirm product approval. |
| W019 | Requested Type A / Class 3 check was skipped at zero pressure because it is non-controlling; engineering review is required. |
| W020 | Requested Type A / Class 3 check was skipped above the qualified Prowrap temperature limit; engineering review is required. |

Every warning emitted to a batch result must resolve to exactly one catalogue
code. An unmapped warning is a processing defect and must not be silently
replaced with an improvised or batch-specific number.

## Calculation and Data Flow

The calculation engines continue to produce their full engineering warning
messages for internal traceability and the v1.1 screen. A batch warning-catalog
layer maps each known warning condition to its permanent code. Row status
classification continues to use the presence of engineering warnings, so
changing the workbook presentation cannot change `OK`, `REVIEW REQUIRED`, or
`NOT REPAIRABLE` classification.

The processor performs these steps:

1. calculate each populated defect row;
2. retain its full internal warnings and resolved codes;
3. write only codes to the row;
4. aggregate affected source rows by code;
5. build the controlled `Warnings` worksheet from the catalogue;
6. write the unchanged summary counts and other results.

The 500 mm cloth approval changes only the approval warning decision. Band
count, procurement length, fabric area, and epoxy mass still use the entered
cloth width and the existing fixed 50 mm stitch overlap.

The Tg change updates the material constant from 78.18 degC to 110 degC. All
derived limits must continue to be calculated from Tg rather than separately
hard-coded as 90 degC or 80 degC.

## Existing v1.1 Calculator

The v1.1 repository receives only the approved material-basis change needed
for this request: Tg becomes 110 degC and all derived temperature checks and
displayed limits follow it. No batch workbook UI or warning worksheet is added
to v1.1. Its existing URL and deployment remain separate from the batch app.

## Error Handling and Integrity

- Workbook-level structural, formula, size, and sparse-cell defenses remain in
  force.
- Old and new controlled workbook layouts are accepted explicitly; other sheet
  sets or orders are rejected.
- Output workbooks are rebuilt from the trusted current template.
- Warning cells and the warning register contain no formulas or macros.
- Unexpected calculation exceptions remain `SYSTEM ERROR` rows and are logged
  without customer inputs.
- Warning codes do not replace row input errors: error code and error message
  columns remain unchanged.

## Verification

Implementation is test-driven and must prove:

- a row with one or more warnings contains codes only;
- repeated warnings reuse the same code and consolidate affected row numbers;
- every generated engineering warning has a catalogue code;
- a no-warning batch has a clear empty-state `Warnings` worksheet;
- the current six-sheet template and previous five-sheet template both process;
- arbitrary extra or reordered sheets remain rejected;
- 300 mm and 500 mm cloth generate no approval warning;
- another valid cloth width still produces `W018` and `REVIEW REQUIRED`;
- Tg is 110 degC in both repositories;
- the general qualification boundary is 90 degC;
- the long-life Class 3 Type B boundary is 80 degC;
- status counts and numerical calculation outputs remain correct;
- generated workbooks contain no formulas and open without Excel repair alerts;
- all existing automated tests pass in both repositories;
- the main results table and every visible worksheet pass a visual legibility
  review.

Deployment verification is separate for the two applications. Each repository
is committed, pushed, and checked at its own Streamlit URL; success in one app
does not imply the other has deployed.
