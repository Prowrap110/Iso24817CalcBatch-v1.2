"""End-to-end release acceptance for the separate linked-corrosion batch app."""

from datetime import UTC, datetime
from io import BytesIO

from openpyxl import load_workbook
import pytest

from batch_schema import (
    DETAIL_INPUT_HEADERS,
    DETAIL_OUTPUT_HEADERS,
    INPUT_HEADERS,
    OUTPUT_HEADERS,
)
from cost_calculation import COST_SOURCE_HEADERS
from tests.helpers import legacy_workbook_bytes_with_rows, valid_row_values
from workbook_processor import process_workbook


FIXED_TIME = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
EXPECTED_SHEETS = [
    'Batch Information', 'Batch Input & Results', 'Individual Defects',
    'Cost Calculation', 'Warnings', 'Summary', 'Instructions', 'Lists',
]


def _columns(headers):
    return {header: index for index, header in enumerate(headers, start=1)}


def _formula_cells(workbook):
    return [
        (f'{worksheet.title}!{cell.coordinate}', cell.value)
        for worksheet in workbook.worksheets
        for row in worksheet.iter_rows()
        for cell in row
        if cell.data_type == 'f'
    ]


def test_linked_corrosion_release_acceptance_workbook(tmp_path):
    """Exercise all v1.2 modes through the production template and processor."""
    from scripts.create_acceptance_workbook import create_acceptance_workbook

    source_path = tmp_path / 'acceptance-input.xlsx'
    create_acceptance_workbook(source_path)
    input_book = load_workbook(source_path, data_only=False)
    main_input = input_book['Batch Input & Results']
    detail_input = input_book['Individual Defects']
    main_columns = _columns(INPUT_HEADERS + OUTPUT_HEADERS)
    detail_columns = _columns(DETAIL_INPUT_HEADERS + DETAIL_OUTPUT_HEADERS)

    assert input_book.sheetnames == EXPECTED_SHEETS
    assert input_book['Batch Information']['A1'].value == 'PROWRAP Batch Repair Calculator'
    assert input_book['Batch Information']['A1'].value != 'PROWRAP v1.1 Calculator'
    assert [input_book['Batch Information'].cell(row, 2).value for row in (3, 4, 5)] == [
        'Acceptance Customer', 'Acceptance Location', 'ACCEPT-001',
    ]
    expected_rows = (
        ('Actual defect length', None, 'Corrosion', 'External'),
        ('Independent defects', None, 'Corrosion', 'External'),
        ('Enter manually', 'R-001', 'Corrosion', 'External'),
        ('Enter manually', 'R-BAD', 'Corrosion', 'External'),
        (None, None, 'Dent no-crack', 'External'),
        (None, None, 'Dent w/crack', 'External'),
    )
    assert [
        tuple(main_input.cell(row, main_columns[header]).value for header in (
            'Defect Length Basis', 'Repair Group ID', 'Mechanism', 'Defect Location',
        )) for row in range(2, 8)
    ] == list(expected_rows)
    for row in range(2, 5):
        assert [main_input.cell(row, main_columns[header]).value for header in (
            'Pipe OD [mm]', 'Nominal Wall [mm]', 'Design Pressure [bar]',
            'Defect Length [mm]', 'Prowrap CF Cloth Width [mm]',
        )] == [1016.0, 12.0, 104.9, 1000.0, 500.0]
    assert main_input.cell(4, main_columns['Remaining Wall [mm]']).value is None
    assert [
        tuple(detail_input.cell(row, detail_columns[header]).value for header in DETAIL_INPUT_HEADERS)
        for row in range(2, 5)
    ] == [
        ('R-001', 'D-01', 10.0, 9.652, 'Yes'),
        ('R-001', 'D-02', 35.0, 10.0, 'Yes'),
        ('R-BAD', 'D-BAD', 10.0, 9.652, 'No'),
    ]

    processed = process_workbook(source_path.read_bytes(), processed_at=FIXED_TIME)
    result_book = load_workbook(BytesIO(processed.workbook_bytes), data_only=False)
    main = result_book['Batch Input & Results']
    detail = result_book['Individual Defects']

    assert result_book.sheetnames == EXPECTED_SHEETS
    assert result_book['Lists'].sheet_state == 'hidden'
    assert main.protection.sheet is True
    assert detail.protection.sheet is True
    assert main.tables['BatchRows'].ref == main.tables['BatchRows'].autoFilter.ref
    assert detail.tables['IndividualDefects'].ref == detail.tables['IndividualDefects'].autoFilter.ref
    assert result_book['Summary']['B24'].value == '1.2.0'
    assert result_book['Summary']['B25'].value == '91b68d6'
    assert [main.cell(row, main_columns['Calculation Status']).value for row in range(2, 8)] == [
        'REVIEW REQUIRED', 'REVIEW REQUIRED', 'REVIEW REQUIRED', 'INPUT ERROR', 'OK', 'OK',
    ]
    assert [main.cell(row, main_columns['Effective Pipe Capacity [bar]']).value / 10.0 for row in (2, 3, 4)] == pytest.approx([
        7.571542406120033, 8.82257484144555, 8.783461911867068,
    ])
    assert [main.cell(row, main_columns['Installed Plies']).value for row in (2, 3, 4)] == [12, 7, 7]
    assert [main.cell(row, main_columns['Repair Zone Length [mm]']).value for row in (2, 3, 4)] == [1000.0, 1000.0, 1000.0]
    assert main.cell(4, main_columns['Governing Defect ID']).value == 'D-02'
    assert main.cell(4, main_columns['Governing B31G Length [mm]']).value == 35.0
    assert main.cell(4, main_columns['Governing B31G Remaining Wall [mm]']).value == 10.0
    assert [main.cell(row, main_columns['B31G Candidate Count']).value for row in (2, 3, 4)] == [1, 1, 2]
    assert [detail.cell(row, detail_columns['Calculation Status']).value for row in (2, 3, 4)] == [
        'OK', 'OK', 'INPUT ERROR',
    ]
    assert [detail.cell(row, detail_columns['Governing Defect']).value for row in (2, 3)] == [None, 'Yes']
    assert [detail.cell(row, detail_columns['Credited Safe Pressure [bar]']).value for row in (2, 3)] == pytest.approx([
        88.2257484144555, 87.83461911867067,
    ])
    assert 'INVALID_SELECTION' in detail.cell(4, detail_columns['Error Code']).value

    warning_rows = {
        result_book['Warnings'].cell(row, 1).value: result_book['Warnings'].cell(row, 3).value
        for row in range(4, result_book['Warnings'].max_row + 1)
        if result_book['Warnings'].cell(row, 1).value
    }
    assert warning_rows['W013'] == 'Main 2, 3, 4; Individual Defects 2, 3'

    cost = result_book['Cost Calculation']
    assert tuple(cost.cell(5, column).value for column in range(1, 21)) == COST_SOURCE_HEADERS
    assert (cost['U5'].value, cost['V5'].value) == ('Cost', 'Price')
    assert (cost.tables['CostRows'].ref, cost.tables['CostRows'].autoFilter.ref) == ('A5:V11', 'A5:V11')
    assert cost.protection.sheet is True
    assert all(not cost[address].protection.locked for address in ('B3', 'E3', 'H3'))
    assert all(cost[address].protection.locked for address in ('A3', 'D3', 'G3'))
    expected_formulas = [
        (f'Cost Calculation!{column}{row}', formula)
        for row in range(6, 12)
        for column, formula in (
            ('U', f'=IF(OR($B$3="",$E$3="",S{row}="",T{row}=""),"",S{row}*$B$3+T{row}*$E$3)'),
            ('V', f'=IF(OR(U{row}="",$H$3=""),"",U{row}*$H$3)'),
        )
    ]
    assert _formula_cells(result_book) == expected_formulas
    source_columns = _columns(INPUT_HEADERS + OUTPUT_HEADERS)
    for cost_row, main_row in zip(range(6, 12), range(2, 8), strict=True):
        assert [cost.cell(cost_row, column).value for column in range(1, 21)] == [
            main.cell(main_row, source_columns[header]).value for header in COST_SOURCE_HEADERS
        ]

    cost['B3'], cost['E3'], cost['H3'] = 25.0, 8.0, 1.4
    reupload = BytesIO()
    result_book.save(reupload)
    rebuilt_book = load_workbook(
        BytesIO(process_workbook(reupload.getvalue(), processed_at=FIXED_TIME).workbook_bytes),
        data_only=False,
    )
    assert rebuilt_book.sheetnames == EXPECTED_SHEETS
    assert [rebuilt_book['Cost Calculation'][address].value for address in ('B3', 'E3', 'H3')] == [25.0, 8.0, 1.4]
    assert _formula_cells(rebuilt_book) == expected_formulas
    rebuilt_main = rebuilt_book['Batch Input & Results']
    assert [rebuilt_main.cell(row, main_columns['Calculation Status']).value for row in range(2, 8)] == [
        'REVIEW REQUIRED', 'REVIEW REQUIRED', 'REVIEW REQUIRED', 'INPUT ERROR', 'OK', 'OK',
    ]


@pytest.mark.parametrize('sheet_count', (5, 6, 7))
def test_legacy_controlled_layouts_upgrade_to_the_v12_eight_sheet_contract(sheet_count):
    """Old controlled five/six/seven-sheet downloads remain safe input files."""
    legacy = legacy_workbook_bytes_with_rows([valid_row_values()], sheet_count=sheet_count)
    upgraded = process_workbook(legacy, processed_at=FIXED_TIME)
    workbook = load_workbook(BytesIO(upgraded.workbook_bytes), data_only=False)
    main_columns = _columns(INPUT_HEADERS + OUTPUT_HEADERS)

    assert workbook.sheetnames == EXPECTED_SHEETS
    assert workbook['Batch Input & Results'].cell(2, main_columns['Defect Length Basis']).value == 'Actual defect length'
    assert workbook['Batch Input & Results'].cell(2, main_columns['Calculation Status']).value == 'OK'
