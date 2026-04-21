-- 清朗法治项目：第一阶段数据库初始化脚本
-- 说明：
-- 1. 先在 PostgreSQL 中创建数据库 qinglang_fazhi
-- 2. 连接到该数据库后执行本脚本
-- 3. 本脚本包含当前第一阶段所需 5 张核心表

BEGIN;

CREATE TABLE IF NOT EXISTS applicants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    gender VARCHAR(50) NOT NULL,
    birth_date VARCHAR(50) NOT NULL,
    ethnicity VARCHAR(100) NOT NULL,
    id_number VARCHAR(100) NOT NULL,
    phone VARCHAR(100) NOT NULL,
    hukou_address TEXT NOT NULL,
    current_address TEXT NOT NULL,
    id_card_front VARCHAR(500) NOT NULL,
    id_card_back VARCHAR(500) NOT NULL,
    signature_file VARCHAR(500) NOT NULL,
    has_agent BOOLEAN DEFAULT FALSE,
    agent_info TEXT
);

CREATE TABLE IF NOT EXISTS case_records (
    id SERIAL PRIMARY KEY,
    applicant_id INTEGER NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    work_start_date VARCHAR(50) NOT NULL,
    work_end_date VARCHAR(50) NOT NULL,
    actual_work_days INTEGER NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    work_address TEXT NOT NULL,
    job_type VARCHAR(255) NOT NULL,
    agreed_wage_standard VARCHAR(255) NOT NULL,
    total_wage_due DOUBLE PRECISION NOT NULL,
    paid_amount DOUBLE PRECISION NOT NULL,
    unpaid_amount DOUBLE PRECISION NOT NULL,
    wage_calc_desc TEXT NOT NULL,
    employer_name VARCHAR(255) NOT NULL,
    employer_phone VARCHAR(100) NOT NULL,
    has_repeated_demand BOOLEAN DEFAULT FALSE,
    demand_desc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS defendants (
    id SERIAL PRIMARY KEY,
    case_id INTEGER NOT NULL REFERENCES case_records(id) ON DELETE CASCADE,
    defendant_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    credit_code_or_id_number VARCHAR(255) NOT NULL,
    phone VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    legal_representative VARCHAR(255) NOT NULL,
    legal_representative_title VARCHAR(255) NOT NULL,
    role_type VARCHAR(100) NOT NULL,
    is_actual_controller BOOLEAN DEFAULT FALSE,
    has_payment_promise BOOLEAN DEFAULT FALSE,
    project_relation_desc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidences (
    id SERIAL PRIMARY KEY,
    case_id INTEGER NOT NULL REFERENCES case_records(id) ON DELETE CASCADE,
    evidence_type VARCHAR(100) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_options (
    id SERIAL PRIMARY KEY,
    case_id INTEGER NOT NULL UNIQUE REFERENCES case_records(id) ON DELETE CASCADE,
    court_name VARCHAR(255) NOT NULL,
    case_cause VARCHAR(255) NOT NULL,
    apply_support_prosecution BOOLEAN DEFAULT FALSE,
    claim_litigation_cost BOOLEAN DEFAULT FALSE,
    document_types TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_case_records_applicant_id ON case_records(applicant_id);
CREATE INDEX IF NOT EXISTS idx_defendants_case_id ON defendants(case_id);
CREATE INDEX IF NOT EXISTS idx_evidences_case_id ON evidences(case_id);
CREATE INDEX IF NOT EXISTS idx_document_options_case_id ON document_options(case_id);

COMMIT;

-- 可选：查看表
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public';
