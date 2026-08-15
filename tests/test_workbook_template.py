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
        'Batch Information', 'Batch Input & Results', 'Cost Calculation',
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


def test_template_has_blank_editable_cost_sheet_in_new_controlled_order():
    workbook = _template_workbook()

    assert workbook.sheetnames == [
        'Batch Information', 'Batch Input & Results', 'Cost Calculation',
        'Warnings', 'Summary', 'Instructions', 'Lists',
    ]
    cost = workbook['Cost Calculation']
    assert [cost[address].value for address in ('B3', 'E3', 'H3')] == [None, None, None]
    assert all(
        cost[address].protection.locked is False
        for address in ('B3', 'E3', 'H3')
    )
    assert [cost.cell(5, column).value for column in range(1, 23)][-2:] == [
        'Cost', 'Price',
    ]
    assert cost.freeze_panes == 'A6'
    assert cost.protection.sheet is True
    assert cost.protection.selectUnlockedCells is False


def test_template_visibly_highlights_cost_assumption_value_cells():
    """Catches editable commercial inputs blending into the white worksheet."""
    cost = _template_workbook()['Cost Calculation']
    inputs = [cost[address] for address in ('B3', 'E3', 'H3')]

    assert [cell.fill.fill_type for cell in inputs] == ['solid'] * 3
    assert [cell.fill.fgColor.rgb for cell in inputs] == ['00FFF2CC'] * 3
    assert [cell.number_format for cell in inputs] == ['#,##0.00'] * 3
    assert [cell.protection.locked for cell in inputs] == [False] * 3
    assert [str(validation.sqref) for validation in cost.data_validations.dataValidation] == [
        'B3 E3 H3',
    ]


def test_cost_count_columns_use_integer_display_without_populating_template_rows():
    """Catch years, plies, or band counts being displayed as fractional quantities."""
    cost = _template_workbook()['Cost Calculation']

    assert [cost.cell(5, column).value for column in (10, 15, 17)] == [
        'Design Life [years]', 'Installed Plies', 'Cloth Band Count',
    ]
    for row in (6, MAX_ROWS + 5):
        assert [cost.cell(row, column).value for column in (10, 15, 17)] == [
            None, None, None,
        ]
        assert [cost.cell(row, column).number_format for column in (10, 15, 17)] == [
            '#,##0', '#,##0', '#,##0',
        ]
        assert cost.cell(row, 11).number_format == '#,##0.00'


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


def test_warning_register_subtitle_spans_the_table_without_clipping():
    """Catches a wrapped subtitle constrained to the narrow code column."""
    warnings = _template_workbook()['Warnings']

    assert 'A2:C2' in {str(cell_range) for cell_range in warnings.merged_cells.ranges}
    assert warnings.row_dimensions[2].height >= 32


def test_diagnostic_detail_columns_do_not_expand_result_rows():
    """Catches wrapped diagnostic JSON making each result row extremely tall."""
    data = _template_workbook()['Batch Input & Results']

    for heading in ('B31G Detail', 'Type A Detail', 'Type B Detail'):
        column = list(INPUT_HEADERS + OUTPUT_HEADERS).index(heading) + 1
        assert data.cell(2, column).alignment.wrap_text is not True
        assert data.cell(2, column).alignment.shrink_to_fit is True


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


def test_template_mechanism_choices_and_guidance_distinguish_dent_routes():
    """Catch a new template that restores ambiguous Dent or hides route limits."""
    workbook = _template_workbook()
    data = workbook['Batch Input & Results']
    lists = workbook['Lists']

    mechanism_values = [lists.cell(row, 1).value for row in range(1, 6)]
    assert mechanism_values == [
        'Corrosion', 'Dent w/crack', 'Dent no-crack', 'Leak', 'Crack',
    ]
    assert 'Dent' not in mechanism_values
    assert data['F1'].comment is not None
    mechanism_note = data['F1'].comment.text.lower()
    assert 'dent w/crack' in mechanism_note
    assert 'full-pressure laminate' in mechanism_note
    assert 'dent no-crack' in mechanism_note
    assert 'component-pipe substrate load sharing' in mechanism_note

    instruction_text = ' '.join(
        str(cell.value).lower()
        for row in workbook['Instructions'].iter_rows()
        for cell in row
        if cell.value is not None
    )
    assert 'dent w/crack' in instruction_text
    assert 'full-pressure laminate' in instruction_text
    assert 'dent no-crack' in instruction_text
    assert 'component-pipe substrate load sharing' in instruction_text
    assert 'legacy dent' in instruction_text
    assert 'older batch workbook' in instruction_text
    assert 'becomes dent w/crack' in instruction_text
    assert 'not a complete dent integrity or fatigue acceptance assessment' in instruction_text


def test_long_dent_instruction_has_room_for_every_wrapped_line():
    """Catches the final legacy-migration sentence being clipped in row 15."""
    instructions = _template_workbook()['Instructions']

    assert instructions['A15'].alignment.wrap_text is True
    assert instructions.row_dimensions[15].height >= 48


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


def test_protected_main_sheet_keeps_inputs_selectable_and_table_filterable():
    """Catches inverted openpyxl protection flags after workbook serialization."""
    workbook = _template_workbook()
    data = workbook['Batch Input & Results']
    input_count = len(INPUT_HEADERS)
    table = data.tables['BatchRows']

    assert data.protection.sheet is True
    assert data.protection.selectUnlockedCells is False
    assert data.protection.autoFilter is False
    assert data['A2'].protection.locked is False
    assert data.cell(2, input_count + 1).protection.locked is True
    assert table.autoFilter.ref == table.ref


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
    instruction_text = ' '.join(
        str(cell.value).lower()
        for row in instructions.iter_rows()
        for cell in row
        if cell.value is not None
    )
    assert 'warnings worksheet' in instruction_text
    assert '300 mm and 500 mm' in instruction_text
    assert 'tg = 110' in instruction_text
    assert 'b3 (cf cost / m2), e3 (epoxy cost / kg), and h3 (price multiplier)' in instruction_text
    assert 'may be blank or retain values from a previously processed workbook' in instruction_text
    assert 'preliminary screening' in ' '.join(
        str(cell.value).lower()
        for row in summary.iter_rows()
        for cell in row
        if cell.value is not None
    )
