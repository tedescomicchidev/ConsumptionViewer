"""Tests for formula computation engine"""

from decimal import Decimal

from src.utils.formulas import compute_derived_fields, generate_monthly_curve


def test_compute_derived_fields_zero_ramp():
    """Test computation with zero ramp-up duration"""
    row = {
        "Ramp-Up Duration (Months)": 0,
        "Ramp-Up Start Consumption (CHF)": 0,
        "Steady-State Monthly Consumption (CHF)": 10000,
    }

    result = compute_derived_fields(row)

    assert result["Avg Monthly Consumption During Ramp-Up (CHF)"] == Decimal("5000.00")
    assert result["Total Ramp-Up Consumption (CHF)"] == Decimal("0.00")
    assert result["Year-1 Steady-State Months"] == 12
    assert result["Year-1 Steady-State Consumption (CHF)"] == Decimal("120000.00")
    assert result["Total Year-1 Estimated ACR (CHF)"] == Decimal("120000.00")


def test_compute_derived_fields_with_ramp():
    """Test computation with 6-month ramp-up"""
    row = {
        "Ramp-Up Duration (Months)": 6,
        "Ramp-Up Start Consumption (CHF)": 5000,
        "Steady-State Monthly Consumption (CHF)": 25000,
    }

    result = compute_derived_fields(row)

    assert result["Avg Monthly Consumption During Ramp-Up (CHF)"] == Decimal("15000.00")
    assert result["Total Ramp-Up Consumption (CHF)"] == Decimal("90000.00")
    assert result["Year-1 Steady-State Months"] == 6
    assert result["Year-1 Steady-State Consumption (CHF)"] == Decimal("150000.00")
    assert result["Total Year-1 Estimated ACR (CHF)"] == Decimal("240000.00")


def test_compute_derived_fields_full_year_ramp():
    """Test computation with 12-month ramp-up (edge case)"""
    row = {
        "Ramp-Up Duration (Months)": 12,
        "Ramp-Up Start Consumption (CHF)": 0,
        "Steady-State Monthly Consumption (CHF)": 20000,
    }

    result = compute_derived_fields(row)

    assert result["Avg Monthly Consumption During Ramp-Up (CHF)"] == Decimal("10000.00")
    assert result["Total Ramp-Up Consumption (CHF)"] == Decimal("120000.00")
    assert result["Year-1 Steady-State Months"] == 0
    assert result["Year-1 Steady-State Consumption (CHF)"] == Decimal("0.00")
    assert result["Total Year-1 Estimated ACR (CHF)"] == Decimal("120000.00")


def test_generate_monthly_curve_zero_ramp():
    """Test monthly curve generation with zero ramp"""
    row = {
        "Ramp-Up Duration (Months)": 0,
        "Ramp-Up Start Consumption (CHF)": 0,
        "Steady-State Monthly Consumption (CHF)": 10000,
    }

    curve = generate_monthly_curve(row)

    assert len(curve) == 12
    assert all(v == 10000 for v in curve)


def test_generate_monthly_curve_with_ramp():
    """Test monthly curve generation with ramp-up"""
    row = {
        "Ramp-Up Duration (Months)": 3,
        "Ramp-Up Start Consumption (CHF)": 0,
        "Steady-State Monthly Consumption (CHF)": 9000,
    }

    curve = generate_monthly_curve(row)

    assert len(curve) == 12
    # First 3 months should ramp up
    assert curve[0] == 3000  # Linear interpolation: 0 + (9000-0) * 1/3
    assert curve[1] == 6000  # Linear interpolation: 0 + (9000-0) * 2/3
    assert curve[2] == 9000  # Linear interpolation: 0 + (9000-0) * 3/3
    # Remaining months should be steady state
    assert all(v == 9000 for v in curve[3:])


def test_generate_monthly_curve_with_baseline():
    """Test monthly curve with non-zero baseline"""
    row = {
        "Ramp-Up Duration (Months)": 4,
        "Ramp-Up Start Consumption (CHF)": 10000,
        "Steady-State Monthly Consumption (CHF)": 30000,
    }

    curve = generate_monthly_curve(row)

    assert len(curve) == 12
    # Should ramp from 10000 to 30000 over 4 months
    assert curve[0] == 15000  # 10000 + (30000-10000) * 1/4
    assert curve[1] == 20000  # 10000 + (30000-10000) * 2/4
    assert curve[2] == 25000  # 10000 + (30000-10000) * 3/4
    assert curve[3] == 30000  # 10000 + (30000-10000) * 4/4
    # Remaining months at steady state
    assert all(v == 30000 for v in curve[4:])
