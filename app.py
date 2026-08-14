"""User interface for the standalone PROWRAP batch workbook calculator."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib

import streamlit as st

from workbook_processor import WorkbookProcessingError, inspect_workbook, process_workbook
from workbook_template import create_template_workbook


_TEMPLATE_FILENAME = 'PROWRAP_Batch_Template.xlsx'
_PROCESSED_BYTES_KEY = 'processed_workbook_bytes'
_PROCESSED_HASH_KEY = 'processed_file_hash'
_PROCESSED_NAME_KEY = 'processed_workbook_name'
_SOURCE_HASH_KEY = 'source_file_hash'


def _clear_processed_result() -> None:
    for key in (_PROCESSED_BYTES_KEY, _PROCESSED_HASH_KEY, _PROCESSED_NAME_KEY):
        st.session_state.pop(key, None)


def _output_filename(processed_at: datetime) -> str:
    return f"PROWRAP_Batch_Results_{processed_at.strftime('%Y%m%d_%H%M%S')}.xlsx"


def _show_workbook_errors(issues) -> None:
    st.error('This workbook needs correction before it can be calculated.')
    for issue in issues:
        st.write(f'• {issue.message}')


def _show_header_summary(inspection) -> None:
    """Show what the uploaded workbook contains without accepting altered headings."""
    recognized = ', '.join(inspection.recognized_input_headers) or 'None'
    missing = ', '.join(inspection.missing_input_headers) or 'None'
    unexpected = ', '.join(inspection.unexpected_headers) or 'None'
    st.write(
        f'Recognized input columns ({len(inspection.recognized_input_headers)}): '
        f'{recognized}'
    )
    st.write(f'Missing input columns: {missing}')
    st.write(f'Unexpected headings: {unexpected}')


def _show_status_counts(status_counts: dict[str, int]) -> None:
    ordered_statuses = (
        'OK',
        'REVIEW REQUIRED',
        'NOT REPAIRABLE',
        'INPUT ERROR',
        'SYSTEM ERROR',
    )
    columns = st.columns(len(ordered_statuses))
    for column, status in zip(columns, ordered_statuses):
        column.metric(status, status_counts.get(status, 0))


def main() -> None:
    st.set_page_config(page_title='PROWRAP Batch Repair Calculator', layout='wide')
    st.title('PROWRAP Batch Repair Calculator')
    st.write(
        'Calculate up to 500 independent pipeline defects from one controlled Excel workbook. '
        'Customer, Project Location, and Report No are entered once for the whole batch.'
    )
    st.info(
        'This is a separate batch calculator. It does not change, replace, or connect to '
        'the existing PROWRAP v1.1 calculator.'
    )

    st.subheader('1. Download template')
    st.download_button(
        'Download Excel Template',
        data=create_template_workbook(),
        file_name=_TEMPLATE_FILENAME,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        help='Use this controlled workbook so the batch calculator can recognize every input.',
    )
    st.caption(
        'Use millimetres, MPa, bar, degC, years, m2, and kg as labelled. '
        'Supported mechanisms: Corrosion, Dent, Leak, and Crack.'
    )

    st.subheader('2. Upload workbook')
    uploaded = st.file_uploader(
        'Upload the completed Excel template',
        type=['xlsx'],
        help='Upload one controlled .xlsx workbook, up to 10 MB. Macros and formulas are not accepted.',
    )

    inspection = None
    source_data = None
    source_hash = None
    if uploaded is not None:
        source_data = uploaded.getvalue()
        source_hash = hashlib.sha256(source_data).hexdigest()
        if st.session_state.get(_SOURCE_HASH_KEY) != source_hash:
            st.session_state[_SOURCE_HASH_KEY] = source_hash
            _clear_processed_result()

        st.caption(f'Uploaded file: {uploaded.name}')
        try:
            inspection = inspect_workbook(source_data)
        except Exception:
            st.error('The workbook could not be read safely. Please download a fresh template and try again.')
        else:
            _show_header_summary(inspection)
            if inspection.workbook_errors:
                _show_workbook_errors(inspection.workbook_errors)
            else:
                st.success(
                    f'Recognized {inspection.populated_rows} populated row(s): '
                    f'{inspection.valid_rows} valid and {inspection.invalid_rows} needing correction.'
                )

    st.subheader('3. Review preview')
    if inspection is None:
        st.write('Upload a workbook to see the first 20 populated rows and their validation status.')
    elif not inspection.workbook_errors:
        if inspection.preview:
            st.dataframe(list(inspection.preview), hide_index=True, width='stretch')
        else:
            st.warning('No populated defect rows were found. A processed workbook can still be created, but it will contain no row results.')

    can_calculate = (
        source_data is not None
        and inspection is not None
        and not inspection.workbook_errors
    )
    calculate = st.button(
        'Calculate Batch',
        type='primary',
        disabled=not can_calculate,
        help='Calculation is available when the controlled workbook structure is valid. '
        'Rows with input errors remain individually reported.',
    )
    if calculate and source_data is not None:
        try:
            processed_at = datetime.now(UTC)
            processed = process_workbook(
                source_data,
                processed_at=processed_at,
                source_name=uploaded.name,
            )
        except WorkbookProcessingError as error:
            _show_workbook_errors(error.issues)
        except Exception:
            st.error('The batch could not be calculated safely. Please try a fresh template or contact PROTAP.')
        else:
            st.session_state[_PROCESSED_BYTES_KEY] = processed.workbook_bytes
            st.session_state[_PROCESSED_HASH_KEY] = source_hash
            st.session_state[_PROCESSED_NAME_KEY] = _output_filename(processed_at)

    processed_bytes = st.session_state.get(_PROCESSED_BYTES_KEY)
    if processed_bytes and st.session_state.get(_PROCESSED_HASH_KEY) == source_hash:
        st.subheader('4. Calculate and download')
        st.success('Batch calculation is complete. Review the status counts and download the processed workbook.')
        if inspection is not None and not inspection.workbook_errors:
            # The workbook itself is the source of truth for detailed row outputs.
            # Reprocessing is deliberately avoided; the result is stored only for this session.
            from openpyxl import load_workbook
            from io import BytesIO

            processed_workbook = load_workbook(BytesIO(processed_bytes), read_only=True, data_only=True)
            summary = processed_workbook['Summary']
            _show_status_counts({
                'OK': summary['B13'].value or 0,
                'REVIEW REQUIRED': summary['B14'].value or 0,
                'NOT REPAIRABLE': summary['B15'].value or 0,
                'INPUT ERROR': summary['B16'].value or 0,
                'SYSTEM ERROR': summary['B17'].value or 0,
            })
            processed_workbook.close()
        st.download_button(
            'Download Processed Workbook',
            data=processed_bytes,
            file_name=st.session_state[_PROCESSED_NAME_KEY],
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type='primary',
        )


if __name__ == '__main__':
    main()
