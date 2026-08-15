from datetime import UTC, datetime
from io import BytesIO
import zipfile

import pytest
from openpyxl import load_workbook
from openpyxl.worksheet.formula import ArrayFormula, DataTableFormula

from batch_schema import INPUT_HEADERS, MAX_ROWS, MAX_UPLOAD_BYTES, OUTPUT_HEADERS
from cost_calculation import COST_TABLE_HEADERS, cost_formula, price_formula
from tests.helpers import valid_row_values, workbook_bytes_with_rows
from workbook_processor import (
    WorkbookProcessingError,
    _commercial_input_errors,
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


def test_formula_scan_uses_loaded_cells_without_dense_worksheet_iteration(monkeypatch):
    import workbook_processor

    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Summary'].cell(1_048_576, 16_384).value = '=1+1'
    for worksheet in workbook.worksheets:
        monkeypatch.setattr(
            worksheet,
            'iter_rows',
            lambda: (_ for _ in ()).throw(AssertionError('dense iteration used')),
        )

    issues = workbook_processor._formula_errors(workbook)

    assert [issue.code for issue in issues] == ['FORMULA_NOT_ALLOWED']
    assert 'Summary!XFD1048576' in issues[0].message


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


def test_dense_worksheet_is_rejected_before_openpyxl_materializes_cells(monkeypatch):
    """Catches small compressed uploads that amplify into excessive cell objects."""
    import workbook_processor

    source = _dense_workbook_bytes(100_001)
    assert len(source) < MAX_UPLOAD_BYTES

    def fail_if_loaded(*_args, **_kwargs):
        raise AssertionError('openpyxl must not parse an over-limit worksheet')

    monkeypatch.setattr(workbook_processor, 'load_workbook', fail_if_loaded)

    inspection = workbook_processor.inspect_workbook(source)

    assert [issue.code for issue in inspection.workbook_errors] == [
        'UNREADABLE_WORKBOOK',
    ]
    assert inspection.workbook_errors[0].message == (
        'The uploaded workbook contains too many worksheet cells.'
    )


def test_relocated_dense_worksheet_is_rejected_before_openpyxl(monkeypatch):
    """Catches a worksheet relationship moved outside xl/worksheets bypassing the cap."""
    import workbook_processor

    source = _relocated_dense_workbook_bytes(100_001)
    assert len(source) < MAX_UPLOAD_BYTES

    def fail_if_loaded(*_args, **_kwargs):
        raise AssertionError('openpyxl reached through relocated worksheet bypass')

    monkeypatch.setattr(workbook_processor, 'load_workbook', fail_if_loaded)

    inspection = workbook_processor.inspect_workbook(source)

    assert [issue.code for issue in inspection.workbook_errors] == [
        'UNREADABLE_WORKBOOK',
    ]
    assert inspection.workbook_errors[0].message == (
        'The uploaded workbook contains too many worksheet cells.'
    )


def test_arbitrary_suffix_dense_worksheet_is_rejected_before_openpyxl(monkeypatch):
    """Catches a valid worksheet content type using a non-XML part suffix."""
    import workbook_processor

    source = _relocated_dense_workbook_bytes(
        100_001,
        new_path='xl/custom/dense.data',
    )
    assert len(source) < MAX_UPLOAD_BYTES

    def fail_if_loaded(*_args, **_kwargs):
        raise AssertionError('openpyxl reached through worksheet-suffix bypass')

    monkeypatch.setattr(workbook_processor, 'load_workbook', fail_if_loaded)

    inspection = workbook_processor.inspect_workbook(source)

    assert [issue.code for issue in inspection.workbook_errors] == [
        'UNREADABLE_WORKBOOK',
    ]
    assert inspection.workbook_errors[0].message == (
        'The uploaded workbook contains too many worksheet cells.'
    )


def test_malformed_arbitrary_suffix_worksheet_is_rejected_before_openpyxl(monkeypatch):
    """Catches recognized non-XML-suffix worksheets escaping malformed handling."""
    import workbook_processor

    source = _relocated_worksheet_workbook_bytes(
        (
            b'<worksheet '
            b'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            b'<sheetData><row>'
        ),
        new_path='xl/custom/malformed.data',
    )

    def fail_if_loaded(*_args, **_kwargs):
        raise AssertionError('openpyxl reached malformed recognized worksheet')

    monkeypatch.setattr(workbook_processor, 'load_workbook', fail_if_loaded)

    inspection = workbook_processor.inspect_workbook(source)

    assert [issue.code for issue in inspection.workbook_errors] == [
        'UNREADABLE_WORKBOOK',
    ]


def test_unrelated_binary_custom_part_is_not_parsed_as_xml():
    """Catches suffix-independent scanning that probes unrelated binary package parts."""
    source = _workbook_with_binary_custom_part()

    inspection = inspect_workbook(source)

    assert inspection.workbook_errors == ()
    assert inspection.populated_rows == 1


def test_strict_spreadsheetml_dense_worksheet_is_still_bounded(monkeypatch):
    """Catches namespace filtering that disables the cap for ISO Strict sheets."""
    import workbook_processor

    source = _dense_workbook_bytes(
        100_001,
        namespace='http://purl.oclc.org/ooxml/spreadsheetml/main',
    )

    def fail_if_loaded(*_args, **_kwargs):
        raise AssertionError('openpyxl reached through strict-namespace bypass')

    monkeypatch.setattr(workbook_processor, 'load_workbook', fail_if_loaded)

    inspection = workbook_processor.inspect_workbook(source)

    assert [issue.code for issue in inspection.workbook_errors] == [
        'UNREADABLE_WORKBOOK',
    ]
    assert inspection.workbook_errors[0].message == (
        'The uploaded workbook contains too many worksheet cells.'
    )


def test_foreign_custom_xml_with_worksheet_names_is_ignored():
    """Catches local-name scanning that treats unrelated customer XML as a sheet."""
    source = _foreign_custom_xml_workbook_bytes(100_001)
    assert len(source) < MAX_UPLOAD_BYTES

    inspection = inspect_workbook(source)

    assert inspection.workbook_errors == ()
    assert inspection.populated_rows == 1


def test_foreign_cell_elements_inside_a_real_worksheet_extension_are_ignored():
    """Catches foreign extension elements being counted as SpreadsheetML cells."""
    source = _worksheet_with_foreign_extension_bytes(100_001)
    assert len(source) < MAX_UPLOAD_BYTES

    with pytest.warns(UserWarning, match='Unknown extension is not supported'):
        inspection = inspect_workbook(source)

    assert inspection.workbook_errors == ()
    assert inspection.populated_rows == 1


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


def test_far_input_scan_uses_loaded_cells_without_max_row_iteration(monkeypatch):
    import workbook_processor

    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    data = workbook['Batch Input & Results']
    data.cell(1_048_576, 1).value = 508.0
    monkeypatch.setattr(type(data), 'max_row', property(lambda _worksheet: MAX_ROWS + 1))

    issues = workbook_processor._out_of_range_input_errors(data)

    assert [issue.code for issue in issues] == ['INPUT_ROW_OUT_OF_RANGE']
    assert 'A1048576' in issues[0].message


def test_populated_row_scan_stays_within_controlled_input_rectangle(monkeypatch):
    import workbook_processor

    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    data = workbook['Batch Input & Results']
    data.cell(1_048_576, len(INPUT_HEADERS) + len(OUTPUT_HEADERS)).value = 'harmless output note'
    original_cell = data.cell

    def controlled_cell(row=None, column=None, *args, **kwargs):
        if row is not None and row > MAX_ROWS + 1:
            raise AssertionError('uncontrolled row scan')
        return original_cell(row=row, column=column, *args, **kwargs)

    monkeypatch.setattr(data, 'cell', controlled_cell)

    populated = workbook_processor._populated_rows(data)

    assert [excel_row for excel_row, _ in populated] == [2]


def test_formula_issue_has_priority_over_far_input_row_issue():
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Batch Input & Results'].cell(1_048_576, 1).value = 508.0
    workbook['Summary'].cell(1_048_576, 16_384).value = '=1+1'

    inspection = inspect_workbook(_saved(workbook))

    assert [issue.code for issue in inspection.workbook_errors] == ['FORMULA_NOT_ALLOWED']


def test_processed_cost_formulas_and_commercial_inputs_are_safe_to_reupload():
    """Catches deny-all formula scanning or a rebuild that drops cost assumptions."""
    first = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]),
        processed_at=FIXED_TIME,
    )
    workbook = _workbook(first.workbook_bytes)
    cost = workbook['Cost Calculation']
    cost['B3'], cost['E3'], cost['H3'] = 50.0, 20.0, 1.5

    second = process_workbook(_saved(workbook), processed_at=FIXED_TIME)
    regenerated = _workbook(second.workbook_bytes)['Cost Calculation']

    assert [regenerated[address].value for address in ('B3', 'E3', 'H3')] == [
        50.0, 20.0, 1.5,
    ]


def test_whitespace_only_commercial_input_is_rebuilt_as_a_true_blank():
    """Catches whitespace bypassing blank validation and breaking Excel IF checks."""
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Cost Calculation']['B3'] = '   '

    result = process_workbook(_saved(workbook), processed_at=FIXED_TIME)
    rebuilt = _workbook(result.workbook_bytes)['Cost Calculation']

    assert rebuilt['B3'].value is None
    assert rebuilt['U6'].value == cost_formula(6)


def test_altered_cost_formula_is_rejected():
    """Catches broad formula allowlisting in the controlled cost range."""
    result = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]),
        processed_at=FIXED_TIME,
    )
    workbook = _workbook(result.workbook_bytes)
    workbook['Cost Calculation']['U6'] = '=1+1'

    inspection = inspect_workbook(_saved(workbook))

    assert [issue.code for issue in inspection.workbook_errors] == ['FORMULA_NOT_ALLOWED']
    assert 'Cost Calculation!U6' in inspection.workbook_errors[0].message


@pytest.mark.parametrize(('address', 'value'), [
    ('B3', -0.01),
    ('E3', 'twenty'),
    ('H3', float('inf')),
    ('B3', float('nan')),
    ('E3', True),
])
def test_invalid_commercial_inputs_are_rejected(address, value):
    """Catches unsafe or unusable values copied into the trusted output."""
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Cost Calculation'][address] = value

    issues = _commercial_input_errors(workbook)

    assert [issue.code for issue in issues] == ['INVALID_COST_INPUT']
    assert address in issues[0].message


def test_formula_commercial_input_keeps_formula_error_priority():
    """Catches formula injection being downgraded to a generic cost-input error."""
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Cost Calculation']['B3'] = '=1+1'
    workbook['Batch Input & Results'].cell(1_048_576, 1).value = 508.0

    inspection = inspect_workbook(_saved(workbook))

    assert [issue.code for issue in inspection.workbook_errors] == ['FORMULA_NOT_ALLOWED']


def test_changed_cost_heading_is_a_workbook_error():
    """Catches accepting a structurally altered commercial table."""
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    workbook['Cost Calculation']['A5'] = 'Outside Diameter [mm]'

    inspection = inspect_workbook(_saved(workbook))

    assert [issue.code for issue in inspection.workbook_errors] == [
        'INVALID_COST_HEADERS',
    ]


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


def test_processed_warning_sheet_consolidates_codes_and_affected_rows():
    """Catches repeated long warning text or one legend entry per defect row."""
    source = workbook_bytes_with_rows([
        valid_row_values(**{'Prowrap CF Cloth Width [mm]': 250.0}),
        valid_row_values(**{'Prowrap CF Cloth Width [mm]': 250.0}),
    ])

    result = process_workbook(source, processed_at=FIXED_TIME)
    workbook = _workbook(result.workbook_bytes)
    data = workbook['Batch Input & Results']
    warnings = workbook['Warnings']

    assert data['W2'].value == 'W018'
    assert data['W3'].value == 'W018'
    assert warnings['A4'].value == 'W018'
    assert '300 mm or 500 mm' in warnings['B4'].value
    assert warnings['C4'].value == '2, 3'
    assert warnings['A4'].font.italic is False
    assert list(warnings.tables) == ['WarningRegister']
    assert warnings.tables['WarningRegister'].ref == 'A3:C4'


def test_processed_workbook_keeps_clear_no_warning_register_state():
    """Catches an empty warning sheet that looks broken or unfinished."""
    result = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]),
        processed_at=FIXED_TIME,
    )
    warnings = _workbook(result.workbook_bytes)['Warnings']

    assert warnings['A4'].value == 'No compliance warnings were generated.'
    assert not warnings.tables


def test_processed_warning_register_remains_filterable_while_protected():
    """Catches sheet protection disabling the warning table filter controls."""
    result = process_workbook(
        workbook_bytes_with_rows([
            valid_row_values(**{'Prowrap CF Cloth Width [mm]': 250.0}),
        ]),
        processed_at=FIXED_TIME,
    )
    warnings = _workbook(result.workbook_bytes)['Warnings']

    assert warnings.protection.sheet is True
    assert warnings.protection.autoFilter is False


def test_previous_five_sheet_template_is_accepted_and_upgraded():
    """Catches a release that strands users holding the previous template."""
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    del workbook['Cost Calculation']
    del workbook['Warnings']

    inspection = inspect_workbook(_saved(workbook))
    result = process_workbook(_saved(workbook), processed_at=FIXED_TIME)

    assert inspection.workbook_errors == ()
    assert _workbook(result.workbook_bytes).sheetnames == [
        'Batch Information', 'Batch Input & Results', 'Cost Calculation', 'Warnings',
        'Summary', 'Instructions', 'Lists',
    ]


def test_previous_six_sheet_template_is_accepted_and_upgraded():
    """Catches a release that strands users holding the warning-register template."""
    workbook = _workbook(workbook_bytes_with_rows([valid_row_values()]))
    del workbook['Cost Calculation']

    result = process_workbook(_saved(workbook), processed_at=FIXED_TIME)

    assert _workbook(result.workbook_bytes).sheetnames == [
        'Batch Information', 'Batch Input & Results', 'Cost Calculation',
        'Warnings', 'Summary', 'Instructions', 'Lists',
    ]


def test_processed_cost_sheet_maps_requested_values_and_formulas():
    """Catches wrong source-column order or missing controlled formulas."""
    result = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]),
        processed_at=FIXED_TIME,
    )
    workbook = _workbook(result.workbook_bytes)
    source = workbook['Batch Input & Results']
    cost = workbook['Cost Calculation']
    expected_source_columns = (
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'R',
        'AC', 'AJ', 'AK', 'AR', 'AS', 'AT', 'AU', 'AV',
    )

    assert tuple(cell.value for cell in cost[5]) == COST_TABLE_HEADERS
    assert [cost.cell(6, column).value for column in range(1, 21)] == [
        source[f'{column}2'].value for column in expected_source_columns
    ]
    assert cost['U6'].value == cost_formula(6)
    assert cost['V6'].value == price_formula(6)
    assert cost.tables['CostRows'].ref == 'A5:V6'


def test_uploaded_cost_table_values_are_never_trusted():
    """Catches user-edited or tampered commercial rows being copied into output."""
    first = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]),
        processed_at=FIXED_TIME,
    )
    edited = _workbook(first.workbook_bytes)
    edited['Cost Calculation']['A6'] = 999999.0
    edited['Cost Calculation']['S6'] = 999999.0

    second = process_workbook(_saved(edited), processed_at=FIXED_TIME)
    regenerated = _workbook(second.workbook_bytes)

    assert regenerated['Cost Calculation']['A6'].value == 457.2
    assert regenerated['Cost Calculation']['S6'].value == (
        regenerated['Batch Input & Results']['AU2'].value
    )


def test_processed_cost_sheet_uses_one_compact_row_per_populated_defect():
    """Catches sparse source row numbers leaking into compact cost-table layout."""
    workbook = _workbook(workbook_bytes_with_rows([
        valid_row_values(),
        valid_row_values(**{'Pipe OD [mm]': 508.0}),
        valid_row_values(**{'Pipe OD [mm]': 610.0}),
    ]))
    data = workbook['Batch Input & Results']
    for column in range(1, len(INPUT_HEADERS) + 1):
        data.cell(3, column).value = None

    result = process_workbook(_saved(workbook), processed_at=FIXED_TIME)
    cost = _workbook(result.workbook_bytes)['Cost Calculation']

    assert [cost['A6'].value, cost['A7'].value, cost['A8'].value] == [
        457.2, 610.0, None,
    ]
    assert cost['U7'].value == cost_formula(7)
    assert cost.tables['CostRows'].ref == 'A5:V7'


def test_processed_cost_table_filter_covers_every_compact_row():
    """Catches the table filter retaining the one-row template range."""
    result = process_workbook(
        workbook_bytes_with_rows([
            valid_row_values(),
            valid_row_values(**{'Pipe OD [mm]': 508.0}),
            valid_row_values(**{'Pipe OD [mm]': 610.0}),
        ]),
        processed_at=FIXED_TIME,
    )
    table = _workbook(result.workbook_bytes)['Cost Calculation'].tables['CostRows']

    assert table.ref == 'A5:V8'
    assert table.autoFilter.ref == table.ref


def test_cleared_processed_defect_ignores_stale_exact_cost_formulas():
    """Catches valid generated formulas blocking a safe processed-workbook rebuild."""
    first = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]),
        processed_at=FIXED_TIME,
    )
    edited = _workbook(first.workbook_bytes)
    data = edited['Batch Input & Results']
    for column in range(1, len(INPUT_HEADERS) + 1):
        data.cell(2, column).value = None

    second = process_workbook(_saved(edited), processed_at=FIXED_TIME)
    cost = _workbook(second.workbook_bytes)['Cost Calculation']

    assert second.populated_rows == 0
    assert [cost.cell(6, column).value for column in range(1, 23)] == [None] * 22
    assert cost.tables['CostRows'].ref == 'A5:V6'


def test_processed_workbook_requests_full_automatic_recalculation():
    """Catches cost formulas remaining stale after users edit commercial assumptions."""
    result = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]),
        processed_at=FIXED_TIME,
    )
    workbook = _workbook(result.workbook_bytes)

    assert workbook.calculation.calcMode == 'auto'
    assert workbook.calculation.fullCalcOnLoad is True
    assert workbook.calculation.forceFullCalc is True


def test_processed_workbook_updates_summary_and_uses_stable_diagnostic_json():
    source = workbook_bytes_with_rows([valid_row_values(**{
        'Mechanism': 'Leak',
        'Design Pressure [bar]': 150.0,
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
    assert summary['B24'].value == '1.1.0'
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

    sensitive_message = 'customer=Top Secret; pipe_od=999'

    def explode(*_args, **_kwargs):
        raise RuntimeError(sensitive_message)

    monkeypatch.setattr(workbook_processor, 'calculate_row', explode)
    with caplog.at_level('ERROR', logger='workbook_processor'):
        result = process_workbook(workbook_bytes_with_rows([valid_row_values()]), processed_at=FIXED_TIME)

    assert result.status_counts == {'SYSTEM ERROR': 1}
    assert 'source Excel row 2' in caplog.text
    assert 'RuntimeError' in caplog.text
    assert 'explode' in caplog.text
    assert sensitive_message not in caplog.text
    assert 'Top Secret' not in caplog.text
    assert 'pipe_od=999' not in caplog.text
    assert 'Batch Customer' not in caplog.text
    assert '457.2' not in caplog.text


def _encrypted_zip_bytes() -> bytes:
    output = BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        entry = zipfile.ZipInfo('xl/workbook.xml')
        entry.flag_bits |= 0x1
        archive.writestr(entry, b'<workbook/>')
    return output.getvalue()


def _dense_workbook_bytes(
    cell_count: int,
    namespace: str = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
) -> bytes:
    """Return a valid controlled XLSX package with one deliberately dense sheet."""
    worksheet_xml = _dense_worksheet_xml(cell_count, namespace)
    source = workbook_bytes_with_rows([valid_row_values()])
    output = BytesIO()
    with zipfile.ZipFile(BytesIO(source)) as input_zip, zipfile.ZipFile(output, 'w') as output_zip:
        for entry in input_zip.infolist():
            content = input_zip.read(entry.filename)
            if entry.filename == 'xl/worksheets/sheet5.xml':
                replacement = zipfile.ZipInfo(entry.filename)
                replacement.compress_type = zipfile.ZIP_STORED
                output_zip.writestr(replacement, worksheet_xml)
            else:
                output_zip.writestr(entry, content)
    return output.getvalue()


def _relocated_dense_workbook_bytes(
    cell_count: int,
    new_path: str = 'xl/custom/dense.xml',
) -> bytes:
    """Return a controlled XLSX whose dense worksheet part uses a custom path."""
    return _relocated_worksheet_workbook_bytes(
        _dense_worksheet_xml(cell_count),
        new_path=new_path,
    )


def _relocated_worksheet_workbook_bytes(
    worksheet_xml: bytes,
    new_path: str,
) -> bytes:
    """Relocate one valid worksheet part and update its OPC declarations."""
    old_path = b'/xl/worksheets/sheet5.xml'
    new_part_name = f'/{new_path}'.encode()
    source = workbook_bytes_with_rows([valid_row_values()])
    output = BytesIO()
    with zipfile.ZipFile(BytesIO(source)) as input_zip, zipfile.ZipFile(output, 'w') as output_zip:
        for entry in input_zip.infolist():
            if entry.filename == 'xl/worksheets/sheet5.xml':
                continue
            content = input_zip.read(entry.filename)
            if entry.filename in {'[Content_Types].xml', 'xl/_rels/workbook.xml.rels'}:
                content = content.replace(old_path, new_part_name)
            output_zip.writestr(entry, content)
        replacement = zipfile.ZipInfo(new_path)
        replacement.compress_type = zipfile.ZIP_STORED
        output_zip.writestr(replacement, worksheet_xml)
    return output.getvalue()


def _workbook_with_binary_custom_part() -> bytes:
    """Add a related binary part with a valid OPC content-type declaration."""
    default_type = (
        b'<Default Extension="data" ContentType="application/octet-stream"/>'
    )
    relationship = (
        b'<Relationship Type="urn:protap:binary-attachment" '
        b'Target="custom/blob.data" Id="rId4"/>'
    )
    source = workbook_bytes_with_rows([valid_row_values()])
    output = BytesIO()
    with zipfile.ZipFile(BytesIO(source)) as input_zip, zipfile.ZipFile(output, 'w') as output_zip:
        for entry in input_zip.infolist():
            content = input_zip.read(entry.filename)
            if entry.filename == '[Content_Types].xml':
                content = content.replace(b'</Types>', default_type + b'</Types>')
            elif entry.filename == '_rels/.rels':
                content = content.replace(b'</Relationships>', relationship + b'</Relationships>')
            output_zip.writestr(entry, content)
        binary_entry = zipfile.ZipInfo('custom/blob.data')
        binary_entry.compress_type = zipfile.ZIP_STORED
        output_zip.writestr(binary_entry, b'\x00\xffnot-xml' * 10_000)
    return output.getvalue()


def _foreign_custom_xml_workbook_bytes(cell_count: int) -> bytes:
    """Add a related custom XML part whose local names resemble a worksheet."""
    custom_xml = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<worksheet xmlns="urn:customer-custom-data">'
        + b'<c/>' * cell_count
        + b'</worksheet>'
    )
    relationship = (
        b'<Relationship '
        b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml" '
        b'Target="customXml/item1.xml" Id="rId4"/>'
    )
    source = workbook_bytes_with_rows([valid_row_values()])
    output = BytesIO()
    with zipfile.ZipFile(BytesIO(source)) as input_zip, zipfile.ZipFile(output, 'w') as output_zip:
        for entry in input_zip.infolist():
            content = input_zip.read(entry.filename)
            if entry.filename == '_rels/.rels':
                content = content.replace(b'</Relationships>', relationship + b'</Relationships>')
            output_zip.writestr(entry, content)
        custom_entry = zipfile.ZipInfo('customXml/item1.xml')
        custom_entry.compress_type = zipfile.ZIP_STORED
        output_zip.writestr(custom_entry, custom_xml)
    return output.getvalue()


def _worksheet_with_foreign_extension_bytes(cell_count: int) -> bytes:
    """Add many foreign c elements inside a valid worksheet extension container."""
    extension = (
        b'<extLst><ext uri="{PROTAP-FOREIGN-CELL-TEST}" '
        b'xmlns:f="urn:customer-custom-data">'
        + b'<f:c/>' * cell_count
        + b'</ext></extLst>'
    )
    source = workbook_bytes_with_rows([valid_row_values()])
    output = BytesIO()
    with zipfile.ZipFile(BytesIO(source)) as input_zip, zipfile.ZipFile(output, 'w') as output_zip:
        for entry in input_zip.infolist():
            content = input_zip.read(entry.filename)
            if entry.filename == 'xl/worksheets/sheet5.xml':
                content = content.replace(b'</worksheet>', extension + b'</worksheet>')
                replacement = zipfile.ZipInfo(entry.filename)
                replacement.compress_type = zipfile.ZIP_STORED
                output_zip.writestr(replacement, content)
            else:
                output_zip.writestr(entry, content)
    return output.getvalue()


def _dense_worksheet_xml(
    cell_count: int,
    namespace: str = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
) -> bytes:
    cells_per_row = 100
    rows = []
    for first_cell in range(0, cell_count, cells_per_row):
        row_number = first_cell // cells_per_row + 1
        row_cell_count = min(cells_per_row, cell_count - first_cell)
        cells = ''.join(
            f'<c r="{_column_name(column)}{row_number}" t="n"><v>1</v></c>'
            for column in range(1, row_cell_count + 1)
        )
        rows.append(f'<row r="{row_number}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{namespace}">'
        f'<sheetData>{"".join(rows)}</sheetData></worksheet>'
    ).encode()


def _column_name(column: int) -> str:
    name = ''
    while column:
        column, remainder = divmod(column - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _stable_json(value: str) -> str:
    import json

    return json.dumps(json.loads(value), sort_keys=True, separators=(',', ':'))
