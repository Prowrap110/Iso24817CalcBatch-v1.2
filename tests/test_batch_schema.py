from batch_schema import BatchInfo, INPUT_HEADERS, MAX_ROWS


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
