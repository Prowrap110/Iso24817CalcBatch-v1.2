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


def test_temperature_above_qualification_limit_becomes_review_required():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Operating Temperature [degC]': 150.0,
    }))

    assert outcome.status.value == 'REVIEW REQUIRED'
    assert outcome.error_message == ''
    assert any('150.0 degC exceeds the qualified Prowrap limit' in warning
               for warning in outcome.outputs['Compliance Warnings'])


def test_zero_pressure_type_a_check_is_skipped_and_requires_review():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Design Pressure [bar]': 0.0,
        'Run Type A / Class 3 Check': 'Yes',
    }))

    assert outcome.status.value == 'REVIEW REQUIRED'
    assert outcome.outputs['Type A / Class 3 Check Run'] is False
    assert any('zero design pressure' in warning.lower()
               for warning in outcome.outputs['Compliance Warnings'])
