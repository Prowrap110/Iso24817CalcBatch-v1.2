"""Canonical workbook contract for the PROWRAP batch calculator."""

from dataclasses import dataclass
from typing import Any


MAX_ROWS = 500
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
STITCH_OVERLAP_MM = 50.0
APPROVED_CLOTH_WIDTHS_MM = (300.0, 500.0)


INPUT_HEADERS = (
    'Pipe OD [mm]',
    'Nominal Wall [mm]',
    'Pipe Yield [MPa]',
    'Design Pressure [bar]',
    'Operating Temperature [degC]',
    'Mechanism',
    'Defect Location',
    'Defect Length [mm]',
    'Remaining Wall [mm]',
    'Internal Corrosion Rate [mm/year]',
    'Design Life [years]',
    'Design Factor',
    'Run Type A / Class 3 Check',
    'Installation Temperature [degC]',
    'Component Type',
    'Cyclic Derating Factor',
    'Axial Load Case',
    'Prowrap CF Cloth Width [mm]',
)


OUTPUT_HEADERS = (
    'Source Excel Row',
    'Calculation Status',
    'Error Code',
    'Error Message',
    'Compliance Warnings',
    'Batch Engine Version',
    'Source Engine Revision',
    'Processed At [UTC]',
    'Thickness Calculation Method',
    'Overlap Calculation Method',
    'Wall Loss [%]',
    'End-of-Life Remaining Wall [mm]',
    'No Substrate Capacity',
    'B31G Applicable',
    'B31G Acceptable',
    'Effective Pipe Capacity [bar]',
    'Composite Pressure Deficit [bar]',
    'Required Structural Thickness [mm]',
    'Installed Plies',
    'Installed Thickness [mm]',
    'Thin-Wall Thickness Check OK',
    'Type A / Class 3 Check Run',
    'Type A / Class 3 Controls',
    'Required Overlap [mm]',
    'Taper Length [mm]',
    'Total Repair Length [mm]',
    'Cloth Band Count',
    'Procurement Axial Length [mm]',
    'Fabric Area [m2]',
    'Epoxy Mass [kg]',
    'B31G Detail',
    'Type A Detail',
    'Type B Detail',
)


@dataclass(frozen=True)
class BatchInfo:
    customer: str
    project_location: str
    report_no: str


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class ValidatedRow:
    source_excel_row: int
    values: dict[str, Any]
