# Package 2：analysis 模块落地说明

这个包是在第 1 包“知识库与基础设施”之上继续补齐 AI 工程师的一段核心工作，主要覆盖两部分：

1. 第一阶段的“案例语料处理与 NLP 基础能力”
2. 第二阶段的“风险评分模型入口”

## 新增内容

- `backend/app/modules/analysis/`
  - `models.py`：案例语料表 `case_corpus`
  - `schemas.py`：请求体 / 返回体定义
  - `repository.py`：案例语料混合检索
  - `rules.py`：规则分类、实体抽取、风险评分
  - `service.py`：业务编排
  - `router.py`：API 路由
- `backend/scripts/seed_case_corpus.py`：样例案例语料导入脚本
- `mock_data/case_corpus_sample.json`：案例样例
- `backend/tests/test_analysis_rules.py`
- `backend/tests/test_risk_score.py`

## 同步修改

- `backend/app/main.py`
  - 用 `lifespan` 替换了 `@app.on_event("startup")`
  - 这样可以消掉你日志里的 deprecation warning
- `backend/app/api/v1/router.py`
  - 已挂载 analysis 路由
- `backend/app/db/session.py`
  - 已把 analysis 模型注册进建表流程
- `backend/app/core/config.py`
  - 补了案例检索与风险评分相关配置项

## 这包解决的能力

### 1. 案件文本分类
- `support_prosecution`
- `labor_service_dispute`
- `labor_dispute`
- `other`

### 2. 关键实体抽取
- 自然人
- 企业主体
- 金额
- 日期
- 地址
- 工地/项目
- 电话
- 身份证号
- 文本中出现的法条引用

### 3. 法条关联
分析文本后，会自动调用你第 1 包的 `knowledge` 模块进行法条召回。

### 4. 风险评分
按方案里的第二阶段权重结构实现：
- 欠薪案件数量 30%
- 涉案总金额 25%
- 涉及人数 20%
- 近期增长趋势 15%
- 同一被告复现率 10%

当前采用“可演示、可配置”的归一化上限，后续接入真实数据后可按样本重新标定。

## API

### 导入案例语料
`POST /api/v1/analysis/corpus/batch-upsert`

### 检索案例语料
`POST /api/v1/analysis/corpus/search`

### 获取案例详情
`GET /api/v1/analysis/corpus/{case_id}`

### 分析案件文本
`POST /api/v1/analysis/text`

### 计算聚合风险分数
`POST /api/v1/analysis/risk-score`

## 本地运行顺序

```bash
cd backend
python -m app.db.init_db
python -m app.main
```

另开一个终端导入案例样例：

```bash
cd backend
python -m scripts.seed_case_corpus
```

## 推荐你立刻验证的 3 个接口

1. `/health`
2. `/api/v1/analysis/text`
3. `/api/v1/analysis/risk-score`

## 建议的继续顺序

先把 analysis 跑通，再继续下一包：
- `support_prosecution`
- `document_gen`
- `workflow`
- `recommendation / propaganda`
