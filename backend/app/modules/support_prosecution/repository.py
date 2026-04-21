from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.support_prosecution.models import (
    Applicant,
    CaseRecord,
    Defendant,
    DocumentOption,
    Evidence,
)
from app.modules.support_prosecution.schemas import CaseCreate


class SupportProsecutionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_case(self, data: CaseCreate) -> tuple[Applicant, CaseRecord]:
        applicant = Applicant(**data.applicant.model_dump())
        self.db.add(applicant)
        self.db.flush()

        case_record = CaseRecord(
            applicant_id=applicant.id,
            **data.work_info.model_dump(),
        )
        self.db.add(case_record)
        self.db.flush()

        for item in data.defendants:
            payload = item.model_dump()
            if not any(str(value).strip() for value in payload.values() if value is not False):
                continue
            self.db.add(Defendant(case_id=case_record.id, **payload))

        for item in data.evidences:
            payload = item.model_dump()
            if not any(str(value).strip() for value in payload.values()):
                continue
            self.db.add(Evidence(case_id=case_record.id, **payload))

        self.db.add(
            DocumentOption(
                case_id=case_record.id,
                court_name=data.document_options.court_name,
                case_cause=data.document_options.case_cause,
                apply_support_prosecution=data.document_options.apply_support_prosecution,
                claim_litigation_cost=data.document_options.claim_litigation_cost,
                document_types=",".join(data.document_options.document_types),
            )
        )
        self.db.flush()
        return applicant, case_record

    def get_case(self, case_id: int) -> CaseRecord | None:
        return self.db.get(CaseRecord, case_id)

    def get_applicant(self, applicant_id: int) -> Applicant | None:
        return self.db.get(Applicant, applicant_id)

    def list_defendants(self, case_id: int) -> list[Defendant]:
        stmt = select(Defendant).where(Defendant.case_id == case_id)
        return list(self.db.scalars(stmt).all())

    def list_evidences(self, case_id: int) -> list[Evidence]:
        stmt = select(Evidence).where(Evidence.case_id == case_id)
        return list(self.db.scalars(stmt).all())

    def get_document_option(self, case_id: int) -> DocumentOption | None:
        stmt = select(DocumentOption).where(DocumentOption.case_id == case_id)
        return self.db.scalar(stmt)
