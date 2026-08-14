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
    assert [input_sheet.cell(row, 1).value for row in range(2, 7)] == [
        457.2, 457.2, 457.2, 457.2, 457.2,
    ]

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
        for row in range(2, 7)
    ]

    assert statuses == [
        'OK', 'REVIEW REQUIRED', 'NOT REPAIRABLE',
        'INPUT ERROR', 'REVIEW REQUIRED',
    ]
    # Preview and processing use the same engine path so the user sees the
    # final row status before generating the download.
    assert calls == [COMMON_INFO] * 8
    assert result_book['Batch Information']['B3'].value == 'Acceptance Customer'
    assert result_book['Batch Information']['B4'].value == 'Acceptance Location'
    assert result_book['Batch Information']['B5'].value == 'ACCEPT-001'
