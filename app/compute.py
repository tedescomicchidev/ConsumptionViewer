from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

from app.schema import REQUIRED_COLUMNS


def _r2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def recompute_columns(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    for col in REQUIRED_COLUMNS:
        if col not in output.columns:
            raise ValueError(f"Missing required column: {col}")

    avg_values = []
    ramp_totals = []
    steady_months = []
    steady_totals = []
    acr_totals = []

    for _, row in output.iterrows():
        ramp = int(row["Ramp-Up Duration (Months)"])
        start = Decimal(str(row["Ramp-Up Start Consumption (CHF)"]))
        steady = Decimal(str(row["Steady-State Monthly Consumption (CHF)"]))

        avg = _r2((start + steady) / Decimal("2"))
        total_ramp = _r2(avg * Decimal(ramp))
        year1_steady_months = max(0, 12 - ramp)
        year1_steady = _r2(steady * Decimal(year1_steady_months))
        total_acr = _r2(total_ramp + year1_steady)

        avg_values.append(float(avg))
        ramp_totals.append(float(total_ramp))
        steady_months.append(year1_steady_months)
        steady_totals.append(float(year1_steady))
        acr_totals.append(float(total_acr))

    output["Avg Monthly Consumption During Ramp-Up (CHF)"] = avg_values
    output["Total Ramp-Up Consumption (CHF)"] = ramp_totals
    output["Year-1 Steady-State Months"] = steady_months
    output["Year-1 Steady-State Consumption (CHF)"] = steady_totals
    output["Total Year-1 Estimated ACR (CHF)"] = acr_totals
    return output


def build_monthly_series(df: pd.DataFrame, months: int = 12) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        ramp = int(row["Ramp-Up Duration (Months)"])
        start = float(row["Ramp-Up Start Consumption (CHF)"])
        steady = float(row["Steady-State Monthly Consumption (CHF)"])
        workload = row["Workload"]

        values: list[float] = []
        for m in range(1, months + 1):
            if ramp <= 0:
                values.append(steady)
            elif m <= ramp:
                if ramp == 1:
                    values.append(steady)
                else:
                    pct = (m - 1) / (ramp - 1)
                    values.append(start + (steady - start) * pct)
            else:
                values.append(steady)

        for idx, val in enumerate(values, start=1):
            rows.append({"Workload": workload, "Month": idx, "Consumption": val})

    return pd.DataFrame(rows)


def risk_flags(df: pd.DataFrame) -> pd.DataFrame:
    risk_rows = []
    for _, row in df.iterrows():
        ramp = int(row["Ramp-Up Duration (Months)"])
        steady = float(row["Steady-State Monthly Consumption (CHF)"])
        start = float(row["Ramp-Up Start Consumption (CHF)"])
        acr = float(row["Total Year-1 Estimated ACR (CHF)"])
        denom = 12 * steady if steady else 0
        realization = (acr / denom) if denom else 0

        issues = []
        if ramp >= 6:
            issues.append("Long ramp-up")
        if denom and realization < 0.7:
            issues.append("Low realization")
        if start == 0 and ramp >= 6:
            issues.append("Zero baseline and long ramp")

        if issues:
            risk_rows.append(
                {
                    "Workload": row["Workload"],
                    "Ramp-Up Duration": ramp,
                    "Realization Ratio": round(realization, 2),
                    "Risk Flags": ", ".join(issues),
                }
            )

    return pd.DataFrame(risk_rows)
