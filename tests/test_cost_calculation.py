from cost_calculation import (
    COST_FIRST_DATA_ROW,
    COST_LAST_DATA_ROW,
    COST_SOURCE_HEADERS,
    COST_TABLE_HEADERS,
    cost_formula,
    is_allowed_cost_formula,
    price_formula,
)


def test_cost_source_headers_survive_inserted_v12_columns():
    assert COST_SOURCE_HEADERS == (
        'Pipe OD [mm]', 'Nominal Wall [mm]', 'Pipe Yield [MPa]',
        'Design Pressure [bar]', 'Operating Temperature [degC]',
        'Mechanism', 'Defect Location', 'Defect Length [mm]',
        'Remaining Wall [mm]', 'Design Life [years]', 'Design Factor',
        'Prowrap CF Cloth Width [mm]', 'Wall Loss [%]',
        'Required Structural Thickness [mm]', 'Installed Plies',
        'Total Repair Length [mm]', 'Cloth Band Count',
        'Procurement Axial Length [mm]', 'Fabric Area [m2]',
        'Epoxy Mass [kg]',
    )
    assert COST_TABLE_HEADERS == COST_SOURCE_HEADERS + ('Cost', 'Price')


def test_cost_formulas_use_absolute_inputs_and_relative_rows():
    assert cost_formula(COST_FIRST_DATA_ROW) == (
        '=IF(OR($B$3="",$E$3="",S6="",T6=""),"",'
        'S6*$B$3+T6*$E$3)'
    )
    assert price_formula(COST_FIRST_DATA_ROW) == (
        '=IF(OR(U6="",$H$3=""),"",U6*$H$3)'
    )


class _FormulaCell:
    def __init__(self, row, column, value):
        self.row = row
        self.column = column
        self.value = value


def test_only_exact_controlled_cost_formulas_are_allowed():
    assert is_allowed_cost_formula(_FormulaCell(6, 21, cost_formula(6))) is True
    assert is_allowed_cost_formula(_FormulaCell(6, 22, price_formula(6))) is True
    assert is_allowed_cost_formula(_FormulaCell(6, 21, '=1+1')) is False
    assert is_allowed_cost_formula(_FormulaCell(5, 21, cost_formula(5))) is False
    assert is_allowed_cost_formula(
        _FormulaCell(COST_LAST_DATA_ROW + 1, 22, price_formula(COST_LAST_DATA_ROW + 1)),
    ) is False
