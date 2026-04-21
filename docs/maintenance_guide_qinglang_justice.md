# 社区法治风险智能预警与精准普法平台维护文档

版本：v1.0  
日期：2026-04-21  
适用对象：部署维护人员、项目交接人员、后续开发人员

## 1. 环境说明

当前常用运行环境：

```text
项目目录：/home/jovyan/data/bugui_v2/web/justice-risk-platform
后端环境：/home/jovyan/data/conda-envs/jiancha
后端框架：FastAPI
前端框架：React + Vite
数据库：SQLite 演示库 backend/justice_risk.db
```

## 2. 启动方式

### 2.1 后端启动

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform/backend
/home/jovyan/data/conda-envs/jiancha/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

### 2.2 前端启动

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform/frontend
npm run dev
```

默认访问：

```text
http://localhost:5173
```

## 3. 常用配置

### 3.1 后端 `.env`

位置：

```text
backend/.env
```

核心配置：

```env
APP_NAME=justice-risk-platform
APP_ENV=dev
APP_DEBUG=true
API_V1_PREFIX=/api/v1

DATABASE_URL=sqlite:///./justice_risk.db

EMBEDDING_PROVIDER=hash
EMBEDDING_DIMENSION=384

LLM_PROVIDER=echo
LLM_MODEL=Qwen/Qwen3-14B
OPENAI_API_KEY=
OPENAI_BASE_URL=
LLM_TIMEOUT_SECONDS=45
LLM_FORCE_JSON_OBJECT=true
LLM_DISABLE_THINKING=true
```

### 3.2 硅基流动 API 配置

如需启用大模型：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=你的硅基流动API_KEY
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen3-14B
LLM_TIMEOUT_SECONDS=45
LLM_FORCE_JSON_OBJECT=true
LLM_DISABLE_THINKING=true
```

重启后端后生效。

验证：

```bash
curl -G "http://127.0.0.1:8000/api/v1/dashboard/street-profile" \
  --data-urlencode "street=西长安街街道" \
  --data-urlencode "prefer_llm=true"
```

返回 `sourceMode=llm` 表示模型已生效；返回 `sourceMode=rule` 表示规则兜底。

### 3.3 前端 `.env.local`

位置：

```text
frontend/.env.local
```

天地图配置：

```env
VITE_TIANDITU_TOKEN=你的天地图Token
```

未配置时，驾驶舱使用本地 JSON 地图兜底。

## 4. 数据维护

### 4.1 生成演示案件

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform
/home/jovyan/data/conda-envs/jiancha/bin/python scripts/generate_demo_cases.py
```

输出：

```text
mock_data/cases/demo_cases_100.json
mock_data/cases/demo_cases_100.csv
```

### 4.2 导入演示案件

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform/backend
/home/jovyan/data/conda-envs/jiancha/bin/python scripts/import_demo_cases.py
```

验证：

```bash
curl http://127.0.0.1:8000/api/v1/dashboard/risk-map
```

### 4.3 导入法律知识库

可使用：

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform/backend
/home/jovyan/data/conda-envs/jiancha/bin/python scripts/seed_legal_knowledge.py
```

或使用 CSV 导入脚本：

```bash
/home/jovyan/data/conda-envs/jiancha/bin/python scripts/import_legal_knowledge_csv.py
```

## 5. 闭环任务维护

### 5.1 创建任务

前端路径：

```text
/workflow/tasks/create
```

接口：

```text
POST /api/v1/workflow/tasks
```

任务保存到：

```text
workflow_tasks
```

### 5.2 查看任务

前端路径：

```text
/workflow/tasks?stage=assigned
```

接口：

```text
GET /api/v1/workflow/tasks?stage=assigned
```

阶段包括：

```text
assigned   已分派
handling   处置中
feedback   已反馈
evaluated  已评估
```

### 5.3 推进任务

接口：

```text
PATCH /api/v1/workflow/tasks/{task_id}/stage
```

示例请求：

```json
{
  "stage": "feedback",
  "feedback": "已完成核查处置并形成反馈记录。"
}
```

进入 `evaluated` 阶段时，后端自动生成 `evaluation_card`。

## 6. 页面维护说明

### 6.1 驾驶舱

文件：

```text
frontend/src/pages/Dashboard/index.tsx
```

维护重点：

- 风险热力图
- 实时预警列表
- 去分派按钮
- 高风险主体 TOP5
- 普法推送效果
- 底部闭环链路

### 6.2 社区风险治理

文件：

```text
frontend/src/pages/CommunityRisk/index.tsx
frontend/src/pages/CommunityRisk/StreetCasesPage.tsx
frontend/src/pages/CommunityRisk/StreetProfilePage.tsx
```

维护重点：

- 街道列表
- 街道案件
- 街道风险画像
- 治理建议
- 普法方案

### 6.3 闭环任务管理

文件：

```text
frontend/src/pages/Workflow/TaskCreatePage.tsx
frontend/src/pages/Workflow/TaskListPage.tsx
frontend/src/components/CaseClosureTimeline.tsx
```

维护重点：

- 任务创建表单
- 阶段筛选
- 任务推进
- 环形闭环轨迹
- 处置成效评估卡

## 7. 常见问题

### 7.1 后端目录不能执行 `npm run dev`

后端是 FastAPI，不是 Node 项目。启动后端应使用：

```bash
/home/jovyan/data/conda-envs/jiancha/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`npm run dev` 只在 `frontend/` 目录使用。

### 7.2 Vite 报 `Unexpected token ??=`

说明 Node 版本过低。建议使用 Node 20 或更高版本。

### 7.3 L7 报 less 缺失

安装前端依赖：

```bash
cd frontend
npm install
```

项目已在 `devDependencies` 中加入：

```text
less
```

### 7.4 天地图不显示

检查：

1. `frontend/.env.local` 是否配置 `VITE_TIANDITU_TOKEN`
2. 前端是否重启
3. 浏览器控制台是否有天地图请求失败
4. 网络是否允许访问天地图瓦片服务

兜底方案：

- 使用本地 JSON 地图，不影响演示闭环能力。

### 7.5 大模型未生效

检查：

1. `LLM_PROVIDER=openai`
2. `OPENAI_API_KEY` 是否正确
3. `OPENAI_BASE_URL` 是否为兼容地址
4. 后端是否重启
5. 后端是否安装 `openai`

### 7.6 闭环数量不一致

当前规则：

- 风险发现、已预警来自案件线索
- 已分派、处置中、已反馈、已评估来自真实任务表

如发现不一致，优先检查：

```text
/api/v1/dashboard/risk-map
/api/v1/dashboard/workflow-cases?stage=alerted
/api/v1/workflow/tasks?stage=assigned
```

## 8. 测试与验证

### 8.1 后端语法检查

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform
/home/jovyan/data/conda-envs/jiancha/bin/python -m py_compile backend/app/modules/workflow/service.py
```

### 8.2 前端类型检查

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform/frontend
npx tsc -b
```

### 8.3 关键接口验证

```bash
curl http://127.0.0.1:8000/api/v1/dashboard/risk-map
curl http://127.0.0.1:8000/api/v1/workflow/tasks?stage=assigned
curl -G http://127.0.0.1:8000/api/v1/dashboard/street-cases --data-urlencode "street=西长安街街道"
```

## 9. 后续扩展建议

1. 将 SQLite 切换为 PostgreSQL，使用 Alembic 做正式迁移。
2. 将 `workflow_tasks` 拆分为任务主表、流转日志表、附件表。
3. 将已预警阶段正式落到 `alerts` 表，形成案件和预警事件强绑定。
4. 引入审计日志，记录任务创建、阶段流转、评估生成操作。
5. 接入真实短信、政务微信或内部消息系统，实现任务推送。
6. 建立法律知识图谱，与治理建议、普法内容生成联动。
7. 将评估卡由规则生成升级为规则加大模型混合生成。

