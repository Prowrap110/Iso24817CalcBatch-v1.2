"""Controlled commercial worksheet contract for PROWRAP batch workbooks."""

from batch_schema import INPUT_HEADERS, MAX_ROWS, OUTPUT_HEADERS


COST_INPUTS = (
    ('B3', 'CF Cost / m2'),
    ('E3', 'Epoxy Cost / kg'),
    ('H3', 'Price Multiplier'),
)

# Preserve the requested A:I, K, L, R, AC, AJ, AK, AR:AV source order while
# tying every heading to the canonical batch workbook schema.
COST_SOURCE_HEADERS = (
    INPUT_HEADERS[:9]
    + INPUT_HEADERS[10:12]
    + (INPUT_HEADERS[17],)
    + tuple(
        OUTPUT_HEADERS[index]
        for index in (10, 17, 18, 25, 26, 27, 28, 29)
    )
)
COST_TABLE_HEADERS = COST_SOURCE_HEADERS + ('Cost', 'Price')

COST_TABLE_HEADER_ROW = 5
COST_FIRST_DATA_ROW = 6
COST_LAST_DATA_ROW = COST_FIRST_DATA_ROW + MAX_ROWS - 1


def cost_formula(row: int) -> str:
    """Return the exact controlled material-cost formula for ``row``."""
    return (
        f'=IF(OR($B$3="",$E$3="",S{row}="",T{row}=""),"",'
        f'S{row}*$B$3+T{row}*$E$3)'
    )


def price_formula(row: int) -> str:
    """Return the exact controlled price formula for ``row``."""
    return f'=IF(OR(U{row}="",$H$3=""),"",U{row}*$H$3)'


def is_allowed_cost_formula(cell) -> bool:
    """Return whether ``cell`` contains an exact app-generated cost formula."""
    if not (COST_FIRST_DATA_ROW <= cell.row <= COST_LAST_DATA_ROW):
        return False
    if cell.column == 21:
        return cell.value == cost_formula(cell.row)
    if cell.column == 22:
        return cell.value == price_formula(cell.row)
    return False
