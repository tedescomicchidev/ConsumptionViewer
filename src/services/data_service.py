"""Data service layer for managing datasets and revisions"""
import json
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from src.models.database import AuditLog, Dataset, DatasetRevision, PlanRow
from src.services.validation import process_csv_data, validate_csv_schema
from src.utils.formulas import compute_derived_fields


class DataService:
    """Service for managing consumption plan datasets"""

    def __init__(self, session: Session, current_user: str = "system"):
        self.session = session
        self.current_user = current_user

    def create_dataset_from_csv(
        self, df: pd.DataFrame, filename: str, dataset_name: Optional[str] = None
    ) -> Tuple[Optional[Dataset], Optional[str]]:
        """
        Create a new dataset from CSV data.
        
        Args:
            df: DataFrame with CSV data
            filename: Original filename
            dataset_name: Optional custom name for the dataset
            
        Returns:
            Tuple of (Dataset object, error message if failed)
        """
        # Validate schema
        validation_result = validate_csv_schema(df)
        if not validation_result.is_valid():
            error_report = validation_result.get_error_report()
            return None, f"Validation failed: {len(validation_result.errors)} errors found"

        # Process data (compute derived fields)
        processed_df = process_csv_data(df)

        # Create dataset
        dataset = Dataset(
            dataset_id=uuid.uuid4(),
            name=dataset_name or filename,
            original_filename=filename,
            created_by=self.current_user,
            schema_version="v1",
        )

        # Create initial revision
        revision = DatasetRevision(
            revision_id=uuid.uuid4(),
            dataset_id=dataset.dataset_id,
            revision_number=1,
            created_by=self.current_user,
            change_summary="Initial upload",
        )

        # Create plan rows
        for _, row in processed_df.iterrows():
            plan_row = PlanRow(
                row_id=uuid.uuid4(),
                revision_id=revision.revision_id,
                workload=str(row["Workload"]),
                scenario=str(row["Scenario"]),
                azure_services=str(row["Azure Services"]),
                start_month=str(row["Start Month"]),
                ramp_up_duration_months=int(row["Ramp-Up Duration (Months)"]),
                ramp_up_start_consumption=float(row["Ramp-Up Start Consumption (CHF)"]),
                steady_state_monthly_consumption=float(
                    row["Steady-State Monthly Consumption (CHF)"]
                ),
                avg_monthly_ramp_up_consumption=float(
                    row["Avg Monthly Consumption During Ramp-Up (CHF)"]
                ),
                total_ramp_up_consumption=float(row["Total Ramp-Up Consumption (CHF)"]),
                year1_steady_state_months=int(row["Year-1 Steady-State Months"]),
                year1_steady_state_consumption=float(
                    row["Year-1 Steady-State Consumption (CHF)"]
                ),
                total_year1_estimated_acr=float(row["Total Year-1 Estimated ACR (CHF)"]),
            )
            revision.plan_rows.append(plan_row)

        # Set current revision
        dataset.current_revision_id = revision.revision_id
        dataset.revisions.append(revision)

        # Save to database
        self.session.add(dataset)
        self.session.commit()

        # Log audit event
        self._log_audit(
            dataset_id=dataset.dataset_id,
            revision_id=revision.revision_id,
            action="UPLOAD",
            details={"filename": filename, "row_count": len(processed_df)},
        )

        return dataset, None

    def save_revision(
        self, dataset_id: uuid.UUID, updated_df: pd.DataFrame, change_summary: str = ""
    ) -> Tuple[Optional[DatasetRevision], Optional[str]]:
        """
        Save changes as a new revision.
        
        Args:
            dataset_id: UUID of the dataset
            updated_df: Updated DataFrame with changes
            change_summary: Summary of changes made
            
        Returns:
            Tuple of (DatasetRevision object, error message if failed)
        """
        # Get dataset
        dataset = self.session.query(Dataset).filter_by(dataset_id=dataset_id).first()
        if not dataset:
            return None, "Dataset not found"

        # Validate data
        validation_result = validate_csv_schema(updated_df)
        if not validation_result.is_valid():
            return None, f"Validation failed: {len(validation_result.errors)} errors"

        # Process data (recompute derived fields)
        processed_df = process_csv_data(updated_df)

        # Get next revision number
        last_revision = (
            self.session.query(DatasetRevision)
            .filter_by(dataset_id=dataset_id)
            .order_by(DatasetRevision.revision_number.desc())
            .first()
        )
        next_revision_num = (last_revision.revision_number + 1) if last_revision else 1

        # Create new revision
        revision = DatasetRevision(
            revision_id=uuid.uuid4(),
            dataset_id=dataset_id,
            revision_number=next_revision_num,
            created_by=self.current_user,
            change_summary=change_summary or "Manual edit",
        )

        # Create plan rows
        for _, row in processed_df.iterrows():
            plan_row = PlanRow(
                row_id=uuid.uuid4(),
                revision_id=revision.revision_id,
                workload=str(row["Workload"]),
                scenario=str(row["Scenario"]),
                azure_services=str(row["Azure Services"]),
                start_month=str(row["Start Month"]),
                ramp_up_duration_months=int(row["Ramp-Up Duration (Months)"]),
                ramp_up_start_consumption=float(row["Ramp-Up Start Consumption (CHF)"]),
                steady_state_monthly_consumption=float(
                    row["Steady-State Monthly Consumption (CHF)"]
                ),
                avg_monthly_ramp_up_consumption=float(
                    row["Avg Monthly Consumption During Ramp-Up (CHF)"]
                ),
                total_ramp_up_consumption=float(row["Total Ramp-Up Consumption (CHF)"]),
                year1_steady_state_months=int(row["Year-1 Steady-State Months"]),
                year1_steady_state_consumption=float(
                    row["Year-1 Steady-State Consumption (CHF)"]
                ),
                total_year1_estimated_acr=float(row["Total Year-1 Estimated ACR (CHF)"]),
            )
            revision.plan_rows.append(plan_row)

        # Update dataset current revision
        dataset.current_revision_id = revision.revision_id

        # Save to database
        self.session.add(revision)
        self.session.commit()

        # Log audit event
        self._log_audit(
            dataset_id=dataset_id,
            revision_id=revision.revision_id,
            action="SAVE",
            details={"row_count": len(processed_df), "change_summary": change_summary},
        )

        return revision, None

    def get_dataset_data(self, dataset_id: uuid.UUID) -> Optional[pd.DataFrame]:
        """Get current revision data as DataFrame"""
        dataset = self.session.query(Dataset).filter_by(dataset_id=dataset_id).first()
        if not dataset or not dataset.current_revision_id:
            return None

        revision = (
            self.session.query(DatasetRevision)
            .filter_by(revision_id=dataset.current_revision_id)
            .first()
        )
        if not revision:
            return None

        # Convert plan rows to DataFrame
        rows_data = []
        for row in revision.plan_rows:
            rows_data.append(
                {
                    "Workload": row.workload,
                    "Scenario": row.scenario,
                    "Azure Services": row.azure_services,
                    "Start Month": row.start_month,
                    "Ramp-Up Duration (Months)": row.ramp_up_duration_months,
                    "Ramp-Up Start Consumption (CHF)": float(row.ramp_up_start_consumption),
                    "Steady-State Monthly Consumption (CHF)": float(
                        row.steady_state_monthly_consumption
                    ),
                    "Avg Monthly Consumption During Ramp-Up (CHF)": float(
                        row.avg_monthly_ramp_up_consumption
                    ),
                    "Total Ramp-Up Consumption (CHF)": float(row.total_ramp_up_consumption),
                    "Year-1 Steady-State Months": row.year1_steady_state_months,
                    "Year-1 Steady-State Consumption (CHF)": float(
                        row.year1_steady_state_consumption
                    ),
                    "Total Year-1 Estimated ACR (CHF)": float(row.total_year1_estimated_acr),
                }
            )

        return pd.DataFrame(rows_data)

    def export_to_csv(self, dataset_id: uuid.UUID) -> Optional[pd.DataFrame]:
        """Export current revision to CSV format"""
        return self.get_dataset_data(dataset_id)

    def _log_audit(
        self,
        action: str,
        dataset_id: Optional[uuid.UUID] = None,
        revision_id: Optional[uuid.UUID] = None,
        details: Optional[dict] = None,
    ):
        """Log audit event"""
        audit = AuditLog(
            audit_id=uuid.uuid4(),
            dataset_id=dataset_id,
            revision_id=revision_id,
            actor=self.current_user,
            action=action,
            details_json=json.dumps(details) if details else None,
        )
        self.session.add(audit)
