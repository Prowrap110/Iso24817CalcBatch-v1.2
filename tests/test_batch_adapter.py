import pytest

from batch_adapter import calculate_row
from tests.helpers import batch_info, validated_row


def test_adapter_applies_common_info_and_matches_baseline():
    outcome = calculate_row(batch_info(), validated_row())

    assert outcome.status.value == 'OK'
    assert outcome.outputs['Installed Plies'] == 3
    assert outcome.outputs['Installed Thickness [mm]'] == 2.49
    assert outcome.outputs['Total Repair Length [mm]'] == pytest.approx(388.934, rel=1e-3)


def test_not_repairable_blanks_installable_quantities():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Mechanism': 'Leak',
        'Design Pressure [bar]': 100.0,
    }))

    assert outcome.status.value == 'NOT REPAIRABLE'
    for heading in (
        'Installed Plies',
        'Installed Thickness [mm]',
        'Fabric Area [m2]',
        'Epoxy Mass [kg]',
    ):
        assert outcome.outputs[heading] is None


def test_unapproved_cloth_width_calculates_but_requires_review():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Prowrap CF Cloth Width [mm]': 250.0,
    }))

    assert outcome.status.value == 'REVIEW REQUIRED'
    assert outcome.outputs['Installed Plies'] == 3
    assert any('250' in warning and 'approval' in warning.lower()
               for warning in outcome.outputs['Compliance Warnings'])


def test_expected_engine_value_error_becomes_input_error():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Operating Temperature [degC]': 150.0,
    }))

    assert outcome.status.value == 'INPUT ERROR'
    assert outcome.error_message == 'Operating temperature (150.0 degC) exceeds Prowrap limit of 58.18 degC.'
