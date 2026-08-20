# Deploy CalcBatch v1.2 as a separate application

## Stop: confirm the target before doing anything

This release is only for a **new GitHub repository** and a **new Streamlit Community Cloud application with a new URL**. Stop immediately if the selected repository or Streamlit application is either:

- the current CalcBatch repository/application; or
- `Prowrap110/Iso24817Calcv1.1` or `https://iso24817calc-prowrapv11.streamlit.app`.

Do not merge into, push to, reconfigure, replace, rename, redirect, or deploy over either older calculator. They remain separate products and URLs.

## Separate release procedure

1. Create or select the dedicated repository for this release, named clearly as `Iso24817CalcBatch-v1.2`. Confirm it is not the current CalcBatch repository.
2. Push only the reviewed CalcBatch v1.2 branch to that new repository.
3. In Streamlit Community Cloud, create a **new** application from that repository, with `app.py` as the entry point and Python 3.11.
4. Choose and record a new, distinct Streamlit URL. Do not reuse a current CalcBatch or v1.1 URL.
5. Download the template and verify this exact eight-sheet order: `Batch Information`, `Batch Input & Results`, `Individual Defects`, `Cost Calculation`, `Warnings`, `Summary`, `Instructions`, and hidden `Lists`.
6. Upload the generated six-row acceptance workbook and confirm Actual, Independent, linked Manual, invalid Manual group, `Dent no-crack`, and `Dent w/crack` all appear in that order.
7. Confirm the three corrosion comparison rows retain a 1,000 mm repair-zone length. Reconcile their safe pressures as 7.571542406120033 MPa, 8.82257484144555 MPa, and 8.783461911867068 MPa; reconcile installed plies as 12, 7, and 7. Confirm Manual defect `D-02` governs.
8. Confirm the processed workbook records Batch Engine Version `1.2.0` and Pinned Source Revision `91b68d6`.
9. Confirm the Cost Calculation table contains the twenty semantic engineering fields plus Cost and Price. `B3`, `E3`, and `H3` remain blank, highlighted, and editable. Cost is `Fabric Area x CF Cost / m2 + Epoxy Mass x Epoxy Cost / kg`; Price is `Cost x Price Multiplier`.
10. Re-upload a processed workbook with non-negative B3/E3/H3 values. Confirm the values persist while the trusted eight-sheet output, linked details, warnings, and exact controlled Cost/Price formulas are rebuilt.
11. Confirm controlled five-, six-, and seven-sheet historical workbooks upgrade into the eight-sheet v1.2 output; eligible legacy external-corrosion rows use Actual defect length.

The application must continue to process one workbook at a time in session/temporary memory only. Do not configure persistent customer-workbook storage.
