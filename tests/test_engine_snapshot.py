from datetime import UTC, datetime
from io import BytesIO

from openpyxl import load_workbook

from tests.helpers import valid_row_values, workbook_bytes_with_rows
from workbook_processor import process_workbook


def test_pinned_engine_revision_is_emitted_in_processed_workbook():
    from engine.prowrap_calculations import calculate_repair

    assert callable(calculate_repair)
    processed = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]),
        datetime(2026, 8, 15, tzinfo=UTC),
        'engine-revision.xlsx',
    )
    workbook = load_workbook(BytesIO(processed.workbook_bytes), data_only=False)

    assert workbook['Summary']['B24'].value == '1.2.0'
    assert workbook['Summary']['B25'].value == '746f3b3'
