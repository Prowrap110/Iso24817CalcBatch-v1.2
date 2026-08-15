# PROWRAP Batch OPC Security and Release Completion Design

**Date:** 2026-08-14
**Status:** Superseded by `2026-08-14-trusted-workbook-release-design.md` at the user's direction
**Repository:** `Prowrap110/Iso24817CalcBatch` only

## 1. Purpose

Complete the blocked Cost Calculation release by replacing the ad-hoc worksheet-part selector with a standards-compliant Open Packaging Conventions (OPC) content-type resolver, correcting upload-result identity, and repeating the complete workbook and live-deployment verification.

The existing PROWRAP v1.1 repository and Streamlit application remain isolated and must not be changed by this work.

## 2. Scope

### In scope

- Resolve the effective content type of every OPC package part using `[Content_Types].xml`.
- Select all real SpreadsheetML worksheet parts independently of ZIP path, filename case, or suffix.
- Enforce the existing 100,000-cell aggregate ceiling before openpyxl loads a workbook.
- Reject ambiguous or malformed packages deterministically and safely.
- Include both uploaded bytes and uploaded filename in Streamlit result identity.
- Correct remaining formula-upload and commercial-input wording.
- Constrain openpyxl to the tested `3.1.x` family because controlled validation deliberately isolates one private openpyxl cell collection.
- Regenerate, inspect, render, and approve the acceptance workbook.
- Publish only the batch repository and verify the batch Streamlit URL live.

### Out of scope

- Engineering formula changes.
- Changes to ISO 24817 classifications, warning codes, Tg, cloth behavior, or commercial formulas.
- Changes to the existing v1.1 repository, app, URL, or deployment.
- Supporting macros, encrypted workbooks, arbitrary workbook layouts, or uncontrolled formulas.

## 3. OPC Resolver Architecture

Introduce an isolated package-policy module named `opc_package.py`. `workbook_processor.py` calls this module before any openpyxl operation. Its internal contract is:

```text
resolve effective package content types
    input: bounded ZIP entry metadata and parsed [Content_Types].xml
    output: exact archive entries whose effective content type is worksheet
    failure: deterministic unreadable-workbook validation issue
```

The resolver performs no openpyxl operations and does not materialize worksheet cells.

### 3.1 Canonical entry index

Build an ASCII-case-insensitive index of archive part names after removing a single package-root slash for comparison. Preserve each entry's exact archive spelling for `ZipFile.open`.

If two entries collapse to the same ASCII-case-insensitive part name, reject the package as ambiguous before openpyxl. Do not guess which duplicate governs.

Directory entries are excluded from part resolution.

### 3.2 Content-type declarations

Parse `[Content_Types].xml` with bounded streaming XML processing.

- Match `Override PartName` against archive part names using ASCII-case-insensitive comparison.
- Normalize a leading package-root slash for comparison.
- Match `Default Extension` ASCII-case-insensitively.
- Derive a part extension from the substring after the rightmost dot in its complete part name. A name such as `xl/custom/.data` therefore has extension `data`.
- Apply a matching part-specific `Override` before any matching `Default`.
- A non-worksheet Override suppresses a worksheet Default for that part.
- A worksheet Override selects that part regardless of its path or filename suffix.
- Missing, duplicate, malformed, encrypted, or ambiguous content-type metadata produces the existing safe unreadable-workbook class of error.

The controlled worksheet media type is:

```text
application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml
```

Content-type token comparison is exact after surrounding whitespace is rejected; the implementation must not broaden arbitrary types into worksheets.

### 3.3 Worksheet XML verification and counting

Only entries whose effective content type is worksheet enter the XML cell scanner.

For each selected part:

- Require a SpreadsheetML `worksheet` root in either the Transitional or ISO Strict main namespace.
- Count only `c` elements in the same recognized SpreadsheetML namespace as the worksheet root.
- Ignore foreign-namespace extension elements.
- Clear parsed elements as they are streamed.
- Aggregate cells across every selected worksheet part.
- Reject at 100,001 cells; accept exactly 100,000 cells.
- Complete this validation before the first openpyxl call.

Malformed declared worksheets, missing selected parts, or mismatched worksheet roots produce a deterministic unreadable-workbook error. Unrelated binary, chart, drawing, and custom-data parts are not XML-parsed as worksheets.

## 4. Upload and Result Identity

The processed workbook depends on both uploaded content and the source filename recorded in `Summary!B7`. Streamlit session identity therefore uses a deterministic digest over:

```text
uploaded XLSX bytes + unambiguous separator + exact uploaded filename bytes
```

Uploading identical workbook bytes under a different filename must:

1. clear the prior processed download and status display;
2. require Calculate Batch again;
3. write the new sanitized filename to `Summary!B7`.

Changing only the file bytes continues to clear prior results as before.

## 5. User Guidance and Dependency Boundary

- The upload help states that macros and uncontrolled formulas are rejected; exact generated Cost and Price formulas are accepted when re-uploading a processed workbook.
- Workbook Instructions state that commercial cells `B3`, `E3`, and `H3` may be blank or may retain previously entered values.
- Design Life, Installed Plies, and Cloth Band Count use integer display formats without altering stored numeric values.
- `requirements.txt` constrains openpyxl to `>=3.1,<3.2`; the Streamlit and Python runtime boundaries remain otherwise unchanged.

## 6. Error Handling and Privacy

- The app continues to show only plain-language workbook correction messages.
- Package-parser details, ZIP paths, stack traces, and customer inputs are not exposed in the UI.
- Internal unexpected-calculation diagnostics continue to log exception type, source row, and sanitized frame locations without exception text or customer/input values.
- All parsing limits execute before openpyxl cell materialization.

## 7. Test Design

### 7.1 OPC conformance matrix

Tests must prove:

- exact-case and case-variant Override matching;
- worksheet Overrides at `.xml`, `.data`, dot-prefixed, nested, and mixed-case paths;
- Default extension mapping using the rightmost dot;
- Override precedence over Default in both worksheet-to-binary and binary-to-worksheet directions;
- ASCII-case-insensitive Default extensions;
- rejection of case-insensitive duplicate archive part names;
- Transitional and ISO Strict worksheet namespaces;
- foreign-root and foreign-extension cells do not count;
- unrelated binary/custom parts remain unparsed and accepted;
- malformed manifest and malformed declared worksheet errors remain deterministic;
- exactly 100,000 worksheet cells pass and 100,001 fail before openpyxl;
- normal, sparse, and maximum controlled 500-row workbooks pass.

Each over-limit test monkeypatches the openpyxl load boundary so reaching it fails the test.

### 7.2 Streamlit identity

App tests upload identical bytes under two different filenames and prove the old result disappears. After recalculation, the downloaded workbook must contain the second sanitized filename in `Summary!B7`.

### 7.3 Regression and acceptance

- Run the complete automated suite with zero failures.
- Rebuild the six-row Cost Calculation acceptance workbook with commercial inputs `50.00`, `20.00`, and `1.50`.
- Confirm seven-sheet order, protected/editable input behavior, matching table/filter ranges, 120/120 source mapping, exact controlled formulas, correct recalculated Cost/Price values, warning-free 500 mm behavior, and hidden Lists.
- Render and visually inspect all sheets, with a full-width Cost Calculation render.
- Run a final whole-branch security and code review with no Critical or Important findings.

## 8. Release Sequence

1. Implement and review the OPC resolver test-first.
2. Implement and review filename-sensitive result identity test-first.
3. Apply guidance, dependency, and low-risk number-format corrections.
4. Run the complete suite and rebuild the acceptance workbook.
5. Perform one independent whole-branch release review.
6. Push the feature branch to `Prowrap110/Iso24817CalcBatch` and merge through GitHub.
7. Confirm the batch Streamlit deployment uses the merged batch repository.
8. Live-test template download, representative upload, calculation, processed download, re-upload, Cost Calculation formulas, and filename traceability.
9. Verify the existing v1.1 URL remains available and unchanged.

Publication is prohibited if any Critical or Important finding remains open or if the final acceptance workbook was generated before the last workbook-format or processor change.
