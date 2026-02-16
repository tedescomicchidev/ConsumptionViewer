"""CSV schema definition and validation for v1"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ColumnType(Enum):
    """Column data types"""

    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"


@dataclass
class ColumnDefinition:
    """Definition of a CSV column"""

    name: str
    type: ColumnType
    required: bool
    editable: bool
    computed: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None


# CSV Schema v1 - matching PRD specification
CSV_SCHEMA_V1: List[ColumnDefinition] = [
    ColumnDefinition(
        name="Workload", type=ColumnType.STRING, required=True, editable=True, computed=False
    ),
    ColumnDefinition(
        name="Scenario", type=ColumnType.STRING, required=True, editable=True, computed=False
    ),
    ColumnDefinition(
        name="Azure Services",
        type=ColumnType.STRING,
        required=True,
        editable=True,
        computed=False,
    ),
    ColumnDefinition(
        name="Start Month", type=ColumnType.STRING, required=True, editable=True, computed=False
    ),
    ColumnDefinition(
        name="Ramp-Up Duration (Months)",
        type=ColumnType.INTEGER,
        required=True,
        editable=True,
        computed=False,
        min_value=0,
        max_value=12,
    ),
    ColumnDefinition(
        name="Ramp-Up Start Consumption (CHF)",
        type=ColumnType.DECIMAL,
        required=True,
        editable=True,
        computed=False,
        min_value=0,
    ),
    ColumnDefinition(
        name="Steady-State Monthly Consumption (CHF)",
        type=ColumnType.DECIMAL,
        required=True,
        editable=True,
        computed=False,
        min_value=0,
    ),
    # Computed columns
    ColumnDefinition(
        name="Avg Monthly Consumption During Ramp-Up (CHF)",
        type=ColumnType.DECIMAL,
        required=False,
        editable=False,
        computed=True,
    ),
    ColumnDefinition(
        name="Total Ramp-Up Consumption (CHF)",
        type=ColumnType.DECIMAL,
        required=False,
        editable=False,
        computed=True,
    ),
    ColumnDefinition(
        name="Year-1 Steady-State Months",
        type=ColumnType.INTEGER,
        required=False,
        editable=False,
        computed=True,
    ),
    ColumnDefinition(
        name="Year-1 Steady-State Consumption (CHF)",
        type=ColumnType.DECIMAL,
        required=False,
        editable=False,
        computed=True,
    ),
    ColumnDefinition(
        name="Total Year-1 Estimated ACR (CHF)",
        type=ColumnType.DECIMAL,
        required=False,
        editable=False,
        computed=True,
    ),
]

# Create lookup dictionaries
SCHEMA_BY_NAME: Dict[str, ColumnDefinition] = {col.name: col for col in CSV_SCHEMA_V1}
REQUIRED_COLUMNS: List[str] = [col.name for col in CSV_SCHEMA_V1 if col.required]
EDITABLE_COLUMNS: List[str] = [col.name for col in CSV_SCHEMA_V1 if col.editable]
COMPUTED_COLUMNS: List[str] = [col.name for col in CSV_SCHEMA_V1 if col.computed]
