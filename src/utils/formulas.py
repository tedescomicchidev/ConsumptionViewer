"""Formula computation engine for derived columns"""
from decimal import Decimal
from typing import Dict, Any


def compute_derived_fields(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute all derived fields for a plan row.
    
    Formulas (from PRD):
    - AvgRampUp = (StartConsumption + SteadyStateMonthly) / 2
    - TotalRampUp = AvgRampUp * RampUpDuration
    - Year1SteadyMonths = 12 - RampUpDuration
    - Year1SteadyConsumption = Year1SteadyMonths * SteadyStateMonthly
    - TotalYear1ACR = TotalRampUp + Year1SteadyConsumption
    
    Args:
        row: Dictionary with input field values
        
    Returns:
        Dictionary with all computed field values
    """
    # Extract input values
    ramp_up_duration = int(row.get("Ramp-Up Duration (Months)", 0))
    ramp_up_start = Decimal(str(row.get("Ramp-Up Start Consumption (CHF)", 0)))
    steady_state_monthly = Decimal(str(row.get("Steady-State Monthly Consumption (CHF)", 0)))
    
    # Compute derived values
    avg_monthly_ramp_up = (ramp_up_start + steady_state_monthly) / Decimal("2")
    total_ramp_up = avg_monthly_ramp_up * Decimal(str(ramp_up_duration))
    year1_steady_months = 12 - ramp_up_duration
    year1_steady_consumption = Decimal(str(year1_steady_months)) * steady_state_monthly
    total_year1_acr = total_ramp_up + year1_steady_consumption
    
    return {
        "Avg Monthly Consumption During Ramp-Up (CHF)": round(avg_monthly_ramp_up, 2),
        "Total Ramp-Up Consumption (CHF)": round(total_ramp_up, 2),
        "Year-1 Steady-State Months": year1_steady_months,
        "Year-1 Steady-State Consumption (CHF)": round(year1_steady_consumption, 2),
        "Total Year-1 Estimated ACR (CHF)": round(total_year1_acr, 2),
    }


def generate_monthly_curve(row: Dict[str, Any]) -> list:
    """
    Generate synthetic 12-month consumption curve for a workload.
    
    Logic (from PRD):
    - If ramp_up_duration = 0: all months at steady_state_monthly
    - Else months 1..ramp: linear interpolation from start to steady_state
    - Remaining months: steady_state_monthly
    
    Args:
        row: Dictionary with plan row data
        
    Returns:
        List of 12 monthly consumption values
    """
    ramp_up_duration = int(row.get("Ramp-Up Duration (Months)", 0))
    ramp_up_start = float(row.get("Ramp-Up Start Consumption (CHF)", 0))
    steady_state = float(row.get("Steady-State Monthly Consumption (CHF)", 0))
    
    monthly_values = []
    
    if ramp_up_duration == 0:
        # All months at steady state
        monthly_values = [steady_state] * 12
    else:
        # Ramp-up months: linear interpolation
        for month in range(1, ramp_up_duration + 1):
            # Linear interpolation from start to steady
            progress = month / ramp_up_duration
            value = ramp_up_start + (steady_state - ramp_up_start) * progress
            monthly_values.append(value)
        
        # Remaining months at steady state
        remaining_months = 12 - ramp_up_duration
        monthly_values.extend([steady_state] * remaining_months)
    
    return monthly_values
