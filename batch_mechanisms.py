"""Canonical and backward-compatible mechanism names at the upload boundary."""


CANONICAL_MECHANISMS = (
    'Corrosion', 'Dent w/crack', 'Dent no-crack', 'Leak', 'Crack',
)
LEGACY_MECHANISM_ALIASES = {'Dent': 'Dent w/crack'}
ACCEPTED_UPLOAD_MECHANISMS = (
    *CANONICAL_MECHANISMS,
    *LEGACY_MECHANISM_ALIASES,
)


def normalize_upload_mechanism(value: object) -> str:
    """Trim an accepted upload value and conservatively migrate legacy Dent."""
    text = '' if value is None else str(value).strip()
    return LEGACY_MECHANISM_ALIASES.get(text, text)
