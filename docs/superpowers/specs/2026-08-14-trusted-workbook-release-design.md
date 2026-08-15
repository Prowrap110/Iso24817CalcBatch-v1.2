# PROWRAP Batch Trusted-Workbook Release Design

**Date:** 2026-08-14
**Status:** Approved by user
**Repository:** `Prowrap110/Iso24817CalcBatch` only

## Purpose

Finish and publish the Cost Calculation release for the user's own controlled Excel workbooks. The application is not required to accept or analyze deliberately unusual OPC/OOXML package constructions.

## Supported workflow

- Download the controlled batch template from the batch Streamlit app.
- Complete it in Microsoft Excel or re-upload a workbook previously processed by the batch app.
- Process no more than 500 populated defect rows.
- Download the seven-sheet result with the separate Cost Calculation and Warnings sheets.
- Enter or change CF cost, epoxy cost, and price multiplier in the processed workbook.

## Practical safeguards retained

- Maximum upload size: 10 MB.
- Existing ZIP expansion, entry-count, and compression-ratio limits.
- Exact controlled sheet order and headings.
- Macro/encryption rejection.
- Uncontrolled-formula rejection; exact generated Cost and Price formulas allowed on re-upload.
- 500-row controlled input boundary.
- Fresh-template rebuild so uploaded result cells, styles, tables, and formulas are not trusted.
- Plain-language errors instruct the user to download a fresh template when the workbook is unreadable or uncontrolled.

The application does not promise compatibility with manually restructured ZIP packages, custom OPC part mappings, intentionally malformed relationship metadata, or hostile files.

## Remaining release work

1. Remove the unintegrated experimental `opc_package.py` work and its test-only fixtures.
2. Bind Streamlit result identity to both workbook bytes and uploaded filename so renaming a source clears stale results and updates `Summary!B7`.
3. Correct formula-upload help, retained-commercial-value wording, and integer display formats.
4. Keep openpyxl within the tested `3.1.x` family.
5. Run the complete suite and regenerate the final acceptance workbook after the last code change.
6. Review the user workflow and calculation output, not exotic package formats.
7. Publish only the batch repository and verify the live batch Streamlit URL.

## Isolation

The existing v1.1 repository, application, URL, and deployment remain unchanged.
