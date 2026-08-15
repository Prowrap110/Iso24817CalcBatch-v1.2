import pytest

from batch_adapter import calculate_row
from batch_schema import ValidatedRow
from tests.helpers import batch_info, validated_row


def test_adapter_applies_common_info_and_matches_baseline():
    outcome = calculate_row(batch_info(), validated_row())

    assert outcome.status.value == 'OK'
    assert outcome.outputs['Installed Plies'] == 3
    assert outcome.outputs['Installed Thickness [mm]'] == 2.49
    assert outcome.outputs['Total Repair Length [mm]'] == pytest.approx(388.934, rel=1e-3)


def test_cracked_dent_reaches_engine_as_full_pressure_type_a():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Mechanism': 'Dent w/crack',
        'Remaining Wall [mm]': 9.53,
    }))

    assert outcome.status.value == 'OK'
    assert outcome.outputs['Effective Pipe Capacity [bar]'] == 0.0
    assert outcome.outputs['Composite Pressure Deficit [bar]'] == 50.0
    assert outcome.outputs['Installed Plies'] == 9
    detail = outcome.outputs['Type A Detail']
    assert set(detail) == {
        'calculation_basis',
        'allowable_pipe_stress_mpa',
        'substrate_allowable_pressure_mpa',
        'composite_pressure_deficit_mpa',
        'baseline_typea_design',
        'optional_class3_check',
    }
    assert detail['calculation_basis'] == (
        'Dent w/crack - full-pressure laminate'
    )
    assert detail['allowable_pipe_stress_mpa'] is None
    assert detail['substrate_allowable_pressure_mpa'] == 0.0
    assert detail['composite_pressure_deficit_mpa'] == 5.0
    assert detail['baseline_typea_design']['substrate_pressure_mpa'] == 0.0
    assert detail['optional_class3_check'] is None


def test_uncracked_dent_reaches_engine_with_approved_substrate_credit():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Mechanism': 'Dent no-crack',
        'Remaining Wall [mm]': 9.53,
    }))

    assert outcome.status.value == 'OK'
    assert outcome.outputs['Effective Pipe Capacity [bar]'] == pytest.approx(
        107.75653543307088
    )
    assert outcome.outputs['Composite Pressure Deficit [bar]'] == 0.0
    assert outcome.outputs['Installed Plies'] == 3
    detail = outcome.outputs['Type A Detail']
    assert detail['calculation_basis'] == (
        'Dent no-crack - substrate load sharing'
    )
    assert detail['allowable_pipe_stress_mpa'] == pytest.approx(258.48)
    assert detail['substrate_allowable_pressure_mpa'] == pytest.approx(
        10.775653543307088
    )
    assert detail['composite_pressure_deficit_mpa'] == 0.0
    assert detail['baseline_typea_design']['substrate_pressure_mpa'] == (
        detail['substrate_allowable_pressure_mpa']
    )
    assert detail['optional_class3_check'] is None


def test_optional_class3_check_is_nested_without_replacing_baseline_audit():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Mechanism': 'Dent w/crack',
        'Remaining Wall [mm]': 9.53,
        'Run Type A / Class 3 Check': 'Yes',
    }))

    detail = outcome.outputs['Type A Detail']
    assert outcome.outputs['Type A / Class 3 Check Run'] is True
    assert detail['calculation_basis'] == (
        'Dent w/crack - full-pressure laminate'
    )
    assert detail['substrate_allowable_pressure_mpa'] == 0.0
    assert detail['composite_pressure_deficit_mpa'] == 5.0
    assert detail['baseline_typea_design']['substrate_pressure_mpa'] == 0.0
    assert detail['optional_class3_check'] is not None
    assert detail['optional_class3_check']['input_summary'][
        'substrate_allowable_pressure_bar'
    ] == 0.0


def test_direct_legacy_dent_caller_is_normalized_before_engine_invocation():
    canonical = validated_row(**{
        'Mechanism': 'Dent w/crack',
        'Remaining Wall [mm]': 9.53,
    })
    legacy = ValidatedRow(
        source_excel_row=canonical.source_excel_row,
        values={**canonical.values, 'Mechanism': ' Dent '},
    )

    outcome = calculate_row(batch_info(), legacy)

    assert outcome.status.value == 'OK'
    assert outcome.outputs['Installed Plies'] == 9
    assert outcome.outputs['Type A Detail']['calculation_basis'] == (
        'Dent w/crack - full-pressure laminate'
    )


def test_not_repairable_blanks_installable_quantities():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Mechanism': 'Leak',
        'Design Pressure [bar]': 150.0,
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
    assert outcome.outputs['Compliance Warnings'] == ('W018',)


def test_500_mm_cloth_is_approved_and_uses_its_entered_procurement_width():
    """Catches treating the approved 500 mm roll as a review-only configuration."""
    outcome = calculate_row(batch_info(), validated_row(**{
        'Prowrap CF Cloth Width [mm]': 500.0,
    }))

    assert outcome.status.value == 'OK'
    assert outcome.outputs['Compliance Warnings'] == ()
    assert outcome.outputs['Procurement Axial Length [mm]'] == 500.0


def test_temperature_above_qualification_limit_becomes_review_required():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Operating Temperature [degC]': 150.0,
    }))

    assert outcome.status.value == 'REVIEW REQUIRED'
    assert outcome.error_message == ''
    assert 'W001' in outcome.outputs['Compliance Warnings']


def test_zero_pressure_type_a_check_is_skipped_and_requires_review():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Design Pressure [bar]': 0.0,
        'Run Type A / Class 3 Check': 'Yes',
    }))

    assert outcome.status.value == 'REVIEW REQUIRED'
    assert outcome.outputs['Type A / Class 3 Check Run'] is False
    assert outcome.outputs['Compliance Warnings'] == ('W019',)
