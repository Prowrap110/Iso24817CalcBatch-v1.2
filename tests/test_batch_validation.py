import math

import pytest

from batch_schema import BatchInfo
from batch_validation import validate_batch_info, validate_row
from tests.helpers import valid_row_values


def test_batch_info_normalizes_all_common_values():
    info, issues = validate_batch_info({
        'Customer': '  ACME  ',
        'Project Location': ' Station 4 ',
        'Report No': ' R-100 ',
    })

    assert info == BatchInfo('ACME', 'Station 4', 'R-100')
    assert issues == ()


def test_batch_info_requires_each_common_value_in_order():
    info, issues = validate_batch_info({
        'Customer': '  ',
        'Project Location': None,
        'Report No': '',
    })

    assert info is None
    assert [issue.code for issue in issues] == [
        'REQUIRED_VALUE',
        'REQUIRED_VALUE',
        'REQUIRED_VALUE',
    ]


def test_valid_row_normalizes_numeric_inputs_and_keeps_source_row():
    row, issues = validate_row(12, valid_row_values(**{
        'Pipe OD [mm]': '457.2',
        'Design Life [years]': '20',
    }))

    assert issues == ()
    assert row is not None
    assert row.source_excel_row == 12
    assert row.values['Pipe OD [mm]'] == 457.2
    assert row.values['Design Life [years]'] == 20


def test_remaining_wall_cannot_exceed_nominal_wall():
    row, issues = validate_row(2, valid_row_values(**{
        'Remaining Wall [mm]': 10.0,
    }))

    assert row is None
    assert [issue.code for issue in issues] == ['OUT_OF_RANGE']


@pytest.mark.parametrize(('header', 'value'), [
    ('Mechanism', 'Erosion'),
    ('Defect Location', 'Outside'),
    ('Run Type A / Class 3 Check', 'Maybe'),
    ('Component Type', 'Elbow'),
    ('Axial Load Case', 2),
])
def test_rejects_selection_outside_the_allowed_set(header, value):
    row, issues = validate_row(2, valid_row_values(**{header: value}))

    assert row is None
    assert [issue.code for issue in issues] == ['INVALID_SELECTION']


def test_formula_marker_is_rejected_before_other_validation():
    row, issues = validate_row(2, valid_row_values(**{
        'Pipe OD [mm]': '=A1',
    }))

    assert row is None
    assert [issue.code for issue in issues] == ['FORMULA_NOT_ALLOWED']


def test_internal_corrosion_requires_rate():
    values = valid_row_values(**{
        'Mechanism': 'Corrosion',
        'Defect Location': 'Internal',
        'Internal Corrosion Rate [mm/year]': None,
    })

    row, issues = validate_row(2, values)

    assert row is None
    assert [issue.code for issue in issues] == ['INTERNAL_CORROSION_RATE_REQUIRED']


def test_cloth_width_at_stitch_overlap_is_rejected():
    row, issues = validate_row(2, valid_row_values(**{
        'Prowrap CF Cloth Width [mm]': 50.0,
    }))

    assert row is None
    assert [issue.code for issue in issues] == ['OUT_OF_RANGE']


def test_unapproved_cloth_width_is_valid_for_later_review():
    row, issues = validate_row(2, valid_row_values(**{
        'Prowrap CF Cloth Width [mm]': 250.0,
    }))

    assert issues == ()
    assert row is not None
    assert row.values['Prowrap CF Cloth Width [mm]'] == 250.0


@pytest.mark.parametrize('value', [math.nan, math.inf, -math.inf, True])
def test_rejects_non_finite_or_boolean_numbers(value):
    row, issues = validate_row(2, valid_row_values(**{'Pipe OD [mm]': value}))

    assert row is None
    assert [issue.code for issue in issues] == ['INVALID_NUMBER']


def test_design_life_requires_a_whole_number_of_at_least_one_year():
    row, issues = validate_row(2, valid_row_values(**{
        'Design Life [years]': 1.5,
    }))

    assert row is None
    assert [issue.code for issue in issues] == ['OUT_OF_RANGE']


def test_issues_follow_input_column_order():
    row, issues = validate_row(2, valid_row_values(**{
        'Pipe OD [mm]': None,
        'Mechanism': 'Erosion',
        'Remaining Wall [mm]': 10.0,
    }))

    assert row is None
    assert [issue.code for issue in issues] == [
        'REQUIRED_VALUE',
        'INVALID_SELECTION',
        'OUT_OF_RANGE',
    ]
