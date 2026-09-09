# 90 天 AI Agent Engineering 进度

> 本文件只记录实际发生的学习、验证证据、未解决问题和下一步；计划内容以 [`ROADMAP.md`](ROADMAP.md) 为准。

- **最后更新**：2026-09-09

## Current Phase

- **Day 0 — 准备阶段（Completed）**
- **Phase 1 九个 Module 全部 Completed（2026-09-09）**；下一步：Day 30 Checkpoint（复盘 + agent-lab Phase 1 baseline 汇总）→ 进入 Phase 2 前置确认。

## Current Day

- **Current Day**：Day 9（2026-09-09）
- **Day 1–8**：Completed。
- **Day 9**：Completed — 概念 → 假设 → 实现 → 运行 → 观察 → 用户解释 → Evaluation 归档（55 累计 cases）。M1.9 是 Phase 1 最后一个 Module。
- **已完成 Module**：M1.1–M1.9（全部）。
- **已完成 Module**：M1.1–M1.8。
- **节奏记录**：2026-09-05～06 无学习记录；Day 6/7 均发生于 2026-09-07，分文件记录。

## Current Module

- **已完成**：M1.1–M1.8；累计 47 条 Evaluation Cases；Day 1–8 均有运行证据与用户解释确认。
- **下一 Module**：M1.9 Retry / Timeout / Error Recovery + Basic Tracing（Week 4）。
- **状态**：M1.9 Completed（2026-09-09）；Phase 1（M1.1–M1.9）全部完成；待做 Day 30 Checkpoint 复盘。

## Completed Milestones

### Day 0 Completed

- [x] 工作区基础目录与文档基线已建立。
- [x] 根目录 `AGENTS.md` 已建立，包含学习模式、实现闸门、实验纪律、安全边界和 Definition of Done。
- [x] 90 天路线已按 Phase → Week → Module 初始化，覆盖 agent-lab、OpenOps、Memory Hub、Evaluation 与 Portfolio milestones。
- [x] `PROGRESS.md` 已初始化，用于区分计划与实际进展。

> Day 0 的“环境搭建”仅指 AI Lab 工作区与治理文档基线，不代表语言运行环境、项目依赖、模型凭据或外部 API 已配置。

### Day 1 Completed（2026-08-31）

- [x] M1.1 LLM API Fundamentals / LLM Client 第一个最小闭环。
- 证据：`playground/agent-lab/m1-1-llm-client/`（mock / client / runner）；self-test 7/7；runner 21/21 命中预测；首批 7 个 Evaluation Cases：`eval_cases.jsonl`。
- 用户解释确认：三类失败边界、timeout 重试不确定性（幂等性雏形）、HTTP success != model task success（各含一次纠偏后通过）。
- 已知限制：结论限于本地 mock 与单一路径；未知 `finish_reason` 与 schema_violation 边界分支未实测。

### Day 2 Completed（2026-09-01）

- [x] M1.2 Messages / Context 第一个最小闭环。
- 证据：`playground/agent-lab/m1-2-messages/`；runner e1–e5 5/5；Day 1 回归 21/21 不变；累计 Evaluation 12 cases（`playground/agent-lab/eval_cases.jsonl`）。
- 用户解释确认：context 是唯一事实来源（连续性由重发历史造出）；drop-oldest 对重要性盲目；构造期 fail-fast 与运行时防御分层。
- 已知限制：字符预算是 proxy 非 token；截断 Policy 是确定性 baseline，语义去噪留给 M4.2/M4.4。

### Day 3 Completed（2026-09-02）

- [x] M1.3 Streaming 第一个最小闭环。
- 证据：`playground/agent-lab/m1-3-streaming/`；runner f1–f5 5/5；Day 1 回归 21/21；self-test 11/11；累计 Evaluation 17 cases。
- 用户解释确认：增量 UTF-8 解码器拼回跨 chunk 字符；EOF 是传输层信号，完整性须 finish_reason 且 [DONE]。
- 已知限制：无主动 backpressure 控制；无 tool-call 流式事件。

### Day 4 Completed（2026-09-03）

- [x] M1.4 Structured Output 第一个最小闭环。
- 证据：`playground/agent-lab/m1-4-structured-output/`；runner g1–g5 5/5；Day 1 回归 21/21；self-test 17/17；累计 Evaluation 22 cases。
- 用户解释确认：retry 输出仍须走同一套 schema；额外字段直接拒绝是为了让契约违规可见，而不是默默放行。
- 已知限制：schema 子集仅 object/required/type/enum/additionalProperties=false；无 semantic validation。

### Day 5 Completed（2026-09-04）

- [x] M1.5 Tool Calling 第一个最小闭环。
- 证据：`playground/agent-lab/m1-5-tool-calling/`；runner t1–t5 5/5；拒绝路径 calls_executed=0；累计 Evaluation 27 cases。
- 用户解释确认：模型提出 ≠ 执行；selection / invocation validation / execution 三段边界；tool result 必须显式回填并用 tool_call_id 关联。
- 已知限制：只支持单 tool call；allowlist 硬编码；工具均为无副作用纯函数；真实执行异常留给 M1.6。

### Day 6 Completed（2026-09-07）

- [x] M1.6 Tool Registry / Dispatch 第一个最小闭环。
- 证据：`playground/agent-lab/m1-6-tool-registry/`；runner r1–r7 7/7；拒绝路径零执行；执行异常计数 1；累计 Evaluation 34 cases。
- 用户解释确认：duplicate name 不可自动替换；authorization 先于 validation；execution failure 必须已进入函数；inventory 不是授权凭证。
- 已知限制：无 timeout / async / 动态卸载 / 并发注册；当前无显式 replace/unregister 生命周期；schema 仅 number/string + required + 无额外字段。

### Day 7 Completed（2026-09-07）

- [x] M1.7 Agent Loop + State / Lifecycle 第一个最小闭环。
- 证据：`playground/agent-lab/m1-7-agent-loop/`；runner l1–l7 7/7；所有路径有 termination reason；资源均 opened=1/closed=1；resume 不重放 add；累计 Evaluation 41 cases。
- 用户解释确认：max_steps 是预算未完成而非故障；副作用不可自动回滚；checkpoint 四要素作用；恢复零重放证明。
- 已知限制：仅在完整 step 后 checkpoint；不覆盖 in-flight tool、外部副作用 exactly-once、持久化存储、并发恢复与 schema migration。

### Day 8 Completed（2026-09-08）

- [x] M1.8 Planning + Reflection + Human-in-the-loop 第一个最小闭环。
- 证据：`playground/agent-lab/m1-8-control-strategies/`；runner p1–p5b 6/6；M1.6/M1.7 回归不变；累计 Evaluation 47 cases。
- 用户解释确认：策略成本对比；Reflection 上限防失控；审批依据 ToolSpec metadata 在 dispatch 前拦截；Reflection 管生成层质量、approval 管执行层不可逆风险。
- 已知限制：checker 为确定性 stub；真实质量收益需真实模型评测；multi-agent 明确非目标；approval 超时未实现。

### Day 9 Completed（2026-09-09）

- [x] M1.9 Retry / Timeout / Error Recovery + Basic Tracing 第一个最小闭环；Phase 1 全部九个 Module 完成。
- 证据：`playground/agent-lab/m1-9-reliability/`；runner n1–n8 8/8；累计 Evaluation 55 cases。
- 用户解释确认：原始尝试 vs 重试计数；deadline 检查必须在发起新尝试前；transient 只是重试的必要条件（次数/预算/幂等/业务策略四道门）；attempt 字段对 trace 消歧的必要性。
- 已知限制：虚拟时钟；backoff 无 jitter；幂等键未实现；trace 未与 M1.7 loop 集成。

### agent-lab Phase 1 baseline（2026-09-09）

- 代码：9 个 Module 目录（m1-1 … m1-9），Python 标准库、无第三方依赖、无真实模型调用。
- 评测：`eval_cases.jsonl` 累计 55 条，覆盖 API 边界、context、streaming、schema、tool、registry、loop/state、控制策略、可靠性。
- 复盘：待 Day 30 Checkpoint 统一进行（含 Week 1/2 顺延的复盘合并）。

## Active Task

- 本次任务：Day 9 / M1.9 Retry / Timeout / Error Recovery + Basic Tracing 最小闭环。
- 当前执行状态：Completed；仅虚拟时钟与本地 fixtures；未调用真实模型/API；代码与证据已推送 GitHub。

## Validation Evidence

- 根规则：[`../AGENTS.md`](../AGENTS.md)
- 工作区说明：[`../README.md`](../README.md)
- 90 天目录说明：[`README.md`](README.md)
- 计划：[`ROADMAP.md`](ROADMAP.md)
- 实际进度：[`PROGRESS.md`](PROGRESS.md)
- 本次验证范围：文件存在性、四个 Phase、三个工程 Artifact、22 个 Core Topics、Engineering / Evaluation / Portfolio Milestones、三个 Checkpoint、PROGRESS 必备字段，以及 Day 1 未被标记完成。
- 验证命令：使用 `test -s`、`grep -Fq`、Phase 计数与 Day 1 状态检查完成离线内容校验。
- 验证结果：`ROADMAP/PROGRESS content validation: PASS`（2026-08-30）。
- 2026-08-31：`python3 mock_server.py --self-test` → `PASS: 7/7 fixtures match the contract`；防火墙实测确认 loopback 可用（ufw `-i lo -j ACCEPT`，未修改防火墙配置）。
- 2026-08-31：`python3 run_scenarios.py` → `PASS`，21/21 观察 outcome 一致且命中 §10.2 预测（`observations.jsonl`）。
- 2026-09-04：`python3 run_tool_scenarios.py` → `PASS: 5 cases`；t2/t3/t4 `calls_executed=0`；累计 Evaluation 27 cases。
- 2026-09-07：`python3 run_registry_scenarios.py` → `PASS: 7 cases`；r3/r4/r5 零执行；r6 执行 1 次后异常；累计 Evaluation 34 cases。
- 2026-09-07：`python3 run_loop_scenarios.py` → `PASS: 7 cases`；l6 checkpoint round-trip；l7 恢复零重放；累计 Evaluation 41 cases。
- 2026-09-08：`python3 run_strategy_scenarios.py` → `PASS: 6 cases`（含回归 m1-7 7/7、m1-6 7/7）；Reflection 封顶；审批前副作用零执行；累计 Evaluation 47 cases。
- 2026-09-09：`python3 run_reliability_scenarios.py` → `PASS: 8 cases`；deadline/幂等门控/fallback/trace 重建全部命中；累计 Evaluation 55 cases。

## Unresolved Questions

### Day 1 前需要确认（已于 2026-08-30 全部确认）

1. 实现语言：Python 3.12；Day 1 仅标准库（不用官方 SDK、requests、httpx、Agent Framework）。
2. 协议 baseline：最小 OpenAI-compatible HTTP schema，不绑定 OpenAI SDK 或特定 provider。
3. Phase 1 先保持纯本地 mock；禁止调用真实 LLM API 与 CLIProxyAPI，不产生外部模型费用。
4. 90 天正式开始日期：2026-08-31（2026-08-30 保持 Day 0）。

### 可延后到对应 Phase 前确认

1. OpenOps 的首批用户、重点环境、开源许可证和发布边界。
2. Multi-model Evaluation 要比较的 provider/model 与费用上限。
3. Memory Hub 的初始持久化方案，以及是否与 OpenOps 做可选集成。
4. 四类目标岗位的优先顺序，以及英文 README、Resume 与 Demo 的主要受众。
5. 后两个 15 天 Phase 默认只做最小可验证 baseline / MVP；需确认是否接受该深度与广度取舍。

## Lessons Learned

### 已确认的规划原则

- 新术语首次出现时向用户提供通俗解释（用户偏好，自 Day 2 起生效）。

- Core Mechanism 必须按“概念 → 最小实验 → 实现 → 运行 → 观察 → 解释 → Evaluation → 改进”推进。
- Evaluation 与 Safety 是跨阶段能力：早期积累 cases，后期形成正式 harness 和基线。
- 路线假设已有后端、Linux、Docker、数据库、Git 与 API 基础，不重复教授基础课程。
- Pi 只是当前 Coding Agent；Artifact、命令、测试和知识状态必须保持 Agent Harness neutral。
- OpenOps 的故障注入必须位于隔离 Docker Test Lab；宿主机重要服务不是实验对象。
- Memory、Context 与 RAG 必须分别验证，不能用接入 Vector Database 代替机制理解。

### 已有实验结论

- M1.1–M1.9 已完成最小实验闭环；机制结论、失败边界与已知限制分别记录在 Day 1–9 daily log 与 Completed Milestones。

## Next Step

1. 已完成（2026-08-30）：确认 Day 1 开工参数；更新 `daily/day-01-llm-api-fundamentals-plan.md`（含第 7 场景：200 + 合法 JSON + `finish_reason="length"`）。
2. 已完成（2026-08-30）：Day 1 概念步确认通过；假设、fixture contract 与分类决策规则见 `daily/day-01-llm-api-fundamentals-plan.md` 第 10 节。
3. 已完成（2026-08-31）：Day 1 闭环完成；M1.1 标记 Completed；首批 7 个 Evaluation Cases 已归档并推送仓库。
4. 已完成（2026-09-01）：用户复述确认（context 唯一事实来源、drop-oldest 盲区），M1.2 标记 Completed。
5. 顺延：Week 1 复盘改至 Week 2 末与 Week 2 复盘合并进行。
6. 已完成（2026-09-02）：用户复述确认（增量 UTF-8 解码器扛跨 chunk 字符；EOF ≠ 完整，须 finish_reason 且 [DONE]），M1.3 标记 Completed。
7. 已完成（2026-09-03）：用户复述确认（retry 仍走同一 schema；extra field 拒绝以保持违规可见），M1.4 标记 Completed。
8. 已完成（2026-09-04）：用户复述确认（unknown vs denied、invocation 零执行、tool result 回填与 tool_call_id 映射），M1.5 标记 Completed。
9. 已完成（2026-09-07）：用户复述确认（重复注册、授权顺序、零执行 vs 已执行异常、inventory 与强制授权边界），M1.6 标记 Completed。
10. 已完成（2026-09-07）：用户复述确认（max_steps 语义、副作用不可自动回滚、checkpoint 四要素、恢复零重放），M1.7 标记 Completed。
11. 下一步：M1.8 Planning + Reflection + Human-in-the-loop（reactive vs plan-first、受限 Reflection、副作用前人工审批）。
12. 已完成（2026-09-08）：用户复述确认（策略成本、Reflection 上限、审批拦截时机与 metadata 依据、双层拦截互补），M1.8 标记 Completed。
13. 下一步：M1.9 Retry / Timeout / Error Recovery + Basic Tracing（transient vs permanent、deadline、backoff、幂等性与 trace schema；Day 30 Checkpoint 前最后一个 Module）。
14. 已完成（2026-09-09）：用户复述确认（重试计数、deadline 检查时机、transient 四道门、trace 消歧），M1.9 标记 Completed；Phase 1 全部九个 Module 完成。
15. 下一步：Day 30 Checkpoint——复盘 Phase 1 全部 Module、合并 Week 1/2 顺延的复盘、汇总 agent-lab baseline；之后进入 Phase 2（OpenOps）前置确认。

## Progress Update Rules

- 不因代码已生成、文件已创建或阅读材料已完成而标记 Module / Day Completed。
- 每次完成状态必须附带运行命令、测试或 Evaluation 结果、Artifact 路径和未解决问题。
- 失败实验同样记录；不得静默覆盖不利结果。
- `ROADMAP.md` 记录计划变化，`PROGRESS.md` 记录实际事实，两者不得混写。
