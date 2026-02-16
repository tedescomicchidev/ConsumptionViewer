"""Tests for CSV validation"""

import pandas as pd

from src.services.validation import process_csv_data, validate_csv_schema


def test_valid_csv_passes_validation():
    """Test that a valid CSV passes validation"""
    data = {
        "Workload": ["Test Workload"],
        "Scenario": ["Replatform"],
        "Azure Services": ["App Service, SQL Database"],
        "Start Month": ["Jan-2026"],
        "Ramp-Up Duration (Months)": [6],
        "Ramp-Up Start Consumption (CHF)": [5000.0],
        "Steady-State Monthly Consumption (CHF)": [25000.0],
    }
    df = pd.DataFrame(data)

    result = validate_csv_schema(df)

    assert result.is_valid()
    assert len(result.errors) == 0


def test_missing_required_column_fails():
    """Test that missing required columns fail validation"""
    data = {
        "Workload": ["Test Workload"],
        "Scenario": ["Replatform"],
        # Missing "Azure Services"
        "Start Month": ["Jan-2026"],
        "Ramp-Up Duration (Months)": [6],
        "Ramp-Up Start Consumption (CHF)": [5000.0],
        "Steady-State Monthly Consumption (CHF)": [25000.0],
    }
    df = pd.DataFrame(data)

    result = validate_csv_schema(df)

    assert not result.is_valid()
    assert len(result.errors) > 0


def test_invalid_integer_fails():
    """Test that invalid integer values fail validation"""
    data = {
        "Workload": ["Test Workload"],
        "Scenario": ["Replatform"],
        "Azure Services": ["App Service"],
        "Start Month": ["Jan-2026"],
        "Ramp-Up Duration (Months)": ["invalid"],  # Should be integer
        "Ramp-Up Start Consumption (CHF)": [5000.0],
        "Steady-State Monthly Consumption (CHF)": [25000.0],
    }
    df = pd.DataFrame(data)

    result = validate_csv_schema(df)

    assert not result.is_valid()


def test_out_of_range_integer_fails():
    """Test that out-of-range integers fail validation"""
    data = {
        "Workload": ["Test Workload"],
        "Scenario": ["Replatform"],
        "Azure Services": ["App Service"],
        "Start Month": ["Jan-2026"],
        "Ramp-Up Duration (Months)": [15],  # Max is 12
        "Ramp-Up Start Consumption (CHF)": [5000.0],
        "Steady-State Monthly Consumption (CHF)": [25000.0],
    }
    df = pd.DataFrame(data)

    result = validate_csv_schema(df)

    assert not result.is_valid()


def test_process_csv_computes_fields():
    """Test that process_csv_data computes derived fields correctly"""
    data = {
        "Workload": ["Test Workload"],
        "Scenario": ["Replatform"],
        "Azure Services": ["App Service"],
        "Start Month": ["Jan-2026"],
        "Ramp-Up Duration (Months)": [6],
        "Ramp-Up Start Consumption (CHF)": [5000.0],
        "Steady-State Monthly Consumption (CHF)": [25000.0],
    }
    df = pd.DataFrame(data)

    result_df = process_csv_data(df)

    # Check computed columns exist
    assert "Avg Monthly Consumption During Ramp-Up (CHF)" in result_df.columns
    assert "Total Ramp-Up Consumption (CHF)" in result_df.columns
    assert "Year-1 Steady-State Months" in result_df.columns
    assert "Year-1 Steady-State Consumption (CHF)" in result_df.columns
    assert "Total Year-1 Estimated ACR (CHF)" in result_df.columns

    # Check computed values
    assert result_df["Avg Monthly Consumption During Ramp-Up (CHF)"][0] == 15000.0
    assert result_df["Total Ramp-Up Consumption (CHF)"][0] == 90000.0
    assert result_df["Year-1 Steady-State Months"][0] == 6
    assert result_df["Year-1 Steady-State Consumption (CHF)"][0] == 150000.0
    assert result_df["Total Year-1 Estimated ACR (CHF)"][0] == 240000.0


def test_extra_columns_warning():
    """Test that extra columns generate a warning"""
    data = {
        "Workload": ["Test Workload"],
        "Scenario": ["Replatform"],
        "Azure Services": ["App Service"],
        "Start Month": ["Jan-2026"],
        "Ramp-Up Duration (Months)": [6],
        "Ramp-Up Start Consumption (CHF)": [5000.0],
        "Steady-State Monthly Consumption (CHF)": [25000.0],
        "Extra Column": ["Extra Data"],  # Extra column
    }
    df = pd.DataFrame(data)

    result = validate_csv_schema(df)

    assert result.is_valid()
    assert len(result.warnings) > 0
