# Deploy the separate PROWRAP Batch Repair Calculator

## Mandatory isolation boundary

Deploy batch version 1.1.0 only from the dedicated `Iso24817CalcBatch` GitHub repository and to the separate batch Streamlit application with its own URL.

Never deploy the batch code over, replace, rename, or redirect the existing v1.1 repository or application:

- repository: `Prowrap110/Iso24817Calc`
- existing application: `https://iso24817calc-prowrapv11.streamlit.app`

This release also contains a separately reviewed v1.1 branch that changes only the approved Tg basis to 110 degC and its derived 90 degC/80 degC limits. Merge and verify that branch in the v1.1 repository independently; never copy batch workbook files into it.

## Independent deployments

1. Push and merge the reviewed batch branch only in `Prowrap110/Iso24817CalcBatch`.
2. Confirm Streamlit Community Cloud keeps `app.py`, Python 3.11, and the existing separate batch-app URL.
3. Download the template, upload the generated acceptance workbook, calculate, and confirm the six statuses in order: `OK`, `REVIEW REQUIRED`, `NOT REPAIRABLE`, `INPUT ERROR`, `REVIEW REQUIRED`, `OK`.
4. Confirm the result has `Warnings` immediately after `Batch Input & Results`, row warnings contain codes only, `W003` lists affected rows `4, 6`, and the 500 mm row has no warning.
5. Separately push and merge `feature/tg110` only in `Prowrap110/Iso24817Calc`.
6. Wait for `https://iso24817calc-prowrapv11.streamlit.app` to redeploy and confirm its displayed Prowrap temperature limit is 90 degC.
7. Confirm both URLs still load their independent calculators.

No uploaded workbook should be configured for persistent storage. Keep the application's temporary-file/session-only behaviour intact.

## Rollback

Rollback affects only the new batch application:

1. Disable, redeploy, or roll back the **new batch Streamlit app** to its last known-good commit.
2. If needed, remove only the new batch app from Streamlit Cloud.
3. Do not change the v1.1 repository, deployment, URL, configuration, or Streamlit app during rollback.

The existing v1.1 calculator remains the independent fallback throughout.
