from __future__ import annotations

from decimal import InvalidOperation

import pandas as pd

from app.compute import recompute_columns
from app.schema import REQUIRED_COLUMNS, ValidationIssue, parse_decimal


def validate_dataframe(df: pd.DataFrame) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        for col in missing:
            issues.append(ValidationIssue(row_index=-1, column=col, error="Missing required column"))
        return issues

    for idx, row in df.iterrows():
        for col in ["Workload", "Scenario", "Azure Services", "Start Month"]:
            if pd.isna(row[col]) or str(row[col]).strip() == "":
                issues.append(ValidationIssue(row_index=int(idx), column=col, error="Value required"))

        try:
            ramp = int(row["Ramp-Up Duration (Months)"])
            if ramp < 0:
                issues.append(
                    ValidationIssue(
                        row_index=int(idx),
                        column="Ramp-Up Duration (Months)",
                        error="Must be >= 0",
                    )
                )
        except (TypeError, ValueError):
            issues.append(
                ValidationIssue(
                    row_index=int(idx),
                    column="Ramp-Up Duration (Months)",
                    error="Must be an integer",
                )
            )

        for col in [
            "Ramp-Up Start Consumption (CHF)",
            "Steady-State Monthly Consumption (CHF)",
        ]:
            try:
                val = parse_decimal(row[col])
                if val < 0:
                    issues.append(ValidationIssue(row_index=int(idx), column=col, error="Must be >= 0"))
            except (InvalidOperation, ValueError):
                issues.append(ValidationIssue(row_index=int(idx), column=col, error="Must be a decimal"))

    return issues


def validate_and_compute(df: pd.DataFrame) -> tuple[pd.DataFrame, list[ValidationIssue]]:
    issues = validate_dataframe(df)
    if issues:
        return df, issues

    normalized = df[REQUIRED_COLUMNS].copy()
    normalized["Ramp-Up Duration (Months)"] = normalized["Ramp-Up Duration (Months)"].astype(int)
    for col in ["Ramp-Up Start Consumption (CHF)", "Steady-State Monthly Consumption (CHF)"]:
        normalized[col] = normalized[col].map(lambda x: float(parse_decimal(x)))

    computed = recompute_columns(normalized)
    return computed, []
