from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Applicant(TimestampMixin, Base):
    __tablename__ = "support_prosecution_applicants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)
    birth_date: Mapped[str] = mapped_column(String(32), nullable=False)
    ethnicity: Mapped[str] = mapped_column(String(32), nullable=False)
    id_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    hukou_address: Mapped[str] = mapped_column(Text, nullable=False)
    current_address: Mapped[str] = mapped_column(Text, nullable=False)
    id_card_front: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    id_card_back: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    signature_file: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    has_agent: Mapped[bool] = mapped_column(Boolean, default=False)
    agent_info: Mapped[str | None] = mapped_column(Text, nullable=True)

    cases: Mapped[list["CaseRecord"]] = relationship(back_populates="applicant")


class CaseRecord(TimestampMixin, Base):
    __tablename__ = "support_prosecution_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    applicant_id: Mapped[int] = mapped_column(
        ForeignKey("support_prosecution_applicants.id"),
        nullable=False,
        index=True,
    )

    work_start_date: Mapped[str] = mapped_column(String(32), nullable=False)
    work_end_date: Mapped[str] = mapped_column(String(32), nullable=False)
    actual_work_days: Mapped[int] = mapped_column(Integer, nullable=False)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    work_address: Mapped[str] = mapped_column(Text, nullable=False)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    agreed_wage_standard: Mapped[str] = mapped_column(String(128), nullable=False)
    total_wage_due: Mapped[float] = mapped_column(Float, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Float, nullable=False)
    unpaid_amount: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    wage_calc_desc: Mapped[str] = mapped_column(Text, nullable=False)
    employer_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    employer_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    has_repeated_demand: Mapped[bool] = mapped_column(Boolean, default=False)
    demand_desc: Mapped[str] = mapped_column(Text, nullable=False)

    applicant: Mapped[Applicant] = relationship(back_populates="cases")
    defendants: Mapped[list["Defendant"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    evidences: Mapped[list["Evidence"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    document_option: Mapped["DocumentOption | None"] = relationship(
        back_populates="case",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Defendant(TimestampMixin, Base):
    __tablename__ = "support_prosecution_defendants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("support_prosecution_cases.id"),
        nullable=False,
        index=True,
    )

    defendant_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    credit_code_or_id_number: Mapped[str] = mapped_column(String(64), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    legal_representative: Mapped[str] = mapped_column(String(64), nullable=False)
    legal_representative_title: Mapped[str] = mapped_column(String(64), nullable=False)
    role_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_actual_controller: Mapped[bool] = mapped_column(Boolean, default=False)
    has_payment_promise: Mapped[bool] = mapped_column(Boolean, default=False)
    project_relation_desc: Mapped[str] = mapped_column(Text, nullable=False)

    case: Mapped[CaseRecord] = relationship(back_populates="defendants")


class Evidence(TimestampMixin, Base):
    __tablename__ = "support_prosecution_evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("support_prosecution_cases.id"),
        nullable=False,
        index=True,
    )

    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    case: Mapped[CaseRecord] = relationship(back_populates="evidences")


class DocumentOption(TimestampMixin, Base):
    __tablename__ = "support_prosecution_document_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("support_prosecution_cases.id"),
        nullable=False,
        unique=True,
    )

    court_name: Mapped[str] = mapped_column(String(255), nullable=False)
    case_cause: Mapped[str] = mapped_column(String(128), nullable=False)
    apply_support_prosecution: Mapped[bool] = mapped_column(Boolean, default=False)
    claim_litigation_cost: Mapped[bool] = mapped_column(Boolean, default=False)
    document_types: Mapped[str] = mapped_column(Text, nullable=False)

    case: Mapped[CaseRecord] = relationship(back_populates="document_option")
