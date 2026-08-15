# Deploy the separate PROWRAP Batch Repair Calculator

## Mandatory isolation boundary

Deploy batch version 1.2.0 only from the dedicated `Iso24817CalcBatch` GitHub repository and to the separate batch Streamlit application with its own URL: `https://prowrap-batch-calculator.streamlit.app/`.

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
6. Confirm the `Dent w/crack` acceptance row reports zero effective pipe capacity, a 50 bar composite pressure deficit, nine plies, and the basis `Dent w/crack - full-pressure laminate`.
7. Confirm the external `Dent no-crack` acceptance row reports component-pipe capacity of approximately 107.76 bar, zero composite pressure deficit, three plies, and the basis `Dent no-crack - substrate load sharing`.
8. On `Summary`, confirm Batch Engine Version is `1.2.0` and Pinned Source Revision is `746f3b3` before accepting the deployment.
9. Confirm the processed result has twenty mapped engineering fields on `Cost Calculation`, six compact rows, and only the exact controlled formulas in `U6:V11`. Verify `Cost = Fabric Area x CF Cost / m2 + Epoxy Mass x Epoxy Cost / kg` and `Price = Cost x Price Multiplier`; no currency symbol should be fixed.
10. Confirm the commercial table and formula cells are protected, row warnings contain codes only, `W003` lists affected rows `4, 6`, and the 500 mm `Dent no-crack` row has fabric/epoxy quantities and no warning.
11. Enter non-negative values in the three commercial cells, save the processed workbook, upload it again, and confirm the values and both canonical dent names are retained while the seven-sheet table and controlled formulas are regenerated. Previously downloaded controlled five-sheet, six-sheet, and seven-sheet workbooks must remain upgradeable under the existing structural validation rules.
12. Confirm the existing v1.1 URL still loads its independent calculator, without changing or redeploying it.

No uploaded workbook should be configured for persistent storage. Keep the application's temporary-file/session-only behaviour intact.

## Batch rollback procedure

1. Redeploy the **batch Streamlit app** from the last known-good commit in
   `Prowrap110/Iso24817CalcBatch`.
2. If needed, disable or remove only the batch app from Streamlit Cloud.
3. Do not change the v1.1 repository, deployment, URL, or configuration during
   a batch rollback.

The existing v1.1 calculator remains outside this release and rollback scope.
