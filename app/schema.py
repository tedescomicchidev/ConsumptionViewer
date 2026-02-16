from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

REQUIRED_COLUMNS = [
    "Workload",
    "Scenario",
    "Azure Services",
    "Start Month",
    "Ramp-Up Duration (Months)",
    "Ramp-Up Start Consumption (CHF)",
    "Steady-State Monthly Consumption (CHF)",
]

COMPUTED_COLUMNS = [
    "Avg Monthly Consumption During Ramp-Up (CHF)",
    "Total Ramp-Up Consumption (CHF)",
    "Year-1 Steady-State Months",
    "Year-1 Steady-State Consumption (CHF)",
    "Total Year-1 Estimated ACR (CHF)",
]

ALL_COLUMNS = REQUIRED_COLUMNS + COMPUTED_COLUMNS


@dataclass(frozen=True)
class ValidationIssue:
    row_index: int
    column: str
    error: str


def parse_decimal(value: Any) -> Decimal:
    if value is None or value == "":
        raise InvalidOperation("empty decimal")
    if isinstance(value, str):
        value = value.replace("CHF", "").replace(",", "").strip()
    return Decimal(str(value))
