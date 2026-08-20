# CalcBatch v1.2 release verification

## Scope

This verification covers the separate CalcBatch v1.2 release only. It does not alter, deploy, redirect, or reconfigure the existing CalcBatch or the v1.1 single-case calculator.

## Controlled acceptance input

The reproducible generator creates an eight-sheet template and six main rows in this order:

1. External Corrosion — Actual defect length.
2. External Corrosion — Independent defects.
3. External Corrosion — Enter manually (`R-001`).
4. External Corrosion — Enter manually, deliberately invalid (`R-BAD`).
5. Dent no-crack.
6. Dent w/crack.

The first three corrosion comparisons use OD 1,016 mm, nominal wall 12 mm, 104.9 bar design pressure, 1,000 mm continuous repair span, and 500 mm cloth. Manual group `R-001` has D-01 `(10 mm, 9.652 mm, Yes)` and D-02 `(35 mm, 10.0 mm, Yes)`. `R-BAD` deliberately includes a `No` separation confirmation.

`t` means nominal pipe wall thickness. Actual assesses the entered continuous/interacting B31G length; Independent uses 10 mm x 10 mm separated-defect assumptions while retaining the entered continuous repair span; Manual assesses only the exact paired detail rows linked by a unique Repair Group ID. The least creditable valid Manual detail governs.

## Required reconciliation

- Actual safe pressure: `7.571542406120033 MPa`; installed plies: `12`.
- Independent safe pressure: `8.82257484144555 MPa`; installed plies: `7`.
- Manual safe pressure: `8.783461911867068 MPa`; installed plies: `7`.
- The continuous repair-zone length is 1,000 mm for all three comparison rows.
- Manual D-02 is governing.

The release checks permanent warning references with main and Individual Defects source rows, semantic commercial-field mapping, the exact protected Cost/Price formulas, processed-workbook re-upload, and controlled five-, six-, and seven-sheet legacy upgrades into the current eight-sheet contract.

## Source and retained corrections

CalcBatch version is `1.2.0`. The verified linked-corrosion engine revision is `91b68d64508a4786934f0e17f2aea0dbebf745a7`, recorded in workbooks as `91b68d6`. The batch retains its documented batch-only corrections: strict upload validation, high-temperature review routing, zero-pressure Type B handling, 300/500 mm cloth configuration behavior, dent routing, protected warning register, and controlled commercial formulas.

## Operator limits

The product accepts at most 500 populated main rows, 2,000 populated Individual Defects rows, and a 10 MB upload. Customer, Project Location, and Report No remain common batch fields. Cost inputs are B3 (CF Cost / m2), E3 (Epoxy Cost / kg), and H3 (Price Multiplier). Cost is Fabric Area x CF Cost / m2 + Epoxy Mass x Epoxy Cost / kg; Price is Cost x Price Multiplier.

## Final artifact verification — 2026-08-20

The full suite passed immediately before workbook generation: **282 passed in
369.61 s**. The spreadsheet artifact operation marker was successfully run once
with `create`, two expected `.xlsx` outputs, and no subsequent marker run.

| Artifact | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `PROWRAP_CalcBatch_v1.2_Acceptance_Input.xlsx` | 171,680 | `1a8bdb0adc21ee9e3bc09b6bdfca5ac969c219dd98c910bc9dc0df4bf3bff39e` |
| `PROWRAP_CalcBatch_v1.2_Acceptance_Processed.xlsx` | 178,112 | `27b645300213c9d720f012b30d376a35c2592c647b1b1caf03a499f0c1f31c29` |

The input workbook has no formulas. The processed workbook has exactly twelve
formulas, and every one is confined to Cost Calculation `U6:V11`: the six
controlled Cost formulas in column U and six controlled Price formulas in
column V. The final processed commercial assumptions B3, E3, and H3 remain
blank and editable.

### Structural and engineering reconciliation

- Exact worksheet order verified: Batch Information, Batch Input & Results,
  Individual Defects, Cost Calculation, Warnings, Summary, Instructions, Lists;
  Lists is hidden.
- Main and detail table/autofilter references match: `A1:BG501` (500 rows) and
  `A1:O2001` (2,000 rows). Input cells are unlocked; result cells are locked;
  filters and selection controls remain enabled under sheet protection.
- Result statuses are `REVIEW REQUIRED`, `REVIEW REQUIRED`, `REVIEW REQUIRED`,
  `INPUT ERROR`, `OK`, `OK`. Main source rows are 2–7 and detail source rows are
  2–4.
- Direct engine calls and workbook results agree: Actual =
  7.571542406120033 MPa / 12 plies; Independent = 8.82257484144555 MPa / 7
  plies; Manual = 8.783461911867068 MPa / 7 plies. Each has a 1,000 mm repair
  zone. The manual result has two candidates and D-02 governs at 35 mm and
  10 mm remaining wall.
- Detail results remain on their respective source rows; D-01 and D-02 report
  88.2257484144555 and 87.83461911867067 bar, respectively. The deliberate
  R-BAD row is localized as an `INVALID_SELECTION` input error.
- The W013 warning register reads `Main 2, 3, 4; Individual Defects 2, 3`.
  The semantic 20-column Cost mapping exactly matches its named main-sheet
  sources.
- Dent no-crack and Dent w/crack direct-engine checks retained their expected
  routes: 10.775653543307088 MPa / 3 plies and 0 MPa / 9 plies, respectively.
- Re-uploading the processed workbook through `process_workbook` at the fixed
  UTC time retained all main/detail engineering results, warnings, summary
  identity, statuses, and the twelve controlled formulas.

### Commercial recalculation and visual inspection

For a temporary, non-delivered acceptance copy only, the approved assumptions
B3 = 25, E3 = 8, and H3 = 1.4 were populated with the spreadsheet artifact
tool, then passed through `process_workbook` to restore the controlled workbook
contract. LibreOffice recalculation verified Cost = Fabric Area x 25 + Epoxy
Mass x 8 and Price = Cost x 1.4 for every calculable row; maximum absolute
reconciliation difference was `4.1e-12`. The invalid row remained blank.

All eight sheets were rendered and reviewed. Batch information, detail inputs,
commercial assumptions, warning register, summary, and instructions are
legible; freezes, input highlighting, result-status colours, warning text, and
detail error wrapping are visible. The 59-column Batch Input & Results sheet is
inherently horizontal; three segmented renders verified the complete left,
middle, and right table without clipped headings. A single full-width renderer
preview is compressed, which is a renderer-only limitation rather than a
workbook defect.

No current CalcBatch, v1.1, existing live target, deployment, remote, or GitHub
publication was changed by this verification. The feature worktree has no
tracked changes apart from this report; the two generated acceptance workbooks
are intentionally untracked release artifacts.
