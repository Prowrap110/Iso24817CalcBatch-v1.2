from batch_corrosion import link_manual_groups
from engine.corrosion_defects import ENTER_MANUALLY
from tests.helpers import valid_detail_row, validated_row


def manual_main(excel_row, repair_group_id):
    row = validated_row(**{
        'Defect Length Basis': ENTER_MANUALLY,
        'Repair Group ID': repair_group_id,
        'Remaining Wall [mm]': None,
    })
    return row.__class__(source_excel_row=excel_row, values=row.values)


def test_linker_preserves_detail_order_and_reports_orphans():
    main = (manual_main(2, 'R-001'),)

    linked = link_manual_groups(
        main,
        (
            valid_detail_row(2, group='R-001', defect='D-02', length=35, wall=9.0),
            valid_detail_row(3, group='R-001', defect='D-01', length=10, wall=9.0),
            valid_detail_row(4, group='ORPHAN', defect='D-X', length=10, wall=9.0),
        ),
        detail_issues={},
    )

    assert [item.defect_id for item in linked.detail_rows_by_main_excel_row[2]] == [
        'D-02', 'D-01',
    ]
    assert [item.defect_id for item in linked.defects_by_main_excel_row[2]] == [
        'D-02', 'D-01',
    ]
    assert linked.detail_issues[4][0].code == 'ORPHAN_REPAIR_GROUP'


def test_duplicate_main_group_marks_both_main_rows_input_error():
    links = link_manual_groups(
        (manual_main(2, 'R-001'), manual_main(3, 'R-001')),
        (),
        {},
    )

    assert links.main_issues[2][0].code == 'DUPLICATE_REPAIR_GROUP'
    assert links.main_issues[3][0].code == 'DUPLICATE_REPAIR_GROUP'


def test_linker_rejects_detail_beyond_its_linked_main_span():
    links = link_manual_groups(
        (manual_main(2, 'R-001'),),
        (valid_detail_row(3, group='R-001', defect='D-01', length=101, wall=4.5),),
        {},
    )

    assert links.detail_issues[3][0].code == 'OUT_OF_RANGE'
    assert links.main_issues[2][0].code == 'INVALID_INDIVIDUAL_DEFECTS'


def test_duplicate_defect_ids_in_a_group_invalidate_the_linked_main_row():
    links = link_manual_groups(
        (manual_main(2, 'R-001'),),
        (
            valid_detail_row(3, group='R-001', defect='D-01', length=10, wall=4.5),
            valid_detail_row(4, group='R-001', defect='D-01', length=20, wall=4.5),
        ),
        {},
    )

    assert links.detail_issues[3][0].code == 'DUPLICATE_DEFECT_ID'
    assert links.detail_issues[4][0].code == 'DUPLICATE_DEFECT_ID'
    assert links.main_issues[2][0].code == 'INVALID_INDIVIDUAL_DEFECTS'
