from io import BytesIO

from openpyxl import load_workbook

from batch_schema import INPUT_HEADERS, MAX_ROWS, OUTPUT_HEADERS


def _template_workbook():
    from workbook_template import create_template_workbook

    return load_workbook(BytesIO(create_template_workbook()))


def test_template_has_common_info_and_row_table():
    """Catches a template that places batch fields in the defect table."""
    workbook = _template_workbook()

    assert workbook.sheetnames == [
        'Batch Information', 'Batch Input & Results',
        'Warnings', 'Summary', 'Instructions', 'Lists',
    ]
    info = workbook['Batch Information']
    assert [info['A3'].value, info['A4'].value, info['A5'].value] == [
        'Customer', 'Project Location', 'Report No',
    ]
    assert [info['B3'].value, info['B4'].value, info['B5'].value] == [None, None, None]

    data = workbook['Batch Input & Results']
    assert data['A1'].value == 'Pipe OD [mm]'
    assert data.freeze_panes == 'B2'
    assert workbook['Lists'].sheet_state == 'hidden'


def test_template_has_a_visible_protected_warning_register_with_empty_state():
    """Catches a template that leaves long warning explanations in result rows."""
    workbook = _template_workbook()
    warnings = workbook['Warnings']

    assert warnings.sheet_state == 'visible'
    assert warnings['A1'].value == 'Compliance Warning Register'
    assert [warnings.cell(3, column).value for column in range(1, 4)] == [
        'Warning Code',
        'Warning Meaning / Required Action',
        'Affected Excel Rows',
    ]
    assert warnings['A4'].value == 'No compliance warnings were generated.'
    assert warnings.freeze_panes == 'A4'
    assert warnings.protection.sheet is True
    assert not warnings.tables


def test_template_uses_canonical_headings_and_a_filterable_500_row_table():
    """Catches a workbook whose headers or accepted row extent diverge from parsing."""
    workbook = _template_workbook()
    data = workbook['Batch Input & Results']
    headings = [cell.value for cell in data[1]]

    assert headings == list(INPUT_HEADERS + OUTPUT_HEADERS)
    assert len(data.tables) == 1
    table = next(iter(data.tables.values()))
    assert table.ref == f'A1:{data.cell(1, len(headings)).coordinate[:-1]}{MAX_ROWS + 1}'
    assert table.autoFilter.ref == table.ref


def test_template_adds_dropdowns_for_every_selection_through_row_501():
    """Catches a controlled selection that can be entered unchecked in later rows."""
    workbook = _template_workbook()
    data = workbook['Batch Input & Results']
    validations = {
        validation.formula1: str(validation.sqref)
        for validation in data.data_validations.dataValidation
    }

    expected_choices = {
        '=MechanismChoices': 'F2:F501',
        '=DefectLocationChoices': 'G2:G501',
        '=TypeACheckChoices': 'M2:M501',
        '=ComponentTypeChoices': 'O2:O501',
        '=AxialLoadCaseChoices': 'Q2:Q501',
    }
    assert validations == expected_choices


def test_template_dropdowns_reject_invalid_selections_but_allow_unused_blank_rows():
    """Catches validations that block a blank unused row or silently accept bad selections."""
    workbook = _template_workbook()
    data = workbook['Batch Input & Results']
    validations = data.data_validations.dataValidation

    assert all(validation.showErrorMessage is True for validation in validations)
    assert all(validation.errorStyle == 'stop' for validation in validations)
    assert all(validation.allow_blank is True for validation in validations)


def test_template_marks_inputs_editable_and_outputs_protected_with_clear_headers():
    """Catches output cells that are editable or visually indistinguishable from inputs."""
    workbook = _template_workbook()
    data = workbook['Batch Input & Results']
    info = workbook['Batch Information']
    input_count = len(INPUT_HEADERS)

    assert data['A1'].fill.fgColor.rgb != data.cell(1, input_count + 1).fill.fgColor.rgb
    assert info['B3'].protection.locked is False
    assert data['A2'].protection.locked is False
    assert data.cell(2, input_count + 1).protection.locked is True
    assert data.protection.sheet is True
    assert data['I1'].comment is not None
    assert 'required only for internal corrosion' in data['J1'].comment.text.lower()


def test_template_has_status_colors_in_conditional_formatting():
    """Catches a template that gives row statuses no visual review signal."""
    workbook = _template_workbook()
    data = workbook['Batch Input & Results']

    rules = [
        rule
        for rules in data.conditional_formatting._cf_rules.values()
        for rule in rules
    ]
    status_rules = [rule for rule in rules if rule.type == 'containsText']
    assert {rule.text for rule in status_rules} == {
        'OK', 'REVIEW REQUIRED', 'NOT REPAIRABLE', 'INPUT ERROR', 'SYSTEM ERROR',
    }
    assert all(rule.dxf.fill.fgColor.rgb for rule in status_rules)


def test_template_contains_no_formulas_and_has_user_guidance():
    """Catches executable workbook logic or a template missing the review disclaimer."""
    workbook = _template_workbook()

    formulas = [
        cell.coordinate
        for worksheet in workbook.worksheets
        for row in worksheet.iter_rows()
        for cell in row
        if isinstance(cell.value, str) and cell.value.startswith('=')
    ]
    assert formulas == []
    instructions = workbook['Instructions']
    summary = workbook['Summary']
    assert 'blank rows are ignored' in ' '.join(
        str(cell.value).lower()
        for row in instructions.iter_rows()
        for cell in row
        if cell.value is not None
    )
    assert 'preliminary screening' in ' '.join(
        str(cell.value).lower()
        for row in summary.iter_rows()
        for cell in row
        if cell.value is not None
    )
