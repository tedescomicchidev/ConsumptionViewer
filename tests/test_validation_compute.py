import pandas as pd

from app.compute import recompute_columns, risk_flags
from app.validation import validate_and_compute


def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Workload": "SAP",
                "Scenario": "Rehost",
                "Azure Services": "VM, Storage",
                "Start Month": "Apr-2026",
                "Ramp-Up Duration (Months)": 6,
                "Ramp-Up Start Consumption (CHF)": 1000,
                "Steady-State Monthly Consumption (CHF)": 3000,
            }
        ]
    )


def test_validate_and_compute_success():
    computed, issues = validate_and_compute(sample_df())
    assert not issues
    assert computed.iloc[0]["Avg Monthly Consumption During Ramp-Up (CHF)"] == 2000
    assert computed.iloc[0]["Year-1 Steady-State Months"] == 6
    assert computed.iloc[0]["Total Year-1 Estimated ACR (CHF)"] == 30000


def test_validate_missing_required_column():
    invalid = sample_df().drop(columns=["Workload"])
    _, issues = validate_and_compute(invalid)
    assert issues
    assert issues[0].column == "Workload"


def test_risk_flag_rules():
    computed = recompute_columns(sample_df())
    risks = risk_flags(computed)
    assert len(risks) == 1
    assert "Long ramp-up" in risks.iloc[0]["Risk Flags"]
