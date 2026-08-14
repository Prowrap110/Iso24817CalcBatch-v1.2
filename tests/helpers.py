def valid_engine_inputs(**overrides):
    values = dict(
        customer='Batch Customer', location='Batch Location', report_no='B-001',
        od=457.2, wall=9.53, pressure=50.0, temp=40.0,
        defect_type='Corrosion', defect_loc='External', length=100.0,
        rem_wall=4.5, yield_strength=359.0, design_factor=0.72,
        design_life=20, internal_corrosion_rate=0.0,
        installation_temp=20.0, component_type='Straight',
        cyclic_derating_factor=1.0, axial_load_case=0,
        cloth_width_mm=300.0,
    )
    values.update(overrides)
    return values


def valid_row_values(**overrides):
    values = {
        'Pipe OD [mm]': 457.2,
        'Nominal Wall [mm]': 9.53,
        'Pipe Yield [MPa]': 359.0,
        'Design Pressure [bar]': 50.0,
        'Operating Temperature [degC]': 40.0,
        'Mechanism': 'Corrosion',
        'Defect Location': 'External',
        'Defect Length [mm]': 100.0,
        'Remaining Wall [mm]': 4.5,
        'Internal Corrosion Rate [mm/year]': None,
        'Design Life [years]': 20,
        'Design Factor': 0.72,
        'Run Type A / Class 3 Check': 'No',
        'Installation Temperature [degC]': 20.0,
        'Component Type': 'Straight',
        'Cyclic Derating Factor': 1.0,
        'Axial Load Case': 0,
        'Prowrap CF Cloth Width [mm]': 300.0,
    }
    values.update(overrides)
    return values


def batch_info():
    from batch_schema import BatchInfo

    return BatchInfo('Batch Customer', 'Batch Location', 'B-001')


def validated_row(**overrides):
    from batch_validation import validate_row

    row, issues = validate_row(2, valid_row_values(**overrides))
    assert not issues
    assert row is not None
    return row
