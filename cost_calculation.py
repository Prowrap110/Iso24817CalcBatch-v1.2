"""Controlled commercial worksheet contract for PROWRAP batch workbooks."""

from batch_schema import MAX_ROWS


COST_INPUTS = (
    ('B3', 'CF Cost / m2'),
    ('E3', 'Epoxy Cost / kg'),
    ('H3', 'Price Multiplier'),
)

# These are semantic source names, deliberately independent of the insertion
# points in the v1.2 main input and output schemas.
COST_SOURCE_HEADERS = (
    'Pipe OD [mm]',
    'Nominal Wall [mm]',
    'Pipe Yield [MPa]',
    'Design Pressure [bar]',
    'Operating Temperature [degC]',
    'Mechanism',
    'Defect Location',
    'Defect Length [mm]',
    'Remaining Wall [mm]',
    'Design Life [years]',
    'Design Factor',
    'Prowrap CF Cloth Width [mm]',
    'Wall Loss [%]',
    'Required Structural Thickness [mm]',
    'Installed Plies',
    'Total Repair Length [mm]',
    'Cloth Band Count',
    'Procurement Axial Length [mm]',
    'Fabric Area [m2]',
    'Epoxy Mass [kg]',
)
COST_TABLE_HEADERS = COST_SOURCE_HEADERS + ('Cost', 'Price', 'Quantity', 'Total Amount')

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


def total_amount_formula(row: int) -> str:
    """Return the exact controlled quantity-based total formula for ``row``."""
    return f'=IF(OR(V{row}="",W{row}=""),"",V{row}*W{row})'


def is_allowed_cost_formula(cell) -> bool:
    """Return whether ``cell`` contains an exact app-generated cost formula."""
    if not (COST_FIRST_DATA_ROW <= cell.row <= COST_LAST_DATA_ROW):
        return False
    if cell.column == 21:
        return cell.value == cost_formula(cell.row)
    if cell.column == 22:
        return cell.value == price_formula(cell.row)
    if cell.column == 24:
        return cell.value == total_amount_formula(cell.row)
    return False
