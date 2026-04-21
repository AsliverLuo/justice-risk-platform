from __future__ import annotations

from datetime import date, timedelta

from app.db.session import SessionLocal, init_db
from app.modules.analysis.models import CaseCorpus


def build_case(index: int, *, title: str, community_id: str, community_name: str, street_name: str, project_name: str | None, risk_type: str, case_type: str, defendant_names: list[str], people_count: int, total_amount: float, judgment_date: date) -> CaseCorpus:
    entities = {
        'persons': ['申请人甲'],
        'companies': defendant_names,
        'amounts': [f'{total_amount:.0f}元'] if total_amount else [],
        'amount_total_estimate': total_amount,
        'projects': [project_name] if project_name else [],
    }
    extra_meta = {
        'community_id': community_id,
        'community_name': community_name,
        'street_name': street_name,
        'project_name': project_name,
        'risk_type': risk_type,
        'people_count': people_count,
        'total_amount': total_amount,
        'defendant_names': defendant_names,
    }
    return CaseCorpus(
        source_type='demo',
        source_ref=f'community-risk-demo-{index}',
        title=title,
        case_no=f'DEMO-{index:03d}',
        full_text=f'{title}，涉及社区{community_name}，主体{",".join(defendant_names)}，项目{project_name or "无"}。',
        case_type=case_type,
        plaintiff_summary='申请人甲',
        defendant_summary='；'.join(defendant_names),
        claim_summary='请求支付费用',
        focus_summary='是否存在持续性风险',
        fact_summary='用于任务6演示数据',
        judgment_summary='演示样本',
        court_name='演示法院',
        city='北京',
        judgment_date=judgment_date,
        entities=entities,
        cited_laws=[],
        extra_meta=extra_meta,
        embedding=None,
    )


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        today = date.today()
        db.query(CaseCorpus).filter(CaseCorpus.source_type == 'demo').delete()  # type: ignore[attr-defined]
        cases: list[CaseCorpus] = []

        # 社区A：高频主体 + 群体性项目
        for i in range(1, 34):
            cases.append(
                build_case(
                    i,
                    title=f'某建设公司欠薪投诉样本{i}',
                    community_id='c-a',
                    community_name='新街口社区',
                    street_name='新街口街道',
                    project_name='新街口排水改造项目',
                    risk_type='wage_arrears',
                    case_type='labor_service_dispute',
                    defendant_names=['某建设公司'],
                    people_count=1,
                    total_amount=3000 + i * 50,
                    judgment_date=today - timedelta(days=i % 20),
                )
            )

        cases.append(
            build_case(
                100,
                title='新街口排水改造项目群体欠薪',
                community_id='c-a',
                community_name='新街口社区',
                street_name='新街口街道',
                project_name='新街口排水改造项目',
                risk_type='wage_arrears',
                case_type='labor_service_dispute',
                defendant_names=['某建设公司'],
                people_count=12,
                total_amount=120000,
                judgment_date=today - timedelta(days=3),
            )
        )

        # 社区B：劳动争议增长
        for i in range(200, 206):
            cases.append(
                build_case(
                    i,
                    title=f'德胜社区劳动争议样本{i}',
                    community_id='c-b',
                    community_name='德胜社区',
                    street_name='德胜街道',
                    project_name=None,
                    risk_type='labor_dispute',
                    case_type='labor_dispute',
                    defendant_names=['某科技有限公司'],
                    people_count=2,
                    total_amount=8000,
                    judgment_date=today - timedelta(days=i - 199),
                )
            )

        for i in range(300, 302):
            cases.append(
                build_case(
                    i,
                    title=f'德胜社区上一周期劳动争议样本{i}',
                    community_id='c-b',
                    community_name='德胜社区',
                    street_name='德胜街道',
                    project_name=None,
                    risk_type='labor_dispute',
                    case_type='labor_dispute',
                    defendant_names=['某科技有限公司'],
                    people_count=1,
                    total_amount=5000,
                    judgment_date=today - timedelta(days=40 + i - 300),
                )
            )

        db.add_all(cases)
        db.commit()
        print({'seeded_cases': len(cases)})
    finally:
        db.close()


if __name__ == '__main__':
    main()
