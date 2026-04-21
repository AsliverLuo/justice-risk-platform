from enum import Enum


class CaseType(str, Enum):
    labor_service_dispute = "labor_service_dispute"
    labor_dispute = "labor_dispute"
    support_prosecution = "support_prosecution"
    other = "other"


class RiskLevel(str, Enum):
    blue = "blue"
    yellow = "yellow"
    orange = "orange"
    red = "red"


class DefendantType(str, Enum):
    company = "company"
    individual = "individual"


class DefendantRole(str, Enum):
    employer = "employer"
    contractor = "contractor"
    project_owner = "project_owner"
    guarantor = "guarantor"
    actual_controller = "actual_controller"
    other = "other"


class LegalDocumentType(str, Enum):
    civil_complaint = "civil_complaint"
    support_prosecution_letter = "support_prosecution_letter"


class KnowledgeSourceType(str, Enum):
    law = "law"
    judicial_interpretation = "judicial_interpretation"
    guidance = "guidance"
    policy = "policy"
    example = "example"


class ScopeType(str, Enum):
    community = "community"
    street = "street"
    project = "project"


class AlertStatus(str, Enum):
    active = "active"
    acknowledged = "acknowledged"
    closed = "closed"


class PropagandaArticleStatus(str, Enum):
    draft = 'draft'
    published = 'published'
    archived = 'archived'


class PropagandaPushStatus(str, Enum):
    active = 'active'
    consumed = 'consumed'
    archived = 'archived'
