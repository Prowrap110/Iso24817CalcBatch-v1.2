from datetime import UTC, datetime
from io import BytesIO
import json

from openpyxl import load_workbook
import pytest

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
    """Catch a release workbook that breaks status, cost, or re-upload contracts."""
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
    mechanism_column = INPUT_HEADERS.index('Mechanism') + 1
    remaining_wall_column = INPUT_HEADERS.index('Remaining Wall [mm]') + 1
    assert [input_sheet.cell(row, mechanism_column).value for row in (2, 7)] == [
        'Dent w/crack', 'Dent no-crack',
    ]
    assert [input_sheet.cell(row, remaining_wall_column).value for row in (2, 7)] == [
        9.53, 9.53,
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
    assert [result_sheet.cell(row, mechanism_column).value for row in (2, 7)] == [
        'Dent w/crack', 'Dent no-crack',
    ]
    expected_no_crack_capacity_bar = (
        2.0 * (359.0 * 0.72) * 9.53 / 457.2 * 10.0
    )
    assert result_sheet.cell(2, output_column['Effective Pipe Capacity [bar]']).value == 0.0
    assert result_sheet.cell(2, output_column['Composite Pressure Deficit [bar]']).value == 50.0
    assert result_sheet.cell(2, output_column['Installed Plies']).value == 9
    assert result_sheet.cell(
        7, output_column['Effective Pipe Capacity [bar]'],
    ).value == pytest.approx(expected_no_crack_capacity_bar)
    assert result_sheet.cell(7, output_column['Composite Pressure Deficit [bar]']).value == 0.0
    assert result_sheet.cell(7, output_column['Installed Plies']).value == 3

    cracked_detail = json.loads(result_sheet.cell(2, output_column['Type A Detail']).value)
    no_crack_detail = json.loads(result_sheet.cell(7, output_column['Type A Detail']).value)
    assert cracked_detail['calculation_basis'] == (
        'Dent w/crack - full-pressure laminate'
    )
    assert cracked_detail['substrate_allowable_pressure_mpa'] == 0.0
    assert cracked_detail['composite_pressure_deficit_mpa'] == 5.0
    assert no_crack_detail['calculation_basis'] == (
        'Dent no-crack - substrate load sharing'
    )
    assert no_crack_detail['allowable_pipe_stress_mpa'] == pytest.approx(258.48)
    assert no_crack_detail['substrate_allowable_pressure_mpa'] == pytest.approx(
        expected_no_crack_capacity_bar / 10.0,
    )
    assert no_crack_detail['composite_pressure_deficit_mpa'] == 0.0
    # Preview and processing use the same engine path so the user sees the
    # final row status before generating the download.
    assert calls == [COMMON_INFO] * 10
    assert result_book['Batch Information']['B3'].value == 'Acceptance Customer'
    assert result_book['Batch Information']['B4'].value == 'Acceptance Location'
    assert result_book['Batch Information']['B5'].value == 'ACCEPT-001'
    assert result_book.sheetnames == [
        'Batch Information', 'Batch Input & Results', 'Cost Calculation',
        'Warnings', 'Summary', 'Instructions', 'Lists',
    ]

    cost_sheet = result_book['Cost Calculation']
    expected_cost_mapping = (
        ('Pipe OD [mm]', 1),
        ('Nominal Wall [mm]', 2),
        ('Pipe Yield [MPa]', 3),
        ('Design Pressure [bar]', 4),
        ('Operating Temperature [degC]', 5),
        ('Mechanism', 6),
        ('Defect Location', 7),
        ('Defect Length [mm]', 8),
        ('Remaining Wall [mm]', 9),
        ('Design Life [years]', 11),
        ('Design Factor', 12),
        ('Prowrap CF Cloth Width [mm]', 18),
        ('Wall Loss [%]', 29),
        ('Required Structural Thickness [mm]', 36),
        ('Installed Plies', 37),
        ('Total Repair Length [mm]', 44),
        ('Cloth Band Count', 45),
        ('Procurement Axial Length [mm]', 46),
        ('Fabric Area [m2]', 47),
        ('Epoxy Mass [kg]', 48),
    )
    assert tuple(cost_sheet.cell(5, column).value for column in range(1, 21)) == tuple(
        heading for heading, _ in expected_cost_mapping
    )
    assert (cost_sheet['U5'].value, cost_sheet['V5'].value) == ('Cost', 'Price')
    for cost_row, result_row in zip(range(6, 12), range(2, 8), strict=True):
        assert [cost_sheet.cell(cost_row, column).value for column in range(1, 21)] == [
            result_sheet.cell(result_row, source_column).value
            for _, source_column in expected_cost_mapping
        ]
    assert [cost_sheet.cell(row, 6).value for row in (6, 11)] == [
        'Dent w/crack', 'Dent no-crack',
    ]

    assert [cost_sheet[address].value for address in ('B3', 'E3', 'H3')] == [
        None, None, None,
    ]
    assert all(not cost_sheet[address].protection.locked for address in ('B3', 'E3', 'H3'))
    assert cost_sheet.protection.sheet is True
    assert all(cost_sheet[address].protection.locked for address in ('A3', 'D3', 'G3'))
    assert all(
        cost_sheet.cell(row, column).protection.locked
        for row in range(5, 12)
        for column in range(1, 23)
    )
    assert cost_sheet.freeze_panes == 'A6'
    assert cost_sheet.tables['CostRows'].ref == 'A5:V11'

    expected_formulas = [
        ('Cost Calculation!U6', '=IF(OR($B$3="",$E$3="",S6="",T6=""),"",S6*$B$3+T6*$E$3)'),
        ('Cost Calculation!V6', '=IF(OR(U6="",$H$3=""),"",U6*$H$3)'),
        ('Cost Calculation!U7', '=IF(OR($B$3="",$E$3="",S7="",T7=""),"",S7*$B$3+T7*$E$3)'),
        ('Cost Calculation!V7', '=IF(OR(U7="",$H$3=""),"",U7*$H$3)'),
        ('Cost Calculation!U8', '=IF(OR($B$3="",$E$3="",S8="",T8=""),"",S8*$B$3+T8*$E$3)'),
        ('Cost Calculation!V8', '=IF(OR(U8="",$H$3=""),"",U8*$H$3)'),
        ('Cost Calculation!U9', '=IF(OR($B$3="",$E$3="",S9="",T9=""),"",S9*$B$3+T9*$E$3)'),
        ('Cost Calculation!V9', '=IF(OR(U9="",$H$3=""),"",U9*$H$3)'),
        ('Cost Calculation!U10', '=IF(OR($B$3="",$E$3="",S10="",T10=""),"",S10*$B$3+T10*$E$3)'),
        ('Cost Calculation!V10', '=IF(OR(U10="",$H$3=""),"",U10*$H$3)'),
        ('Cost Calculation!U11', '=IF(OR($B$3="",$E$3="",S11="",T11=""),"",S11*$B$3+T11*$E$3)'),
        ('Cost Calculation!V11', '=IF(OR(U11="",$H$3=""),"",U11*$H$3)'),
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
        (f'{worksheet.title}!{cell.coordinate}', cell.value)
        for worksheet in result_book.worksheets
        for row in worksheet.iter_rows()
        for cell in row
        if cell.data_type == 'f'
    ]
    assert formulas == expected_formulas

    # Both no-solution and invalid rows remain aligned in the cost table, but
    # unavailable material quantities are never converted into commercial data.
    assert [cost_sheet.cell(row, column).value for row in (8, 9) for column in (19, 20)] == [
        None, None, None, None,
    ]
    assert cost_sheet['S11'].value is not None
    assert cost_sheet['T11'].value is not None
    assert (cost_sheet['U11'].value, cost_sheet['V11'].value) == (
        expected_formulas[-2][1], expected_formulas[-1][1],
    )
    cached_book = load_workbook(BytesIO(processed.workbook_bytes), data_only=True)
    cached_cost = cached_book['Cost Calculation']
    assert [cached_cost.cell(row, column).value for row in range(6, 12) for column in (21, 22)] == [
        None,
    ] * 12

    # A processed workbook is a supported upload: the user-controlled
    # assumptions survive while the commercial table and exact formulas rebuild.
    cost_sheet['B3'] = 25.0
    cost_sheet['E3'] = 8.0
    cost_sheet['H3'] = 1.4
    reupload = BytesIO()
    result_book.save(reupload)
    rebuilt = process_workbook(reupload.getvalue(), processed_at=FIXED_TIME)
    rebuilt_book = load_workbook(BytesIO(rebuilt.workbook_bytes), data_only=False)
    rebuilt_cost = rebuilt_book['Cost Calculation']
    assert [rebuilt_cost[address].value for address in ('B3', 'E3', 'H3')] == [
        25.0, 8.0, 1.4,
    ]
    rebuilt_result = rebuilt_book['Batch Input & Results']
    assert [rebuilt_result.cell(row, mechanism_column).value for row in (2, 7)] == [
        'Dent w/crack', 'Dent no-crack',
    ]
    assert [rebuilt_cost.cell(row, 6).value for row in (6, 11)] == [
        'Dent w/crack', 'Dent no-crack',
    ]
    rebuilt_formulas = [
        (f'{worksheet.title}!{cell.coordinate}', cell.value)
        for worksheet in rebuilt_book.worksheets
        for row in worksheet.iter_rows()
        for cell in row
        if cell.data_type == 'f'
    ]
    assert rebuilt_formulas == expected_formulas
