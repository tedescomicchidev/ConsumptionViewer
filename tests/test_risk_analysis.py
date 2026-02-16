"""Tests for risk analysis engine"""

from src.utils.risk_analysis import calculate_risk_flags


def test_long_ramp_up_flag():
    """Test detection of long ramp-up risk"""
    row = {
        "Workload": "Test Workload",
        "Ramp-Up Duration (Months)": 8,
        "Ramp-Up Start Consumption (CHF)": 5000,
        "Steady-State Monthly Consumption (CHF)": 20000,
        "Total Year-1 Estimated ACR (CHF)": 150000,
    }

    flags = calculate_risk_flags(row)

    # Should have at least the long ramp-up flag
    assert any(flag.risk_type == "Long Ramp-Up" for flag in flags)
    long_ramp_flag = [f for f in flags if f.risk_type == "Long Ramp-Up"][0]
    assert long_ramp_flag.severity == "MEDIUM"
    assert long_ramp_flag.workload == "Test Workload"


def test_low_realization_flag():
    """Test detection of low year-1 realization"""
    row = {
        "Workload": "Low Realization Workload",
        "Ramp-Up Duration (Months)": 9,
        "Ramp-Up Start Consumption (CHF)": 0,
        "Steady-State Monthly Consumption (CHF)": 30000,
        "Total Year-1 Estimated ACR (CHF)": 180000,  # Much less than 12 * 30000 = 360000
    }

    flags = calculate_risk_flags(row)

    # Should have low realization flag (180000 / 360000 = 0.5 < 0.7)
    assert any(flag.risk_type == "Low Year-1 Realization" for flag in flags)
    low_real_flag = [f for f in flags if f.risk_type == "Low Year-1 Realization"][0]
    assert low_real_flag.severity == "HIGH"


def test_zero_baseline_long_ramp_flag():
    """Test detection of zero baseline with long ramp"""
    row = {
        "Workload": "Zero Start Workload",
        "Ramp-Up Duration (Months)": 10,
        "Ramp-Up Start Consumption (CHF)": 0,
        "Steady-State Monthly Consumption (CHF)": 25000,
        "Total Year-1 Estimated ACR (CHF)": 175000,
    }

    flags = calculate_risk_flags(row)

    # Should have zero baseline + long ramp flag
    assert any(flag.risk_type == "Zero Baseline + Long Ramp" for flag in flags)
    zero_flag = [f for f in flags if f.risk_type == "Zero Baseline + Long Ramp"][0]
    assert zero_flag.severity == "HIGH"


def test_no_risk_flags():
    """Test workload with no risk flags"""
    row = {
        "Workload": "Healthy Workload",
        "Ramp-Up Duration (Months)": 3,
        "Ramp-Up Start Consumption (CHF)": 10000,
        "Steady-State Monthly Consumption (CHF)": 20000,
        "Total Year-1 Estimated ACR (CHF)": 225000,  # 10000+20000/2 * 3 + 9*20000 = 45000+180000
    }

    flags = calculate_risk_flags(row)

    # Should have no flags
    assert len(flags) == 0


def test_multiple_risk_flags():
    """Test workload with multiple risk flags"""
    row = {
        "Workload": "High Risk Workload",
        "Ramp-Up Duration (Months)": 10,
        "Ramp-Up Start Consumption (CHF)": 0,
        "Steady-State Monthly Consumption (CHF)": 40000,
        "Total Year-1 Estimated ACR (CHF)": 280000,  # 200000 + 80000, < 0.7 * 480000
    }

    flags = calculate_risk_flags(row)

    # Should have all three flags
    assert len(flags) == 3
    risk_types = [f.risk_type for f in flags]
    assert "Long Ramp-Up" in risk_types
    assert "Low Year-1 Realization" in risk_types
    assert "Zero Baseline + Long Ramp" in risk_types
