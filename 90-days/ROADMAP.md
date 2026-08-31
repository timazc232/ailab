# 90 天 AI Agent Engineering 路线

## 路线配置与执行原则

- **状态**：路线已初始化，Day 1 尚未开始。
- **路线定位**：面向 AI Agent Engineer、AI Application Engineer、AI-Native Backend Engineer 与海外 Remote / Contract AI Engineering；以工程实践和 production-oriented Agent systems 为核心，不以 AI research 或 model training 为主线。
- **开始日期**：TBD
- **结束日期**：TBD
- **每周投入**：约 10–12 小时；按有全职工作的节奏设计，每日范围必须现实，不追求每天大量提交代码。复杂模块可跨周，简单模块可组合。
- **已有基础**：假设学习者具备软件/后端、Linux、Docker、数据库、Git 与 API 开发经验；只补充 Agent Engineering 场景需要的细节，不重复教授基础课程。
- **组织方式**：以 **Phase → Week → Module** 为主；Day 仅用于记录实际进度和关键 Checkpoint，不写成每日流水账。
- **学习模式**：`90-days/` 与 `playground/` 默认采用 Learning Mode。理解机制、运行实验和解释结果优先于实现速度。
- **Agent Harness 中立**：Pi 仅作为当前主要 Coding Agent；课程、Artifact、命令、测试和知识状态必须能由其他 Agent Harness 或人类独立接手。
- **技术选择**：关键协议优先使用原生 HTTP；需要 SDK 时优先官方 SDK；其他能力优先标准库，再考虑职责单一的小型依赖。初期不使用 LangChain、LlamaIndex 或类似大型 Agent Framework。
- **语言**：说明以中文为主；技术术语、API、Protocol、类名、函数名、Command、Code 和行业标准词保留英文。
- **实验边界**：先使用 fixture、mock 和本地协议实验；真实外部 API 调用必须另行确认。OpenOps 故障实验必须优先在隔离的 Docker Test Lab 中运行，绝不以宿主机重要服务为实验或故障注入目标。
- **质量原则**：Evaluation 与 Safety 从早期模块开始积累案例，在后续阶段形成正式 harness 和基线；代码生成不等于模块完成。
- **思想地图**：见「Engineering Ideas & Intellectual Map」章节。领域内有影响力的思想只用于产生假设（Authority is input, not evidence），结论一律由本路线自己的实验与 Evaluation 形成。

## 1. 90 天 Objectives

1. 形成竞争 AI Agent Engineer、AI Application Engineer、AI-Native Backend Engineer 与海外 Remote / Contract AI Engineering 工作所需的工程证据和表达能力。
2. 通过 **agent-lab** 从底层逐步掌握 LLM API fundamentals、Messages / Context、Streaming、Structured Output、Tool Calling、Tool Registry / Dispatch、Agent Loop、State / Lifecycle、Retry / Timeout / Error Recovery、Planning、Reflection、Human-in-the-loop、MCP、RAG、Memory、Context Engineering、Tracing / Observability、Evaluation、Safety / Policy、Multi-model / Provider Abstraction、Cost / Latency Engineering 与 Production-oriented Agent Architecture。
3. 能说明每层为什么存在、解决什么问题、协议与状态边界、主要 trade-offs、失败模式、可观察信号和验证方法，而不只会调用某个 AI Framework。
4. 开发独立、开源就绪的 AI Ops / SRE Agent **OpenOps**，形成可追踪的 Investigation Loop：问题 → 假设 → 工具选择 → 证据收集 → 判断更新 → Root Cause → Recommendation。
5. 实现小型 **Memory Hub** MVP，验证 Short-term Memory、Long-term Memory、Retrieval、Summarization、Forgetting、Memory Quality 与 Context Assembly 的真实工程权衡。
6. 从早期 agent-lab 起逐步建立 Evaluation Dataset；Day 90 至少保留 50 个有意义、可复现的 Evaluation Cases，并报告质量、安全、Model Calls、Latency 与 Cost。
7. 形成可展示的工程成果：可运行实验、测试、评测报告、失败案例、架构说明、8–12 篇高质量 Engineering Notes、2–3 个英文 Demo、英文 GitHub README 与英文 Resume，并能用英文解释重要 Agent Architecture 和 Engineering Trade-offs。

## 2. Capability Map

| 能力层 | 核心机制 | 主要解决的问题 | 预期证据 |
|---|---|---|---|
| Model I/O | LLM API fundamentals、Messages / Context、Streaming、Structured Output、Multi-model / Provider Abstraction | 稳定调用不同 provider，并明确输入、输出、增量响应和数据契约 | 原生 HTTP baseline、官方 SDK 对照、协议记录、错误样例、测试 |
| Tool System | Tool Calling、Tool Registry / Dispatch | 将模型提出的动作与可信执行、schema、权限和错误边界分离 | dispatch 测试、工具选择案例、权限失败记录 |
| Agent Runtime | Agent Loop、State / Lifecycle | 管理多步决策、状态转换、终止、中断、恢复和资源生命周期 | 状态图、终止条件测试、恢复轨迹 |
| Agent Control | Planning、Reflection、Human-in-the-loop | 控制何时规划、何时复盘、何时请求人工批准，避免无界循环和自动化越权 | 策略对照、审批状态、失败与成本比较 |
| Reliability | Retry、Timeout、Error Recovery、幂等性 | 区分瞬时与永久失败，控制 deadline、重复副作用和降级恢复 | 故障注入、恢复矩阵、幂等性测试 |
| Observability & Economics | Tracing / Observability、Model Calls、Latency、Cost | 重建一次运行，并量化质量、调用、延迟和费用 trade-offs | trace、指标报告、预算与性能 baseline |
| Interoperability | MCP | 以标准 Protocol 发现和调用 capabilities，并理解 transport、权限与信任边界 | 最小 client/server、兼容性与直接集成对照 |
| Knowledge | RAG、Context Engineering、Context Assembly | 在有限 context 中选择可引用、相关、可控且不过载的信息 | retrieval baseline、assembly trace、引用与噪声实验 |
| Memory | Short-term / Long-term Memory、Retrieval、Summarization、Forgetting、Memory Quality | 跨步骤或跨会话保存有价值状态，同时控制陈旧、污染、冲突和膨胀 | Memory Hub、质量评测、冲突与遗忘案例 |
| Quality | Evaluation | 用可重复 Dataset、rubric 与 baseline 判断任务质量和失败模式 | Eval harness、versioned Dataset、baseline 报告 |
| Safety | Safety / Policy、权限、注入防护、数据边界 | 防止不可信输入驱动危险工具、越权动作或敏感信息泄漏 | Safety cases、Unsafe Action Rate、拒绝与审批证据 |
| Production Architecture | 边界分层、配置、持久化、异步/并发、backpressure、恢复、部署边界 | 将透明的机制组合成可维护、可观察、可扩展且 Agent Harness neutral 的系统 | 架构图、failure/recovery matrix、关键 trade-off 记录 |
| Applied Engineering | OpenOps Investigation Loop | 将机制组合成有证据约束的 AI Ops / SRE 调查流程 | Docker Test Lab、RCA 案例、Recommendation 与回滚说明 |
| Technical Communication | Notes、English Demo、GitHub README、Resume | 清楚解释架构、证据、限制与 Engineering Trade-offs | 中英文作品材料、异步书面表达和演示 |

### 三个工程成果

| Stage | Artifact | 作用与范围 | 阶段性完成证据 |
|---|---|---|---|
| **Stage 1 — agent-lab** | 底层 Agent mechanism 实验系列 | 先建立无大型框架 baseline；Day 30 完成 runtime 核心，后续继续加入 MCP、RAG、Memory、Evaluation 与 Safety 对照 | 可运行实验、测试、trace、Evaluation Cases、机制与 trade-off 说明 |
| **Stage 2 — OpenOps** | 独立、开源就绪的 AI Ops / SRE Agent | 在隔离 Docker Test Lab 中验证完整 Investigation Loop，不操作宿主机重要基础设施 | fixture incidents、evidence traces、RCA、Recommendations、Safety Policy、Evaluation |
| **Stage 3 — Memory Hub** | 小型 Agent Memory / Context Hub MVP | 验证 write、retrieve、summarize、forget 与 Context Assembly，不把 Memory 简化为 Vector Database 接入 | 独立接口、对照实验、Memory Quality 报告、已知限制 |

## 3. 学习闭环、时间预算与 Module Contract

核心模块默认遵循：

**概念 → 最小实验 → 自己实现 → 实际运行 → 观察结果 → 解释原因 → Evaluation → 改进**

每个重要 Module 必须明确：**学什么、为什么重要、要实现什么、做什么实验、如何验证、Definition of Done、Artifact**。下方模块表将这些字段成对合并以控制篇幅，但每一项都必须有实际证据后才能标记完成。

建议每周 10–12 小时分配：

- 6–7 小时：机制理解、最小实现和调试。
- 2–3 小时：实验、Evaluation、失败分析。
- 1 小时左右：知识提炼、进度与决策记录。
- 不超过 1 小时：英文表达或 Portfolio 整理；Phase 4 可适度提高，但工程能力始终优先。

---

## Engineering Ideas & Intellectual Map

本章不新增学习任务，不改变四阶段结构与 Module Contract，只做一件事：把 AI Engineering / Agent Engineering 领域有影响力的公开思想映射到现有模块，并转换为可验证的假设。

**核心原则：Authority is input, not evidence.**
专家与机构观点只用于产生假设和 Engineering Question；本路线不因某人推荐就默认某机制有效、某模式必要或某 Framework 应引入。每个有争议的机制都走「思想 → 工程问题 → 我们的假设 → 最小实验 → Evaluation → 自己的结论」链路。例如：Reflection 不因 Andrew Ng 推荐而默认进入路线，必须在 M1.8 以相同 Dataset、模型、工具与预算做 baseline vs reflection 对照（task success、model calls、latency、token cost、failure recovery）；考察 LangChain 生态暴露的生产问题不等于采用 LangChain；OpenAI 实践只是问题来源，路线保持 provider-neutral。

| 思想来源 | 核心思想（公开主张） | 对应模块 | 我们要验证的问题（Engineering Questions） |
|---|---|---|---|
| Andrew Ng | Agentic workflow、Reflection、Tool Use、Planning、Multi-agent patterns、迭代式 AI 开发（DeepLearning.AI 及公开演讲） | M1.8 / M2.5 / Phase 3 | Reflection 在净收益上是否成立？Planning 与 Multi-agent patterns 何时值得引入？OpenOps Investigation Loop 本质上是否是带证据约束的迭代 agentic workflow？ |
| Andrej Karpathy | LLM as a new computing primitive；保持系统可理解；对复杂 abstraction/Framework 谨慎；Software 2.0 / LLM OS 视角 | M1.1 / M1.2 / Phase 1 整体 | Framework abstraction 在什么系统复杂度下才开始产生正收益？自底向上 baseline 能否精确暴露协议与状态边界？ |
| Simon Willison | Tool Use 边界、Prompt Injection、untrusted input、security boundaries（simonwillison.net） | M1.5 / M2.1 / M2.3 / M3.4 | 工具执行、证据采集与 Policy 如何防御模型输出、日志、observation 这类不可信输入？ |
| Chip Huyen | AI Engineering、evaluation-first、latency/cost/observability 与系统 trade-offs（《AI Engineering》，huyenchip.com） | M3.2 / M3.3 / M3.5 | Agent Evaluation 应测模型还是整个 System？Model Calls / Latency / Cost 如何成为评测一等公民？ |
| Harrison Chase / LangChain 生态 | State、checkpoint、durable execution、human-in-the-loop、agent lifecycle、observability 暴露的生产 Agent 问题（blog.langchain.dev；不学习其 API） | M1.7 / M1.8 / M3.5 | durable execution 与 checkpoint 在什么任务规模下才必要？HITL 审批如何嵌入状态机与恢复轨迹？ |
| Anthropic | Workflows vs Agents、simple composable patterns、tool design、context management、避免不必要的复杂度（《Building Effective Agents》，2024） | M1.5 / M1.7 / M4.2 | 哪些任务根本不应该使用 Agent，普通 Workflow 更好？好的工具接口长什么样？Context Assembly 何时开始过度设计？ |
| OpenAI | Agent loop、tool use、evals、tracing、safety、context engineering、生产 Agent 设计（《A Practical Guide to Building Agents》，2025） | M3.2 / M3.3 / M3.4 | 其指南推荐的评测、tracing 与安全边界与我们的可测指标是否一致？能否泛化为我们自己的 policy 与 eval 实验？ |

> 以上为公开思想的提炼总结，不整段复制原文，也不代表认可其产品或 Framework；假设生成服从各 Module Contract，结论以本路线自己的实验与 Evaluation 结果为准。

---

## Phase 1 — Agent Foundations + Core Mechanisms（Days 1–30）

### Phase Goal

以 **agent-lab** 为载体，不依赖大型 Agent Framework，建立从模型 I/O 到可观察 Agent Runtime 的最小透明链路。Phase 1 先完成到 basic Tracing 的 baseline；MCP、RAG、Memory、Evaluation 与 Safety 在后续 Phase 继续扩展。所有实验先走本地 mock；是否调用真实模型在对应 Module 单独确认。

### Week 1 — LLM API Fundamentals、LLM Client 与 Messages / Context

**Weekly Milestone**：能够通过原生 HTTP 与本地 mock 完成一次模型请求，显式构造 messages，并区分 transport、protocol 与 model-level error。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M1.1 LLM API Fundamentals / LLM Client** | 学习 HTTP request/response、认证配置、payload、status code 和错误分类；<br>**思想来源**：Andrej Karpathy——LLM fundamentals 与保持系统可理解；**Engineering Question**：不依赖官方 SDK 抽象，能否精确区分 transport、protocol 与 model-level error？它是隔离 provider 变化与上层逻辑的边界。 | 计划实现最小同步 HTTP client；用本地 mock 覆盖 200、畸形 JSON、401、429、500 和 timeout。 | 确定性测试通过；日志不泄漏凭据；学习者能解释网络错误、协议错误与模型错误的区别。 | 一个独立实验、请求/响应样例、错误观察表和测试。 |
| **M1.2 Messages / Context** | 学习 role、顺序、上下文预算、截断与显式状态；避免把 context 误认为 memory。<br>**思想来源**：Andrej Karpathy / Anthropic——context 是显式、有界的输入；**Engineering Question**：显式构造与截断策略是否足以支撑多步 Agent Runtime，而不把 context 误当 memory？ | 计划实现 messages 数据结构与序列化；实验消息重排、空内容、非法 role、超预算输入。 | 序列化可重复；边界行为有测试；学习者能解释 message history、context window 与 persistent memory 的区别。 | Messages contract、fixture、边界测试和机制说明。 |

### Week 2 — Streaming 与 Structured Output

**Weekly Milestone**：能够增量消费响应，并将“自然语言看似正确”与“满足机器可验证契约”区分开。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M1.3 Streaming** | 学习 chunk、delta、finish signal、增量解码、取消和中断；Streaming 改变的是传输与用户体验，不自动提高答案质量。 | 计划实现最小 stream parser；实验任意分块、Unicode 跨 chunk、畸形事件、中途断开和取消。 | 重组结果与非流式 fixture 一致；中断可观察且不会静默产出完整结果；能解释 backpressure 与取消边界。 | Streaming parser 实验、chunk fixtures、失败记录。 |
| **M1.4 Structured Output** | 学习 JSON/schema contract、校验、拒绝与修复边界；prompt 要求不是可靠的数据契约。 | 计划实现最小结构化输出解析与校验；实验缺字段、错类型、额外字段、无效 JSON 和一次受控重试。 | 无效输出不得进入下游；错误分类与重试条件明确；能解释 schema validation 与 semantic validation 的差异。 | Schema、有效/无效 fixtures、校验测试与失败分类。 |

### Week 3 — Tool Calling 与 Tool Registry

**Weekly Milestone**：模型只能提出 tool call，由本地可信代码验证、授权并执行；工具发现与 dispatch 不依赖硬编码分支堆积。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M1.5 Tool Calling** | 学习 tool schema、call arguments、tool result 和模型/执行器责任边界；模型提出动作不等于动作已执行。<br>**思想来源**：Simon Willison / Anthropic——tool use 边界与 tool design；**Engineering Question**：把模型提出的动作视为 untrusted input，执行边界应防御哪些无效、危险与注入动作？ | 计划用 scripted model fixture 产生合法、未知、参数错误和危险 tool call；工具先采用无副作用函数。 | 非法调用被拒绝且可观察；工具结果能回填下一轮；能够解释 tool selection 与 tool execution 的不同失败模式。 | Tool-calling protocol note、fixtures、选择与参数测试。 |
| **M1.6 Tool Registry / Dispatch** | 学习注册、schema 暴露、dispatch、权限 metadata 和命名冲突；Registry 为扩展与治理提供单一边界。 | 计划实现最小 registry；实验重复注册、未知工具、schema 不匹配、未授权工具和执行异常。 | dispatch 确定且有测试；未知或未授权工具不执行；能解释 registry 与普通函数映射的额外价值。 | Registry API、测试矩阵、tool inventory。 |

### Week 4 — Agent Loop、State / Lifecycle、Control 与 Reliability

**Weekly Milestone**：形成可终止、可中断、可恢复、可观察和可故障注入的最小 Agent Runtime，并建立首批 Evaluation Cases。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M1.7 Agent Loop + State / Lifecycle** | 学习 request → decision → tool → observation → next request、状态转换、资源生命周期和终止条件；防止无限循环、隐式状态漂移和不可恢复执行。<br>**思想来源**：Anthropic——workflows vs agents；LangChain 生态生产问题——state 与 checkpoint；**Engineering Question**：哪些任务根本不应该使用 Agent（固定 Workflow 更简单可靠）？为支持中断/恢复，state checkpoint 最小需要什么？ | 计划实现 scripted loop 与显式 state；实验直接回答、单工具、多工具、重复调用、max steps、取消、中断和恢复。 | 每条路径都有终止原因；state 可序列化/检查；资源能清理；能够画出状态转换并解释每次 context 更新。 | 最小 loop、state/lifecycle model、轨迹 fixtures、状态图。 |
| **M1.8 Planning + Reflection + Human-in-the-loop** | 学习 reactive 与 plan-first 策略、受限 Reflection 和人工审批点；这些机制可能提升复杂任务，也会增加调用、延迟和循环风险。<br>**思想来源**：Andrew Ng——agentic workflow、Reflection、Planning、multi-agent patterns；LangGraph 生产实践——human-in-the-loop；**Engineering Question**：在相同 Dataset/模型/工具/预算下，Reflection 是否提高任务成功率？增加的 Model Calls/Latency/Cost 是否值得？Multi-agent patterns 在此阶段是否必要？ | 在同一 scripted task 上比较 reactive baseline、有限 plan、失败后一次 Reflection，以及副作用前 human approval。 | 策略使用条件明确；Reflection 有次数上限；审批可暂停/恢复；能够解释质量收益是否值得额外 Model Calls、Latency 与 Cost。 | Control-strategy comparison、approval state、失败轨迹和结论。 |
| **M1.9 Retry / Timeout / Error Recovery + Basic Tracing** | 学习 transient/permanent error、deadline、backoff、降级、幂等性、correlation id 与 span；可靠性不能靠无限重试。 | 计划注入 429、畸形输出、连接超时、工具异常、工具挂起和重复副作用风险；为 model/tool/loop step 记录基础 trace。 | 重试有上限且只覆盖允许错误；timeout 能终止；永久失败有明确恢复/降级路径；trace 可重建一次运行；累计至少 15 个有意义 Evaluation Cases。 | Reliability policy、error-recovery matrix、trace schema、故障实验、agent-lab Phase 1 baseline。 |

### Day 30 Checkpoint

详见“Checkpoint”章节。未完成运行、Evaluation 和机制解释时，Phase 1 不得标记完成。

---

## Phase 2 — OpenOps Engineering Project（Days 31–60）

### Phase Goal

开发独立、开源就绪的 AI Ops / SRE Agent **OpenOps**。初期默认只执行低风险、只读诊断；所有故障均在隔离的 Docker Test Lab 中构造，不接触 `CLIProxyAPI`、`Xray`、`Caddy` 或其他宿主机重要服务。

### Week 5 — 用户问题、Investigation Contract 与 Docker Test Lab

**Weekly Milestone**：明确 OpenOps 的用户问题、非目标、证据模型、安全策略和隔离实验环境。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M2.1 Investigation Contract + Safety Policy** | 学习问题、假设、证据、判断、Root Cause 与 Recommendation 的数据边界；避免先下结论再寻找证据。 | 计划定义 investigation state、证据来源、允许/禁止动作、只读默认策略和 human approval 点；桌面演练正常与危险请求。 | 每个结论可回溯到证据；危险动作默认拒绝；能解释何时应停止、升级给人或声明证据不足。 | OpenOps scope、state contract、Safety Policy、threat assumptions。 |
| **M2.2 Docker Test Lab** | 学习可重复故障环境、隔离和可回滚注入；重要宿主机服务不能作为学习实验对象。 | 计划构造仅含测试容器和合成数据的 lab；准备已知故障、reset 流程和资源限制。 | 故障可重复创建和清理；不修改宿主机关键服务；无敏感挂载或真实凭据；每个场景有 ground truth。 | Test Lab 设计、场景清单、启动/重置/验证说明。 |

### Week 6 — Linux、Docker 与 Logs Diagnostics

**Weekly Milestone**：OpenOps 能从受控工具收集标准化证据，而不是直接输出未经验证的猜测。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M2.3 Linux / Docker / Logs Evidence Collection** | 学习 process、CPU、memory、disk、network、container state 与日志时间线；统一 evidence contract 才能比较和审计。<br>**思想来源**：Simon Willison——日志与 observation 属于 untrusted input；**Engineering Question**：证据应如何隔离、结构化与引用，防止注入内容驱动动作或被当作结论？ | 计划实现只读诊断工具契约；在 lab 中构造资源压力、进程退出、容器重启和错误日志场景。 | 工具输出结构化、带时间与来源；超时/权限失败可观察；证据不等于结论；相关工具测试通过。 | Diagnostic tools、evidence schema、fixture incidents、工具说明。 |

### Week 7 — Nginx、MySQL / PostgreSQL 与 Hypothesis Update

**Weekly Milestone**：覆盖典型服务故障，并让 Agent 根据新证据提高、降低或淘汰假设。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M2.4 Nginx + MySQL / PostgreSQL Diagnostics** | 学习配置、端口、上游、连接、锁、慢查询、容量和健康信号；服务诊断需要领域证据而非通用文本。 | 计划在 lab 容器中构造配置错误、上游不可达、连接耗尽、锁等待或磁盘压力；工具保持只读。 | 每个场景有 ground truth、必要证据和误导证据；诊断不访问宿主机真实服务；结果可重复。 | Service-specific tools、incident fixtures、evidence checklist。 |
| **M2.5 Hypothesis Generation + Planning / Reflection + Root Cause Analysis** | 学习候选假设、信息增益、有限计划、证据支持/反驳、受限 Reflection 和不确定性；RCA 必须区分症状、相关性与根因。 | 计划实现 investigation loop：生成有限假设 → 选择下一工具 → 收集证据 → 更新判断 → 必要时一次 Reflection → 终止。 | 轨迹显示假设如何变化；规划与 Reflection 有边界；无证据时不强行给 Root Cause；已知故障上的 Root Cause Accuracy 可计算。 | Investigation traces、hypothesis state、planning/reflection comparison、RCA rubric、失败案例。 |

### Week 8 — Recommendations、Safety 与 OpenOps Baseline

**Weekly Milestone**：完成端到端 Investigation Loop，并为 OpenOps 建立首个可比较质量与安全基线。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M2.6 Recommendation + OpenOps Evaluation** | 学习建议的证据引用、风险、验证步骤、回滚和权限边界；正确诊断不代表可以安全执行修复。 | 计划输出分级 Recommendations，不自动执行高风险动作；回放 Linux、Docker、Logs、Nginx、MySQL/PostgreSQL 场景及 unsafe request。 | 测量 Task Success、Tool Selection Accuracy、Root Cause Accuracy、Evidence Quality、Unsafe Action Rate、Model Calls、Latency 与 Cost；累计至少 30 个有意义案例。 | `projects/openops/` 计划基线、评测报告、Safety Policy、开源就绪 README 草案。 |

### Day 60 Checkpoint

详见“Checkpoint”章节。发布到外部仓库或服务不在默认范围内，必须另行明确授权。

---

## Phase 3 — Evaluation + Safety + Observability + Multi-model Engineering（Days 61–75）

### Phase Goal

把早期零散测试升级为可重复 Evaluation 体系；补齐 MCP、Tracing / Observability、Multi-model / Provider Abstraction、Cost / Latency Engineering、系统化 Safety Evaluation 与 Production-oriented Agent Architecture。

### Week 9 — MCP 与 Evaluation Harness

**Weekly Milestone**：完成直接 Tool Registry 与 MCP 集成的最小对照，并让已有案例可批量、可重复运行。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M3.1 MCP** | 学习 client/server、capability discovery、tools/resources/prompts、transport 与 trust boundary；标准协议带来互操作，也增加权限和故障面。 | 计划实现最小本地 MCP server/client，只暴露低风险 fixture capability；与直接 Tool Registry 做同条件对照。 | capability 可发现；协议错误、超时和拒绝可观察；能解释 MCP 何时有价值、何时直接集成更简单。 | MCP 实验、兼容性记录、直接集成对照。 |
| **M3.2 Evaluation Harness + Dataset** | 学习 case schema、ground truth、rubric、deterministic check 与人工校准；没有稳定 runner 就无法做回归比较。<br>**思想来源**：Chip Huyen——系统级 AI Evaluation；OpenAI——evals 实践；**Engineering Question**：Agent Evaluation 应测模型，还是测 tools + state + policy 组成的整个 System？ | 计划统一 Phase 1–2 cases，建立离线 runner、结果版本和 failure taxonomy；LLM-as-judge 只在有人工校准时使用。 | 同一配置可重复运行；失败不会静默丢失；指标定义明确；不以挑选样例宣称提升。 | Eval harness、versioned dataset、baseline、failure taxonomy。 |

### Week 10 — Observability、Provider Abstraction、Safety 与 Production Architecture

**Weekly Milestone**：能够在同一条件下比较不同模型/配置的质量、Model Calls、Latency 与 Cost，用攻击案例验证 Safety 边界，并说明从实验 runtime 走向 production-oriented architecture 仍需哪些系统边界。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M3.3 Tracing / Observability + Multi-model / Provider Abstraction + Cost / Latency Engineering** | 学习统一 provider boundary、trace、token/cost、latency、配置版本和可比实验条件；模型切换不能掩盖 Protocol 差异。<br>**思想来源**：Chip Huyen——latency/cost/observability 的系统 trade-offs；**Engineering Question**：在相同条件下，不同模型配置在质量、Model Calls、Latency 与 Cost 上的真实差异有多大？ | 计划扩展 trace 并建立至少两种模型配置的可替换适配层；未获真实调用授权时使用录制 fixture 或 mock。 | 每次运行可关联 model/tool/state；比较条件一致；报告质量、Model Calls、Latency 与 Cost，不宣称未经测量的优势。 | Provider comparison、trace report、配置、性能与成本 baseline。 |
| **M3.4 Safety / Policy Evaluation** | 学习 prompt injection、tool misuse、secret leakage、privilege escalation、unsafe recommendation 和审批边界；Safety 必须可测试。 | 计划加入恶意日志、冲突指令、敏感字段和高风险操作请求；验证 Policy、拒绝、降级和 Human-in-the-loop approval。 | Unsafe Action Rate 可计算；敏感信息不进入结果；高风险动作默认不执行；累计至少 40 个有意义案例。 | Safety suite、threat model 更新、Day 75 quality/safety report。 |
| **M3.5 Production-oriented Agent Architecture** | 学习边界分层、持久化、异步/并发、backpressure、配置与 secret、权限、恢复和部署边界；实验成功不等于可生产运行。<br>**思想来源**：Harrison Chase / LangGraph——durable execution、checkpoint、agent lifecycle；Chip Huyen——production AI trade-offs；**Engineering Question**：durable execution 与 checkpoint 在什么状态与并发规模下才开始产生正收益？ | 计划形成 reference architecture，并对 restart/resume、重复消息、并发 tool call、部分失败和配置切换做最小 failure/recovery walkthrough。 | 架构不依赖 Pi；状态、工具、模型、Policy 与 observability 边界明确；失败恢复路径和已知限制可解释。 | Architecture diagram、failure/recovery matrix、trade-off note 与 ADR candidates。 |

---

## Phase 4 — Memory Hub + Portfolio + Technical Writing + Interview / Remote Preparation（Days 76–90）

### Phase Goal

先建立 RAG 与 Context Engineering baseline，再实现范围受控的 Memory Hub MVP；完成跨阶段 Evaluation 和已有工程证据的 Portfolio 包装。Technical Writing、Interview 与 Remote Preparation 服务于工程成果，不挤占核心实现与验证。

### Week 11 — RAG 与 Context Engineering

**Weekly Milestone**：能够区分 retrieval、Context Assembly 和 persistent Memory，并用 baseline 判断复杂检索技术是否真的有收益。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M4.1 RAG Baseline** | 学习 ingestion、chunking、retrieval、reranking、citation 与 freshness；RAG 解决外部知识注入，不自动形成长期记忆。 | 计划先实现简单 lexical baseline，再在有证据时比较 embedding/vector 方案；实验 chunk、top-k、噪声和过期资料。 | 使用固定问题集测 retrieval/task quality；回答可追溯来源；能解释 retrieval failure 与 generation failure。 | RAG experiment、Dataset、baseline report、引用失败案例。 |
| **M4.2 Context Engineering + Context Assembly** | 学习预算、优先级、来源、去重、冲突、provenance 和 instruction/data boundary；检索到内容不等于应全部放入 prompt。<br>**思想来源**：Anthropic——context engineering 与 simple composable patterns；**Engineering Question**：依据什么证据标准决定检索内容的丢弃、压缩或全量组装？ | 计划实现显式 Context Assembly Policy；实验相关/无关/冲突/恶意片段、预算不足和不同信息排序。 | assembled context 可检查；来源、选择和截断原因明确；能解释 Context Engineering 的质量、Latency 与 Cost trade-offs。 | Context Policy、assembly traces、噪声与冲突实验。 |

### Week 12 + Final Window — Memory Hub MVP、综合 Evaluation 与 Portfolio

**Weekly Milestone**：在约 8 天的 final window 内完成范围受控的 Memory Hub MVP 和证据汇总；Portfolio 主要整理前期已完成工作，不临时制造大量内容。

| Module | 学什么 / 为什么重要 | 要实现什么 / 做什么实验 | 如何验证 / Definition of Done | Artifact |
|---|---|---|---|---|
| **M4.3 Short-term / Long-term Memory + Retrieval** | 学习 working、episodic、semantic memory、write criteria 和 retrieval boundary；不同 Memory 类型服务不同时间尺度。 | 计划实现最小 memory record、写入策略与 retrieval 接口；实验跨步骤状态、跨会话事实、重复和冲突 Memory。 | 写入理由和来源可追踪；错误 Memory 可更正；能解释 Memory、Context 与 RAG 的边界。 | Memory model、storage/retrieval experiment、冲突案例。 |
| **M4.4 Summarization + Forgetting + Memory Quality + Memory Hub MVP** | 学习压缩损失、陈旧、污染、衰减、去重、删除、数据生命周期和独立服务边界；无限累积会降低质量并增加成本。 | 计划组合 write/retrieve/summarize/forget/Context Assembly；比较原文、summary、过期和删除策略，并注入陈旧、矛盾、低价值与恶意 Memory。 | 接口可独立测试；有无 Memory 的条件可比较；遗忘可解释且可审计；累计至少 50 个有意义 Evaluation Cases；记录已知限制。 | `projects/memory-hub/` 计划 MVP、Memory Quality report、architecture note、失败与恢复记录。 |
| **M4.5 Portfolio + Technical Writing + Interview / Remote Preparation** | 学习用证据解释 Architecture 与 Trade-offs，并用清晰异步书面表达支持海外 Remote / Contract 协作；内容创作不能替代工程。 | 计划整理既有实验、失败、指标、diagram、英文 Demo、GitHub README、Resume、architecture walkthrough 和 interview stories。 | 8–12 篇高质量 Notes、2–3 个英文 Demo、英文 GitHub README、英文 Resume；能用英文解释重要 Agent Architecture 与 Engineering Trade-offs。 | Portfolio index、Demo scripts、English README、Resume、interview/remote communication pack、90-day retrospective。 |

---

## 4. Engineering Deliverables

| 时间点 | Planned Deliverable | 最低证据 |
|---|---|---|
| Day 30 | **agent-lab runtime baseline**：从 LLM Client 到 basic Tracing，并包含 State / Lifecycle、Planning、Reflection 与 Human-in-the-loop 的最小对照 | 可运行实验、测试、trace、至少 15 个 Evaluation Cases、机制说明 |
| Day 60 | **OpenOps baseline**：隔离 Docker Test Lab 中的端到端 Investigation Loop | 多类故障 fixture、Evidence/RCA/Recommendation 轨迹、Safety Policy、至少 30 个累计案例 |
| Day 75 | **agent-lab advanced baseline**：MCP、Evaluation、Observability、Provider Abstraction、Safety 与 Production Architecture | 可重复 eval harness、failure taxonomy、trace/Cost 报告、architecture note、至少 40 个累计案例 |
| Day 90 | **Memory Hub MVP + Portfolio-ready artifacts** | RAG/Context/Memory 对照、至少 50 个累计案例、作品文档、英文材料与 remote/interview pack |

## 5. Evaluation Milestones

> 数量是最低路线目标，不是打卡指标。只有覆盖真实能力、失败模式或安全边界且可重复的 case 才计入；不得为了凑数复制低价值样例。

| Milestone | Dataset 目标 | 重点指标 |
|---|---:|---|
| Week 1 | 建立 case schema，并保留首批 3–5 个协议/错误案例 | request success、错误分类、可重复性 |
| Day 30 | ≥15 cases | Task Success、Structured Output validity、Tool Selection Accuracy、终止正确性、Model Calls、Latency |
| Day 60 | ≥30 cases | Task Success、Tool Selection Accuracy、Root Cause Accuracy、Evidence Quality、Unsafe Action Rate、Model Calls、Latency |
| Day 75 | ≥40 cases | 回归率、跨模型差异、trace 完整性、Cost、安全攻击覆盖 |
| Day 90 | ≥50 cases | 全链路质量、安全、RAG/Memory 影响、调用次数、Latency、Cost 与失败分类 |

核心指标定义必须版本化：

- **Task Success**：任务是否在约束内完成，而非文本是否流畅。
- **Tool Selection Accuracy**：选择了必要工具，并避免无关或禁止工具。
- **Root Cause Accuracy**：结论是否匹配实验 ground truth，并区分症状与根因。
- **Evidence Quality**：证据是否相关、充分、带来源且支持/反驳假设。
- **Unsafe Action Rate**：高风险、越权或被策略禁止的动作被执行的比例。
- **Model Calls / Latency / Cost**：在相同数据、配置和预算下记录，不混用不可比结果。

## 6. Portfolio Milestones

| 时间点 | Planned Milestone | 时间控制 |
|---|---|---|
| Day 30 | 2–3 篇 Core Mechanism Engineering Notes；一份可讲解的 Agent Loop diagram | 只整理已验证实验，不追求发布频率 |
| Day 60 | 累计 5–7 篇 Notes；OpenOps 英文 README 草案；第 1 个英文 Demo | 每周技术表达通常不超过 1 小时 |
| Day 75 | 累计 7–9 篇 Notes；Evaluation/Safety 报告；第 2 个英文 Demo | 以指标与失败案例为核心 |
| Day 90 | 8–12 篇 Notes；2–3 个英文 Demo；英文 GitHub README、英文 Resume、架构讲解与 remote/interview communication pack | 最终整理不得挤占核心实现和验证 |

## 7. Checkpoints

### Day 30 Checkpoint — Core Mechanisms

通过条件：

- **agent-lab** 的原生 HTTP baseline 已覆盖 LLM Client、Messages / Context、Streaming、Structured Output、Tool Calling、Tool Registry / Dispatch、Agent Loop、State / Lifecycle、Planning、Reflection、Human-in-the-loop、Retry / Timeout / Error Recovery 与 basic Tracing。
- 至少 15 个有意义 Evaluation Cases 可重复运行，并保留失败样例。
- 学习者能够说明每层为什么存在、输入输出、状态边界、主要失败模式和可观察信号。
- 没有用大型 Agent Framework 隐藏核心机制。
- 若代码已生成但没有运行、Evaluation 或机制解释，则 Checkpoint 不通过。

### Day 60 Checkpoint — OpenOps

通过条件：

- OpenOps 在隔离 Docker Test Lab 中完成问题 → 假设 → 工具 → 证据 → 判断更新 → Root Cause → Recommendation 的端到端闭环。
- 覆盖 Linux、Docker、Logs、Nginx、MySQL / PostgreSQL 的代表性 fixture；不要求每类都做大而全功能。
- Root Cause 与 Recommendation 可追溯到证据；证据不足时能够停止或升级给人。
- Safety Policy 生效，高风险动作默认不执行；宿主机重要服务从未作为故障注入目标。
- 累计至少 30 个有意义 cases，并报告核心质量、安全与运行指标。

### Day 90 Checkpoint — Integrated Engineering & Portfolio

通过条件：

- Evaluation Dataset 至少包含 50 个有意义 cases，能够重复运行并保留配置、结果和失败分类。
- agent-lab 已逐步覆盖 MCP、RAG、Memory、Evaluation 与 Safety，并记录直接实现、Provider Abstraction、Cost / Latency 和 Production Architecture 的 trade-offs。
- OpenOps 有可运行、可测试、可演示的版本和已知限制；未经授权不自动发布或部署。
- Memory Hub MVP 能演示 write、retrieve、summarize、forget 与 Context Assembly，并有 baseline 对照。
- 能解释 RAG、Context 与 Memory 的边界，以及 storage/retrieval 技术的真实 trade-offs；运行、测试和知识状态不依赖 Pi。
- 完成 8–12 篇 Notes、2–3 个英文 Demo、英文 GitHub README 与英文 Resume，并能用英文说明重要 Agent Architecture 与 Engineering Trade-offs。
- `PROGRESS.md` 中的完成状态都有验证证据；未验证内容明确标为待完成或待确认。

## 8. Day 1 Planned Module

Day 1 只启动 **M1.1 LLM API Fundamentals / LLM Client** 的第一个最小闭环，不同时铺开后续层：

1. 解释模型 API 的 HTTP request/response 边界、配置、认证、status code 和三类错误。
2. 定义假设：一个不依赖官方 SDK 的最小 client 可以通过本地 mock 稳定区分成功、畸形响应、限流、服务错误和 timeout。
3. 写清成功指标、fixtures、观察字段和安全边界；默认不调用真实外部 API。
4. 在用户确认语言与协议后，再创建单一实验并实现最小同步请求。
5. 实际运行 200、畸形 JSON、401/429/500、timeout 场景，记录观察和失败。
6. 建立首批 Evaluation Cases，并解释结果与下一次改进。

**Day 1 Definition of Done**：实验真实运行；验证证据已记录；学习者能解释 transport、protocol 与 model-level error；`PROGRESS.md` 更新为实际结果。仅生成代码不算完成。

## 9. 启动前与后续待确认问题

### Day 1 前需要确认

- 实现语言与版本：建议 Python 3，但尚未由用户确认。
- 首个协议 baseline：是否采用 OpenAI-compatible HTTP schema。
- 首阶段是否保持纯本地 mock；任何真实 provider、模型和费用预算需另行授权。
- 90 天正式开始日期，以便计算 Day / Week 和复盘节奏。

### 可在对应阶段前确认

- OpenOps 的首批用户、重点环境、支持边界、开源许可证与是否单独发布仓库。
- Multi-model Evaluation 需要比较的 provider/model 与最大费用预算。
- Memory Hub 的持久化 baseline，以及是否需要与 OpenOps 做可选集成。
- 四类目标岗位的优先顺序，以及英文 README、Resume 与 Demo 的主要受众。
- Days 61–75 与 Days 76–90 均只有约 15 天；当前默认以“最小可验证 baseline / MVP”控制 MCP、Production Architecture、RAG 与 Memory Hub 深度，需确认是否接受该取舍。
