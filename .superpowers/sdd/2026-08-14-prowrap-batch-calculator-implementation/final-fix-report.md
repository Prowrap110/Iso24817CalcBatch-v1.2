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
- ZIP metadata is checked before `openpyxl` parsing: entry count, individual
  and total expanded bytes, and compression ratio limits reject unsafe input.
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
  the Streamlit page.

## Regression coverage

- Reprocessed/cleared row has no stale outputs.
- Array formulas, data-table formulas, zip expansion, extra sheets, and
  tampered trusted-sheet content are handled safely.
- Zero-pressure optional check, qualification-temperature review status,
  preview/final consistency, source-name sanitization, and privacy-preserving
  exception logging are covered.

## Verification

- `python3 -m pytest tests/engine tests/test_app_smoke.py tests/test_batch_status.py tests/test_batch_validation.py tests/test_full_batch_acceptance.py -q` — 80 passed.
- `python3 -m pytest tests/test_app_smoke.py tests/test_full_batch_acceptance.py tests/test_batch_adapter.py tests/test_workbook_template.py -q` — 17 passed.
- `python3 -m pytest tests/test_workbook_processor.py -k 'not (unexpected_row_exception or processing_regenerates or processing_restores or process_rejects or processed_workbook or one_invalid)' -q` — 20 passed.
- `python3 -m pytest tests/test_workbook_processor.py -k 'unexpected_row_exception or processing_regenerates or processing_restores or process_rejects or processed_workbook or one_invalid' -q` — 7 passed.
- `python3 -m pytest tests/test_batch_schema.py tests/test_engine_batch_hardening.py tests/test_engine_snapshot.py -q` — 9 passed.

These non-overlapping checks cover the complete 128-test suite (the second
command also rechecks the Streamlit and acceptance paths after wiring the
uploaded source filename).
