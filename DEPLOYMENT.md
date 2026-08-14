# Deploy the separate PROWRAP Batch Repair Calculator

## Mandatory isolation boundary

Deploy version 1.0.0 only from a **new GitHub repository** created for `Iso24817CalcBatch` and to a **new Streamlit application** with its own URL.

Never select, edit, replace, rename, redirect, or redeploy the existing v1.1 repository or application:

- repository: `Prowrap110/Iso24817Calcv1.1`
- existing application: `https://iso24817calc-prowrapv11.streamlit.app`

If either existing v1.1 item appears as a deployment target, stop. Select the new batch repository and create a separate Streamlit app instead.

## New staging deployment

1. Create a new GitHub repository named `Iso24817CalcBatch`; do not fork over or push this code to `Iso24817Calcv1.1`.
2. Push the reviewed batch-calculator branch to that new repository.
3. In Streamlit Community Cloud, create a new application from the new repository and select `app.py` as the entry point.
4. Set the runtime to Python 3.11. Streamlit installs dependencies from `requirements.txt`.
5. Name the application clearly as a batch/staging calculator and confirm its URL is different from the v1.1 URL before deployment.
6. Download the template, upload the generated acceptance workbook, calculate, and confirm the five statuses in order: `OK`, `REVIEW REQUIRED`, `NOT REPAIRABLE`, `INPUT ERROR`, `REVIEW REQUIRED`.
7. Confirm the existing v1.1 URL still loads its independent single-case calculator without any change.

No uploaded workbook should be configured for persistent storage. Keep the application's temporary-file/session-only behaviour intact.

## Rollback

Rollback affects only the new batch application:

1. Disable, redeploy, or roll back the **new batch Streamlit app** to its last known-good commit.
2. If needed, remove only the new batch app from Streamlit Cloud.
3. Do not change the v1.1 repository, deployment, URL, configuration, or Streamlit app during rollback.

The existing v1.1 calculator remains the independent fallback throughout.
