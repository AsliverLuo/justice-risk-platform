from context_builders import build_complaint_context

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import engine, SessionLocal
from models import Base, Applicant, CaseRecord, Defendant, Evidence, DocumentOption
from schemas import CaseCreate

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "后端启动成功"}


@app.get("/ping")
def ping():
    return {"ping": "pong"}


@app.post("/cases")
def create_case(data: CaseCreate):
    db = SessionLocal()
    try:
        applicant = Applicant(
            name=data.applicant.name,
            gender=data.applicant.gender,
            birth_date=data.applicant.birth_date,
            ethnicity=data.applicant.ethnicity,
            id_number=data.applicant.id_number,
            phone=data.applicant.phone,
            hukou_address=data.applicant.hukou_address,
            current_address=data.applicant.current_address,
            id_card_front=data.applicant.id_card_front,
            id_card_back=data.applicant.id_card_back,
            signature_file=data.applicant.signature_file,
            has_agent=data.applicant.has_agent,
            agent_info=data.applicant.agent_info,
        )
        db.add(applicant)
        db.commit()
        db.refresh(applicant)

        case_record = CaseRecord(
            applicant_id=applicant.id,
            work_start_date=data.work_info.work_start_date,
            work_end_date=data.work_info.work_end_date,
            actual_work_days=data.work_info.actual_work_days,
            project_name=data.work_info.project_name,
            work_address=data.work_info.work_address,
            job_type=data.work_info.job_type,
            agreed_wage_standard=data.work_info.agreed_wage_standard,
            total_wage_due=data.work_info.total_wage_due,
            paid_amount=data.work_info.paid_amount,
            unpaid_amount=data.work_info.unpaid_amount,
            wage_calc_desc=data.work_info.wage_calc_desc,
            employer_name=data.work_info.employer_name,
            employer_phone=data.work_info.employer_phone,
            has_repeated_demand=data.work_info.has_repeated_demand,
            demand_desc=data.work_info.demand_desc,
        )
        db.add(case_record)
        db.commit()
        db.refresh(case_record)

        for item in data.defendants:
            is_empty_defendant = (
                not item.defendant_type.strip()
                and not item.name.strip()
                and not item.credit_code_or_id_number.strip()
                and not item.phone.strip()
                and not item.address.strip()
                and not item.legal_representative.strip()
                and not item.legal_representative_title.strip()
                and not item.role_type.strip()
                and not item.project_relation_desc.strip()
            )
            if is_empty_defendant:
                continue

            defendant = Defendant(
                case_id=case_record.id,
                defendant_type=item.defendant_type,
                name=item.name,
                credit_code_or_id_number=item.credit_code_or_id_number,
                phone=item.phone,
                address=item.address,
                legal_representative=item.legal_representative,
                legal_representative_title=item.legal_representative_title,
                role_type=item.role_type,
                is_actual_controller=item.is_actual_controller,
                has_payment_promise=item.has_payment_promise,
                project_relation_desc=item.project_relation_desc,
            )
            db.add(defendant)

        for item in data.evidences:
            is_empty_evidence = (
                not item.evidence_type.strip()
                and not item.file_path.strip()
                and not item.description.strip()
            )
            if is_empty_evidence:
                continue

            evidence = Evidence(
                case_id=case_record.id,
                evidence_type=item.evidence_type,
                file_path=item.file_path,
                description=item.description,
            )
            db.add(evidence)

        document_option = DocumentOption(
            case_id=case_record.id,
            court_name=data.document_options.court_name,
            case_cause=data.document_options.case_cause,
            apply_support_prosecution=data.document_options.apply_support_prosecution,
            claim_litigation_cost=data.document_options.claim_litigation_cost,
            document_types=",".join(data.document_options.document_types),
        )
        db.add(document_option)

        db.commit()

        return {
            "message": "案件提交成功，并已保存到数据库",
            "applicant_id": applicant.id,
            "case_id": case_record.id,
            "received_data": data.model_dump()
        }
    finally:
        db.close()


@app.get("/cases/{case_id}")
def get_case_detail(case_id: int):
    db = SessionLocal()
    try:
        case_record = db.query(CaseRecord).filter(CaseRecord.id == case_id).first()
        if not case_record:
            raise HTTPException(status_code=404, detail="案件不存在")

        applicant = db.query(Applicant).filter(Applicant.id == case_record.applicant_id).first()
        if not applicant:
            raise HTTPException(status_code=404, detail="申请人信息不存在")

        defendants = db.query(Defendant).filter(Defendant.case_id == case_id).all()
        evidences = db.query(Evidence).filter(Evidence.case_id == case_id).all()
        document_option = db.query(DocumentOption).filter(DocumentOption.case_id == case_id).first()

        document_types = []
        if document_option and document_option.document_types:
            document_types = [
                item.strip()
                for item in document_option.document_types.split(",")
                if item.strip()
            ]

        result = {
            "case_id": case_record.id,
            "applicant_id": applicant.id,
            "applicant": {
                "name": applicant.name,
                "gender": applicant.gender,
                "birth_date": applicant.birth_date,
                "ethnicity": applicant.ethnicity,
                "id_number": applicant.id_number,
                "phone": applicant.phone,
                "hukou_address": applicant.hukou_address,
                "current_address": applicant.current_address,
                "id_card_front": applicant.id_card_front,
                "id_card_back": applicant.id_card_back,
                "signature_file": applicant.signature_file,
                "has_agent": applicant.has_agent,
                "agent_info": applicant.agent_info,
            },
            "work_info": {
                "work_start_date": case_record.work_start_date,
                "work_end_date": case_record.work_end_date,
                "actual_work_days": case_record.actual_work_days,
                "project_name": case_record.project_name,
                "work_address": case_record.work_address,
                "job_type": case_record.job_type,
                "agreed_wage_standard": case_record.agreed_wage_standard,
                "total_wage_due": case_record.total_wage_due,
                "paid_amount": case_record.paid_amount,
                "unpaid_amount": case_record.unpaid_amount,
                "wage_calc_desc": case_record.wage_calc_desc,
                "employer_name": case_record.employer_name,
                "employer_phone": case_record.employer_phone,
                "has_repeated_demand": case_record.has_repeated_demand,
                "demand_desc": case_record.demand_desc,
            },
            "defendants": [
                {
                    "id": item.id,
                    "defendant_type": item.defendant_type,
                    "name": item.name,
                    "credit_code_or_id_number": item.credit_code_or_id_number,
                    "phone": item.phone,
                    "address": item.address,
                    "legal_representative": item.legal_representative,
                    "legal_representative_title": item.legal_representative_title,
                    "role_type": item.role_type,
                    "is_actual_controller": item.is_actual_controller,
                    "has_payment_promise": item.has_payment_promise,
                    "project_relation_desc": item.project_relation_desc,
                }
                for item in defendants
            ],
            "evidences": [
                {
                    "id": item.id,
                    "evidence_type": item.evidence_type,
                    "file_path": item.file_path,
                    "description": item.description,
                }
                for item in evidences
            ],
            "document_options": {
                "court_name": document_option.court_name if document_option else "",
                "case_cause": document_option.case_cause if document_option else "",
                "apply_support_prosecution": (
                    document_option.apply_support_prosecution if document_option else False
                ),
                "claim_litigation_cost": (
                    document_option.claim_litigation_cost if document_option else False
                ),
                "document_types": document_types,
            },
        }

        return result
    finally:
        db.close()
@app.get("/cases/{case_id}/complaint-context")
def get_complaint_context(case_id: int):
    return build_complaint_context(case_id)
