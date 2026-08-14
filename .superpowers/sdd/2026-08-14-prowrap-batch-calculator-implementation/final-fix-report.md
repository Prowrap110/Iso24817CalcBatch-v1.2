# Final fix wave report

## Safety and integrity corrections

- Processed workbooks are generated from a fresh trusted template.  Only the
  three common values and defect input cells are copied from the validated
  upload, so clearing a prior result row cannot retain stale calculated values.
- The upload must have the exact controlled worksheet set and order.  Extra
  worksheets are rejected; regenerated workbooks restore the trusted Summary,
  Instructions, hidden Lists worksheet, protection, and formatting.
- Formula rejection checks both formula data types and string formula markers,
  including Excel array and data-table formulas.
- Any populated input cell outside controlled rows 2 through 501 is rejected
  before processing, so no defect can be silently omitted from regenerated output.
- ZIP metadata is checked before `openpyxl` parsing: entry count, individual
  and total expanded bytes, and compression ratio limits reject unsafe input.
- Workbook cell validation inspects only cells actually loaded by openpyxl,
  rather than expanding the worksheet's declared dimension; sparse far-away
  cells therefore cannot exhaust processing resources.
- Defect-row collection is separately capped to the controlled input rectangle
  (rows 2 through 501 and input columns), so harmless far-away output cells
  cannot cause a dense `max_row` traversal.
- Unexpected row exceptions are logged with `logger.exception` and only the
  source Excel row number.  User/common input values are not logged.

## Engineering-status corrections

- A requested Type A/Class 3 check at zero design pressure is skipped as
  non-controlling and returned as `REVIEW REQUIRED`, with a clear warning.
- The batch adapter requests numeric results for temperatures above the
  qualified limit, then marks the result `REVIEW REQUIRED`; the baseline
  engine default remains strict for non-batch callers.
- The preview uses the same calculation classification as processing, so its
  displayed status agrees with the downloaded workbook.

## Usability corrections

- The table freezes the header plus the Pipe OD column at `B2`.
- The Summary records a sanitized uploaded source filename when supplied by
  the Streamlit page, neutralizing leading Excel formula prefixes as literal text.

## Regression coverage

- Reprocessed/cleared row has no stale outputs.
- Array formulas, data-table formulas, zip expansion, extra sheets, and
  tampered trusted-sheet content are handled safely.
- Zero-pressure optional check, qualification-temperature review status,
  preview/final consistency, source-name sanitization, and privacy-preserving
  exception logging are covered.
- Row 502/far-row rejection, an exact 500-row valid batch, and all leading
  formula-style filename prefixes are covered.
- Sparse `Summary!XFD1048576` formulas and far input cells are rejected without
  dense iteration; formula rejection deterministically takes priority.
- A far output cell at row 1,048,576 cannot expand defect-row collection;
  500 controlled rows still work and row 502 inputs still reject.

## Verification

- `python3 -m pytest tests/engine tests/test_app_smoke.py tests/test_batch_status.py tests/test_batch_validation.py tests/test_full_batch_acceptance.py -q` — 80 passed.
- `python3 -m pytest tests/test_workbook_processor.py -k 'not (one_invalid or processed_workbook or processing_regenerates or processing_restores or process_rejects or unexpected_row_exception)' -q` — 27 passed.
- `python3 -m pytest tests/test_workbook_processor.py -k 'one_invalid or processed_workbook or processing_regenerates or processing_restores or process_rejects or unexpected_row_exception' -q` — 12 passed.
- `python3 -m pytest tests/test_batch_adapter.py tests/test_workbook_template.py tests/test_batch_schema.py tests/test_engine_batch_hardening.py tests/test_engine_snapshot.py -q` — 21 passed.

These non-overlapping checks cover the complete 140-test suite.
