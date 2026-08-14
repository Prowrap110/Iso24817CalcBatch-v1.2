import pytest

from engine.prowrap_calculations import calculate_repair
from tests.helpers import valid_engine_inputs


def test_zero_pressure_type_b_returns_three_ply_review_warning():
    result = calculate_repair(**valid_engine_inputs(
        pressure=0.0, defect_type='Leak', defect_loc='External'
    ))
    assert result['num_plies'] == 3
    assert any('zero design pressure' in warning.lower()
               for warning in result['compliance_warnings'])


@pytest.mark.parametrize(('field', 'value'), [
    ('defect_type', 'Erosion'),
    ('defect_loc', 'Outside'),
    ('axial_load_case', 2),
])
def test_invalid_route_enumeration_is_rejected(field, value):
    with pytest.raises(ValueError, match='Unsupported'):
        calculate_repair(**valid_engine_inputs(**{field: value}))


def test_type_b_life_warning_uses_two_year_limit():
    result = calculate_repair(**valid_engine_inputs(defect_type='Leak'))
    assert any('2 years' in warning for warning in result['compliance_warnings'])
