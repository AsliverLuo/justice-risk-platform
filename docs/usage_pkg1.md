# AI工程师第1包：知识库与基础设施使用说明（重建版）

## 文件清单

压缩包里你会看到：

- `backend/app/main.py`：FastAPI 入口
- `backend/app/api/v1/router.py`：总路由
- `backend/app/core/config.py`：统一配置
- `backend/app/db/session.py`：数据库会话与建表入口
- `backend/app/db/init_db.py`：单独的初始化入口
- `backend/app/infra/embedding.py`：embedding 客户端与 hash 回退方案
- `backend/app/infra/llm_client.py`：后续 LLM 客户端底座
- `backend/app/modules/knowledge/`：第一阶段核心知识库模块
- `backend/scripts/seed_legal_knowledge.py`：示例法条入库脚本
- `mock_data/legal_knowledge_sample.json`：示例数据

## 最短落地路径

### 1. 安装依赖

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. 启动服务

```bash
python -m app.main
```

### 3. 初始化并导入示例法条

```bash
python -m app.db.init_db
python scripts/seed_legal_knowledge.py
```

### 4. 验证接口

先测健康检查：

```bash
curl http://127.0.0.1:8000/health
```

再测知识检索：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/knowledge/search   -H "Content-Type: application/json"   -d '{
    "query": "工地拖欠工资，发包方承诺过付款，现在还没给",
    "scenario_tag": "发包方责任",
    "top_k": 5
  }'
```

## 你和后端的接口边界

你负责：

- 条文结构定义
- embedding 生成
- 检索逻辑
- 知识上下文组装

后端负责：

- Alembic 迁移
- 权限与鉴权
- 对象存储
- 统一异常处理
- 审计日志

## 这一包跑通后的下一步

优先做 `modules/analysis`，不要先掉进大屏和复杂图谱里。先把案件解析、实体抽取和法条关联做出来，后面第二阶段的风险预警和治理建议才会顺。
