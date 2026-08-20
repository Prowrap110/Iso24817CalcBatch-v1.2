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
