# pkg2.5：判例结构化解析 + 基础 NLP 能力增强说明

本次增强基于 `pkg2_analysis_full.zip` 的目录结构继续补齐，目标对应两项任务：

1. 对两份北京地区判例和一份指导性案例做结构化解析，提取：案由、原告信息、被告信息、诉请、争议焦点、法院认定事实、裁判结果、适用法条。
2. 搭建三个基础 NLP 能力：案件文本分类、关键实体抽取、法条关联；优先支持大模型 API（Claude / OpenAI），未配置 API key 时自动回退到规则版。

## 一、本次新增内容

### 1. 新增接口

- `POST /api/v1/analysis/structured-case`
  - 输入：判例全文/指导性案例全文
  - 输出：结构化字段 + 实体 + 匹配法条
- `POST /api/v1/analysis/nlp/classify`
  - 三分类：`labor_service_dispute / labor_dispute / other`
- `POST /api/v1/analysis/nlp/entities`
  - 抽取人名、公司名、金额、日期、地址，同时兼容项目名、手机号、身份证号、法条引用
- `POST /api/v1/analysis/nlp/law-link`
  - 先走知识库召回，再根据是否配置 LLM 决定是否做 LLM 重排

### 2. 新增代码文件

- `backend/app/modules/analysis/prompts.py`
- `backend/app/modules/analysis/parsers.py`
- `backend/scripts/seed_case_structured_samples.py`
- `mock_data/case_corpus_structured_seed.json`

### 3. 更新文件

- `backend/app/modules/analysis/schemas.py`
- `backend/app/modules/analysis/service.py`
- `backend/app/modules/analysis/router.py`
- `backend/app/modules/analysis/rules.py`
- `backend/app/infra/llm_client.py`

## 二、三份样本案例已经整理成结构化种子数据

位置：`mock_data/case_corpus_structured_seed.json`

包含 3 条样本：

1. `崔某劳务合同纠纷二审民事判决书`
2. `某公司;张某;魏某劳务合同纠纷二审民事判决书`
3. `张某云与张某森离婚纠纷支持起诉案（检例第126号）`

每条样本都已经写入：

- `case_type`
- `plaintiff_summary`
- `defendant_summary`
- `claim_summary`
- `focus_summary`
- `fact_summary`
- `judgment_summary`
- `entities`
- `cited_laws`
- `extra_meta.structured_case`

这样你后续做文书划分、案件标签化、风险规则验证时，可以直接使用这 3 条样本作为基准语料。

## 三、推荐运行方式

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 初始化数据库与法律知识库

```bash
python -m app.db.init_db
python -m scripts.seed_legal_knowledge
```

### 3. 导入三份结构化样本

```bash
python -m scripts.seed_case_structured_samples
```

### 4. 启动服务

```bash
python -m app.main
```

## 四、LLM 配置方式

默认是离线回退模式：

```env
LLM_PROVIDER=echo
```

### Claude / Anthropic

```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=你的key
```

### OpenAI

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=你的key
```

当未配置真实 key 时：

- 分类 -> 走规则版
- 实体抽取 -> 走规则版
- 法条关联 -> 走知识库召回版
- 结构化解析 -> 走规则解析版

## 五、接口示例

### 1. 结构化解析

```json
POST /api/v1/analysis/structured-case
{
  "title": "崔某劳务合同纠纷二审民事判决书",
  "text": "上诉人（原审被告）：北京某公司。被上诉人（原审原告）：崔某。...",
  "source_type": "judgment",
  "source_ref": "bj_cui_case_raw_doc",
  "prefer_llm": true,
  "persist_to_corpus": true,
  "top_k_laws": 5
}
```

### 2. 分类

```json
POST /api/v1/analysis/nlp/classify
{
  "title": "某公司;张某;魏某劳务合同纠纷二审民事判决书",
  "text": "...",
  "prefer_llm": true
}
```

### 3. 实体抽取

```json
POST /api/v1/analysis/nlp/entities
{
  "title": "崔某劳务合同纠纷二审民事判决书",
  "text": "崔某向一审法院提出以下诉讼请求：北京某公司、张某支付崔某劳务费23127元。",
  "prefer_llm": true
}
```

### 4. 法条关联

```json
POST /api/v1/analysis/nlp/law-link
{
  "title": "崔某劳务合同纠纷二审民事判决书",
  "text": "北京某公司允许张某将项目挂至其名下独立承包经营，导致拖欠农民工工资。",
  "top_k": 5,
  "prefer_llm": true
}
```

## 六、这版能力边界

### 已经补齐

- 三份案例的结构化样本
- 结构化解析接口
- LLM / 规则双模式分类
- LLM / 规则双模式实体抽取
- 知识库召回 + LLM 重排的法条关联

### 仍然预留

- 直接上传 doc/docx/pdf 后自动抽取正文的文件解析入口
- 批量解析 200 份案例的任务队列脚本
- 针对真实业务数据的 prompt 评测集与指标统计

## 七、后续最建议做的两步

1. 把这 3 条样本先导入数据库，跑通 `structured-case` 和 `nlp/*` 接口。
2. 再把你后续收集到的 50~200 份同类案例按同样 schema 落到 `case_corpus`，这样分类、抽取、法条匹配和后续文书生成就能共用一套数据底座。
