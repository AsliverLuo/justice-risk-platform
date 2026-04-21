from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    birth_date = Column(String, nullable=False)
    ethnicity = Column(String, nullable=False)
    id_number = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    hukou_address = Column(Text, nullable=False)
    current_address = Column(Text, nullable=False)
    id_card_front = Column(String, nullable=False)
    id_card_back = Column(String, nullable=False)
    signature_file = Column(String, nullable=False)
    has_agent = Column(Boolean, default=False)
    agent_info = Column(Text, nullable=True)

    cases = relationship("CaseRecord", back_populates="applicant")


class CaseRecord(Base):
    __tablename__ = "case_records"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False)

    work_start_date = Column(String, nullable=False)
    work_end_date = Column(String, nullable=False)
    actual_work_days = Column(Integer, nullable=False)
    project_name = Column(String, nullable=False)
    work_address = Column(Text, nullable=False)
    job_type = Column(String, nullable=False)
    agreed_wage_standard = Column(String, nullable=False)
    total_wage_due = Column(Float, nullable=False)
    paid_amount = Column(Float, nullable=False)
    unpaid_amount = Column(Float, nullable=False)
    wage_calc_desc = Column(Text, nullable=False)
    employer_name = Column(String, nullable=False)
    employer_phone = Column(String, nullable=False)
    has_repeated_demand = Column(Boolean, default=False)
    demand_desc = Column(Text, nullable=False)

    applicant = relationship("Applicant", back_populates="cases")
    defendants = relationship("Defendant", back_populates="case", cascade="all, delete-orphan")
    evidences = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    document_option = relationship("DocumentOption", back_populates="case", uselist=False, cascade="all, delete-orphan")


class Defendant(Base):
    __tablename__ = "defendants"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case_records.id"), nullable=False)

    defendant_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    credit_code_or_id_number = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    legal_representative = Column(String, nullable=False)
    legal_representative_title = Column(String, nullable=False)
    role_type = Column(String, nullable=False)
    is_actual_controller = Column(Boolean, default=False)
    has_payment_promise = Column(Boolean, default=False)
    project_relation_desc = Column(Text, nullable=False)

    case = relationship("CaseRecord", back_populates="defendants")


class Evidence(Base):
    __tablename__ = "evidences"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case_records.id"), nullable=False)

    evidence_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    case = relationship("CaseRecord", back_populates="evidences")


class DocumentOption(Base):
    __tablename__ = "document_options"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case_records.id"), nullable=False, unique=True)

    court_name = Column(String, nullable=False)
    case_cause = Column(String, nullable=False)
    apply_support_prosecution = Column(Boolean, default=False)
    claim_litigation_cost = Column(Boolean, default=False)
    document_types = Column(Text, nullable=False)

    case = relationship("CaseRecord", back_populates="document_option")
