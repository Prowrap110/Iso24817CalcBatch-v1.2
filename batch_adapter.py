"""Map one validated worksheet row to the isolated PROWRAP engine."""

from dataclasses import dataclass
from typing import Any

from batch_schema import APPROVED_CLOTH_WIDTHS_MM, BatchInfo, ValidatedRow
from batch_status import CalculationStatus, classify_result
from engine.prowrap_calculations import (
    apply_type_a_class3_result_to_repair,
    calculate_repair,
    calculate_type_a_class3_prowrap_check,
    substrate_credit_bar_for_iso_check,
)
from engine.prowrap_materials import PROWRAP
from warning_catalog import warning_codes


@dataclass(frozen=True)
class RowCalculation:
    source_excel_row: int
    status: CalculationStatus
    outputs: dict[str, object]
    error_code: str = ''
    error_message: str = ''


_INSTALLABLE_OUTPUTS = (
    'Required Structural Thickness [mm]',
    'Installed Plies',
    'Installed Thickness [mm]',
    'Thin-Wall Thickness Check OK',
    'Required Overlap [mm]',
    'Taper Length [mm]',
    'Total Repair Length [mm]',
    'Cloth Band Count',
    'Procurement Axial Length [mm]',
    'Fabric Area [m2]',
    'Epoxy Mass [kg]',
)


def calculate_row(batch_info: BatchInfo, row: ValidatedRow) -> RowCalculation:
    """Calculate a validated row without translating unexpected failures."""
    values = row.values
    try:
        result = calculate_repair(
            customer=batch_info.customer,
            location=batch_info.project_location,
            report_no=batch_info.report_no,
            od=values['Pipe OD [mm]'],
            wall=values['Nominal Wall [mm]'],
            yield_strength=values['Pipe Yield [MPa]'],
            pressure=values['Design Pressure [bar]'],
            temp=values['Operating Temperature [degC]'],
            defect_type=values['Mechanism'],
            defect_loc=values['Defect Location'],
            length=values['Defect Length [mm]'],
            rem_wall=values['Remaining Wall [mm]'],
            internal_corrosion_rate=values['Internal Corrosion Rate [mm/year]'] or 0.0,
            design_life=values['Design Life [years]'],
            design_factor=values['Design Factor'],
            installation_temp=values['Installation Temperature [degC]'],
            component_type=values['Component Type'],
            cyclic_derating_factor=values['Cyclic Derating Factor'],
            axial_load_case=values['Axial Load Case'],
            cloth_width_mm=values['Prowrap CF Cloth Width [mm]'],
            allow_unqualified_temperature=True,
        )
        if _should_run_type_a_check(values, result):
            type_a = calculate_type_a_class3_prowrap_check(
                od=values['Pipe OD [mm]'],
                pressure_bar=values['Design Pressure [bar]'],
                temp=values['Operating Temperature [degC]'],
                rem_wall=values['Remaining Wall [mm]'],
                design_life=values['Design Life [years]'],
                substrate_allowable_pressure_bar=substrate_credit_bar_for_iso_check(result),
                installation_temp=values['Installation Temperature [degC]'],
                component_type=values['Component Type'],
                cyclic_derating_factor=values['Cyclic Derating Factor'],
                nominal_wall_mm=values['Nominal Wall [mm]'],
                axial_load_case=values['Axial Load Case'],
            )
            result = apply_type_a_class3_result_to_repair(
                result,
                type_a,
                cloth_width_mm=values['Prowrap CF Cloth Width [mm]'],
            )
    except ValueError as error:
        return RowCalculation(
            source_excel_row=row.source_excel_row,
            status=CalculationStatus.INPUT_ERROR,
            outputs={},
            error_code='ENGINE_INPUT_ERROR',
            error_message=str(error),
        )

    extra_warnings = (
        _cloth_width_warnings(values['Prowrap CF Cloth Width [mm]'])
        + _type_a_check_warnings(values, result)
    )
    warnings = tuple(result['compliance_warnings']) + extra_warnings
    status = classify_result(result, extra_warnings)
    outputs = _map_outputs(
        result,
        warning_codes(warnings),
        _should_run_type_a_check(values, result),
    )
    if status is CalculationStatus.NOT_REPAIRABLE:
        for heading in _INSTALLABLE_OUTPUTS:
            outputs[heading] = None

    return RowCalculation(
        source_excel_row=row.source_excel_row,
        status=status,
        outputs=outputs,
    )


def _should_run_type_a_check(values: dict[str, Any], result: dict[str, Any]) -> bool:
    return (
        values['Run Type A / Class 3 Check'] == 'Yes'
        and 'Type A' in result['calc_method_thick']
        and values['Design Pressure [bar]'] > 0
        and values['Operating Temperature [degC]'] <= PROWRAP['max_temp']
    )


def _type_a_check_warnings(values: dict[str, Any], result: dict[str, Any]) -> tuple[str, ...]:
    if (
        values['Run Type A / Class 3 Check'] != 'Yes'
        or 'Type A' not in result['calc_method_thick']
    ):
        return ()
    if values['Design Pressure [bar]'] == 0:
        return (
            'Type A / Class 3 check was not run at zero design pressure; '
            'the check is non-controlling and engineering review is required.',
        )
    if values['Operating Temperature [degC]'] > PROWRAP['max_temp']:
        return (
            'Type A / Class 3 check was not run above the qualified Prowrap '
            'temperature limit; engineering review is required.',
        )
    return ()


def _cloth_width_warnings(cloth_width_mm: float) -> tuple[str, ...]:
    if cloth_width_mm in APPROVED_CLOTH_WIDTHS_MM:
        return ()
    return (
        f'Prowrap CF cloth width {cloth_width_mm:g} mm is not an approved '
        '300 mm or 500 mm configuration; confirm product approval before installation.',
    )


def _map_outputs(
    result: dict[str, Any], warnings: tuple[str, ...], type_a_check_run: bool,
) -> dict[str, object]:
    b31g = result['b31g_details']
    return {
        'Thickness Calculation Method': result['calc_method_thick'],
        'Overlap Calculation Method': result['calc_method_overlap'],
        'Wall Loss [%]': result['wall_loss_ratio'] * 100.0,
        'End-of-Life Remaining Wall [mm]': result['rem_wall_eol'],
        'No Substrate Capacity': result['has_no_substrate_capacity'],
        'B31G Applicable': None if b31g is None else b31g['applicable'],
        'B31G Acceptable': None if b31g is None else b31g['acceptable'],
        'Effective Pipe Capacity [bar]': result['p_steel_capacity'] * 10.0,
        'Composite Pressure Deficit [bar]': result['p_composite_design'] * 10.0,
        'Required Structural Thickness [mm]': result['t_required'],
        'Installed Plies': result['num_plies'],
        'Installed Thickness [mm]': round(result['final_thickness'], 2),
        'Thin-Wall Thickness Check OK': result['thickness_check_ok'],
        'Type A / Class 3 Check Run': type_a_check_run,
        'Type A / Class 3 Controls': result.get('iso_typea_class3_controls'),
        'Required Overlap [mm]': result['overlap_length'],
        'Taper Length [mm]': result['taper_length'],
        'Total Repair Length [mm]': result['iso_length'],
        'Cloth Band Count': result['num_bands'],
        'Procurement Axial Length [mm]': result['proc_length'],
        'Fabric Area [m2]': result['optimized_sqm'],
        'Epoxy Mass [kg]': result['epoxy_kg'],
        'Compliance Warnings': warnings,
        'B31G Detail': b31g,
        'Type A Detail': result.get('iso_typea_class3'),
        'Type B Detail': result['type_b_details'],
    }
