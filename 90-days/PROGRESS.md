# 90 天 AI Agent Engineering 进度

> 本文件只记录实际发生的学习、验证证据、未解决问题和下一步；计划内容以 [`ROADMAP.md`](ROADMAP.md) 为准。

- **最后更新**：2026-08-31

## Current Phase

- **Day 0 — 准备阶段（Completed）**
- Phase 1 — Day 1 进行中（2026-08-31 开始）。

## Current Day

- **Current Day**：Day 2（2026-09-01）
- **Day 1**：Completed — 概念 → 假设 → 实现 → 运行 → 观察 → 用户解释 → Evaluation 归档。
- **Day 2**：In Progress — 实现与实测完成（e1–e5 全部 5/5）；Evaluation 已归档；M1.2 Completed 待用户解释观察结果。
- **已完成 Module**：M1.1（Day 1 第一个最小闭环，2026-08-31）。

## Current Module

- **已完成**：工作区初始化与治理基线；Day 1 开工参数确认；Day 1 全流程（概念 / 假设 / mock / client / runner / 实测验证 / 用户解释确认 / 首批 7 个 Evaluation Cases 归档）。
- **下一 Module**：M1.2 Messages / Context（Week 1 剩余部分）。
- **状态**：M1.1 Completed（2026-08-31）；M1.2 实现与实测完成（12 条累计 Evaluation Cases），待用户解释后关闭。

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

## Active Task

- 本次任务：按完整需求初始化并校准 `90-days/ROADMAP.md` 与 `90-days/PROGRESS.md`。
- 当前执行状态：文档工作完成；未开始 Day 1、未编写实现代码、未安装依赖、未调用外部 API。

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

- Core Mechanism 必须按“概念 → 最小实验 → 实现 → 运行 → 观察 → 解释 → Evaluation → 改进”推进。
- Evaluation 与 Safety 是跨阶段能力：早期积累 cases，后期形成正式 harness 和基线。
- 路线假设已有后端、Linux、Docker、数据库、Git 与 API 基础，不重复教授基础课程。
- Pi 只是当前 Coding Agent；Artifact、命令、测试和知识状态必须保持 Agent Harness neutral。
- OpenOps 的故障注入必须位于隔离 Docker Test Lab；宿主机重要服务不是实验对象。
- Memory、Context 与 RAG 必须分别验证，不能用接入 Vector Database 代替机制理解。

### 尚无实验结论

- Day 1 尚未开始，因此当前没有关于模型 API、实现方案或评测结果的实验证据。

## Next Step

1. 已完成（2026-08-30）：确认 Day 1 开工参数；更新 `daily/day-01-llm-api-fundamentals-plan.md`（含第 7 场景：200 + 合法 JSON + `finish_reason="length"`）。
2. 已完成（2026-08-30）：Day 1 概念步确认通过；假设、fixture contract 与分类决策规则见 `daily/day-01-llm-api-fundamentals-plan.md` 第 10 节。
3. 已完成（2026-08-31）：Day 1 闭环完成；M1.1 标记 Completed；首批 7 个 Evaluation Cases 已归档并推送仓库。
4. 进行中（2026-09-01）：M1.2 实现、运行、观察完成（5/5），Evaluation 已归档；待用户解释 e2/e5 观察后关闭 M1.2。

## Progress Update Rules

- 不因代码已生成、文件已创建或阅读材料已完成而标记 Module / Day Completed。
- 每次完成状态必须附带运行命令、测试或 Evaluation 结果、Artifact 路径和未解决问题。
- 失败实验同样记录；不得静默覆盖不利结果。
- `ROADMAP.md` 记录计划变化，`PROGRESS.md` 记录实际事实，两者不得混写。
