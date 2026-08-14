"""User-facing calculation-status classification for batch rows."""

from enum import Enum
from typing import Any, Iterable, Mapping


class CalculationStatus(str, Enum):
    OK = 'OK'
    REVIEW_REQUIRED = 'REVIEW REQUIRED'
    NOT_REPAIRABLE = 'NOT REPAIRABLE'
    INPUT_ERROR = 'INPUT ERROR'
    SYSTEM_ERROR = 'SYSTEM ERROR'


def classify_result(
    result: Mapping[str, Any],
    extra_warnings: Iterable[str],
) -> CalculationStatus:
    """Classify a completed engine result using the defined safety priority."""
    type_b_details = result.get('type_b_details') or {}
    if type_b_details.get('repairable_formula12') is False:
        return CalculationStatus.NOT_REPAIRABLE
    if result.get('compliance_warnings') or tuple(extra_warnings):
        return CalculationStatus.REVIEW_REQUIRED
    return CalculationStatus.OK
