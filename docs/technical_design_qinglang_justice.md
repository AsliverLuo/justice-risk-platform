# 社区法治风险智能预警与精准普法平台技术文档

版本：v1.0  
日期：2026-04-21  
适用对象：项目申报书、技术评审材料、答辩 PPT、后续研发交接

## 1. 项目定位

本平台面向“青朗法治”法治建设专项赛中基层法治治理、风险预警、精准普法、闭环处置等应用需求，建设“社区法治风险智能预警与精准普法平台”。平台以北京市西城区街道治理场景为演示对象，围绕社区矛盾纠纷、劳动争议、合同诈骗、物业纠纷、未成年人保护等高发案件类型，形成从数据接入、智能研判、风险预警、任务分派、处置反馈到效果评估的全流程闭环。

平台目标不是单纯展示案件数据，而是形成可解释、可分派、可追踪、可评估的基层法治治理工作机制。

## 2. 建设目标

1. 建立多源法治风险数据接入能力，支持演示案件、案件语料、街道风险点、法律知识库等数据统一管理。
2. 建立风险分级预警机制，按红、橙、黄、蓝对街道、主体、案件类型进行风险识别和解释。
3. 建立社区风险治理驾驶舱，用热力图、统计面板、预警列表、闭环链路展示治理态势。
4. 建立街道风险画像能力，自动识别高发案件类型并生成治理建议与精准普法方案。
5. 建立真实任务闭环，支持预警分派、任务保存、阶段流转、处置反馈和效果评估。
6. 接入大模型能力，优先使用 OpenAI 兼容接口，可配置硅基流动等国产模型服务；无模型时自动规则兜底。

## 3. 总体架构

项目采用前后端分离、模块化单体后端、单仓库管理架构。

```text
justice-risk-platform/
├── frontend/              React + TypeScript + Vite + Ant Design
├── backend/               FastAPI 主后端
│   ├── app/
│   │   ├── api/v1/        API 总路由
│   │   ├── core/          配置、日志
│   │   ├── db/            数据库连接和初始化
│   │   ├── infra/         LLM、Embedding 等基础设施
│   │   └── modules/       业务模块
│   ├── scripts/           后端数据导入和初始化脚本
│   └── tests/             后端测试
├── mock_data/             示例案件、法律知识等演示数据
├── scripts/               数据生成和导入脚本
├── docs/                  技术、维护、接口和说明文档
└── docker-compose.yml     PostgreSQL、Redis、Neo4j 预留部署
```

### 3.1 前端架构

前端技术栈：

- React 19
- TypeScript
- Vite
- Ant Design
- AntV L7
- Axios
- React Router

核心页面：

| 页面 | 路径 | 作用 |
|---|---|---|
| 登录页 | `/login` | 平台入口 |
| 驾驶舱 | `/dashboard` | 风险热力图、预警列表、闭环链路 |
| 预警案件详情 | `/dashboard/cases/:caseId` | 单案件结构化详情和闭环轨迹 |
| 高风险主体案件 | `/dashboard/defendants` | 按主体查看关联案件 |
| 社区风险治理 | `/community-risk` | 西城区街道列表 |
| 街道案件列表 | `/community-risk/:street/cases` | 某街道所有案件 |
| 街道风险画像 | `/community-risk/:street/profile` | 高发类型、画像、建议、普法方案 |
| 任务创建 | `/workflow/tasks/create` | 由预警生成处置任务 |
| 闭环任务管理 | `/workflow/tasks` | 真实任务查询、反馈、评估 |
| NLP 研判 | `/analysis/nlp` | 案件分析能力演示 |

### 3.2 后端架构

后端技术栈：

- FastAPI
- SQLAlchemy 2.x
- Pydantic 2.x
- SQLite 演示数据库，PostgreSQL 生产预留
- OpenAI SDK 兼容 LLM 客户端
- Hash Embedding 兜底，SentenceTransformer 预留

核心后端模块：

| 模块 | 目录 | 作用 |
|---|---|---|
| analysis | `backend/app/modules/analysis` | 案件语料、NLP 分析、风险评分、法律关联 |
| alert | `backend/app/modules/alert` | 风险画像、预警事件、规则引擎 |
| dashboard | `backend/app/modules/dashboard` | 驾驶舱聚合接口 |
| knowledge | `backend/app/modules/knowledge` | 法律知识库 |
| recommendation | `backend/app/modules/recommendation` | 治理建议 |
| propaganda | `backend/app/modules/propaganda` | 普法内容推荐与推送 |
| workflow | `backend/app/modules/workflow` | 闭环任务表、保存接口、阶段流转 |
| document_gen | `backend/app/modules/document_gen` | 文书生成 |
| support_prosecution | `backend/app/modules/support_prosecution` | 支持起诉专题能力，当前入口已关闭但保留能力 |

## 4. 核心业务链路

### 4.1 风险发现

数据导入后写入案件语料库 `case_corpus`，每条案件包含：

- 案件编号
- 案件类型
- 所属街道
- 风险等级
- 风险评分
- 涉案金额
- 涉及人数
- 责任主体
- 预警特征
- 治理建议
- 普法主题

示例数据来自：

```text
mock_data/cases/demo_cases_100.json
```

导入脚本：

```text
backend/scripts/import_demo_cases.py
```

### 4.2 智能预警

系统基于案件状态、风险等级和预警特征将案件划入闭环阶段。

当前规则：

```text
待审查、已受理 -> 风险发现
补充材料、存在预警特征、红色或橙色风险 -> 已预警
已转入支持起诉评估 -> 已分派
调解中 -> 处置中
联合核查中 -> 已反馈
拟制发检察建议 -> 已评估
```

风险等级用于前端展示和热力图权重：

```text
红色：高风险
橙色：较高风险
黄色：一般风险
蓝色：关注风险
```

### 4.3 任务分派

驾驶舱右侧“实时预警列表”中每条预警都有“去分派”按钮。点击后进入任务创建页，系统自动带入：

- 街道
- 风险等级
- 高发类型
- 建议承办单位
- 建议处置动作
- 关联预警标题
- 关联案件编号

提交后保存到真实任务表：

```text
workflow_tasks
```

### 4.4 处置反馈

任务进入闭环任务管理页后，可按阶段推进：

```text
已分派 -> 处置中 -> 已反馈 -> 已评估
```

任务详情中可填写：

- 处置反馈
- 效果评估
- 处置动作
- 闭环轨迹

### 4.5 效果评估

任务进入 `已评估` 阶段时，后端自动生成“处置成效评估卡”，写入：

```text
workflow_tasks.extra_meta.evaluation_card
```

评估维度包括：

| 维度 | 指标 |
|---|---|
| 风险变化 | 风险等级是否下降、风险评分是否下降 |
| 事件变化 | 同类案件新增是否减少、重复主体是否再次触发 |
| 治理效果 | 任务按期办结率、联动处置完成率 |
| 普法效果 | 普法覆盖人数、阅读率、回访满意度 |

示例评估卡：

```text
处置前：红色 86分
处置后：黄色 48分
风险下降：38分
同类案件新增：下降 42%
重复主体预警：未再次触发
按期办结率：100%
联动处置完成率：92%
普法覆盖：1260人
阅读率：76%
回访满意度：83%
```

## 5. 驾驶舱设计

驾驶舱是评审第一视觉入口，采用“一图三栏一闭环”的结构。

### 5.1 中央热力图

中央区域展示北京市西城区街道法治风险热力图。

技术实现：

- 优先使用天地图底图
- 使用 AntV L7 `HeatmapLayer` 实现热力层
- 热力值按“案件数量 × 风险等级权重”计算
- 未配置天地图时使用本地 JSON 地图兜底

### 5.2 左侧核心数据

展示：

- 风险线索总数
- 涉及群众人数
- 涉案金额
- 本月新增
- 案件类型分布
- 月度趋势

### 5.3 右侧预警处置

展示：

- 实时预警列表
- 去分派按钮
- 高风险主体 TOP5
- 普法推送效果

### 5.4 底部闭环链路

底部展示平台级闭环：

```text
风险发现 -> 已预警 -> 已分派 -> 处置中 -> 已反馈 -> 已评估
```

数据源已区分：

- 风险发现、已预警：来自案件语料库
- 已分派、处置中、已反馈、已评估：来自真实任务表

## 6. 街道风险治理

街道风险治理入口展示西城区所有街道风险概览。

功能：

1. 街道列表
2. 街道案件列表
3. 街道风险画像
4. 高发案件类型识别
5. 智能治理建议
6. 精准普法方案

街道风险画像接口优先调用大模型，失败时规则兜底：

```text
GET /api/v1/dashboard/street-profile?street=西长安街街道&prefer_llm=true
```

## 7. 大模型与知识增强

平台预留 OpenAI 兼容大模型接口，可接入硅基流动等服务。

配置项：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=你的API_KEY
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen3-14B
LLM_TIMEOUT_SECONDS=45
LLM_FORCE_JSON_OBJECT=true
LLM_DISABLE_THINKING=true
```

当前应用场景：

- NLP 案件分类
- 实体抽取
- 法律关联
- 街道风险画像
- 治理建议生成
- 普法方案生成

离线兜底：

- 未配置 API Key 时，`EchoLLMClient` 生效
- 规则引擎继续提供基础分析结果
- 页面不因模型不可用而空白

## 8. 主要接口

### 8.1 驾驶舱

```text
GET /api/v1/dashboard/risk-map
GET /api/v1/dashboard/community-streets
GET /api/v1/dashboard/street-cases?street=西长安街街道
GET /api/v1/dashboard/street-profile?street=西长安街街道&prefer_llm=true
GET /api/v1/dashboard/workflow-cases?stage=discovered
GET /api/v1/dashboard/defendant-cases?defendant=主体名称
```

### 8.2 案件分析

```text
GET  /api/v1/analysis/corpus/{case_id}
POST /api/v1/analysis/nlp/classify
POST /api/v1/analysis/nlp/entities
POST /api/v1/analysis/nlp/laws
POST /api/v1/analysis/nlp/analyze
```

### 8.3 闭环任务

```text
POST  /api/v1/workflow/tasks
GET   /api/v1/workflow/tasks?stage=assigned
PATCH /api/v1/workflow/tasks/{task_id}/stage
```

### 8.4 知识库、建议、普法

```text
GET/POST /api/v1/knowledge/...
GET/POST /api/v1/recommendations/...
GET/POST /api/v1/propaganda/...
```

## 9. 数据模型摘要

### 9.1 案件语料表 `case_corpus`

用于存储导入案件和结构化分析结果。

关键字段：

- `source_type`
- `source_ref`
- `title`
- `case_no`
- `full_text`
- `case_type`
- `entities`
- `cited_laws`
- `extra_meta`
- `embedding`

### 9.2 闭环任务表 `workflow_tasks`

用于保存真实处置任务和闭环阶段。

关键字段：

- `task_name`
- `alert_id`
- `alert_title`
- `street`
- `risk_level`
- `case_type`
- `main_unit`
- `deadline`
- `actions`
- `description`
- `stage`
- `feedback`
- `evaluation`
- `extra_meta.evaluation_card`

### 9.3 法律知识表 `legal_knowledge`

用于法律知识检索和法条关联。

关键字段：

- `law_name`
- `article_no`
- `title`
- `content`
- `keywords`
- `scenario_tags`
- `embedding`

## 10. 技术创新点

1. 以街道为治理单元，将案件数据、风险等级、主体重复、趋势变化统一聚合。
2. 风险热力图与闭环任务链路联动，既能看风险分布，也能看处置进展。
3. 建立“风险发现、智能预警、任务分派、处置反馈、效果评估”完整闭环。
4. 处置评估不止停留在办结状态，而是生成风险变化、事件变化、治理效果、普法效果四类指标。
5. 大模型与规则引擎混合，既支持智能生成，也保证演示和内网部署可用。
6. 平台按业务域拆分模块，后续可扩展民事支持起诉、法律知识图谱、审计日志和多部门协同。

## 11. 比赛展示建议

答辩时建议按以下顺序展示：

1. 进入驾驶舱，展示风险热力图和总体态势。
2. 点击实时预警，说明风险发现与已预警机制。
3. 点击“去分派”，展示自动带入街道、等级、类型、承办单位和处置动作。
4. 进入闭环任务管理，推进任务阶段。
5. 展示案件详情中的环形闭环轨迹。
6. 将任务推进到已评估，展示处置成效评估卡。
7. 进入社区风险治理，展示街道画像、治理建议和普法方案。

