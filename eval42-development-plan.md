# Eval42 完整开发计划

> 项目定位：面向可验证 AI 应用的轻量、CI 优先评测工具  
> 英文定位：A lightweight, CI-first evaluation harness for verifiable AI applications.  
> 计划版本：v1.2
> 编写日期：2026-07-16  
> 修订日期：2026-07-18
> 目标读者：后续开发窗口、项目维护者、代码审查者  

---

## 1. 项目背景

当前项目组合包含多种 AI 应用：

- PhoneMall：基于商品数据的 RAG 智能导购。
- GroundedSeek：强调来源、证据、引用和冲突保留的研究工作台。
- NovelFlow：强调作者审批和 Canon 一致性的长篇写作工作台。
- Guarded Agent Pipeline：带独立复核、确定性测试和人工批准的多模型开发流程。
- ecc-init：强调检测、可预览写入、幂等、配置保留和回滚的开发者工具。

这些项目都在强调“可控、可验证”，但当前缺少统一回答以下问题的工具：

1. 本次修改是否让 AI 质量提高？
2. 检索器是否找到正确数据？
3. 模型是否编造事实或违反业务约束？
4. 新模型、新 Prompt 或新 Embedding 是否导致回归？
5. 延迟和调用成本是否明显增加？
6. 哪些测试案例失败，为什么失败？
7. 质量下降时能否阻止代码合并？

Eval42 用统一测试协议、Adapter、指标、基线对比和 CI 门禁解决这些问题。

### 1.1 真实项目审阅基线

本计划 v1.1 已对照以下仓库的默认分支实现修订：

- PhoneMall：`yuyukosama2004/rag-shopping-assistant-platform`，审阅 revision `a7f8bb216367a3ba7476e2591d3b8ce3bfad6719`，版本 `v0.8.0-alpha.2`。
- GroundedSeek：`yuyukosama2004/grounded-seek`，审阅 revision `d2f9b11ef8d73f1c1f92fe966c5d2c18e21dcf47`，版本 `v1.1.0`。

已确认的现实约束：

- PhoneMall 的生产接口是带用户历史和持久化副作用的 SSE 聊天接口，当前不返回结构化检索结果。
- PhoneMall 的模型、Temperature、Prompt 和额度由商家设置动态控制，不适合作为可重复评测入口。
- PhoneMall 已有商品、SKU、库存、AI 请求耗时和估算成本数据，可复用但需要补充评测专用观测字段。
- GroundedSeek 已有异步 Run API、版本化 Research Artifact、Evidence、Citation、内容哈希和 JSON/Markdown 导出。
- GroundedSeek 已有 50 条冻结案例，但现有脚本主要检查“运行完成且有来源”，尚不能证明证据或引用质量。
- 两个真实项目都可通过 HTTP 接入，因此 Command Adapter 不进入 v0.1.0。

---

## 2. 核心目标

### 2.1 产品目标

Eval42 应能够：

1. 从 JSONL 读取固定评测数据集，并使用 YAML 定义运行配置。
2. 通过 Adapter 调用不同的被测系统。
3. 保存检索结果、最终输出、事实、延迟和 Token 使用信息。
4. 执行确定性指标和项目专属检查。
5. 将当前结果与基线版本进行比较。
6. 根据阈值输出 PASS、WARN 或 FAIL。
7. 生成 JSON 与 Markdown 报告。
8. 通过退出码接入 GitHub Actions 等 CI。
9. 精确展示失败案例，而不是只输出一个总分。
10. 在至少两个真实项目中使用后，再将通用实现迁入本仓库并公开发布。

### 2.2 工程目标

- 本地优先，不依赖 Eval42 云服务。
- 默认不上传用户数据、Prompt、回答或评测结果。
- 确定性指标优先。
- Adapter 与指标接口保持简单、可测试。
- 相同输入和相同被测版本应产生可解释的结果。
- 报告可被人审查，不隐藏失败细节。
- 第一版不依赖数据库和 Web 服务。
- 可以在普通开发机和 CI 中运行。

### 2.3 成功标准

通用实现迁入 Eval42 仓库并公开发布前必须满足：

- PhoneMall 已使用 Eval42 运行至少 30 条固定案例，其中首批 20 条形成最小闭环。
- GroundedSeek 已从现有 50 条数据中审计并升级至少 15 条可判定 Gold Set。
- 支持至少 5 个确定性指标。
- 支持基线比较和 CI 失败退出码。
- 评测报告能明确定位失败案例。
- 核心模块单元测试覆盖率不低于 85%。
- 示例项目能在无真实 API Key 的 Mock 模式下运行。
- 文档允许陌生开发者在 15 分钟内完成第一次评测。

---

## 3. 非目标

首个稳定版本不做以下内容：

- 不做 LangSmith、Weights & Biases 或完整实验管理平台。
- 不做在线 SaaS。
- 不做用户、团队、权限和计费系统。
- 不做实时监控 Dashboard。
- 不做模型代理或自动 Prompt 优化平台。
- 不自动生成大量测试集并假设其正确。
- 不建立插件市场。
- 不强制依赖 RAGAS 或某个模型供应商。
- 不将 LLM Judge 作为唯一 CI 门禁。
- 不尝试统一所有 AI 项目的“正确”定义。
- 不保存生产环境敏感数据。
- 不在只有一个 Adapter 时设计复杂的动态插件框架。

---

## 4. 总体开发策略

采用“独立规范仓库留痕 + 项目内验证 → 第二项目验证 → 抽取通用实现”的路线。

```text
阶段 A：Eval42 仓库维护协议、计划和变更留痕
        ↓
阶段 B：PhoneMall 内部评测模块
        ↓
阶段 C：整理最小 Core 与 PhoneMall Adapter
        ↓
阶段 D：接入 GroundedSeek 现有 Run / Artifact API
        ↓
阶段 E：确认抽象边界
        ↓
阶段 F：将经过验证的通用实现迁入 Eval42 仓库
        ↓
阶段 G：发布 v0.1.0
```

### 4.1 为什么不直接在独立仓库实现全部能力

如果只根据想象设计通用框架，容易出现：

- 测试案例格式过度复杂。
- Adapter 接口不符合真实项目。
- 指标系统只有抽象，没有实际消费者。
- 花费大量时间开发插件机制和配置系统。
- 最终没有任何项目真正使用。

因此，Eval42 仓库可以先承载计划、协议、Issue、PR、Tag 和 Release，但通用代码必须由至少两个真实项目共同需求推动后再稳定下来。

### 4.2 v1.2 执行顺序调整

PhoneMall 和 GroundedSeek 的技术接入已经分别完成并合并，但人工 Gold 审核、真实 Nightly
和跨迭代使用证据仍未完成。随后，项目所有者明确要求 Eval42 本身必须成为可安装、可交互的
通用测试工具，而不能只保留协议。因此 v1.2 记录以下执行决策：

- 允许在人工 Gold 审核完成前，以公开协议和两个目标项目已验证的 HTTP 接口为输入，
  clean-room 实现独立 Core、CLI、Mock 示例和 CI。
- 不从 PhoneMall 或 GroundedSeek 复制源码；目标项目继续保留各自实现和许可边界。
- 提前实现不等于完成双项目真实验证，不得把候选标注称为人工审核 Gold Set，也不得声称
  Nightly 或真实基线已经验证。
- v0.1.0 稳定开源发布门禁不变：Eval42 LICENSE、人工数据审核、真实使用证据以及发布安装
  验证仍须逐项满足。
- 在上述门禁完成前，只能把当前包称为 standalone alpha；GitHub prerelease 也必须明确
  标注其非稳定性质。

此调整改变 Phase 4–6 的实施顺序，不改变质量、数据治理、许可或最终验收标准。对应实现
与差异证据记录在 `docs/implementation-evidence.md` 和
`docs/compatibility-decisions.md`。

---

## 5. 用户与使用场景

### 5.1 主要用户

- 开发 RAG、Agent 或受约束生成系统的个人开发者。
- 希望在 CI 中阻止 AI 质量回归的小团队。
- 需要业务规则检查，而不只需要通用语义评分的项目。

### 5.2 PhoneMall 使用场景

开发者修改了：

- Embedding 模型。
- Top-K 参数。
- 商品文本拼接方式。
- Prompt。
- 生成模型。
- 商品可售过滤规则。

随后执行：

```bash
eval42 run evals/phonemall.yml
```

系统报告：

```text
Cases:                  40
Recall@5:               0.850  (+0.025)
MRR:                    0.762  (-0.008)
Constraint pass rate:   0.975  (-0.025)
Out-of-scope rate:      0.000  (-0.025)
Fact accuracy:          0.964  (+0.012)
P95 latency:            2840ms (+410ms)

Gate: PASS WITH WARNINGS
```

### 5.3 GroundedSeek 使用场景

开发者修改来源排序或报告生成 Prompt，Eval42 检查：

- 是否找到要求的一手来源。
- 关键证据是否被召回。
- 引用是否支持对应 Claim。
- 重要 Claim 是否都有证据。
- 冲突证据是否被保留。
- 信息是否符合时间要求。

### 5.4 CI 使用场景

Pull Request 修改检索逻辑后，CI 自动运行小型评测集：

```text
Recall@5 从 0.84 降到 0.70
下降幅度超过允许的 0.05
Gate: FAIL
Process exit code: 2
```

PR 因质量回归被阻止合并。

---

## 6. 技术选型

### 6.1 推荐技术栈

- Python 3.11+；CI 覆盖 3.11、3.12、3.13、3.14
- `pydantic`：配置、案例、结果和报告模型
- `typer`：CLI
- `httpx`：HTTP Adapter
- `PyYAML`：YAML 配置
- `pytest`：测试
- `pytest-cov`：覆盖率
- `ruff`：格式和静态检查
- `mypy` 或 `pyright`：类型检查
- `jinja2`：后续静态 HTML 报告，可在 MVP 后加入

### 6.2 依赖原则

- 核心包不直接依赖某个 LLM SDK。
- OpenAI-compatible API 通过可选 Adapter 支持。
- RAGAS 等第三方评测框架作为可选扩展，不进入最小核心。
- 第一阶段可以只使用 Python 标准库、Pydantic、Typer、httpx 和 PyYAML。
- Eval42 与被测项目通过 HTTP 协议隔离，不要求与 GroundedSeek 使用同一 Python 版本。

### 6.3 Python 包名

建议：

```text
项目品牌：Eval42
PyPI 包：eval42
CLI 命令：eval42
Python 模块：eval42
```

发布前必须检查 PyPI 和 GitHub 名称可用性。如果不可用，可选择：

- `eval42-cli`
- `guardrail-eval`
- `verifiable-eval`

---

## 7. 架构设计

### 7.1 核心流程

```text
Config
  ↓
Dataset Loader
  ↓
Test Cases
  ↓
Adapter
  ↓
Raw Case Results
  ↓
Metric Evaluators
  ↓
Aggregated Metrics
  ↓
Baseline Comparator
  ↓
Gate Engine
  ↓
JSON / Markdown Report + Exit Code
```

### 7.2 模块职责

#### Config Loader

- 加载 YAML 配置。
- 解析环境变量引用。
- 校验数据集、Adapter、指标和门禁配置。
- 不读取或打印秘密值。

#### Dataset Loader

- 加载 JSONL。
- 校验 Case ID 唯一性。
- 校验输入和期望字段。
- 支持按 tag、case ID、数量筛选。

#### Adapter

- 将通用 EvalCase 转换为目标系统请求。
- 调用被测系统。
- 收集检索结果、推荐结果、回答、事实和 Usage。
- 返回统一 CaseResult。

#### Metric

- 接收 EvalCase 与 CaseResult。
- 计算单案例分数。
- 返回分数、通过状态和证据说明。
- 不直接负责打印报告。

#### Aggregator

- 汇总单案例指标。
- 计算均值、比例、p50、p95。
- 按 tag 生成分组结果。

#### Baseline Comparator

- 加载固定基线。
- 计算绝对差值与相对差值。
- 标注新增失败和已修复案例。

#### Gate Engine

- 根据阈值决定 PASS、WARN、FAIL。
- 支持最低值、最高值和最大退化量。
- 返回稳定退出码。

#### Reporter

- JSON：供机器读取。
- Markdown：供开发者和 PR 查看。
- 后续 HTML：供静态浏览。

---

## 8. 推荐目录结构

### 8.1 PhoneMall 内部阶段

```text
rag-shopping-assistant-platform/
└─ evals/
   ├─ README.md
   ├─ config/
   │  └─ phonemall.yml
   ├─ datasets/
   │  └─ shopping_queries.jsonl
   ├─ baselines/
   │  └─ phonemall-main.json
   ├─ reports/
   │  └─ .gitkeep
   └─ src/
      ├─ run_eval.py
      ├─ models.py
      ├─ adapter.py
      ├─ metrics.py
      ├─ gates.py
      └─ report.py
```

### 8.2 通用实现迁入后

```text
eval42/
├─ .github/
│  ├─ workflows/
│  │  ├─ ci.yml
│  │  └─ release.yml
│  └─ ISSUE_TEMPLATE/
├─ docs/
│  ├─ concepts.md
│  ├─ datasets.md
│  ├─ adapters.md
│  ├─ metrics.md
│  ├─ gates.md
│  ├─ ci.md
│  └─ security.md
├─ examples/
│  ├─ mock-shopping/
│  └─ mock-research/
├─ src/
│  └─ eval42/
│     ├─ __init__.py
│     ├─ cli.py
│     ├─ config.py
│     ├─ models.py
│     ├─ datasets.py
│     ├─ runner.py
│     ├─ aggregation.py
│     ├─ baseline.py
│     ├─ gates.py
│     ├─ errors.py
│     ├─ adapters/
│     │  ├─ base.py
│     │  ├─ http.py
│     │  └─ command.py
│     ├─ metrics/
│     │  ├─ base.py
│     │  ├─ retrieval.py
│     │  ├─ constraints.py
│     │  ├─ facts.py
│     │  ├─ citations.py
│     │  └─ performance.py
│     └─ reporters/
│        ├─ json_reporter.py
│        └─ markdown_reporter.py
├─ tests/
│  ├─ fixtures/
│  ├─ unit/
│  ├─ integration/
│  └─ e2e/
├─ CHANGELOG.md
├─ CONTRIBUTING.md
├─ LICENSE
├─ README.md
├─ SECURITY.md
└─ pyproject.toml
```

---

## 9. 数据协议

### 9.1 通用测试案例

JSONL 每行一个对象：

```json
{
  "schema_version": "1",
  "id": "phone-camera-001",
  "input": {
    "query": "预算 4000 元，重视拍照和续航，不要苹果"
  },
  "expected": {
    "relevant_ids": [12, 18, 26],
    "forbidden_ids": [3, 4, 5],
    "constraints": {
      "max_price": 4000,
      "excluded_brands": ["Apple"],
      "must_be_sellable": true
    },
    "expected_empty_result": false,
    "facts": {
      "12.price": 3999,
      "18.price": 3899
    }
  },
  "tags": ["budget", "camera", "battery"],
  "metadata": {
    "dataset_version": "2026-07-16",
    "reviewed_by": "human",
    "notes": "允许多个正确商品"
  }
}
```

数据集规则：

- `input` 只包含实际发送给被测系统的内容。
- `expected` 只包含评分使用的答案，不得由 Adapter 发送给被测系统。
- GroundedSeek 的 `allowed_domains` 属于输入限制；`accepted_domains` 属于期望结果，两者不得复用同一字段。
- Loader 为规范化后的整条 Case 计算 `case_hash`，用于判断同 ID 案例是否真的可与基线比较。
- 所有 Schema 从第一次实现开始版本化，不等待 v0.1.0 发布。

### 9.2 通用 CaseResult

```json
{
  "schema_version": "1",
  "case_id": "phone-camera-001",
  "status": "completed",
  "retrieved_items": [
    {
      "id": 18,
      "score": 0.91,
      "attributes": {
        "brand": "Xiaomi",
        "price": 3899,
        "sellable": true
      }
    }
  ],
  "eligible_items": [
    {
      "id": 18,
      "score": 0.91,
      "rank": 1,
      "attributes": {
        "brand": "Xiaomi",
        "price": 3899,
        "sellable": true
      }
    }
  ],
  "recommended_ids": [18, 12],
  "answer": "根据你的预算和拍照需求……",
  "claims": [
    {
      "subject_id": 18,
      "field": "price",
      "value": 3899
    }
  ],
  "citations": [],
  "usage": {
    "total_latency_ms": 2450,
    "retrieval_latency_ms": 318,
    "first_token_latency_ms": 912,
    "input_tokens": 1530,
    "output_tokens": 281,
    "token_count_kind": "actual",
    "estimated_cost": 0.032,
    "currency": "CNY"
  },
  "system": {
    "adapter": "phonemall",
    "model": "deepseek-chat",
    "embedding_model": "example-embedding",
    "revision": "git-sha",
    "prompt_hash": "sha256:...",
    "config_hash": "sha256:...",
    "index_fingerprint": "sha256:...",
    "retrieval_mode": "vector",
    "index_ready": true
  },
  "error": null
}
```

### 9.3 失败结果

Adapter 调用失败也必须生成结果：

```json
{
  "case_id": "phone-camera-001",
  "status": "error",
  "retrieved_items": [],
  "recommended_ids": [],
  "answer": null,
  "usage": {
    "total_latency_ms": 30000
  },
  "error": {
    "type": "timeout",
    "message": "Target system did not respond within 30 seconds",
    "retryable": true
  }
}
```

报告不得因单个 Case 异常而丢失其他结果。

执行错误不得自动转换为指标 0 分，否则会把基础设施故障伪装成质量下降。默认执行策略：

```yaml
execution_policy:
  min_completion_rate: 1.0
  retries: 1
  max_retryable_error_rate: 0.0
```

- 结果完整且质量 Gate 失败时返回退出码 `2`。
- 完成率低于可信阈值或存在未解决的部分失败时返回退出码 `3`。
- 配置、Schema、数据集和 Runner 启动失败时返回退出码 `1`。
- 同时存在质量失败和不可信执行结果时优先返回 `3`，因为质量结论不完整。

---

## 10. 配置协议

示例 `phonemall.yml`：

```yaml
project:
  name: phonemall
  revision: ${GIT_SHA:-local}

dataset:
  path: evals/datasets/shopping_queries.jsonl
  include_tags: []
  exclude_tags: []

adapter:
  type: http
  base_url: ${PHONEMALL_BASE_URL:-http://localhost:8080}
  endpoint: /api/merchant/ai/evaluate
  timeout_seconds: 60
  headers:
    Authorization: Bearer ${PHONEMALL_MERCHANT_TOKEN}

execution_policy:
  min_completion_rate: 1.0
  retries: 1
  max_retryable_error_rate: 0.0

metrics:
  - type: recall_at_k
    k: 5
  - type: mrr
  - type: forbidden_item_rate
  - type: constraint_pass_rate
  - type: fact_accuracy
  - type: latency

gates:
  - metric: recall_at_5
    min: 0.80
  - metric: mrr
    min: 0.70
  - metric: forbidden_item_rate
    max: 0.00
  - metric: constraint_pass_rate
    min: 0.97
  - metric: p95_total_latency_ms
    max: 5000
    severity: warning
  - metric: recall_at_5
    max_regression: 0.05

baseline:
  path: evals/baselines/phonemall-main.json

report:
  formats: [json, markdown]
  output_dir: evals/reports
  include_inputs: true
  include_answers: false
  include_retrieved_content: false
  include_claims: true
```

### 10.1 环境变量规则

- `${NAME}`：必须存在，否则配置失败。
- `${NAME:-default}`：不存在时使用默认值。
- 报告中不得打印环境变量实际内容。
- Header 中的 Authorization 默认自动脱敏。

---

## 11. Adapter 设计

### 11.1 第一阶段：PhoneMall 专用 Adapter

PhoneMall 应提供独立评测端点，避免从最终自然语言回答中反向猜测检索结果。该端点复用现有店主/店员认证，并由 `AI_EVAL_ENABLED=false` 默认关闭：

```text
POST /api/merchant/ai/evaluate
```

请求：

```json
{
  "query": "预算 4000 元，重视拍照和续航，不要苹果",
  "generate_answer": false
}
```

返回：

```json
{
  "retrieved_products": [
    {
      "id": 18,
      "score": 0.91,
      "rank": 1,
      "brand": "Xiaomi",
      "price": 3899,
      "sellable": true
    }
  ],
  "eligible_products": [
    {
      "id": 18,
      "score": 0.91,
      "rank": 1,
      "brand": "Xiaomi",
      "price": 3899,
      "sellable": true
    }
  ],
  "recommended_ids": [18, 12],
  "answer": "……",
  "usage": {
    "retrieval_latency_ms": 318,
    "first_token_latency_ms": 912,
    "total_latency_ms": 2450,
    "input_tokens": 1530,
    "output_tokens": 281,
    "token_count_kind": "actual"
  },
  "versions": {
    "model": "deepseek-chat",
    "embedding_model": "example-embedding",
    "prompt_hash": "sha256:...",
    "setting_hash": "sha256:...",
    "index_fingerprint": "sha256:...",
    "retrieval_mode": "vector",
    "index_ready": true
  }
}
```

PhoneMall 接入前必须先从现有 `AiServiceImpl` 提取可复用的 `AiRetrievalService`：

- 检索结果返回 `{product, score, rank}`，而不是只返回 `Product`。
- 生产聊天和评测端点调用同一检索与可售过滤逻辑。
- 明确区分原始检索结果和过滤后的可售候选。
- 向量未就绪或 Embedding 调用失败时记录 `retrieval_mode=fallback_all`，不得伪装成正常向量结果。
- 修正当前 Prompt 中把 Product ID 标为“SKU”的字段命名。

### 11.2 评测端点安全要求

- 默认只在测试或受保护环境启用。
- 复用现有店主/店员权限和网关认证，不新建第二套长期 Token。
- 不允许修改订单、库存或用户数据。
- 默认只运行检索，不调用生成模型。
- 不读取用户聊天历史。
- 不写入 `AiConversation`，不消耗用户每日额度。
- 生成回答时可以写入独立的评测 Usage，但必须与生产用户 Usage 分开。
- 不返回 API Key、系统 Prompt 或内部异常堆栈。
- 生产环境默认关闭。

### 11.3 通用 HTTP Adapter

通用实现迁入 Eval42 后，提供字段映射：

```yaml
adapter:
  type: http
  method: POST
  endpoint: /evaluate
  request:
    json:
      query: $.input.query
  response_mapping:
    retrieved_items: $.retrieved_products
    recommended_ids: $.recommended_ids
    answer: $.answer
    usage: $.usage
```

如果字段映射复杂，再允许编写 Python Adapter。不要在 MVP 中实现完整模板语言。

### 11.4 GroundedSeek HTTP Adapter

GroundedSeek 已提供版本化 Run 和 Research Artifact API，Adapter 直接复用：

```text
POST /api/v1/runs
GET  /api/v1/runs/{run_id}
GET  /api/v1/runs/{run_id}/result
```

Adapter 负责：

- 创建 Run 并轮询到终态。
- 将 `ResearchArtifact.sources`、`evidence`、`citations` 和 `execution_summary` 映射为 CaseResult。
- 保留 Artifact `schema_version`、内容哈希和运行状态。
- 将 `failed`、`cancelled`、队列满和模型不可用映射为明确执行错误。
- 不修改 GroundedSeek Core，也不建立第二条研究队列。

### 11.5 Command Adapter

Command Adapter 不进入 v0.1.0。只有 ecc-init 或其他真实项目成为消费者后再评估：

```yaml
adapter:
  type: command
  command:
    - python
    - scripts/evaluate_case.py
  input: stdin_json
  output: stdout_json
```

适合：

- ecc-init。
- 无 HTTP 服务的离线程序。

Command 配置属于可信可执行输入。未来实现时必须包含命令白名单、工作目录、环境变量白名单、子进程超时、输出上限和进程树终止策略；来自外部 PR 的配置不得在带秘密的 CI Job 中执行。

---

## 12. 指标设计

### 12.0 通用聚合规则

- 每个指标必须声明适用条件、空分母策略和最少适用案例数。
- `not_applicable` 不进入均值，但报告必须显示适用案例数和跳过案例数。
- 默认同时报告 Macro（按 Case 平均）和必要的 Micro（按项目或 Claim 汇总），不得只给一个含义不明的总分。
- 完成失败的 Case 不进入质量指标，并由 Execution Policy 单独决定结果是否可信。
- 报告同时展示分数变化和变化案例数；小数据集中 `0.05` 的变化可能只代表一个 Case。

## 12.1 Recall@K

```text
Recall@K = Top K 中相关项目数量 / 全部相关项目数量
```

规则：

- `expected.relevant_ids` 为空时不计算，标为 `not_applicable`。
- 返回结果需要去重。
- 缺少的相关项必须进入失败详情。

输出示例：

```json
{
  "metric": "recall_at_5",
  "score": 0.6667,
  "details": {
    "matched": [12, 18],
    "missing": [26]
  }
}
```

## 12.2 MRR

取第一个相关项目排名的倒数：

```text
第 1 名：1
第 2 名：0.5
第 3 名：0.333
未找到：0
```

聚合结果为所有适用案例的平均值。

## 12.3 Forbidden Item Rate

```text
越界推荐率 = 推荐结果中 forbidden ID 数 / 全部推荐结果数
```

PhoneMall 中还要自动将以下项目视为越界：

- 不存在。
- 已下架。
- 不可售。
- 明确排除品牌。
- 超出硬预算限制。

没有推荐结果时：

- 若 `expected.expected_empty_result=true`，该 Case 的空结果检查通过。
- 否则 Forbidden Item Rate 标为 `not_applicable`，并由 `unexpected_empty_result_count` 记录硬失败，不能把空回答解释为 0% 越界率。

## 12.4 Constraint Pass Rate

每条推荐逐项检查约束：

```text
预算
品牌排除
可售状态
库存
指定类别
项目专属硬规则
```

```text
Constraint pass rate = 通过全部硬约束的推荐数 / 全部推荐数
```

没有推荐结果时不得记为 100%；按 `expected_empty_result` 判断通过，否则标为 `not_applicable` 并产生空结果失败。

## 12.5 Fact Accuracy

将可验证 Claim 与事实快照比较：

```text
Fact accuracy = 正确 Claim 数 / 全部可验证 Claim 数
```

第一阶段只检查结构化事实：

- 商品 ID。
- 价格。
- 品牌。
- 型号。
- 可售状态。
- 库存状态。

不要在第一阶段尝试自动理解所有自然语言事实。

Fact Accuracy 必须与 `claim_coverage` 同时展示。模型不输出任何 Claim 时 Fact Accuracy 标为 `not_applicable`，不能得到虚假的满分。

## 12.6 Latency

记录：

- Retrieval latency。
- First-token latency。
- Total latency。

聚合：

- Mean。
- p50。
- p95。
- Maximum。

小样本下必须在报告中显示样本数，避免将少量案例的 p95 解释为稳定生产指标。

## 12.7 Token 与成本

记录：

- Input tokens。
- Output tokens。
- Total tokens。
- Estimated cost。

成本计算必须记录：

- 模型名称。
- 价格表版本。
- 货币。
- 估算方法。

无法获得 Token 时标记 `unavailable`，不能用字符数伪装成精确 Token。PhoneMall 当前基于字符数估算 Token，必须输出 `token_count_kind: estimated`；只有供应商 Usage 返回值才能标记为 `actual`。

---

## 13. GroundedSeek 指标扩展

GroundedSeek 接入时基于现有 Research Artifact 增加：

### 13.1 Source Quality

来源等级示例：

```text
3：官方文档、标准、论文原文、政府或原始数据
2：权威二手分析、专业媒体
1：普通转载、社区讨论
0：无法验证或明显不可靠来源
```

等级规则必须允许项目配置，不能由 Eval42 固定宣称普遍真理。

### 13.2 Evidence Recall

```text
找到的关键证据数 / 标注的全部关键证据数
```

### 13.3 Citation Validity

确定性检查：

- 回答中的引用编号是否存在。
- 引用是否映射到当前 Run 的 Source 和 Evidence。
- 是否引用未知或已截断的来源。

GroundedSeek 当前 `verification_status=supported` 只表示引用编号和警告状态，不代表语义蕴含。Eval42 不得将该字段直接报告为 Citation Entailment。

### 13.4 Citation Entailment

检查引用片段是否支持对应 Claim。

第一版采用：

- 人工标注的 Claim–Evidence 对。
- 关键词或结构化事实确定性检查。

LLM Judge 只能作为补充评分，并必须记录模型和 Prompt。

### 13.5 Claim Coverage

```text
有证据支持的重要 Claim 数 / 全部重要 Claim 数
```

### 13.6 Conflict Preservation

标注存在冲突的测试案例，检查报告是否：

- 保留双方证据。
- 标明来源。
- 未将冲突隐藏成单一确定结论。

GroundedSeek 当前冲突识别是关键词启发式，只能作为诊断信号。真正的 Conflict Preservation Gold Case 必须提供冻结的双方证据和人工期望。

---

## 14. 基线管理

### 14.1 基线内容

基线文件应包含：

- 项目名称。
- Git revision。
- 数据集版本与哈希。
- Eval42 版本。
- Adapter 版本。
- 模型与 Embedding 版本。
- Prompt、配置和索引指纹。
- 事实快照哈希。
- Metric 实现版本与参数。
- 运行环境标识。
- 聚合指标。
- 单案例结果摘要。
- 生成时间。

### 14.2 基线生成

```bash
eval42 baseline create evals/phonemall.yml \
  --output evals/baselines/phonemall-main.json
```

### 14.3 基线更新规则

禁止 CI 自动覆盖基线。

更新基线必须：

1. 显式执行命令。
2. 生成差异报告。
3. 人工审查新增失败和指标变化。
4. 通过 PR 提交。

### 14.4 数据集变化

数据集哈希变化时：

- 报告必须标注“不可直接与旧基线比较”。
- 只有 Case ID 和规范化 `case_hash` 都相同时才比较单案例结果。
- 总体指标差异标为 `dataset_changed`。

以下变化默认使对应指标不可直接比较：

- 价格表版本变化：成本指标。
- 运行机器、容器资源或网络路径变化：延迟指标。
- Prompt、模型、Embedding、索引或 Metric 实现变化：必须在报告中明确显示变化来源。

---

## 15. Gate Engine

### 15.1 Gate 类型

#### 最低值

```yaml
- metric: recall_at_5
  min: 0.80
```

#### 最高值

```yaml
- metric: forbidden_item_rate
  max: 0.00
```

#### 最大绝对退化

```yaml
- metric: mrr
  max_regression: 0.05
```

#### 最大相对退化

```yaml
- metric: average_cost
  max_relative_regression: 0.20
```

#### 案例级硬失败

```yaml
- metric: nonexistent_recommendation_count
  max: 0
  scope: every_case
```

### 15.2 严重级别

- `error`：导致 FAIL。
- `warning`：整体可 PASS，但报告警告。
- `info`：只展示变化。

每个 Gate 应记录：

- 阈值负责人。
- 设定日期。
- 设定时的数据集版本和样本量。
- 调整原因。

成本和真实网络延迟在 v0.1.0 默认只允许 `warning` 或 `info`。不存在商品、不可售商品和意外空结果必须使用案例级硬失败，不能被平均分掩盖。

### 15.3 退出码

```text
0：PASS
1：配置、数据集或执行错误
2：质量门禁失败
3：部分案例未完成，结果不可信
```

退出码在 v0.x 阶段也应保持稳定。

---

## 16. CLI 设计

### 16.1 核心命令

```bash
eval42 run <config>
eval42 validate <config>
eval42 dataset validate <dataset>
eval42 baseline create <config>
eval42 baseline compare <current> <baseline>
eval42 report <result>
eval42 version
```

### 16.2 `run`

```bash
eval42 run evals/phonemall.yml
```

常用参数：

```text
--case ID
--tag TAG
--limit N
--concurrency N
--no-gate
--mock
--output DIR
--format json
--format markdown
--verbose
```

### 16.3 输出原则

默认终端输出保持简洁：

```text
Eval42 · phonemall
Dataset: shopping_queries.jsonl · 40 cases

Running ........................ 40/40

Recall@5              0.850   PASS
MRR                   0.762   PASS
Forbidden item rate   0.000   PASS
Constraint pass rate  0.975   PASS
P95 latency           2840ms  WARN

Gate: PASS WITH WARNINGS
Report: evals/reports/phonemall-20260716.md
```

敏感 Header、Token 和完整系统 Prompt 不得出现在输出中。

---

## 17. 报告设计

### 17.1 Markdown 报告结构

```text
# Eval42 Report

## Run metadata
## Gate summary
## Metric summary
## Baseline comparison
## Regressed cases
## Fixed cases
## Failed cases
## Results by tag
## Latency and cost
## Warnings and limitations
```

### 17.2 失败案例展示

每条失败案例至少包含：

- Case ID。
- 输入摘要。
- 期望 ID。
- 实际检索 ID。
- 实际推荐 ID。
- 违反的约束。
- 指标详情。
- 被测版本。

输入、完整回答、检索正文和 Claim 是否写入报告分别由配置控制。

### 17.3 JSON 报告

Dataset、Config、CaseResult、Report 和 Baseline Schema 从第一版实现开始分别版本化：

```json
{
  "schema_version": "1",
  "run": {},
  "summary": {},
  "gates": [],
  "cases": []
}
```

---

## 18. CI 集成

### 18.1 PhoneMall GitHub Actions

首阶段使用 Mock 或固定测试服务：

```yaml
- name: Run deterministic AI evaluation
  run: |
    python -m pip install -r evals/requirements.txt
    python evals/src/run_eval.py \
      --config evals/config/phonemall-ci.yml
```

发布 Eval42 包后：

```yaml
- name: Install Eval42
  run: pip install eval42

- name: Run AI quality gate
  run: eval42 run evals/phonemall-ci.yml
```

### 18.2 CI 分层

#### 每个 PR

- 运行 10–20 条确定性、无外部付费 API 的小型数据集。
- PhoneMall 使用固定商品快照、固定 Embedding 或预计算检索 Fixture。
- GroundedSeek 使用冻结网页快照、固定搜索结果和 Mock Ollama。
- 检查检索、约束和事实。
- 外部 PR Job 不获得真实模型、商户或生产环境秘密。

#### Nightly

- 运行完整数据集。
- 调用真实 Embedding 和生成模型。
- GroundedSeek 调用真实 SearXNG、网页 Reader 和 Ollama。
- 记录延迟和成本。
- 避免因为供应商短暂波动阻止所有 PR。

#### Release Gate

- 固定模型、Prompt、数据快照。
- 运行完整评测。
- 人工审查报告。
- 保存 Release artifact。

### 18.3 PR 报告

第一版将 Markdown 报告作为 GitHub Actions artifact。

后续可选择：

- 写入 Job Summary。
- 由独立脚本更新 PR 评论。

不要在核心包中直接耦合 GitHub API。

---

## 19. 测试计划

### 19.1 单元测试

必须覆盖：

- JSONL 加载。
- 重复 Case ID。
- 配置环境变量解析。
- Recall@K。
- MRR。
- 越界率。
- Constraint pass rate。
- Fact accuracy。
- p50/p95。
- Baseline diff。
- Gate 判定。
- 退出码映射。
- 敏感字段脱敏。

### 19.2 集成测试

- Mock HTTP Server + HTTP Adapter。
- 完整数据集 → Adapter → Metrics → Report。
- Adapter 部分失败。
- 超时和重试。
- 基线数据集版本不一致。
- 同 ID 但 `case_hash` 不一致。
- GroundedSeek Run 轮询、队列满、失败和取消状态。

### 19.3 E2E 测试

示例项目中运行：

```bash
eval42 run examples/mock-shopping/eval.yml
```

验证：

- 终端退出码。
- JSON 报告结构。
- Markdown 报告内容。
- Gate PASS/FAIL。

### 19.4 Golden Tests

为报告保留小型快照：

- 固定输入生成稳定 JSON。
- Markdown 只对结构进行快照，不依赖运行时间。

### 19.5 测试覆盖率

- Core、Metric、Gate：至少 90%。
- 全项目：至少 85%。
- Adapter 网络错误路径必须覆盖。

---

## 20. 安全与隐私

### 20.1 默认隐私原则

- Eval42 不发送遥测。
- 不要求账户。
- 不上传评测数据。
- 报告默认不包含完整回答。
- 报告默认不包含检索正文。
- 配置中的秘密只从环境变量读取。

### 20.2 敏感数据

以下已知秘密字段必须确定性脱敏：

- Authorization Header。
- API Key。
- Cookie。
- 完整生产 Prompt。
- 内部服务器 URL，可由配置决定是否显示。

姓名、地址、电话、邮箱和其他个人信息不能仅靠通用自动识别保证安全。项目必须在数据进入 Eval42 前完成脱敏，并可配置字段删除和项目专属正则脱敏。

### 20.3 Prompt 注入

被测系统的回答、网页内容、检索文档和评测配置均视为不可信数据；其中 Command Adapter 配置还属于可执行输入。

Eval42 不应执行回答中的：

- Shell 命令。
- URL 操作。
- 文件写入指令。
- 动态 Python 代码。

### 20.4 Adapter 安全

- HTTP Adapter 设置最大响应体。
- 设置连接和读取超时。
- 限制重试次数。
- 默认不跟随跨域重定向；必须校验目标地址，避免 SSRF。
- 报告异常时不输出秘密。
- 外部 PR 运行的评测 Job 不注入生产秘密。
- Command Adapter 未来实现时默认禁用 Shell 字符串，并采用第 11.5 节的额外限制。

---

## 21. 数据集治理

### 21.1 数据集必须版本化

每个数据集记录：

- 版本。
- 创建日期。
- 标注人或标注方式。
- 数据来源快照。
- 适用项目版本。
- 已知限制。

### 21.2 PhoneMall 数据集分类

建议首批 40 条：

| 类别 | 数量 |
|---|---:|
| 预算约束 | 6 |
| 拍照需求 | 5 |
| 游戏性能 | 5 |
| 续航需求 | 5 |
| 品牌排除 | 4 |
| 多条件组合 | 6 |
| 无合适商品 | 3 |
| 下架/无库存 | 3 |
| Prompt 注入或越权 | 3 |

### 21.3 标注审查

每条案例必须回答：

- 为什么这些商品相关？
- 是否允许其他正确商品？
- 数据基于哪个商品快照？
- 哪些约束是硬约束？
- 哪些偏好只是软排序？

### 21.4 GroundedSeek 现有数据集治理

GroundedSeek 当前已有 50 条冻结案例：

| 类别 | 数量 |
|---|---:|
| static_web | 20 |
| timely | 10 |
| unverifiable | 10 |
| conflict | 5 |
| security | 5 |

不重新从零编写 15–20 条案例，而是先审计这 50 条，并选择至少 15 条升级为 Eval42 Gold Set：

- `static_web` PR 门禁必须使用冻结网页快照，不能继续依赖实时网页。
- `accepted_domains` 只能用于评分，不能同时作为发送给系统的 `allowed_domains`。
- 增加 `required_evidence_matchers`、期望事实或人工 Claim–Evidence 对。
- `conflict` 案例必须包含真实且冻结的冲突材料，不能只询问“应如何处理冲突”。
- `security` 案例必须验证 URL 安全边界实际被触发。
- `timely` 案例只进入 Nightly，不进入稳定 PR 基线。

### 21.5 数据来源与许可

- 记录商品快照、网页快照和人工标注的来源及使用授权。
- 开源前确认 Eval42、PhoneMall 和 GroundedSeek 的许可证与代码迁移授权。
- 未确认授权的网页全文不进入公开示例数据集。
- 定义评测数据和报告的保留期限与删除方式。

### 21.6 防止测试集污染

- 不将所有评测问题直接写进系统 Prompt。
- 开发集和最终评测集分开。
- 模型调优时避免只优化固定措辞。
- 后续增加改写版本与边界案例。

---

## 22. LLM Judge 策略

### 22.1 首阶段原则

LLM Judge 不进入硬门禁，只作为实验性报告。

### 22.2 可用场景

- 回答是否相关。
- 引用是否大体支持 Claim。
- 回答是否完整解释推荐理由。
- NovelFlow 内容是否存在语义冲突。

### 22.3 必须记录

- Judge 模型。
- Judge Prompt 版本。
- Temperature。
- 原始分数。
- 结构化解释。
- 重试情况。

### 22.4 校准

在启用 Judge 前：

1. 准备人工评分样本。
2. 比较 Judge 与人工评分。
3. 检查不同模型评分一致性。
4. 明确它只用于辅助还是门禁。

没有校准的 LLM Judge 不得宣称为客观准确率。

---

## 23. 性能与并发

### 23.1 默认并发

第一版默认串行，允许配置小并发：

```bash
eval42 run eval.yml --concurrency 4
```

### 23.2 并发限制

- 遵守目标 API 限流。
- 每个 Adapter 可声明最大并发。
- 429 应区分为供应商限流，不直接视为质量错误。
- 结果顺序按 Case ID 稳定输出。

### 23.3 缓存

第一版不默认缓存真实模型输出。

后续可增加内容哈希缓存：

```text
case input
+ adapter config
+ model version
+ prompt version
+ target revision
= cache key
```

缓存必须可关闭，并在报告中标注命中状态。

### 23.4 运行预算

Runner 支持：

```yaml
run_budget:
  max_cases: 20
  max_duration_seconds: 600
  max_estimated_cost: 5.00
  currency: CNY
```

预算耗尽属于执行终止，不属于质量失败。报告必须说明停止原因和未运行 Case。

---

## 24. 分阶段实施计划

## Phase 0：真实仓库审计与协议冻结

预计：3–4 个工作日。

任务：

- `EVAL-001` 确认 PhoneMall 生产检索、可售过滤、生成和 Usage 路径。
- `EVAL-002` 导出脱敏商品事实快照。
- `EVAL-003` 编写首批 20 条人工审核案例。
- `EVAL-004` 定义硬约束和软偏好。
- `EVAL-005` 确定 `/api/merchant/ai/evaluate` 安全策略。
- `EVAL-006` 审计 GroundedSeek 现有 50 条数据及 Research Artifact v1。
- `EVAL-007` 决定 Eval42、PhoneMall 和 GroundedSeek 的许可证及代码迁移授权。
- `EVAL-008` 固定 Dataset、Config、CaseResult、Report、Baseline Schema v1 草案。

交付物：

- `shopping_queries.jsonl`
- 数据集说明。
- 指标定义说明。
- 示例期望结果。
- GroundedSeek 数据审计清单。
- 协议 Schema 草案。

验收：

- 每条案例有唯一 ID。
- 每条相关商品有人工解释。
- 不包含真实用户数据。
- `input` 与 `expected` 字段不存在答案泄漏。
- 开源所需的许可证和数据授权已有明确决定。

## Phase 1：最小 Core 与 PhoneMall 检索闭环

预计：6–8 个工作日。

任务：

- `EVAL-101` 建立 `evals/` 目录。
- `EVAL-102` 实现数据模型和 JSONL Loader。
- `EVAL-103` 从 PhoneMall `AiServiceImpl` 提取 `AiRetrievalService`。
- `EVAL-104` 实现只读 `/api/merchant/ai/evaluate`。
- `EVAL-105` 实现 PhoneMall HTTP Adapter。
- `EVAL-106` 实现 Mock HTTP Adapter 和固定 Fixture。
- `EVAL-107` 实现 Recall@5。
- `EVAL-108` 实现 MRR。
- `EVAL-109` 实现越界商品和意外空结果检查。
- `EVAL-110` 实现约束通过率。
- `EVAL-111` 生成 JSON/Markdown 报告。
- `EVAL-112` 增加基础测试。

验收：

- 本地一条命令运行 20 条案例。
- 报告列出每条失败原因。
- 无需手工复制结果。
- 生产聊天与评测端点复用同一检索和可售过滤逻辑。
- Mock 路径完全离线运行，不需要真实 API Key。

## Phase 2：PhoneMall 基线与 PR 质量门禁

预计：5–7 个工作日。

任务：

- `EVAL-201` 实现基线创建和运行指纹。
- `EVAL-202` 实现 `case_hash` 可比性判断。
- `EVAL-203` 实现基线差异和新增失败/已修复列表。
- `EVAL-204` 实现 Gate Engine 和稳定退出码。
- `EVAL-205` 构建 PhoneMall PR 固定 Fixture 评测。
- `EVAL-206` 上传 Markdown/JSON 报告 artifact。
- `EVAL-207` 配置 Nightly 真实 Embedding 评测。
- `EVAL-208` 增加运行预算和部分失败策略。

验收：

- 可比较当前结果与主分支基线。
- 数据集变化能被识别。
- 故意降低 Recall 后 CI 失败。
- 供应商临时错误与质量失败能区分。
- PR 不需要真实付费模型即可运行确定性检查。

## Phase 3：GroundedSeek HTTP 接入与 Gold Set

预计：5–7 个工作日。

任务：

- `EVAL-301` 实现 GroundedSeek 异步 Run HTTP Adapter。
- `EVAL-302` 将现有 50 条数据转换为 Eval42 数据协议。
- `EVAL-303` 选择并升级至少 15 条 Gold Set。
- `EVAL-304` 准备冻结搜索结果、网页和 Ollama Fixture。
- `EVAL-305` 实现 Source Domain、Evidence Recall 和 Citation Validity。
- `EVAL-306` 实现 expected outcome 检查。
- `EVAL-307` 增加 GroundedSeek PR 离线评测。
- `EVAL-308` 增加真实网络 Nightly。

验收：

- Eval42 直接消费 Research Artifact v1，不修改 GroundedSeek Core。
- PR 评测不访问实时网页或真实 Ollama。
- `accepted_domains` 不会作为输入泄漏给被测系统。
- 现有“有来源即成功”的评测升级为可定位的质量指标。

## Phase 4：双项目验证与 Core 边界确认

预计：4–6 个工作日。

前置条件：

- PhoneMall 连续使用至少两次功能迭代。
- 已发现并修复真实回归。
- GroundedSeek Gold Set 已运行并产生可审查报告。

任务：

- `EVAL-401` 分离 Loader、Runner、Metric、Gate、Reporter。
- `EVAL-402` 定义 Base Adapter。
- `EVAL-403` 实现通用 HTTP Adapter。
- `EVAL-404` 建立 Mock Shopping 和 Mock Research 示例。
- `EVAL-405` 补齐类型与异常模型。
- `EVAL-406` 记录两个项目对 Core 的真实反馈和兼容性决策。

验收：

- PhoneMall 专属逻辑只存在于 Adapter/项目 Metric。
- Core 不导入 PhoneMall 代码。
- Mock 示例可离线运行。
- 如果修改 Core，必须记录原因和兼容性影响；不要求为了验收而刻意制造抽象变化。

## Phase 5：高级事实、引用和运行指标

预计：5–8 个工作日。

任务：

- `EVAL-501` 为 PhoneMall 增加结构化 Claim 输出。
- `EVAL-502` 实现 Fact Accuracy 和 Claim Coverage。
- `EVAL-503` 补充 PhoneMall 检索、首 Token 和总延迟。
- `EVAL-504` 区分实际与估算 Token，完善成本估算。
- `EVAL-505` 定义 GroundedSeek 来源等级。
- `EVAL-506` 实现 GroundedSeek Claim Coverage。
- `EVAL-507` 建立真实冲突 Fixture 并实现 Conflict Preservation。
- `EVAL-508` 实验性评估 Citation Entailment。

验收：

- 同一个 Core 同时运行两个项目。
- 项目专属 Metric 不需要修改 Core。
- Citation Entailment 未经人工校准不进入硬门禁。
- 成本缺失时正确显示 `unavailable`，PhoneMall 字符估算显示 `estimated`。

## Phase 6：通用实现迁入 Eval42 仓库与开源准备

预计：4–6 个工作日。

任务：

- `EVAL-601` 将经过双项目验证的通用 Core 迁入现有 Eval42 仓库。
- `EVAL-602` 保留迁移来源、许可证和提交历史说明。
- `EVAL-603` 编写 README。
- `EVAL-604` 编写 Quick Start。
- `EVAL-605` 添加 LICENSE。
- `EVAL-606` 添加 SECURITY 和 CONTRIBUTING。
- `EVAL-607` 配置 Ruff、类型检查、pytest 和 coverage。
- `EVAL-608` 配置多平台 CI。
- `EVAL-609` 清除所有私人路径和秘密。
- `EVAL-610` 固定所有公开 Schema v1 和升级策略。

验收：

- 新环境 15 分钟内运行 Mock 示例。
- 安全扫描无秘密。
- 文档不依赖私有仓库访问。
- Python 3.11、3.12、3.13、3.14 CI 通过。

## Phase 7：v0.1.0 发布

预计：2–4 个工作日。

任务：

- `EVAL-701` 确认 PyPI 名称。
- `EVAL-702` 构建 sdist/wheel。
- `EVAL-703` TestPyPI 安装验证。
- `EVAL-704` 发布 PyPI。
- `EVAL-705` 创建 GitHub Release。
- `EVAL-706` 验证公开 Schema 与 Phase 6 固定版本一致。

验收：

```bash
pipx install eval42
eval42 run examples/mock-shopping/eval.yml
```

能够成功执行。

---

## 25. 版本路线

### v0.1.0

- JSONL 数据集。
- HTTP Adapter。
- Recall@K、MRR、约束、事实、延迟、成本。
- JSON/Markdown 报告。
- 基线比较。
- CI Gate。

### v0.2.0

- 静态 HTML 报告。
- 按 tag 趋势和失败聚类。
- 内容哈希缓存。
- 更灵活的字段映射。
- GroundedSeek 引用指标稳定化。
- 当 ecc-init 或其他真实消费者出现时评估 Command Adapter。

### v0.3.0

- 可选 RAGAS 集成。
- 可校准的 LLM Judge。
- 多次运行方差分析。
- 统计显著性提示。
- GitHub Job Summary 辅助工具。

### v1.0.0 条件

- 至少 3 个真实项目使用。
- Adapter 和 JSON Schema 稳定。
- 升级策略清晰。
- 有外部用户反馈。
- 核心指标有完整定义与测试。
- 已证明能够发现真实质量回归。

---

## 26. README 首屏草稿

```markdown
# Eval42

A lightweight, CI-first evaluation harness for verifiable AI applications.

Eval42 runs versioned test cases against RAG and model-driven systems,
checks deterministic business constraints, compares results with a baseline,
and fails CI when quality regresses.

## Why

Generic AI scores cannot tell a shopping assistant whether it recommended
a nonexistent product, exceeded a hard budget, or used stale inventory.
Eval42 combines retrieval metrics with project-specific checks.

## Quick start

pipx install eval42
eval42 run examples/mock-shopping/eval.yml

## Core features

- JSONL evaluation datasets
- HTTP adapters for synchronous and asynchronous targets
- Recall@K and MRR
- deterministic constraint and fact checks
- latency and cost reporting
- baseline comparison
- CI quality gates
- JSON and Markdown reports
```

---

## 27. 风险与应对

### 风险 1：过度抽象

应对：

- 第一阶段不设计插件市场。
- 第二个项目接入前不冻结 Adapter API。
- 删除没有真实消费者的配置能力。

### 风险 2：测试集标注错误

应对：

- 数据集版本化。
- 每条案例保存标注说明。
- 支持多个正确答案。
- 重要案例进行二次人工审查。

### 风险 3：针对固定测试集过拟合

应对：

- 开发集和最终评测集分离。
- 增加查询改写。
- 保留隐藏或低频运行案例。
- 按能力分类分析，不只看总分。

### 风险 4：真实模型结果波动

应对：

- PR 门禁优先使用确定性 Mock。
- Nightly 执行真实模型。
- 重要指标允许多次运行并报告方差。
- 固定模型版本和 Temperature。

### 风险 5：评测成本失控

应对：

- 默认支持 `generate_answer: false`。
- PR 使用小型数据集。
- 提供最大 Case 数和预算限制。
- Nightly 记录成本。

### 风险 6：敏感数据泄漏

应对：

- 数据集脱敏。
- 报告默认不保存完整回答。
- 自动脱敏 Authorization。
- Gitleaks 和安全审查。

### 风险 7：指标看似精确但实际无意义

应对：

- 报告显示样本数和数据集版本。
- 指标文档说明适用条件。
- 不将 LLM Judge 包装成绝对真值。
- 不只展示单个总分。

### 风险 8：计划与真实项目继续漂移

应对：

- 每个 Phase 开始时重新记录 PhoneMall、GroundedSeek 和 Eval42 revision。
- 接口或 Artifact Schema 变化时先更新 Adapter 契约和本计划。
- 不依据过期代码行号实现功能。

---

## 28. 项目质量要求

### 28.1 代码质量

- Python 类型注解完整。
- 公共 API 有 Docstring。
- 不使用无必要的全局状态。
- 错误类型明确。
- CLI 错误信息可操作。
- 不吞掉 Adapter 异常。

### 28.2 兼容性

首个开源版本：

- Python 3.11、3.12、3.13、3.14。
- Windows、Linux、macOS。
- UTF-8 数据集。
- 中文和英文内容。

### 28.3 发布质量

- `python -m build` 成功。
- wheel 安装测试成功。
- `pipx install` smoke test。
- README 命令在干净环境实际运行。
- `git diff --check`。
- 依赖安全扫描。

---

## 29. 完成定义

一项任务只有满足以下条件才算完成：

- 代码已实现。
- 单元或集成测试已添加。
- 文档和示例已更新。
- 本地验证通过。
- CI 通过。
- 没有暴露秘密或私人路径。
- 行为符合数据协议。
- 对外输出包含可操作错误信息。

只有后续工作依赖的验收门槛满足后才能进入对应实现；数据标注、文档、许可确认和其他无依赖工作可以并行，不采用严格瀑布流程。

---

## 30. 最终验收清单

### 功能

- [ ] 能加载并校验 JSONL 数据集。
- [ ] 能运行 HTTP Adapter。
- [ ] 能计算 Recall@K。
- [ ] 能计算 MRR。
- [ ] 能检查项目业务约束。
- [ ] 能检查结构化事实。
- [ ] 能统计延迟和成本。
- [ ] 能创建和比较基线。
- [ ] 能根据 Gate 返回稳定退出码。
- [ ] 能生成 JSON 和 Markdown 报告。

### PhoneMall

- [ ] 至少 30 条人工审核案例。
- [ ] 包含无结果、下架、无库存和 Prompt 注入案例。
- [ ] 评测端点只读且受保护。
- [ ] 评测不读取聊天历史、不写用户对话、不消耗用户额度。
- [ ] 原始检索结果与可售候选分别记录。
- [ ] Token 统计明确区分 actual、estimated 和 unavailable。
- [ ] CI 能检测故意制造的检索回归。
- [ ] 报告能定位越界商品和错误事实。

### GroundedSeek

- [ ] 已审计现有 50 条研究案例。
- [ ] 至少 15 条已升级为可判定 Gold Set。
- [ ] 支持来源质量。
- [ ] 支持 Evidence Recall。
- [ ] 支持 Citation Validity。
- [ ] 支持 Claim Coverage。
- [ ] 支持冲突保留检查。
- [ ] PR 评测使用冻结搜索、网页和模型 Fixture。

### 工程

- [ ] Core 测试覆盖率达到目标。
- [ ] Windows/Linux/macOS CI 通过。
- [ ] Ruff 和类型检查通过。
- [ ] Mock 示例完全离线运行。
- [ ] 无秘密和个人路径。
- [ ] 完整 License、Security、Contributing。

### 发布

- [ ] TestPyPI 验证。
- [ ] PyPI 或 pipx 安装成功。
- [ ] GitHub Release。
- [ ] Quick Start 在干净环境验证。

---

## 31. 给后续开发窗口的执行提示词

```text
请按照《Eval42 完整开发计划》实施当前阶段。

执行原则：
1. 先确认当前处于哪个 Phase，只实现当前阶段，不提前构建 SaaS、Dashboard 或复杂插件系统。
2. Eval42 仓库负责协议和留痕；Phase 1–2 在 PhoneMall 验证，Phase 3 接入 GroundedSeek，双项目验证后再将通用实现迁入 Eval42。
3. 优先实现确定性指标：Recall@K、MRR、业务约束、Citation Validity 和结构化事实；延迟与成本首版只作辅助指标。
4. LLM Judge 只能作为可选辅助报告，不作为第一版唯一 CI 门禁。
5. 所有测试数据必须脱敏、版本化，并记录数据快照和标注依据。
6. 不在日志、报告和 CI 输出中泄露 Token、Authorization、完整生产 Prompt 或真实用户数据。
7. 每次改动必须附带测试、文档、执行命令和验证结果。
8. 不自动更新基线。基线变化必须生成差异并经过人工审查。
9. 保持 Core 与项目专属规则分离，但不要实现没有真实消费者的 Command Adapter 或插件框架。
10. 完成后报告：实现任务编号、修改文件、测试结果、评测结果、风险和下一阶段建议。
```

---

## 32. 推荐的第一批实际任务

后续窗口首次接手时，按以下顺序开始：

1. `EVAL-001`：以当前 revision 重新确认 PhoneMall 检索、可售过滤、生成、Usage 和 CI 结构。
2. `EVAL-002`：设计脱敏商品事实快照格式。
3. `EVAL-003`：编写 20 条首批查询，不急于达到 40 条。
4. `EVAL-006`：审计 GroundedSeek 现有 50 条数据，选出首批 Gold Set 候选。
5. `EVAL-102`：实现最小数据模型。
6. `EVAL-103`：提取 PhoneMall `AiRetrievalService`。
7. `EVAL-104`：实现只读 `/api/merchant/ai/evaluate`。
8. `EVAL-107`：实现 Recall@5。
9. `EVAL-108`：实现 MRR。
10. `EVAL-109`：实现不存在、下架、无库存、超预算、排除品牌和意外空结果检查。
11. `EVAL-111`：生成第一份 Markdown 报告。
12. 使用报告发现至少一个真实问题后，再继续基线和 CI 门禁。

最重要的第一个里程碑不是“Eval42 仓库创建成功”，而是：

> PhoneMall 的一次真实改动能够通过 Eval42 被证明为进步或回归。
