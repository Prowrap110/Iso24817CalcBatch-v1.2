from datetime import UTC, datetime
from io import BytesIO

import pytest
from openpyxl import load_workbook

from batch_schema import (
    INPUT_HEADERS,
    LEGACY_INPUT_HEADERS,
    LEGACY_OUTPUT_HEADERS,
    OUTPUT_HEADERS,
)
from engine.corrosion_defects import ACTUAL_DEFECT_LENGTH
from tests.helpers import legacy_workbook_bytes_with_rows, valid_row_values
from workbook_processor import inspect_workbook, process_workbook


FIXED_TIME = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
CURRENT_SHEETS = [
    'Batch Information',
    'Batch Input & Results',
    'Individual Defects',
    'Cost Calculation',
    'Warnings',
    'Summary',
    'Instructions',
    'Lists',
]


def _saved(workbook) -> bytes:
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _legacy_source(sheet_count: int) -> bytes:
    """Freeze the former v1.1 header contract in each supported sheet layout."""
    workbook = load_workbook(BytesIO(legacy_workbook_bytes_with_rows(
        [valid_row_values()], sheet_count=sheet_count,
    )))
    main = workbook['Batch Input & Results']
    assert tuple(cell.value for cell in main[1]) == (
        LEGACY_INPUT_HEADERS + LEGACY_OUTPUT_HEADERS
    )
    installed_plies_column = (
        len(LEGACY_INPUT_HEADERS) + LEGACY_OUTPUT_HEADERS.index('Installed Plies') + 1
    )
    main.cell(2, installed_plies_column).value = 999
    return _saved(workbook)


@pytest.mark.parametrize('sheet_count', [5, 6, 7])
def test_supported_legacy_workbooks_upgrade_to_current_contract(sheet_count):
    """Catches stranding any controlled pre-v1.2 workbook generation."""
    source = _legacy_source(sheet_count)

    inspection = inspect_workbook(source)
    processed = process_workbook(source, FIXED_TIME, f'legacy-{sheet_count}.xlsx')
    workbook = load_workbook(BytesIO(processed.workbook_bytes), data_only=False)
    main = workbook['Batch Input & Results']
    headings = tuple(cell.value for cell in main[1])

    assert inspection.workbook_errors == ()
    assert workbook.sheetnames == CURRENT_SHEETS
    assert headings == INPUT_HEADERS + OUTPUT_HEADERS
    assert main.cell(2, headings.index('Defect Length Basis') + 1).value == (
        ACTUAL_DEFECT_LENGTH
    )
    assert main.cell(2, headings.index('Repair Group ID') + 1).value is None
    assert main.cell(2, headings.index('Installed Plies') + 1).value == 3
    detail = workbook['Individual Defects']
    assert all(cell.value is None for cell in detail[2])


def test_legacy_upgrade_sets_actual_basis_only_for_eligible_external_corrosion():
    """Catches adding a corrosion-only choice to unrelated legacy repair rows."""
    workbook = load_workbook(BytesIO(_legacy_source(7)))
    main = workbook['Batch Input & Results']
    headings = tuple(cell.value for cell in main[1])
    main.cell(2, headings.index('Mechanism') + 1).value = 'Leak'

    processed = process_workbook(_saved(workbook), FIXED_TIME, 'legacy-leak.xlsx')
    rebuilt = load_workbook(BytesIO(processed.workbook_bytes), data_only=False)
    rebuilt_main = rebuilt['Batch Input & Results']
    rebuilt_headings = tuple(cell.value for cell in rebuilt_main[1])

    assert rebuilt_main.cell(
        2, rebuilt_headings.index('Defect Length Basis') + 1,
    ).value is None
