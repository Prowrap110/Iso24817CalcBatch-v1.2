import pytest

from engine.corrosion_defects import (
    ACTUAL_DEFECT_LENGTH,
    ENTER_MANUALLY,
    INDEPENDENT_DEFECTS,
    IndividualCorrosionDefect,
)
from engine.prowrap_calculations import calculate_repair
from tests.helpers import valid_engine_inputs


def test_three_modes_match_verified_v12_and_keep_the_full_repair_zone():
    base = dict(
        customer="PROTAP", location="Turkey", report_no="BATCH-V12",
        od=1016.0, wall=12.0, pressure=104.9, temp=40.0,
        defect_type="Corrosion", defect_loc="External", length=1000.0,
        rem_wall=9.652, yield_strength=450.0, design_factor=0.72,
        design_life=20, cloth_width_mm=500.0,
        allow_unqualified_temperature=True,
    )
    actual = calculate_repair(**base, defect_length_basis=ACTUAL_DEFECT_LENGTH)
    independent = calculate_repair(**base, defect_length_basis=INDEPENDENT_DEFECTS)
    manual = calculate_repair(
        **base,
        defect_length_basis=ENTER_MANUALLY,
        individual_defects=(
            IndividualCorrosionDefect("D-01", 10.0, 9.652, True),
            IndividualCorrosionDefect("D-02", 35.0, 10.0, True),
        ),
    )
    assert actual["p_steel_capacity"] == pytest.approx(7.571542406120033)
    assert independent["p_steel_capacity"] == pytest.approx(8.82257484144555)
    assert manual["p_steel_capacity"] == pytest.approx(8.783461911867068)
    assert (actual["num_plies"], independent["num_plies"], manual["num_plies"]) == (12, 7, 7)
    assert manual["governing_defect_id"] == "D-02"
    assert manual["governing_b31g_length_mm"] == 35.0
    for result in (actual, independent, manual):
        covered = result["iso_length"] - 2 * result["overlap_length"] - 2 * result["taper_length"]
        assert covered == pytest.approx(1000.0)


def test_actual_default_preserves_existing_batch_result():
    implicit = calculate_repair(**valid_engine_inputs())
    explicit = calculate_repair(
        **valid_engine_inputs(), defect_length_basis=ACTUAL_DEFECT_LENGTH,
    )
    assert explicit == implicit


def test_manual_never_pairs_length_and_wall_from_different_defects():
    result = calculate_repair(
        **valid_engine_inputs(wall=12.0, length=500.0),
        defect_length_basis=ENTER_MANUALLY,
        individual_defects=(
            IndividualCorrosionDefect("LONG", 300.0, 11.0, True),
            IndividualCorrosionDefect("DEEP", 10.0, 9.0, True),
        ),
    )
    pairs = {
        item["defect_id"]: (item["length_mm"], item["remaining_wall_mm"])
        for item in result["b31g_assessments"]
    }
    assert pairs == {"LONG": (300.0, 11.0), "DEEP": (10.0, 9.0)}


def test_nonexternal_corrosion_ignores_the_new_basis_route():
    baseline = calculate_repair(**valid_engine_inputs(defect_loc="Internal"))
    changed = calculate_repair(
        **valid_engine_inputs(defect_loc="Internal"),
        defect_length_basis=INDEPENDENT_DEFECTS,
    )
    assert changed == baseline


def test_high_smys_governing_assessment_retains_original_b31g_fallback():
    result = calculate_repair(**valid_engine_inputs(yield_strength=555.0))

    assert result["b31g_details"]["method"] == "original"
    assert result["calculation_basis"] == "ASME B31G-2023 Level 1 (Original)"
    assert any(
        "falling back to Original B31G" in warning
        for warning in result["compliance_warnings"]
    )


def test_nonapplicable_manual_candidate_removes_substrate_credit():
    result = calculate_repair(
        **valid_engine_inputs(wall=12.0, length=500.0, rem_wall=1.8),
        defect_length_basis=ENTER_MANUALLY,
        individual_defects=(
            IndividualCorrosionDefect("SOUND", 10.0, 8.0, True),
            IndividualCorrosionDefect("OUTSIDE-B31G", 10.0, 1.8, True),
        ),
    )
    assessments = {
        item["defect_id"]: item for item in result["b31g_assessments"]
    }

    assert assessments["OUTSIDE-B31G"]["assessment"]["applicable"] is False
    assert assessments["OUTSIDE-B31G"]["credited_pressure_mpa"] == 0.0
    assert result["governing_defect_id"] == "OUTSIDE-B31G"
    assert result["p_steel_capacity"] == 0.0
