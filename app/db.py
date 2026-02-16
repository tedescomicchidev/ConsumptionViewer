from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from app.config import SCHEMA_VERSION, get_database_url


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "datasets"

    dataset_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(400), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_by: Mapped[str] = mapped_column(String(200), nullable=False)
    current_revision_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(50), nullable=False)

    revisions: Mapped[list[DatasetRevision]] = relationship(back_populates="dataset")


class DatasetRevision(Base):
    __tablename__ = "dataset_revisions"

    revision_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.dataset_id"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_by: Mapped[str] = mapped_column(String(200), nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String, nullable=True)

    dataset: Mapped[Dataset] = relationship(back_populates="revisions")
    rows: Mapped[list[PlanRow]] = relationship(back_populates="revision")


class PlanRow(Base):
    __tablename__ = "plan_rows"

    row_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    revision_id: Mapped[str] = mapped_column(String(36), ForeignKey("dataset_revisions.revision_id"), nullable=False)
    workload: Mapped[str] = mapped_column(String(300), nullable=False)
    scenario: Mapped[str] = mapped_column(String(100), nullable=False)
    azure_services: Mapped[str] = mapped_column(String(800), nullable=False)
    start_month: Mapped[str] = mapped_column(String(30), nullable=False)
    ramp_up_duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    ramp_up_start_consumption: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    steady_state_monthly_consumption: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    avg_monthly_ramp_up_consumption: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    total_ramp_up_consumption: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    year1_steady_state_months: Mapped[int] = mapped_column(Integer, nullable=False)
    year1_steady_state_consumption: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    total_year1_estimated_acr: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    extras_json: Mapped[str | None] = mapped_column(String, nullable=True)

    revision: Mapped[DatasetRevision] = relationship(back_populates="rows")


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    revision_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor: Mapped[str] = mapped_column(String(200), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    details_json: Mapped[str | None] = mapped_column(String, nullable=True)


def get_engine(db_url: str | None = None):
    return create_engine(db_url or get_database_url(), future=True)


def init_db(db_url: str | None = None) -> None:
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _record_audit(session: Session, dataset_id: str, revision_id: str | None, actor: str, action: str, details: dict[str, Any] | None = None) -> None:
    session.add(
        AuditLog(
            audit_id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            revision_id=revision_id,
            actor=actor,
            action=action,
            timestamp=_now(),
            details_json=json.dumps(details or {}),
        )
    )


def create_dataset_with_revision(df: pd.DataFrame, filename: str, actor: str, dataset_name: str | None = None) -> str:
    engine = get_engine()
    dataset_id = str(uuid.uuid4())
    revision_id = str(uuid.uuid4())
    with Session(engine) as session:
        dataset = Dataset(
            dataset_id=dataset_id,
            name=dataset_name or filename,
            original_filename=filename,
            created_at=_now(),
            created_by=actor,
            current_revision_id=revision_id,
            schema_version=SCHEMA_VERSION,
        )
        rev = DatasetRevision(
            revision_id=revision_id,
            dataset_id=dataset_id,
            revision_number=1,
            created_at=_now(),
            created_by=actor,
            change_summary="Initial upload",
        )
        session.add(dataset)
        session.add(rev)
        _insert_rows(session, revision_id, df)
        _record_audit(session, dataset_id, revision_id, actor, "UPLOAD", {"filename": filename})
        session.commit()
    return dataset_id


def _insert_rows(session: Session, revision_id: str, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        session.add(
            PlanRow(
                row_id=str(uuid.uuid4()),
                revision_id=revision_id,
                workload=row["Workload"],
                scenario=row["Scenario"],
                azure_services=row["Azure Services"],
                start_month=row["Start Month"],
                ramp_up_duration_months=int(row["Ramp-Up Duration (Months)"]),
                ramp_up_start_consumption=float(row["Ramp-Up Start Consumption (CHF)"]),
                steady_state_monthly_consumption=float(row["Steady-State Monthly Consumption (CHF)"]),
                avg_monthly_ramp_up_consumption=float(row["Avg Monthly Consumption During Ramp-Up (CHF)"]),
                total_ramp_up_consumption=float(row["Total Ramp-Up Consumption (CHF)"]),
                year1_steady_state_months=int(row["Year-1 Steady-State Months"]),
                year1_steady_state_consumption=float(row["Year-1 Steady-State Consumption (CHF)"]),
                total_year1_estimated_acr=float(row["Total Year-1 Estimated ACR (CHF)"]),
                extras_json=None,
            )
        )


def get_dataset_rows(dataset_id: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    engine = get_engine()
    with Session(engine) as session:
        dataset = session.get(Dataset, dataset_id)
        if not dataset or not dataset.current_revision_id:
            raise ValueError("Dataset not found")

        rows = session.scalars(
            select(PlanRow).where(PlanRow.revision_id == dataset.current_revision_id)
        ).all()
        data = [
            {
                "Workload": r.workload,
                "Scenario": r.scenario,
                "Azure Services": r.azure_services,
                "Start Month": r.start_month,
                "Ramp-Up Duration (Months)": r.ramp_up_duration_months,
                "Ramp-Up Start Consumption (CHF)": float(r.ramp_up_start_consumption),
                "Steady-State Monthly Consumption (CHF)": float(r.steady_state_monthly_consumption),
                "Avg Monthly Consumption During Ramp-Up (CHF)": float(r.avg_monthly_ramp_up_consumption),
                "Total Ramp-Up Consumption (CHF)": float(r.total_ramp_up_consumption),
                "Year-1 Steady-State Months": r.year1_steady_state_months,
                "Year-1 Steady-State Consumption (CHF)": float(r.year1_steady_state_consumption),
                "Total Year-1 Estimated ACR (CHF)": float(r.total_year1_estimated_acr),
            }
            for r in rows
        ]
        df = pd.DataFrame(data)
        meta = {
            "dataset_id": dataset.dataset_id,
            "name": dataset.name,
            "current_revision_id": dataset.current_revision_id,
        }
        return df, meta


def save_revision(dataset_id: str, df: pd.DataFrame, actor: str, change_summary: str | None = None) -> str:
    engine = get_engine()
    with Session(engine) as session:
        dataset = session.get(Dataset, dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")

        current_rev_number = (
            session.query(DatasetRevision.revision_number)
            .filter_by(dataset_id=dataset_id)
            .order_by(DatasetRevision.revision_number.desc())
            .first()
        )
        next_number = 1 if not current_rev_number else int(current_rev_number[0]) + 1
        revision_id = str(uuid.uuid4())
        session.add(
            DatasetRevision(
                revision_id=revision_id,
                dataset_id=dataset_id,
                revision_number=next_number,
                created_at=_now(),
                created_by=actor,
                change_summary=change_summary,
            )
        )
        _insert_rows(session, revision_id, df)
        dataset.current_revision_id = revision_id
        _record_audit(session, dataset_id, revision_id, actor, "SAVE", {"revision": next_number})
        session.commit()
        return revision_id
