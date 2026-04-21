# 100 条高发案件示例数据说明

## 数据用途

本目录用于数据接入平台的全流程测试，覆盖数据接入、结构化解析、NLP 标签识别、风险评分、预警触发、治理建议生成、普法内容推荐、驾驶舱统计展示和支持起诉流转。

所有人名、公司名、机构名、案情均为虚构，仅用于系统测试和演示。

## 文件清单

| 文件 | 说明 |
|---|---|
| `demo_cases_100.json` | 主数据文件，保留嵌套结构，适合后端导入和接口调试 |
| `demo_cases_100.csv` | 扁平化数据文件，适合 Excel 查看和人工核对 |
| `../../scripts/generate_demo_cases.py` | 可重复执行的数据生成脚本 |
| `../../backend/scripts/import_demo_cases.py` | 将示例案件导入后端案件语料库的脚本 |

## 案件类型分布

| 案件类型 | 数量 |
|---|---:|
| 劳动争议 | 25 |
| 邻里纠纷 | 15 |
| 合同诈骗 | 15 |
| 婚姻家庭纠纷 | 10 |
| 物业纠纷 | 10 |
| 工伤赔偿 | 8 |
| 消费维权 | 7 |
| 民间借贷 | 5 |
| 未成年人保护线索 | 5 |
| 合计 | 100 |

## 风险等级分布

| 风险等级 | 数量 | 评分范围 |
|---|---:|---|
| red | 15 | 84-98 |
| orange | 25 | 64-79 |
| yellow | 35 | 43-59 |
| blue | 25 | 18-39 |

## 主要字段说明

| 字段 | 说明 |
|---|---|
| `case_id` | 案件唯一编号 |
| `case_type` | 案件类型 |
| `sub_type` | 细分类型 |
| `region` | 行政区 |
| `street` | 街道 |
| `longitude` / `latitude` | 风险点坐标，用于驾驶舱地图 |
| `source` | 数据来源 |
| `report_time` | 接入时间 |
| `title` | 案件标题 |
| `description` | 案情描述 |
| `parties.claimants` | 申请人或反映人，均为虚构姓名 |
| `parties.defendants` | 被告、责任主体或涉事机构，均为虚构名称 |
| `amount` | 涉案金额，单位为元 |
| `people_count` | 涉及人数 |
| `evidence` | 证据材料 |
| `risk_level` | 红橙黄蓝风险等级 |
| `risk_score` | 风险评分 |
| `tags` | NLP 预期标签 |
| `warning_features` | 预警特征 |
| `expected_modules` | 预期流转模块 |
| `recommended_actions` | 治理建议方向 |
| `propaganda_topics` | 普法推送主题 |
| `status` | 当前处理状态 |
| `support_prosecution_candidate` | 是否适合进入支持起诉评估 |
| `is_fictional` | 是否虚构数据 |

## 重新生成数据

在项目根目录执行：

```bash
python scripts/generate_demo_cases.py
```

脚本会覆盖生成：

```text
mock_data/cases/demo_cases_100.json
mock_data/cases/demo_cases_100.csv
```

## 建议测试流程

1. 将 `demo_cases_100.json` 导入 analysis 案件语料库。
2. 检查总数是否为 100。
3. 验证 `case_type`、`street`、`amount`、`people_count` 能否被正确入库。
4. 调用 analysis 模块，检查 `tags` 和 `risk_score` 是否能被识别或复算。
5. 调用 alert 模块，检查 `red`、`orange` 以及包含 `群体性风险`、`重复投诉` 的案件是否进入预警。
6. 调用 recommendation 模块，检查不同案件类型能否生成差异化治理建议。
7. 调用 propaganda 模块，检查普法主题是否匹配案件类型。
8. 在 dashboard 中检查案件总量、金额、人数、街道分布和风险等级。
9. 对劳动争议、工伤赔偿、婚姻家庭、未成年人保护线索类案件检查支持起诉评估流程。

## 导入平台

当前平台还没有单独的 `ingest` API 路由，但 `analysis` 模块已经提供案件语料批量入库能力。建议先将 100 条示例案件导入案件语料库，再用 analysis、alert、recommendation、propaganda、dashboard 等模块测试完整流程。

### 1. 先做 dry-run 校验

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform/backend
./.venv/bin/python scripts/import_demo_cases.py --dry-run
```

预期输出：

```text
validated 100 demo cases
{'劳动争议': 25, '邻里纠纷': 15, '合同诈骗': 15, '婚姻家庭纠纷': 10, '物业纠纷': 10, '工伤赔偿': 8, '消费维权': 7, '民间借贷': 5, '未成年人保护线索': 5}
```

### 2. 正式写入数据库

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform/backend
/home/jovyan/data/conda-envs/jiancha/bin/python scripts/import_demo_cases.py
```

脚本会把 `mock_data/cases/demo_cases_100.json` 转换为 `CaseCorpusBatchUpsertRequest`，再调用 `AnalysisService.batch_upsert_corpus()` 写入案件语料库。

### 3. 运行风险引擎

导入后，案件会先进入 `case_corpus`。如果要让 `dashboard/overview`、实时预警和风险画像也有数据，需要继续运行风险引擎：

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform/backend
/home/jovyan/data/conda-envs/jiancha/bin/python scripts/run_alert_engine.py --scope-type community --window-days 180 --compare-window-days 30 --out ../docs/alert_engine_demo_cases_result.json
```

当前 100 条示例数据横跨 2026 年 1 月到 4 月，建议 `window-days` 使用 `180`，否则只会统计最近 30 天或 120 天内的部分案件。

### 4. 查看驾驶舱接口

前端驾驶舱会优先读取：

```text
GET /api/v1/dashboard/risk-map
```

该接口直接从 `case_corpus` 聚合街道风险点、核心统计、案件类型分布、趋势、预警列表、高风险被告 TOP5 和支持起诉进度。

也可以查看风险引擎生成后的总览：

```text
GET /api/v1/dashboard/overview
```

推荐验证命令：

```bash
curl http://localhost:8000/api/v1/dashboard/risk-map
curl http://localhost:8000/api/v1/dashboard/overview
```

### 5. 只导入前 N 条测试

```bash
/home/jovyan/data/conda-envs/jiancha/bin/python scripts/import_demo_cases.py --limit 10
```

### 6. 导入其他 JSON 文件

```bash
/home/jovyan/data/conda-envs/jiancha/bin/python scripts/import_demo_cases.py --file /path/to/your_cases.json
```

自定义 JSON 需要保持与 `demo_cases_100.json` 相同的字段结构。

## 当前完整链路

```text
demo_cases_100.json
  ↓ import_demo_cases.py
case_corpus
  ↓ /api/v1/dashboard/risk-map
前端驾驶舱地图和统计

case_corpus
  ↓ run_alert_engine.py 或 POST /api/v1/alerts/engine/run
community_risk_profiles + alerts
  ↓ /api/v1/dashboard/overview
前端驾驶舱预警和画像扩展
```
