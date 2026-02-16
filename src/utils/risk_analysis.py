"""Risk flag calculation engine"""

from decimal import Decimal
from typing import Any, Dict, List


class RiskFlag:
    """Represents a risk flag for a workload"""

    def __init__(self, workload: str, risk_type: str, severity: str, description: str):
        self.workload = workload
        self.risk_type = risk_type
        self.severity = severity  # HIGH, MEDIUM, LOW
        self.description = description


def calculate_risk_flags(row: Dict[str, Any]) -> List[RiskFlag]:
    """
    Calculate risk flags for a plan row based on PRD rules.

    Risk flag rules (from PRD Section 9.3):
    1. Long ramp-up: Ramp-Up Duration >= 6
    2. Low realization: Total Year-1 ACR / (12 * Steady-State Monthly) < 0.7
    3. Zero baseline and long ramp: StartConsumption == 0 and Ramp-Up Duration >= 6

    Args:
        row: Dictionary with plan row data

    Returns:
        List of RiskFlag objects
    """
    flags = []
    workload = row.get("Workload", "Unknown")

    # Extract values
    ramp_up_duration = int(row.get("Ramp-Up Duration (Months)", 0))
    ramp_up_start = Decimal(str(row.get("Ramp-Up Start Consumption (CHF)", 0)))
    steady_state_monthly = Decimal(str(row.get("Steady-State Monthly Consumption (CHF)", 0)))
    total_year1_acr = Decimal(str(row.get("Total Year-1 Estimated ACR (CHF)", 0)))

    # Rule 1: Long ramp-up
    if ramp_up_duration >= 6:
        flags.append(
            RiskFlag(
                workload=workload,
                risk_type="Long Ramp-Up",
                severity="MEDIUM",
                description=f"Ramp-up duration of {ramp_up_duration} months may delay realization",
            )
        )

    # Rule 2: Low realization
    if steady_state_monthly > 0:
        full_year_potential = 12 * steady_state_monthly
        realization_ratio = (
            float(total_year1_acr / full_year_potential) if full_year_potential > 0 else 0
        )

        if realization_ratio < 0.7:
            flags.append(
                RiskFlag(
                    workload=workload,
                    risk_type="Low Year-1 Realization",
                    severity="HIGH",
                    description=f"Year-1 ACR realizes only {realization_ratio:.1%} of full-year potential",
                )
            )

    # Rule 3: Zero baseline and long ramp
    if ramp_up_start == 0 and ramp_up_duration >= 6:
        flags.append(
            RiskFlag(
                workload=workload,
                risk_type="Zero Baseline + Long Ramp",
                severity="HIGH",
                description="Starting from zero with long ramp-up indicates high execution risk",
            )
        )

    return flags


def calculate_all_risk_flags(data: List[Dict[str, Any]]) -> List[RiskFlag]:
    """
    Calculate risk flags for all workloads.

    Args:
        data: List of plan row dictionaries

    Returns:
        List of all RiskFlag objects
    """
    all_flags = []
    for row in data:
        flags = calculate_risk_flags(row)
        all_flags.extend(flags)
    return all_flags
