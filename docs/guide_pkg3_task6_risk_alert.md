# pkg3 / Task6：社区风险识别与预警引擎接入说明

## 1. 这包补了什么

本包围绕第二阶段任务6，新增了三块能力：

1. `modules/alert/`：社区风险评分、四级预警、预警落库。
2. `modules/dashboard/`：驾驶舱概览与实时预警拉取接口。
3. `scripts/seed_community_risk_demo.py` 与 `scripts/run_alert_engine.py`：演示数据与一键跑通脚本。

实现策略遵循现有代码架构：按业务域拆模块，每个模块内部按 `router / schemas / models / repository / service / rules / tasks` 分层。

## 2. 风险评分模型（统一模板，预留扩展口）

默认权重模板：

- 案件数量：30%
- 涉及人数：20%
- 近期增长趋势：20%
- 同一被告复现率：20%
- 涉案金额：10%

四级风险阈值：

- 红色：>= 80
- 橙色：60-79
- 黄色：40-59
- 蓝色：< 40

当前实现不是直接对原始值做线性加权，而是先把每个指标映射成 0-100 的“分档分数”，再按权重汇总，便于解释和答辩。

## 3. 预警触发规则

本包默认内置三类触发：

1. `risk_level_upgrade`
   - 某社区 / 街道 / 项目的风险等级较上一统计窗口升级时触发。

2. `high_frequency_defendant`
   - 同一主体近 30 天重复出现次数达到阈值时触发。
   - 默认阈值为 `32`，因为你当前任务描述里写的是“>=32次”。
   - 若你们后续确认这是笔误，应为 `3`，只需改配置：
     - `.env` 中 `ALERT_REPEAT_DEFENDANT_THRESHOLD=3`
     - 或请求体中 `repeat_defendant_threshold=3`

3. `group_wage_arrears`
   - 某工地 / 项目近 30 天涉及人数 >= 10 时触发“群体性欠薪”预警。

最终落库到 `alerts` 表，并通过 `/api/v1/dashboard/alerts/realtime` 给驾驶舱取数。

## 4. 数据来源约定

本包尽量复用你现有的 `case_corpus`，不强制新增案件主表。

风险引擎会优先从 `CaseCorpus.extra_meta` 和 `CaseCorpus.entities` 里取聚合字段：

推荐你后续新增 / 入库案例时，把这些字段放进 `extra_meta`：

```json
{
  "community_id": "c-a",
  "community_name": "新街口社区",
  "street_id": "s-a",
  "street_name": "新街口街道",
  "project_id": "p-001",
  "project_name": "新街口排水改造项目",
  "risk_type": "wage_arrears",
  "people_count": 12,
  "total_amount": 120000,
  "defendant_names": ["某建设公司"]
}
```

已兼容的回退逻辑：

- `risk_type` 缺失时，回退到 `case_type`
- `total_amount` 缺失时，回退到 `entities.amount_total_estimate`
- `project_name` 缺失时，回退到 `entities.projects[0]`
- `defendant_names` 缺失时，回退到 `entities.companies` 或 `defendant_summary`

## 5. 新增表

### `community_risk_profiles`
用于保存每次计算出的社区 / 街道 / 项目风险画像。

### `alerts`
用于保存已触发的预警事件，供驾驶舱实时列表与后续工单流转使用。

## 6. 新增接口

### 6.1 运行风险引擎

`POST /api/v1/alerts/engine/run`

示例：

```json
{
  "scope_type": "community",
  "window_days": 30,
  "compare_window_days": 30,
  "persist_profiles": true,
  "generate_alerts": true,
  "weights": {
    "case_count": 0.30,
    "people_count": 0.20,
    "growth_rate": 0.20,
    "repeat_defendant_rate": 0.20,
    "total_amount": 0.10
  },
  "repeat_defendant_threshold": 32,
  "group_people_threshold": 10,
  "only_level_upgrade_alert": true
}
```

### 6.2 查询预警列表

`GET /api/v1/alerts`

### 6.3 查询风险画像

`GET /api/v1/alerts/profiles`

### 6.4 驾驶舱总览

`GET /api/v1/dashboard/overview`

### 6.5 驾驶舱实时预警

`GET /api/v1/dashboard/alerts/realtime`

## 7. 本地接入步骤

### 第一步：覆盖补丁文件

把 patch 包中的文件覆盖到当前工程对应位置。

### 第二步：初始化数据库表

```bash
cd backend
python -m app.db.init_db
```

### 第三步：可选，注入演示数据

```bash
python -m scripts.seed_community_risk_demo
```

### 第四步：运行风险引擎

```bash
python -m scripts.run_alert_engine --scope-type community
```

运行结果会写到：

```text
../docs/alert_engine_run_result.json
```

### 第五步：启动服务

```bash
python -m app.main
```

## 8. 你后面最该补的数据

如果你希望这个模块尽快从“可演示”变成“可用”，优先补三类字段：

1. `community_id / community_name / street_name`
2. `project_name / defendant_names`
3. `people_count / total_amount`

因为这四级预警是否可靠，80% 取决于这些聚合字段是否齐。

## 9. 这一包的定位

这一包完成的是：

- 社区风险评分模型
- 四级风险分层
- 规则预警触发
- 预警落库
- 驾驶舱取数接口

下一步最自然的衔接是：

- `recommendation`：AI 治理建议生成
- `propaganda`：普法内容推荐
- `workflow`：预警转工单、处置反馈、效果评估
