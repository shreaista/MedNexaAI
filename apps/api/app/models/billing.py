"""Billing tables mapped to `public.*` (explicit PK columns)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Charge(Base):
    __tablename__ = "charges"

    charge_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=False,
    )
    visit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("clinical_visits.visit_id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("providers.provider_id", ondelete="SET NULL"),
        nullable=True,
    )
    charge_status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    primary_icd10: Mapped[str | None] = mapped_column(String(16), nullable=True)
    primary_cpt: Mapped[str | None] = mapped_column(String(16), nullable=True)
    total_units: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    charge_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    ai_charge_suggested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    documentation_support_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class BillingQueue(Base):
    __tablename__ = "billing_queue"

    queue_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=False,
    )
    charge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("charges.charge_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    queue_status: Mapped[str] = mapped_column(String(32), nullable=False, default="NEW")
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="NORMAL")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ClaimReadiness(Base):
    __tablename__ = "claim_readiness"

    readiness_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=False,
    )
    charge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("charges.charge_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    readiness_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    missing_note_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    missing_diagnosis_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    missing_cpt_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    missing_authorization_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payer_rule_issue_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    readiness_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class DenialRisk(Base):
    __tablename__ = "denial_risk"

    denial_risk_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    charge_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("charges.charge_id", ondelete="CASCADE"),
        nullable=True,
    )
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ClaimEvent(Base):
    __tablename__ = "claim_events"

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    charge_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("charges.charge_id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
