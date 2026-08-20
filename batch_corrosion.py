"""Link validated external-corrosion detail rows to their repair rows."""

from collections import defaultdict
from dataclasses import dataclass

from batch_schema import (
    ValidatedIndividualDefectRow,
    ValidatedRow,
    ValidationIssue,
)
from engine.corrosion_defects import ENTER_MANUALLY, IndividualCorrosionDefect


@dataclass(frozen=True)
class ManualGroupLinks:
    defects_by_main_excel_row: dict[int, tuple[IndividualCorrosionDefect, ...]]
    detail_rows_by_main_excel_row: dict[int, tuple[ValidatedIndividualDefectRow, ...]]
    main_issues: dict[int, tuple[ValidationIssue, ...]]
    detail_issues: dict[int, tuple[ValidationIssue, ...]]


def link_manual_groups(
    main_rows: tuple[ValidatedRow, ...],
    detail_rows: tuple[ValidatedIndividualDefectRow, ...],
    detail_issues: dict[int, tuple[ValidationIssue, ...]],
) -> ManualGroupLinks:
    """Link exact trimmed IDs, retain worksheet order, and localize ambiguity."""
    mutable_main_issues: dict[int, list[ValidationIssue]] = defaultdict(list)
    mutable_detail_issues = {
        row_number: list(issues)
        for row_number, issues in detail_issues.items()
    }
    mains_by_group: dict[str, list[ValidatedRow]] = defaultdict(list)
    for main_row in main_rows:
        if main_row.values.get('Defect Length Basis') == ENTER_MANUALLY:
            mains_by_group[main_row.values['Repair Group ID']].append(main_row)

    for group_id, grouped_mains in mains_by_group.items():
        if len(grouped_mains) > 1:
            for main_row in grouped_mains:
                _append_issue(
                    mutable_main_issues,
                    main_row.source_excel_row,
                    'DUPLICATE_REPAIR_GROUP',
                    f'Repair Group ID {group_id!r} is used by more than one manual main row.',
                )

    rows_by_main_row: dict[int, list[ValidatedIndividualDefectRow]] = defaultdict(list)
    for detail_row in detail_rows:
        grouped_mains = mains_by_group.get(detail_row.repair_group_id, [])
        if not grouped_mains:
            _append_issue(
                mutable_detail_issues,
                detail_row.source_excel_row,
                'ORPHAN_REPAIR_GROUP',
                f'Repair Group ID {detail_row.repair_group_id!r} does not link to a manual main row.',
            )
            continue
        if len(grouped_mains) > 1:
            _append_issue(
                mutable_detail_issues,
                detail_row.source_excel_row,
                'AMBIGUOUS_REPAIR_GROUP',
                f'Repair Group ID {detail_row.repair_group_id!r} links to multiple manual main rows.',
            )
            continue
        rows_by_main_row[grouped_mains[0].source_excel_row].append(detail_row)

    defects_by_main_excel_row: dict[int, tuple[IndividualCorrosionDefect, ...]] = {}
    detail_rows_by_main_excel_row: dict[int, tuple[ValidatedIndividualDefectRow, ...]] = {}
    for group_id, grouped_mains in mains_by_group.items():
        if len(grouped_mains) != 1:
            continue
        main_row = grouped_mains[0]
        main_excel_row = main_row.source_excel_row
        linked_rows = rows_by_main_row[main_excel_row]
        detail_rows_by_main_excel_row[main_excel_row] = tuple(linked_rows)
        if not linked_rows:
            _append_issue(
                mutable_main_issues,
                main_excel_row,
                'MISSING_INDIVIDUAL_DEFECTS',
                f'Repair Group ID {group_id!r} has no complete individual defect rows.',
            )
            defects_by_main_excel_row[main_excel_row] = ()
            continue

        _validate_unique_defect_ids(linked_rows, mutable_detail_issues)
        _validate_linked_bounds(main_row, linked_rows, mutable_detail_issues)

        valid_rows = tuple(
            detail_row for detail_row in linked_rows
            if not mutable_detail_issues.get(detail_row.source_excel_row)
        )
        defects_by_main_excel_row[main_excel_row] = tuple(
            IndividualCorrosionDefect(
                defect_id=detail_row.defect_id,
                longitudinal_length_mm=detail_row.longitudinal_length_mm,
                remaining_wall_mm=detail_row.remaining_wall_mm,
                separation_exceeds_3t=True,
            )
            for detail_row in valid_rows
        )
        if len(valid_rows) != len(linked_rows):
            _append_issue(
                mutable_main_issues,
                main_excel_row,
                'INVALID_INDIVIDUAL_DEFECTS',
                f'Repair Group ID {group_id!r} contains invalid individual defect rows.',
            )

    return ManualGroupLinks(
        defects_by_main_excel_row=defects_by_main_excel_row,
        detail_rows_by_main_excel_row=detail_rows_by_main_excel_row,
        main_issues={row: tuple(issues) for row, issues in mutable_main_issues.items()},
        detail_issues={row: tuple(issues) for row, issues in mutable_detail_issues.items()},
    )


def _validate_unique_defect_ids(
    detail_rows: list[ValidatedIndividualDefectRow],
    detail_issues: dict[int, list[ValidationIssue]],
) -> None:
    rows_by_defect_id: dict[str, list[ValidatedIndividualDefectRow]] = defaultdict(list)
    for detail_row in detail_rows:
        rows_by_defect_id[detail_row.defect_id].append(detail_row)
    for defect_id, duplicate_rows in rows_by_defect_id.items():
        if len(duplicate_rows) > 1:
            for detail_row in duplicate_rows:
                _append_issue(
                    detail_issues,
                    detail_row.source_excel_row,
                    'DUPLICATE_DEFECT_ID',
                    f'Defect ID {defect_id!r} is duplicated within Repair Group ID {detail_row.repair_group_id!r}.',
                )


def _validate_linked_bounds(
    main_row: ValidatedRow,
    detail_rows: list[ValidatedIndividualDefectRow],
    detail_issues: dict[int, list[ValidationIssue]],
) -> None:
    repair_zone_length = main_row.values['Defect Length [mm]']
    nominal_wall = main_row.values['Nominal Wall [mm]']
    for detail_row in detail_rows:
        if detail_row.longitudinal_length_mm > repair_zone_length:
            _append_issue(
                detail_issues,
                detail_row.source_excel_row,
                'OUT_OF_RANGE',
                'Individual longitudinal length [mm]: cannot exceed linked Defect Length [mm].',
            )
        if detail_row.remaining_wall_mm > nominal_wall:
            _append_issue(
                detail_issues,
                detail_row.source_excel_row,
                'OUT_OF_RANGE',
                'Remaining wall [mm]: cannot exceed linked Nominal Wall [mm].',
            )


def _append_issue(
    issues_by_row: dict[int, list[ValidationIssue]],
    row_number: int,
    code: str,
    message: str,
) -> None:
    issue = ValidationIssue(code=code, message=message)
    existing = issues_by_row.setdefault(row_number, [])
    if issue not in existing:
        existing.append(issue)
