"""Read, validate, calculate, and return controlled PROWRAP batch workbooks."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
import json
import logging
from pathlib import Path, PurePosixPath
import zipfile
from xml.etree.ElementTree import ParseError

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

try:  # openpyxl uses lxml when it is available.
    from lxml.etree import XMLSyntaxError
except ImportError:  # pragma: no cover - exercised where lxml is unavailable.
    XMLSyntaxError = ParseError

from batch_adapter import RowCalculation, calculate_row
from batch_schema import (
    INPUT_HEADERS,
    MAX_ROWS,
    MAX_UPLOAD_BYTES,
    OUTPUT_HEADERS,
    BatchInfo,
    ValidationIssue,
)
from batch_status import CalculationStatus
from batch_validation import validate_batch_info, validate_row
from workbook_template import create_template_workbook


BATCH_ENGINE_VERSION = '1.0.0'
SOURCE_ENGINE_REVISION = '68e5409'
_COMMON_HEADERS = ('Customer', 'Project Location', 'Report No')
_REQUIRED_SHEETS = (
    'Batch Information',
    'Batch Input & Results',
    'Summary',
    'Instructions',
    'Lists',
)
_PREVIEW_LIMIT = 20
_MAX_ZIP_ENTRIES = 250
_MAX_ZIP_UNCOMPRESSED_BYTES = 25 * 1024 * 1024
_MAX_ZIP_ENTRY_BYTES = 16 * 1024 * 1024
_MAX_ZIP_COMPRESSION_RATIO = 100

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkbookInspection:
    """Workbook-level validation outcome and a concise row preview."""

    batch_info: BatchInfo | None
    populated_rows: int
    valid_rows: int
    invalid_rows: int
    workbook_errors: tuple[ValidationIssue, ...]
    preview: tuple[dict[str, object], ...]
    recognized_input_headers: tuple[str, ...]
    missing_input_headers: tuple[str, ...]
    unexpected_headers: tuple[str, ...]


@dataclass(frozen=True)
class ProcessedBatch:
    """A new in-memory workbook and the row-level status totals it contains."""

    workbook_bytes: bytes
    status_counts: dict[str, int]
    populated_rows: int


class WorkbookProcessingError(ValueError):
    """Raised only when the controlled workbook itself cannot be processed."""

    def __init__(self, issues: tuple[ValidationIssue, ...]):
        self.issues = issues
        super().__init__('; '.join(issue.message for issue in issues))


def inspect_workbook(data: bytes) -> WorkbookInspection:
    """Validate a controlled upload and preview the final row classifications."""
    workbook, errors = _load_controlled_workbook(data)
    if errors:
        return _empty_inspection(errors)

    assert workbook is not None
    header_summary = _input_header_summary(workbook)
    structure_errors = _validate_structure(workbook)
    if structure_errors:
        return _empty_inspection(structure_errors, header_summary)

    info_sheet = workbook['Batch Information']
    common_values = {
        header: info_sheet.cell(row, 2).value
        for row, header in enumerate(_COMMON_HEADERS, start=3)
    }
    formula_errors = _formula_errors(workbook)
    if formula_errors:
        return _empty_inspection(formula_errors, header_summary)

    batch_info, batch_issues = validate_batch_info(common_values)
    data_sheet = workbook['Batch Input & Results']
    populated = _populated_rows(data_sheet)
    row_limit_errors = (
        (_issue('TOO_MANY_ROWS', f'No more than {MAX_ROWS} populated defect rows are allowed.'),)
        if len(populated) > MAX_ROWS else ()
    )

    valid_rows = 0
    invalid_rows = 0
    preview: list[dict[str, object]] = []
    for excel_row, values in populated:
        _, issues = validate_row(excel_row, values)
        if issues:
            invalid_rows += 1
            status = CalculationStatus.INPUT_ERROR.value
            error_code = _issue_codes(issues)
            error_message = _issue_message(issues)
        elif batch_info is None:
            valid_rows += 1
            status = 'READY'
            error_code = ''
            error_message = ''
        else:
            valid_rows += 1
            calculation = _calculate_one(batch_info, excel_row, values)
            status = calculation.status.value
            error_code = calculation.error_code
            error_message = calculation.error_message
        if len(preview) < _PREVIEW_LIMIT:
            preview.append({
                'Source Excel Row': excel_row,
                'Pipe OD [mm]': values['Pipe OD [mm]'],
                'Mechanism': values['Mechanism'],
                'Defect Location': values['Defect Location'],
                'Calculation Status': status,
                'Error Code': error_code,
                'Error Message': error_message,
            })

    return WorkbookInspection(
        batch_info=batch_info,
        populated_rows=len(populated),
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        workbook_errors=tuple(batch_issues) + row_limit_errors,
        preview=tuple(preview),
        recognized_input_headers=header_summary[0],
        missing_input_headers=header_summary[1],
        unexpected_headers=header_summary[2],
    )


def process_workbook(
    data: bytes,
    processed_at: datetime,
    source_name: str | None = None,
) -> ProcessedBatch:
    """Return a new workbook with calculation results appended to each populated row."""
    inspection = inspect_workbook(data)
    if inspection.workbook_errors:
        raise WorkbookProcessingError(inspection.workbook_errors)
    assert inspection.batch_info is not None

    workbook, load_errors = _load_controlled_workbook(data)
    if load_errors or workbook is None:  # Defensive: bytes were just inspected.
        raise WorkbookProcessingError(load_errors)

    output_workbook = load_workbook(BytesIO(create_template_workbook()), data_only=False)
    _copy_controlled_inputs(workbook, output_workbook)
    data_sheet = output_workbook['Batch Input & Results']
    status_counts: Counter[str] = Counter()
    processed_timestamp = _utc_timestamp(processed_at)
    for excel_row, values in _populated_rows(data_sheet):
        calculation = _calculate_one(inspection.batch_info, excel_row, values)
        _write_result_row(data_sheet, excel_row, calculation, processed_timestamp)
        status_counts[calculation.status.value] += 1

    _write_summary(
        output_workbook,
        inspection.batch_info,
        processed_timestamp,
        inspection.populated_rows,
        status_counts,
        _sanitized_source_name(source_name),
    )
    output = BytesIO()
    output_workbook.save(output)
    return ProcessedBatch(
        workbook_bytes=output.getvalue(),
        status_counts=dict(status_counts),
        populated_rows=inspection.populated_rows,
    )


def _load_controlled_workbook(data: bytes):
    if len(data) > MAX_UPLOAD_BYTES:
        return None, (_issue('FILE_TOO_LARGE', 'The uploaded workbook exceeds the 10 MB limit.'),)
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            safety_errors = _zip_safety_errors(archive)
            if safety_errors:
                return None, safety_errors
            for entry in archive.infolist():
                if entry.flag_bits & 0x1:
                    return None, (_issue('UNREADABLE_WORKBOOK', 'Password-protected workbooks are not supported.'),)
                if PurePosixPath(entry.filename).name.lower() == 'vbaproject.bin':
                    return None, (_issue('MACROS_NOT_ALLOWED', 'Macro-enabled workbooks are not supported.'),)
        return load_workbook(BytesIO(data), data_only=False, keep_vba=False), ()
    except (
        InvalidFileException,
        KeyError,
        OSError,
        ValueError,
        zipfile.BadZipFile,
        ParseError,
        XMLSyntaxError,
    ):
        return None, (_issue('UNREADABLE_WORKBOOK', 'The uploaded file is not a readable .xlsx workbook.'),)


def _validate_structure(workbook) -> tuple[ValidationIssue, ...]:
    missing = [sheet for sheet in _REQUIRED_SHEETS if sheet not in workbook.sheetnames]
    if missing:
        return (_issue('MISSING_WORKSHEET', f'Missing required worksheet: {missing[0]}.'),)
    extras = [sheet for sheet in workbook.sheetnames if sheet not in _REQUIRED_SHEETS]
    if extras:
        return (_issue('UNEXPECTED_WORKSHEET', f'Unexpected worksheet: {extras[0]}.'),)
    if tuple(workbook.sheetnames) != _REQUIRED_SHEETS:
        return (_issue('INVALID_WORKSHEET_ORDER', 'Worksheets do not match the controlled template order.'),)

    info_sheet = workbook['Batch Information']
    common_headers = tuple(info_sheet.cell(row, 1).value for row in range(3, 6))
    if common_headers != _COMMON_HEADERS:
        return (_issue(
            'INVALID_BATCH_INFORMATION_LABELS',
            'Batch Information must contain Customer, Project Location, and Report No labels.',
        ),)

    headings = tuple(cell.value for cell in workbook['Batch Input & Results'][1])
    expected = INPUT_HEADERS + OUTPUT_HEADERS
    duplicate = _first_duplicate(headings)
    if duplicate:
        return (_issue('DUPLICATE_INPUT_HEADER', f'Duplicate workbook heading: {duplicate}.'),)
    if headings != expected:
        return (_issue('INVALID_INPUT_HEADERS', 'Batch Input & Results headings do not match the controlled template.'),)
    return ()


def _input_header_summary(workbook) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Return user-facing input-header recognition details without relaxing validation."""
    if 'Batch Input & Results' not in workbook.sheetnames:
        return (), (), ()

    headings = tuple(cell.value for cell in workbook['Batch Input & Results'][1])
    expected = INPUT_HEADERS + OUTPUT_HEADERS
    recognized = tuple(header for header in INPUT_HEADERS if header in headings)
    missing = tuple(header for header in INPUT_HEADERS if header not in headings)
    unexpected = tuple(
        _display_heading(heading) for heading in headings if heading not in expected
    )
    return recognized, missing, unexpected


def _formula_errors(workbook) -> tuple[ValidationIssue, ...]:
    for worksheet in workbook.worksheets:
        for row in worksheet.iter_rows():
            for cell in row:
                if _is_formula_cell(cell):
                    return (_issue(
                        'FORMULA_NOT_ALLOWED',
                        f'Formula cells are not allowed: {worksheet.title}!{cell.coordinate}.',
                    ),)
    return ()


def _populated_rows(worksheet) -> list[tuple[int, dict[str, object]]]:
    populated: list[tuple[int, dict[str, object]]] = []
    for excel_row in range(2, worksheet.max_row + 1):
        values = {
            header: worksheet.cell(excel_row, column).value
            for column, header in enumerate(INPUT_HEADERS, start=1)
        }
        if any(not _is_blank(value) for value in values.values()):
            populated.append((excel_row, values))
    return populated


def _calculate_one(
    batch_info: BatchInfo,
    excel_row: int,
    values: dict[str, object],
) -> RowCalculation:
    row, issues = validate_row(excel_row, values)
    if issues:
        return RowCalculation(
            source_excel_row=excel_row,
            status=CalculationStatus.INPUT_ERROR,
            outputs={},
            error_code=_issue_codes(issues),
            error_message=_issue_message(issues),
        )
    assert row is not None
    try:
        return calculate_row(batch_info, row)
    except Exception:
        logger.exception('Unexpected calculation exception for source Excel row %s', excel_row)
        return RowCalculation(
            source_excel_row=excel_row,
            status=CalculationStatus.SYSTEM_ERROR,
            outputs={},
            error_code='SYSTEM_ERROR',
            error_message='Unexpected calculation error. Please contact PROTAP.',
        )


def _write_result_row(worksheet, excel_row: int, calculation: RowCalculation, timestamp: str) -> None:
    outputs = {
        'Source Excel Row': calculation.source_excel_row,
        'Calculation Status': calculation.status.value,
        'Error Code': calculation.error_code,
        'Error Message': calculation.error_message,
        'Batch Engine Version': BATCH_ENGINE_VERSION,
        'Source Engine Revision': SOURCE_ENGINE_REVISION,
        'Processed At [UTC]': timestamp,
        **calculation.outputs,
    }
    for column, heading in enumerate(OUTPUT_HEADERS, start=len(INPUT_HEADERS) + 1):
        worksheet.cell(excel_row, column).value = _output_value(heading, outputs.get(heading))


def _write_summary(
    workbook,
    batch_info: BatchInfo,
    timestamp: str,
    populated_rows: int,
    status_counts: Counter[str],
    source_name: str,
) -> None:
    summary = workbook['Summary']
    summary['B3'] = batch_info.customer
    summary['B4'] = batch_info.project_location
    summary['B5'] = batch_info.report_no
    summary['B7'] = source_name
    summary['B8'] = timestamp
    summary['B10'] = populated_rows
    for row, status in enumerate(CalculationStatus, start=13):
        summary.cell(row, 2).value = status_counts.get(status.value, 0)

    rows = _result_rows(workbook['Batch Input & Results'])
    methods = [row['Thickness Calculation Method'] for row in rows]
    summary['B19'] = sum(_is_type_a(method) for method in methods)
    summary['B20'] = sum(_is_type_b(method) for method in methods)
    summary['B21'] = sum(bool(row['Compliance Warnings']) for row in rows)
    summary['B22'] = sum(
        row['Calculation Status'] in {
            CalculationStatus.REVIEW_REQUIRED.value,
            CalculationStatus.NOT_REPAIRABLE.value,
        }
        for row in rows
    )
    summary['B24'] = BATCH_ENGINE_VERSION
    summary['B25'] = SOURCE_ENGINE_REVISION


def _result_rows(worksheet) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for excel_row, _ in _populated_rows(worksheet):
        results.append({
            header: worksheet.cell(excel_row, column).value
            for column, header in enumerate(OUTPUT_HEADERS, start=len(INPUT_HEADERS) + 1)
        })
    return results


def _output_value(heading: str, value: object) -> object:
    if value is None:
        return None
    if heading in {'B31G Detail', 'Type A Detail', 'Type B Detail'}:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str)
    if heading == 'Compliance Warnings' and isinstance(value, (tuple, list)):
        return '\n'.join(str(item) for item in value)
    return value


def _utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _empty_inspection(
    errors: tuple[ValidationIssue, ...],
    header_summary: tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]] = ((), (), ()),
) -> WorkbookInspection:
    return WorkbookInspection(None, 0, 0, 0, errors, (), *header_summary)


def _issue(code: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, message=message)


def _issue_codes(issues: tuple[ValidationIssue, ...]) -> str:
    return '; '.join(issue.code for issue in issues)


def _issue_message(issues: tuple[ValidationIssue, ...]) -> str:
    return ' '.join(issue.message for issue in issues)


def _first_duplicate(values: tuple[object, ...]) -> object | None:
    seen: set[object] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None


def _display_heading(value: object) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        return '(blank)'
    return str(value)


def _is_blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _is_formula(value: object) -> bool:
    return isinstance(value, str) and value.lstrip().startswith('=')


def _is_formula_cell(cell) -> bool:
    return cell.data_type == 'f' or _is_formula(cell.value)


def _zip_safety_errors(archive: zipfile.ZipFile) -> tuple[ValidationIssue, ...]:
    entries = archive.infolist()
    if len(entries) > _MAX_ZIP_ENTRIES:
        return (_issue('UNREADABLE_WORKBOOK', 'The uploaded workbook has too many compressed entries.'),)
    total_uncompressed = 0
    for entry in entries:
        if entry.file_size > _MAX_ZIP_ENTRY_BYTES:
            return (_issue('UNREADABLE_WORKBOOK', 'The uploaded workbook has an oversized compressed entry.'),)
        total_uncompressed += entry.file_size
        if total_uncompressed > _MAX_ZIP_UNCOMPRESSED_BYTES:
            return (_issue('UNREADABLE_WORKBOOK', 'The uploaded workbook expands beyond the safe processing limit.'),)
        if (
            entry.file_size > 0
            and entry.compress_size > 0
            and entry.file_size / entry.compress_size > _MAX_ZIP_COMPRESSION_RATIO
        ):
            return (_issue('UNREADABLE_WORKBOOK', 'The uploaded workbook has a suspicious compression ratio.'),)
    return ()


def _copy_controlled_inputs(source_workbook, output_workbook) -> None:
    source_info = source_workbook['Batch Information']
    output_info = output_workbook['Batch Information']
    for row in range(3, 6):
        output_info.cell(row, 2).value = source_info.cell(row, 2).value

    source_data = source_workbook['Batch Input & Results']
    output_data = output_workbook['Batch Input & Results']
    for excel_row in range(2, MAX_ROWS + 2):
        for column in range(1, len(INPUT_HEADERS) + 1):
            output_data.cell(excel_row, column).value = source_data.cell(excel_row, column).value


def _sanitized_source_name(source_name: str | None) -> str:
    if not source_name:
        return 'PROWRAP Batch Results Workbook'
    filename = Path(str(source_name).replace('\\', '/')).name
    clean = ''.join(character for character in filename if character.isprintable()).strip()
    return clean or 'PROWRAP Batch Results Workbook'


def _is_type_a(method: object) -> bool:
    return isinstance(method, str) and 'type a' in method.lower()


def _is_type_b(method: object) -> bool:
    return isinstance(method, str) and 'type b' in method.lower()
