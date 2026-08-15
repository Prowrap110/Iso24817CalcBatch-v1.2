# Deploy the separate PROWRAP Batch Repair Calculator

## Mandatory isolation boundary

Deploy batch version 1.1.0 only from the dedicated `Iso24817CalcBatch` GitHub repository and to the separate batch Streamlit application with its own URL.

Never deploy the batch code over, replace, rename, or redirect the existing v1.1 repository or application:

- repository: `Prowrap110/Iso24817Calcv1.1`
- existing application: `https://iso24817calc-prowrapv11.streamlit.app`

This release changes only the separate batch repository and batch application. It does not include, merge, redeploy, or roll back any v1.1 branch or application.

## Independent deployments

1. Push and merge the reviewed batch branch only in `Prowrap110/Iso24817CalcBatch`.
2. Confirm Streamlit Community Cloud keeps `app.py`, Python 3.11, and the existing separate batch-app URL.
3. Download the template and confirm the exact seven-sheet order: `Batch Information`, `Batch Input & Results`, `Cost Calculation`, `Warnings`, `Summary`, `Instructions`, `Lists`.
4. Confirm `Cost Calculation!B3`, `E3`, and `H3` are blank, highlighted, and editable; the input template itself contains no formulas.
5. Upload the generated acceptance workbook, calculate, and confirm the six statuses in order: `OK`, `REVIEW REQUIRED`, `NOT REPAIRABLE`, `INPUT ERROR`, `REVIEW REQUIRED`, `OK`.
6. Confirm the processed result has twenty mapped engineering fields on `Cost Calculation`, six compact rows, and only the exact controlled formulas in `U6:V11`. Verify `Cost = Fabric Area x CF Cost / m2 + Epoxy Mass x Epoxy Cost / kg` and `Price = Cost x Price Multiplier`; no currency symbol should be fixed.
7. Confirm the commercial table and formula cells are protected, row warnings contain codes only, `W003` lists affected rows `4, 6`, and the 500 mm row has fabric/epoxy quantities and no warning.
8. Enter non-negative values in the three commercial cells, save the processed workbook, upload it again, and confirm the values are retained while the seven-sheet table and controlled formulas are regenerated. Previously downloaded controlled five-sheet and six-sheet layouts must also upgrade to this seven-sheet result.
9. Confirm the existing v1.1 URL still loads its independent calculator, without changing or redeploying it.

No uploaded workbook should be configured for persistent storage. Keep the application's temporary-file/session-only behaviour intact.

## Batch rollback procedure

1. Redeploy the **batch Streamlit app** from the last known-good commit in
   `Prowrap110/Iso24817CalcBatch`.
2. If needed, disable or remove only the batch app from Streamlit Cloud.
3. Do not change the v1.1 repository, deployment, URL, or configuration during
   a batch rollback.

The existing v1.1 calculator remains outside this release and rollback scope.
