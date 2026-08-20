from batch_schema import BatchInfo, INPUT_HEADERS, MAX_ROWS, OUTPUT_HEADERS


def test_row_inputs_begin_with_pipe_od_and_exclude_common_fields():
    assert INPUT_HEADERS[0] == 'Pipe OD [mm]'
    assert 'Customer' not in INPUT_HEADERS
    assert 'Project Location' not in INPUT_HEADERS
    assert 'Report No' not in INPUT_HEADERS
    assert MAX_ROWS == 500


def test_batch_info_holds_three_common_values():
    info = BatchInfo('ACME', 'Station 4', 'R-100')

    assert info.customer == 'ACME'
    assert info.project_location == 'Station 4'
    assert info.report_no == 'R-100'


def test_v12_inputs_insert_basis_and_group_after_defect_length():
    from batch_schema import MAX_DETAIL_ROWS

    start = INPUT_HEADERS.index('Defect Length [mm]')

    assert INPUT_HEADERS[start:start + 4] == (
        'Defect Length [mm]',
        'Defect Length Basis',
        'Repair Group ID',
        'Remaining Wall [mm]',
    )
    assert MAX_ROWS == 500
    assert MAX_DETAIL_ROWS == 2000


def test_current_outputs_keep_legacy_outputs_and_add_linked_corrosion_results():
    from batch_schema import LEGACY_OUTPUT_HEADERS

    assert OUTPUT_HEADERS[:len(LEGACY_OUTPUT_HEADERS)] == LEGACY_OUTPUT_HEADERS
    assert OUTPUT_HEADERS[-6:] == (
        'Repair Zone Length [mm]',
        '3t Interaction Threshold [mm]',
        'B31G Candidate Count',
        'Governing Defect ID',
        'Governing B31G Length [mm]',
        'Governing B31G Remaining Wall [mm]',
    )
