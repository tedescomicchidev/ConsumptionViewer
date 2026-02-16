"""Database models for MACC Consumption Viewer"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Dataset(Base):
    """Dataset table model"""

    __tablename__ = "datasets"

    dataset_id = Column(
        UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4, nullable=False
    )
    name = Column(String(200), nullable=True)
    original_filename = Column(String(400), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(200), nullable=False)
    current_revision_id = Column(UNIQUEIDENTIFIER, nullable=True)
    schema_version = Column(String(50), nullable=False, default="v1")

    # Relationships
    revisions = relationship(
        "DatasetRevision", back_populates="dataset", cascade="all, delete-orphan"
    )


class DatasetRevision(Base):
    """Dataset revision table model"""

    __tablename__ = "dataset_revisions"

    revision_id = Column(
        UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4, nullable=False
    )
    dataset_id = Column(
        UNIQUEIDENTIFIER, ForeignKey("datasets.dataset_id", ondelete="CASCADE"), nullable=False
    )
    revision_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(200), nullable=False)
    change_summary = Column(Text, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="revisions")
    plan_rows = relationship("PlanRow", back_populates="revision", cascade="all, delete-orphan")


class PlanRow(Base):
    """Plan row table model"""

    __tablename__ = "plan_rows"
    __table_args__ = (
        CheckConstraint(
            "ramp_up_duration_months >= 0 AND ramp_up_duration_months <= 12",
            name="CHK_ramp_up_duration",
        ),
        CheckConstraint(
            "year1_steady_state_months >= 0 AND year1_steady_state_months <= 12",
            name="CHK_year1_steady_months",
        ),
    )

    row_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4, nullable=False)
    revision_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("dataset_revisions.revision_id", ondelete="CASCADE"),
        nullable=False,
    )
    workload = Column(String(300), nullable=False)
    scenario = Column(String(100), nullable=False)
    azure_services = Column(String(800), nullable=False)
    start_month = Column(String(30), nullable=False)
    ramp_up_duration_months = Column(Integer, nullable=False)
    ramp_up_start_consumption = Column(DECIMAL(18, 2), nullable=False)
    steady_state_monthly_consumption = Column(DECIMAL(18, 2), nullable=False)
    avg_monthly_ramp_up_consumption = Column(DECIMAL(18, 2), nullable=False)
    total_ramp_up_consumption = Column(DECIMAL(18, 2), nullable=False)
    year1_steady_state_months = Column(Integer, nullable=False)
    year1_steady_state_consumption = Column(DECIMAL(18, 2), nullable=False)
    total_year1_estimated_acr = Column(DECIMAL(18, 2), nullable=False)
    extras_json = Column(Text, nullable=True)

    # Relationships
    revision = relationship("DatasetRevision", back_populates="plan_rows")


class AuditLog(Base):
    """Audit log table model"""

    __tablename__ = "audit_log"

    audit_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4, nullable=False)
    dataset_id = Column(UNIQUEIDENTIFIER, nullable=True)
    revision_id = Column(UNIQUEIDENTIFIER, nullable=True)
    actor = Column(String(200), nullable=False)
    action = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    details_json = Column(Text, nullable=True)
