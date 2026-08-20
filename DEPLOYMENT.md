# Deploy CalcBatch v1.2 to its existing public application

## Fixed release target

Deploy only the reviewed `feature/linked-corrosion-v12` branch of the existing
CalcBatch v1.2 repository to the existing public Streamlit application:

`https://iso24817calcbatch-prowrapv12.streamlit.app`

Do not create a new repository, branch, Streamlit application, or URL. Do not
merge into, push to, reconfigure, replace, rename, redirect, or deploy over
the PROWRAP v1.1 calculator or any older CalcBatch application.

## Release procedure

1. Confirm the checked-out repository is CalcBatch v1.2 and the branch is `feature/linked-corrosion-v12`.
2. Push only the reviewed CalcBatch v1.2 commit to that existing branch. Do not alter Streamlit application settings, entry point, secrets, or URL.
3. Allow the existing public application at `https://iso24817calcbatch-prowrapv12.streamlit.app` to redeploy from that branch.
4. Download the template and verify this exact eight-sheet order: `Batch Information`, `Batch Input & Results`, `Individual Defects`, `Cost Calculation`, `Warnings`, `Summary`, `Instructions`, and hidden `Lists`.
5. Verify the main table/filter is `A1:AC151`, the Individual Defects table/filter is `A1:X151`, and both accept no more than 150 populated rows. Confirm a populated input at Excel row 152 is rejected on either input sheet.
6. Verify the only nine main outputs, in order, are `Wall Loss [%]`, `Required Structural Thickness [mm]`, `Installed Plies`, `Total Repair Length [mm]`, `Cloth Band Count`, `Procurement Axial Length [mm]`, `Fabric Area [m2]`, `Epoxy Mass [kg]`, and `Repair Zone Length [mm]`.
7. Upload the generated six-row acceptance workbook and confirm Actual, Independent, linked Manual, invalid Manual group, `Dent no-crack`, and `Dent w/crack` all appear in that order.
8. Confirm the three corrosion comparison rows retain a 1,000 mm repair-zone length. Reconcile their safe pressures as 7.571542406120033 MPa, 8.82257484144555 MPa, and 8.783461911867068 MPa; reconcile installed plies as 12, 7, and 7. Confirm Manual defect `D-02` governs.
9. Confirm the processed workbook records Batch Engine Version `1.2.0` and Pinned Source Revision `91b68d6`.
10. Confirm the Cost Calculation table has `A5:X...` coverage for the populated compact rows. `B3`, `E3`, `H3`, and `W6:W155` Quantity are highlighted and editable; Quantity accepts only a blank or non-negative number. `U`, `V`, and `X` hold only the controlled Cost, Price, and Total Amount formulas, with Total Amount equal to `Price x Quantity`.
11. Re-upload a processed workbook with non-negative B3/E3/H3 values and valid Quantity values. Confirm assumptions and Quantity persist while the trusted eight-sheet output, linked details, warnings, and exact controlled formulas are rebuilt.
12. Confirm the release guidance requires users to download and use the current 150/150 template. Older 500/2,000-row templates are not supported or guaranteed.

The application must continue to process one workbook at a time in session/temporary memory only. Do not configure persistent customer-workbook storage.
