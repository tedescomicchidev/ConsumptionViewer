"""CSV validation service"""

from typing import List

import pandas as pd

from src.models.schema import (
    REQUIRED_COLUMNS,
    SCHEMA_BY_NAME,
    ColumnType,
)
from src.utils.formulas import compute_derived_fields


class ValidationError:
    """Validation error details"""

    def __init__(self, row_index: int, column: str, error: str):
        self.row_index = row_index
        self.column = column
        self.error = error

    def __repr__(self):
        return f"Row {self.row_index}, Column '{self.column}': {self.error}"


class ValidationResult:
    """Result of CSV validation"""

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []

    def add_error(self, row_index: int, column: str, error: str):
        """Add a validation error"""
        self.errors.append(ValidationError(row_index, column, error))

    def add_warning(self, warning: str):
        """Add a validation warning"""
        self.warnings.append(warning)

    def is_valid(self) -> bool:
        """Check if validation passed"""
        return len(self.errors) == 0

    def get_error_report(self) -> pd.DataFrame:
        """Generate error report as DataFrame"""
        if not self.errors:
            return pd.DataFrame(columns=["Row", "Column", "Error"])

        return pd.DataFrame(
            [{"Row": e.row_index, "Column": e.column, "Error": e.error} for e in self.errors]
        )


def validate_csv_schema(df: pd.DataFrame) -> ValidationResult:
    """
    Validate CSV schema and data types.

    Args:
        df: DataFrame loaded from CSV

    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()

    # Check required columns
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        for col in missing_columns:
            result.add_error(0, col, f"Required column missing: {col}")
        return result  # Cannot continue without required columns

    # Check for extra columns (warning only)
    extra_columns = set(df.columns) - set(SCHEMA_BY_NAME.keys())
    if extra_columns:
        result.add_warning(f"Extra columns found (will be ignored): {', '.join(extra_columns)}")

    # Validate each row
    for idx, row in df.iterrows():
        row_num = idx + 2  # +2 for 1-based indexing and header row

        # Validate required fields
        for col_name in REQUIRED_COLUMNS:
            if col_name not in df.columns:
                continue

            value = row[col_name]
            col_def = SCHEMA_BY_NAME[col_name]

            # Check for null/empty values
            if pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
                result.add_error(row_num, col_name, "Value is required but missing")
                continue

            # Validate data type
            if col_def.type == ColumnType.INTEGER:
                try:
                    int_value = int(value)
                    # Check constraints
                    if col_def.min_value is not None and int_value < col_def.min_value:
                        result.add_error(
                            row_num,
                            col_name,
                            f"Value {int_value} is below minimum {col_def.min_value}",
                        )
                    if col_def.max_value is not None and int_value > col_def.max_value:
                        result.add_error(
                            row_num,
                            col_name,
                            f"Value {int_value} exceeds maximum {col_def.max_value}",
                        )
                except (ValueError, TypeError):
                    result.add_error(row_num, col_name, f"Invalid integer value: {value}")

            elif col_def.type == ColumnType.DECIMAL:
                try:
                    # Handle currency symbols and formatting
                    clean_value = str(value).replace(",", "").replace("CHF", "").strip()
                    decimal_value = float(clean_value)
                    # Check constraints
                    if col_def.min_value is not None and decimal_value < col_def.min_value:
                        result.add_error(
                            row_num,
                            col_name,
                            f"Value {decimal_value} is below minimum {col_def.min_value}",
                        )
                except (ValueError, TypeError):
                    result.add_error(row_num, col_name, f"Invalid decimal value: {value}")

    return result


def process_csv_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process and clean CSV data, compute derived fields.

    Args:
        df: Raw DataFrame from CSV

    Returns:
        Processed DataFrame with computed fields
    """
    # Create a copy to avoid modifying original
    processed_df = df.copy()

    # Clean decimal fields (remove currency symbols, commas)
    decimal_columns = [
        "Ramp-Up Start Consumption (CHF)",
        "Steady-State Monthly Consumption (CHF)",
    ]
    for col in decimal_columns:
        if col in processed_df.columns:
            processed_df[col] = (
                processed_df[col]
                .astype(str)
                .str.replace(",", "")
                .str.replace("CHF", "")
                .str.strip()
                .astype(float)
            )

    # Ensure integer columns are integers
    integer_columns = ["Ramp-Up Duration (Months)"]
    for col in integer_columns:
        if col in processed_df.columns:
            processed_df[col] = processed_df[col].astype(int)

    # Compute derived fields for each row
    for idx, row in processed_df.iterrows():
        computed = compute_derived_fields(row.to_dict())
        for col_name, value in computed.items():
            processed_df.at[idx, col_name] = value

    return processed_df
