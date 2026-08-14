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
