"""Permanent, human-auditable warning references for batch workbooks."""

from dataclasses import dataclass
from typing import Iterable


class UnmappedWarningError(ValueError):
    """Raised when an engine warning has no permanent workbook reference."""


@dataclass(frozen=True)
class WarningDefinition:
    code: str
    meaning: str
    markers: tuple[str, ...]

    def matches(self, message: str) -> bool:
        normalized = message.casefold()
        return all(marker.casefold() in normalized for marker in self.markers)


WARNING_DEFINITIONS = (
    WarningDefinition(
        'W001',
        'Design temperature exceeds the general qualified Prowrap limit; '
        'engineering review is required before repair design or installation.',
        ('Design temperature', 'qualified Prowrap limit'),
    ),
    WarningDefinition(
        'W002',
        'No Type B Formula 12 repair solution exists for the requested case; '
        'do not install without changing the design basis or repair method.',
        ('NOT REPAIRABLE PER ISO 24817 FORMULA 12',),
    ),
    WarningDefinition(
        'W003',
        'Requested Type B life exceeds the qualified PRW110 life; inspect, '
        'revalidate, or replace at the qualified limit.',
        ('Type B service life is capped',),
    ),
    WarningDefinition(
        'W004',
        'Class 3 Type B design temperature exceeds the applicable Tg - 30 '
        'service limit.',
        ('Design temperature', 'Type B upper service limit'),
    ),
    WarningDefinition(
        'W005',
        'Zero-pressure Type B Formula 12 is non-controlling; the impact-qualified '
        'minimum is shown and classification requires review.',
        ('Type B defect at zero design pressure',),
    ),
    WarningDefinition(
        'W006',
        'Type B design uses the defined through-wall defect basis and Annex F '
        'impact-qualified minimum; assessor confirmation is required.',
        ('Type B design assumes a circular/near-circular defect',),
    ),
    WarningDefinition(
        'W007',
        'Type B Formula 12 defect-size validity limit is exceeded; an engineered '
        'assessment is required.',
        ('Formula 12 validity exceeded',),
    ),
    WarningDefinition(
        'W008',
        'B31G d/t exceeds 0.80; B31G is not applicable and no substrate credit '
        'is taken.',
        ('B31G:', 'd/t > 0.80'),
    ),
    WarningDefinition(
        'W009',
        'B31G d/t is at or below 0.10; the section 3(a) length limitation note '
        'applies.',
        ('B31G:', 'd/t <= 0.10'),
    ),
    WarningDefinition(
        'W010',
        'B31G safety factor is below the permitted minimum.',
        ('B31G:', 'Safety factor < 1.25'),
    ),
    WarningDefinition(
        'W011',
        'Modified B31G SMYS validity is exceeded and the calculation falls back '
        'to Original B31G.',
        ('B31G:', 'SMYS > 483 MPa'),
    ),
    WarningDefinition(
        'W012',
        'B31G flow stress has been capped at SMTS.',
        ('B31G:', 'Flow stress capped at SMTS'),
    ),
    WarningDefinition(
        'W013',
        'B31G Level 1 finds the corroded pipe unacceptable at design pressure; '
        'the composite repair is structural.',
        ('B31G Level 1:', 'corroded pipe alone', 'NOT acceptable', 'design pressure'),
    ),
    WarningDefinition(
        'W014',
        'Internal corrosion has been projected to end of design life; assessment '
        'uses the end-of-life remaining wall.',
        ('Internal corrosion projected at',),
    ),
    WarningDefinition(
        'W015',
        'Internal corrosion rate is zero; enter a justified rate or perform '
        'engineering review.',
        ('Internal corrosion with corrosion rate = 0 mm/yr',),
    ),
    WarningDefinition(
        'W016',
        'Type B with axial load case 1 requires an engineered axial-load-path '
        'assessment.',
        ('Axial load case 1', 'Type B defect'),
    ),
    WarningDefinition(
        'W017',
        'Repair thickness exceeds D/12; the ISO thin-wall formulae are outside '
        'their validity range.',
        ('Repair thickness exceeds D/12',),
    ),
    WarningDefinition(
        'W018',
        'Entered Prowrap CF cloth width is not an approved 300 mm or 500 mm '
        'configuration; confirm product approval before installation.',
        ('Prowrap CF cloth width', 'not an approved'),
    ),
    WarningDefinition(
        'W019',
        'Requested Type A / Class 3 check was skipped at zero pressure because '
        'it is non-controlling; engineering review is required.',
        ('Type A / Class 3 check was not run at zero design pressure',),
    ),
    WarningDefinition(
        'W020',
        'Requested Type A / Class 3 check was skipped above the qualified '
        'Prowrap temperature limit; engineering review is required.',
        ('Type A / Class 3 check was not run above the qualified Prowrap temperature limit',),
    ),
)

_DEFINITIONS_BY_CODE = {definition.code: definition for definition in WARNING_DEFINITIONS}


def warning_codes(messages: Iterable[str]) -> tuple[str, ...]:
    """Resolve full warnings to unique permanent codes in first-seen order."""
    resolved: list[str] = []
    for message in messages:
        matches = [
            definition.code
            for definition in WARNING_DEFINITIONS
            if definition.matches(str(message))
        ]
        if len(matches) != 1:
            raise UnmappedWarningError(f'Unmapped compliance warning: {message}')
        if matches[0] not in resolved:
            resolved.append(matches[0])
    return tuple(resolved)


def warning_meaning(code: str) -> str:
    """Return the permanent meaning associated with one warning code."""
    try:
        return _DEFINITIONS_BY_CODE[code].meaning
    except KeyError as error:
        raise UnmappedWarningError(f'Unknown warning code: {code}') from error


def format_affected_rows(
    main_rows: Iterable[int], detail_rows: Iterable[int],
) -> str:
    """Format compact, source-sheet-aware warning locations for the register."""
    main = tuple(sorted(set(main_rows)))
    detail = tuple(sorted(set(detail_rows)))
    main_text = ', '.join(str(row) for row in main)
    detail_text = ', '.join(str(row) for row in detail)
    if not detail:
        return main_text
    sections = []
    if main_text:
        sections.append(f'Main {main_text}')
    sections.append(f'Individual Defects {detail_text}')
    return '; '.join(sections)
