from pathlib import Path


def test_pinned_engine_is_importable_and_documented():
    from engine.prowrap_calculations import calculate_repair

    assert callable(calculate_repair)
    provenance = Path('ENGINE_SOURCE.md').read_text(encoding='utf-8')
    assert 'Prowrap110/Iso24817Calcv1.1' in provenance
    assert '68e5409' in provenance
