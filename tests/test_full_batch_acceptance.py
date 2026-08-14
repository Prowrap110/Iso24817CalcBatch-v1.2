from datetime import UTC, datetime
from io import BytesIO

from openpyxl import load_workbook

import batch_adapter
from batch_schema import INPUT_HEADERS, OUTPUT_HEADERS
from workbook_processor import process_workbook


FIXED_TIME = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
COMMON_INFO = {
    'customer': 'Acceptance Customer',
    'location': 'Acceptance Location',
    'report_no': 'ACCEPT-001',
}


def test_acceptance_workbook_exercises_all_statuses_and_uses_common_batch_info(
    tmp_path, monkeypatch,
):
    """Catch a generator that omits a required status case or bypasses batch fields."""
    from scripts.create_acceptance_workbook import create_acceptance_workbook

    source_path = tmp_path / 'acceptance-input.xlsx'
    create_acceptance_workbook(source_path)
    source = source_path.read_bytes()
    input_book = load_workbook(BytesIO(source), data_only=False)
    input_sheet = input_book['Batch Input & Results']

    assert tuple(cell.value for cell in input_sheet[1]) == INPUT_HEADERS + OUTPUT_HEADERS
    assert {'Customer', 'Project Location', 'Report No'}.isdisjoint(INPUT_HEADERS)
    assert [input_sheet.cell(row, 1).value for row in range(2, 8)] == [
        457.2, 457.2, 457.2, 457.2, 457.2, 457.2,
    ]
    assert input_sheet.cell(7, INPUT_HEADERS.index('Prowrap CF Cloth Width [mm]') + 1).value == 500.0

    calls = []
    original_calculate_repair = batch_adapter.calculate_repair

    def capture_common_info(**kwargs):
        calls.append({key: kwargs[key] for key in COMMON_INFO})
        return original_calculate_repair(**kwargs)

    monkeypatch.setattr(batch_adapter, 'calculate_repair', capture_common_info)
    processed = process_workbook(source, processed_at=FIXED_TIME)
    result_book = load_workbook(BytesIO(processed.workbook_bytes), data_only=False)
    result_sheet = result_book['Batch Input & Results']
    output_column = {
        header: index
        for index, header in enumerate(INPUT_HEADERS + OUTPUT_HEADERS, start=1)
    }
    statuses = [
        result_sheet.cell(row, output_column['Calculation Status']).value
        for row in range(2, 8)
    ]

    assert statuses == [
        'OK', 'REVIEW REQUIRED', 'NOT REPAIRABLE',
        'INPUT ERROR', 'REVIEW REQUIRED', 'OK',
    ]
    # Preview and processing use the same engine path so the user sees the
    # final row status before generating the download.
    assert calls == [COMMON_INFO] * 10
    assert result_book['Batch Information']['B3'].value == 'Acceptance Customer'
    assert result_book['Batch Information']['B4'].value == 'Acceptance Location'
    assert result_book['Batch Information']['B5'].value == 'ACCEPT-001'
    assert result_book.sheetnames == [
        'Batch Information', 'Batch Input & Results', 'Warnings',
        'Summary', 'Instructions', 'Lists',
    ]

    warning_values = [
        result_sheet.cell(row, output_column['Compliance Warnings']).value
        for row in range(2, 8)
    ]
    assert warning_values[1] == 'W018'
    assert warning_values[5] is None
    assert all(
        value is None or all(code.startswith('W') and len(code) == 4
                             for code in value.split(', '))
        for value in warning_values
    )
    warning_sheet = result_book['Warnings']
    warning_rows = {
        warning_sheet.cell(row, 1).value: warning_sheet.cell(row, 3).value
        for row in range(4, warning_sheet.max_row + 1)
    }
    assert warning_rows['W003'] == '4, 6'
    assert warning_rows['W018'] == '3'

    formulas = [
        f'{worksheet.title}!{cell.coordinate}'
        for worksheet in result_book.worksheets
        for row in worksheet.iter_rows()
        for cell in row
        if cell.data_type == 'f'
    ]
    assert formulas == []
