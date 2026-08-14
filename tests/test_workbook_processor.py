from datetime import UTC, datetime
from io import BytesIO
import zipfile

import pytest
from openpyxl import load_workbook
from openpyxl.worksheet.formula import ArrayFormula, DataTableFormula

from batch_schema import INPUT_HEADERS, MAX_UPLOAD_BYTES, OUTPUT_HEADERS
from tests.helpers import valid_row_values, workbook_bytes_with_rows
from workbook_processor import (
    WorkbookProcessingError,
    inspect_workbook,
    process_workbook,
)


FIXED_TIME = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)


def _workbook(data: bytes):
    return load_workbook(BytesIO(data), data_only=False)


def _saved(workbook) -> bytes:
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def test_inspects_a_valid_template_and_previews_populated_rows():
    inspection = inspect_workbook(workbook_bytes_with_rows([valid_row_values()]))

    assert inspection.workbook_errors == ()
    assert inspection.batch_info is not None
    assert inspection.batch_info.customer == 'Batch Customer'
    assert inspection.populated_rows == 1
    assert inspection.valid_rows == 1
    assert inspection.invalid_rows == 0
    assert inspection.recognized_input_headers == INPUT_HEADERS
    assert inspection.missing_input_headers == ()
    assert inspection.unexpected_headers == ()
    assert inspection.preview == ({
        'Source Excel Row': 2,
        'Pipe OD [mm]': 457.2,
        'Mechanism': 'Corrosion',
        'Defect Location': 'External',
        'Calculation Status': 'OK',
        'Error Code': '',
        'Error Message': '',
    },)


def test_preview_uses_the_same_qualification_review_status_as_processing():
    source = workbook_bytes_with_rows([valid_row_values(**{
        'Operating Temperature [degC]': 150.0,
    })])

    inspection = inspect_workbook(source)
    processed = process_workbook(source, processed_at=FIXED_TIME)

    assert inspection.preview[0]['Calculation Status'] == 'REVIEW REQUIRED'
    assert processed.status_counts == {'REVIEW REQUIRED': 1}


def test_missing_batch_information_is_a_workbook_error():
    source = workbook_bytes_with_rows([valid_row_values()])
    workbook = _workbook(source)
    workbook['Batch Information']['B3'] = None

    inspection = inspect_workbook(_saved(workbook))

    assert inspection.batch_info is None
    assert [issue.code for issue in inspection.workbook_errors] == ['REQUIRED_VALUE']


@pytest.mark.parametrize('worksheet', [
    'Batch Information', 'Batch Input & Results', 'Summary', 'Instructions', 'Lists',
])
def test_missing_required_worksheet_is_a_workbook_error(worksheet):
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    del workbook[worksheet]

    inspection = inspect_workbook(_saved(workbook))

    assert [issue.code for issue in inspection.workbook_errors] == ['MISSING_WORKSHEET']


def test_extra_worksheet_is_a_workbook_error():
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook.create_sheet('Unexpected')

    inspection = inspect_workbook(_saved(workbook))

    assert [issue.code for issue in inspection.workbook_errors] == ['UNEXPECTED_WORKSHEET']


def test_missing_or_duplicate_headings_are_workbook_errors():
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    data = workbook['Batch Input & Results']
    data['A1'] = 'Outside Diameter [mm]'

    inspection = inspect_workbook(_saved(workbook))
    assert [issue.code for issue in inspection.workbook_errors] == ['INVALID_INPUT_HEADERS']

    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    data = workbook['Batch Input & Results']
    data.cell(1, 2).value = INPUT_HEADERS[0]

    inspection = inspect_workbook(_saved(workbook))
    assert [issue.code for issue in inspection.workbook_errors] == ['DUPLICATE_INPUT_HEADER']


def test_header_inspection_identifies_recognized_missing_and_unexpected_headings():
    """Catch a generic header failure that leaves users unable to correct their workbook."""
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    data = workbook['Batch Input & Results']
    data['A1'] = 'Outside Diameter [mm]'

    inspection = inspect_workbook(_saved(workbook))

    assert [issue.code for issue in inspection.workbook_errors] == ['INVALID_INPUT_HEADERS']
    assert inspection.recognized_input_headers == INPUT_HEADERS[1:]
    assert inspection.missing_input_headers == ('Pipe OD [mm]',)
    assert inspection.unexpected_headers == ('Outside Diameter [mm]',)


def test_oversized_and_macro_enabled_workbooks_are_rejected_before_processing():
    oversized = b'x' * (MAX_UPLOAD_BYTES + 1)
    assert [issue.code for issue in inspect_workbook(oversized).workbook_errors] == ['FILE_TOO_LARGE']

    source = workbook_bytes_with_rows([valid_row_values()])
    macro = BytesIO()
    with zipfile.ZipFile(BytesIO(source)) as input_zip, zipfile.ZipFile(macro, 'w') as output_zip:
        for entry in input_zip.infolist():
            output_zip.writestr(entry, input_zip.read(entry.filename))
        output_zip.writestr('xl/vbaProject.bin', b'not-a-real-macro')

    assert [issue.code for issue in inspect_workbook(macro.getvalue()).workbook_errors] == ['MACROS_NOT_ALLOWED']


def test_formula_inputs_and_corrupt_or_encrypted_data_are_rejected_safely():
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Batch Information']['B3'] = '=CONCAT("Batch", " Customer")'
    inspection = inspect_workbook(_saved(workbook))
    assert [issue.code for issue in inspection.workbook_errors] == ['FORMULA_NOT_ALLOWED']

    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Batch Input & Results']['A2'] = '=1+1'
    inspection = inspect_workbook(_saved(workbook))
    assert [issue.code for issue in inspection.workbook_errors] == ['FORMULA_NOT_ALLOWED']

    for data in (b'not an xlsx', _encrypted_zip_bytes()):
        inspection = inspect_workbook(data)
        assert [issue.code for issue in inspection.workbook_errors] == ['UNREADABLE_WORKBOOK']


@pytest.mark.parametrize(('worksheet_name', 'coordinate'), [
    ('Batch Input & Results', 'AY501'),
    ('Summary', 'B30'),
])
def test_formula_anywhere_in_the_controlled_workbook_is_rejected(worksheet_name, coordinate):
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook[worksheet_name][coordinate] = '=1+1'

    inspection = inspect_workbook(_saved(workbook))

    assert [issue.code for issue in inspection.workbook_errors] == ['FORMULA_NOT_ALLOWED']
    assert coordinate in inspection.workbook_errors[0].message


@pytest.mark.parametrize('formula', [
    ArrayFormula(ref='A2', text='=1+1'),
    DataTableFormula(ref='A2'),
])
def test_non_string_excel_formula_objects_are_rejected(formula):
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Batch Input & Results']['A2'].value = formula

    inspection = inspect_workbook(_saved(workbook))

    assert [issue.code for issue in inspection.workbook_errors] == ['FORMULA_NOT_ALLOWED']
    assert 'A2' in inspection.workbook_errors[0].message


def test_zip_valid_workbook_with_malformed_xml_is_rejected_safely():
    source = workbook_bytes_with_rows([valid_row_values()])
    malformed = BytesIO()
    with zipfile.ZipFile(BytesIO(source)) as input_zip, zipfile.ZipFile(malformed, 'w') as output_zip:
        for entry in input_zip.infolist():
            content = input_zip.read(entry.filename)
            if entry.filename == 'xl/workbook.xml':
                content = b'<workbook><sheets>'
            output_zip.writestr(entry, content)

    inspection = inspect_workbook(malformed.getvalue())

    assert [issue.code for issue in inspection.workbook_errors] == ['UNREADABLE_WORKBOOK']


def test_zip_expansion_bomb_is_rejected_before_openpyxl_parsing():
    source = workbook_bytes_with_rows([valid_row_values()])
    compressed = BytesIO()
    with zipfile.ZipFile(BytesIO(source)) as input_zip, zipfile.ZipFile(
        compressed, 'w', compression=zipfile.ZIP_DEFLATED,
    ) as output_zip:
        for entry in input_zip.infolist():
            output_zip.writestr(entry, input_zip.read(entry.filename))
        output_zip.writestr('xl/large-compressed-payload.bin', b'x' * (2 * 1024 * 1024))

    inspection = inspect_workbook(compressed.getvalue())

    assert [issue.code for issue in inspection.workbook_errors] == ['UNREADABLE_WORKBOOK']


def test_more_than_500_populated_rows_is_a_workbook_error():
    source = workbook_bytes_with_rows([valid_row_values() for _ in range(501)])

    inspection = inspect_workbook(source)

    assert inspection.populated_rows == 0
    assert [issue.code for issue in inspection.workbook_errors] == ['INPUT_ROW_OUT_OF_RANGE']


@pytest.mark.parametrize('excel_row', [502, 1000])
def test_populated_input_beyond_controlled_rows_is_a_workbook_error(excel_row):
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Batch Input & Results'].cell(excel_row, 1).value = 508.0

    inspection = inspect_workbook(_saved(workbook))

    assert [issue.code for issue in inspection.workbook_errors] == ['INPUT_ROW_OUT_OF_RANGE']
    assert f'A{excel_row}' in inspection.workbook_errors[0].message


def test_exactly_500_controlled_rows_remain_valid():
    inspection = inspect_workbook(
        workbook_bytes_with_rows([valid_row_values() for _ in range(500)])
    )

    assert inspection.populated_rows == 500
    assert inspection.workbook_errors == ()


def test_one_invalid_row_does_not_stop_valid_rows_and_inputs_are_preserved():
    source = workbook_bytes_with_rows([
        valid_row_values(),
        valid_row_values(**{'Remaining Wall [mm]': 12.0}),
        valid_row_values(),
    ])

    result = process_workbook(source, processed_at=FIXED_TIME)

    assert result.status_counts == {'OK': 2, 'INPUT ERROR': 1}
    assert result.populated_rows == 3
    processed = _workbook(result.workbook_bytes)
    data = processed['Batch Input & Results']
    assert [data.cell(3, column).value for column in range(1, len(INPUT_HEADERS) + 1)] == [
        _workbook(source)['Batch Input & Results'].cell(3, column).value
        for column in range(1, len(INPUT_HEADERS) + 1)
    ]
    assert data['T2'].value == 'OK'
    assert data['T3'].value == 'INPUT ERROR'
    assert data['U3'].value == 'OUT_OF_RANGE'
    assert 'Remaining Wall [mm]' in data['V3'].value
    assert data['T4'].value == 'OK'


def test_processed_workbook_updates_summary_and_uses_stable_diagnostic_json():
    source = workbook_bytes_with_rows([valid_row_values(**{
        'Mechanism': 'Leak',
        'Design Pressure [bar]': 100.0,
    })])

    result = process_workbook(source, processed_at=FIXED_TIME)
    workbook = _workbook(result.workbook_bytes)
    data = workbook['Batch Input & Results']
    summary = workbook['Summary']

    assert result.status_counts == {'NOT REPAIRABLE': 1}
    assert data['T2'].value == 'NOT REPAIRABLE'
    assert data['AY2'].value.startswith('{')
    assert data['AY2'].value == _stable_json(data['AY2'].value)
    assert summary['B3'].value == 'Batch Customer'
    assert summary['B4'].value == 'Batch Location'
    assert summary['B5'].value == 'B-001'
    assert summary['B8'].value == '2026-08-14T12:00:00Z'
    assert summary['B10'].value == 1
    assert summary['B15'].value == 1
    assert summary['B24'].value == '1.0.0'
    assert summary['B25'].value == '68e5409'


def test_processed_workbook_records_the_sanitized_uploaded_source_name():
    source = workbook_bytes_with_rows([valid_row_values()])

    result = process_workbook(
        source,
        processed_at=FIXED_TIME,
        source_name='../../Customer Batch.xlsx',
    )

    assert _workbook(result.workbook_bytes)['Summary']['B7'].value == 'Customer Batch.xlsx'


@pytest.mark.parametrize('source_name', [
    '=1+1.xlsx',
    '+1+1.xlsx',
    '-1+1.xlsx',
    '@danger.xlsx',
    '../../\x00  @unsafe.xlsx',
])
def test_processed_workbook_neutralizes_formula_like_source_names(source_name):
    result = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]),
        processed_at=FIXED_TIME,
        source_name=source_name,
    )

    source_cell = _workbook(result.workbook_bytes)['Summary']['B7']

    assert source_cell.data_type == 's'
    assert source_cell.value.startswith("'")
    assert '\x00' not in source_cell.value


def test_processing_regenerates_a_clean_workbook_after_a_row_is_cleared():
    first = process_workbook(workbook_bytes_with_rows([valid_row_values()]), processed_at=FIXED_TIME)
    edited = _workbook(first.workbook_bytes)
    data = edited['Batch Input & Results']
    for column in range(1, len(INPUT_HEADERS) + 1):
        data.cell(2, column).value = None

    second = process_workbook(_saved(edited), processed_at=FIXED_TIME)
    cleaned = _workbook(second.workbook_bytes)
    output_values = [
        cleaned['Batch Input & Results'].cell(2, column).value
        for column in range(
            len(INPUT_HEADERS) + 1,
            len(INPUT_HEADERS) + len(OUTPUT_HEADERS) + 1,
        )
    ]

    assert second.populated_rows == 0
    assert output_values == [None] * len(output_values)


def test_processing_restores_the_trusted_summary_and_instruction_content():
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Summary']['A27'] = 'TAMPERED DISCLAIMER'
    workbook['Instructions']['A3'] = 'TAMPERED INSTRUCTIONS'
    workbook['Lists'].sheet_state = 'visible'

    result = process_workbook(_saved(workbook), processed_at=FIXED_TIME)
    processed = _workbook(result.workbook_bytes)

    assert 'preliminary screening outputs' in processed['Summary']['A27'].value
    assert processed['Instructions']['A3'].value.startswith('1. Complete Customer')
    assert processed['Lists'].sheet_state == 'hidden'
    assert processed['Batch Input & Results'].protection.sheet is True


def test_process_rejects_workbook_level_errors():
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Batch Information']['B3'] = None
    with pytest.raises(WorkbookProcessingError, match='Customer'):
        process_workbook(_saved(workbook), processed_at=FIXED_TIME)


def test_unexpected_row_exception_is_logged_with_source_row_only(caplog, monkeypatch):
    import workbook_processor

    def explode(*_args, **_kwargs):
        raise RuntimeError('synthetic calculation failure')

    monkeypatch.setattr(workbook_processor, 'calculate_row', explode)
    with caplog.at_level('ERROR', logger='workbook_processor'):
        result = process_workbook(workbook_bytes_with_rows([valid_row_values()]), processed_at=FIXED_TIME)

    assert result.status_counts == {'SYSTEM ERROR': 1}
    assert 'source Excel row 2' in caplog.text
    assert 'Batch Customer' not in caplog.text
    assert '457.2' not in caplog.text


def _encrypted_zip_bytes() -> bytes:
    output = BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        entry = zipfile.ZipInfo('xl/workbook.xml')
        entry.flag_bits |= 0x1
        archive.writestr(entry, b'<workbook/>')
    return output.getvalue()


def _stable_json(value: str) -> str:
    import json

    return json.dumps(json.loads(value), sort_keys=True, separators=(',', ':'))
