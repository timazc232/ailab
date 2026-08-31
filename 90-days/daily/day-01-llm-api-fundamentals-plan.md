# Day 1 计划 — M1.1 LLM API Fundamentals / LLM Client

> 状态：**开工参数已确认，Day 1 于 2026-08-31 开始**（2026-08-30 保持 Day 0）。实现开始后按 `templates/daily-log.md` 创建 `2026-08-31.md` 记录实际进展。
> 预计投入：约 3 小时（Week 1 共 10–12 小时的一部分）。
>
> **已确认开工参数（2026-08-30）**
> - 实现语言：Python 3.12；Day 1 只用标准库，不用官方 SDK、requests、httpx 或任何 Agent Framework。
> - 协议 baseline：最小 OpenAI-compatible HTTP schema，仅作为学习 request/response boundary 的协议样本，不与 OpenAI SDK 或任何 provider 强绑定。
> - 实验边界：只用本地 mock server；禁止调用真实 LLM API、CLIProxyAPI，不产生任何外部模型费用。
> - 90 天正式开始日期：2026-08-31。

## 1. 学什么

Module：**M1.1 LLM API Fundamentals / LLM Client**（ROADMAP Week 1）。

- 一次模型调用的 HTTP request/response 完整边界：endpoint、method、认证头、payload 形状、status code、response body。
- 认证与配置放在边界层：key、base URL、model 标识不进入业务逻辑，不写入版本库。
- 四层数据流与三类失败的判别：
  - **Transport failure**：请求没有可靠到达/返回（timeout、连接失败）。
  - **HTTP / API protocol failure**：传输成功但协议或数据契约失败（401 认证失败、429 限流、500 服务错误；或 200 但 body 是畸形 JSON、缺失字段）。
  - **Model / Result-level condition**：HTTP 与 payload 全部成功，但模型结果本身未正常完成（如 `finish_reason="length"` 截断）。这是结果条件，不一定是 error。
  - 核心命题：**HTTP success != model task success**。
- 与后续模块的接口：本模块**不**做 streaming、不做 schema 校验、不做 retry 实现，只记录「是否值得重试」的初步判断（retry/backoff 属于 M1.9）。

## 2. 为什么重要

LLM Client 是隔离 provider 变化与上层逻辑的边界：后续 Agent Loop、Tool 执行、Evaluation 全部依赖「一次模型调用」这个原语的可靠与可观察。跳过这一层直接用框架封装，后续所有错误路径、重试策略和成本核算都无法解释。这也是 agent-lab「底层优先、无大型框架 baseline」的第一个环节。

## 3. Engineering Question（本次要回答的）

> 不依赖官方 SDK 抽象，仅凭 client 观察到的信号，能否精确区分 transport failure、HTTP / API protocol failure 与 model / result-level condition——并解释 HTTP success != model task success？

对应 ROADMAP「Engineering Ideas & Intellectual Map」M1.1 条目。答案以实验观察表为证据，不以任何教程结论为准。

## 4. 假设（可证伪）

**H1**：一个仅用标准库实现的最小同步 HTTP client，配合本地 mock，能对 6 类场景产生确定性、可区分的结果，且不发出任何真实外部请求。

若 6 类场景结果不稳定、相互混淆，或实现必须依赖第三方库才能区分，则 H1 被证伪，需记录原因并调整方案。

## 5. 最小实验计划

### 5.1 范围与非目标

- 范围：1 个最小同步 client + 1 个本地 mock + 6 个场景 + 观察记录。
- 非目标：真实外部 API 调用（默认禁止，另行授权）、streaming、structured output、tool calling、retry/backoff 实现、多 provider、任何第三方依赖。

### 5.2 环境与安全边界

- 纯本地运行：mock 服务与 client 同机；认证头用占位假 key（如 `test-key-000`），不提交真实凭据。
- 禁止调用真实 LLM API 与 CLIProxyAPI；不产生任何外部模型费用。
- 实现：Python 3.12，仅标准库（无官方 SDK、requests、httpx、Agent Framework）；实验代码建议放 `playground/agent-lab/`，自带 README 与运行说明，不污染全局环境。
- 日志与证据不包含任何密钥；`.env.example` 只写变量名。

### 5.3 场景矩阵

| # | 场景 | mock 行为 | 预期错误分类（实验时填写） | 重试判断（实验时填写） |
|---|---|---|---|---|
| 1 | 成功响应 | 200 + 合法 JSON | success | no |
| 2 | 畸形 JSON | 200 + 非法 JSON | http-api-protocol（payload 契约失败） | no：确定性契约违反 |
| 3 | 认证失败 | 401 + 错误说明体 | http-api-protocol（HTTP 层拒绝） | no：永久性认证失败 |
| 4 | 限流 | 429（可含 Retry-After 头） | http-api-protocol（HTTP 层拒绝） | yes：遵守 Retry-After |
| 5 | 服务错误 | 500 | http-api-protocol（HTTP 层拒绝） | maybe：服务端瞬时故障 |
| 6 | 超时 | 延迟超过 client timeout | transport（读阶段超时） | uncertain：先确认第一请求结果/幂等键 |
| 7 | 结果未正常完成 | 200 + 合法 JSON + `finish_reason="length"` | model-result-condition | no：重试无助于结果完整性 |

场景 7 与场景 1 在 HTTP 层完全同构（都是 200 + 合法 JSON），唯一差异在 result-level 信号；它用于验证 **HTTP success != model task success**。分类与重试判断两列已由 2026-08-31 的 21 次实测填充；原始观察 `observations.jsonl` 仅本地保留，不入库。

### 5.4 观察字段（每个场景一条记录）

`scenario_id`、`started_at`、`elapsed_ms`、`request_target`、`request_headers_summary`（脱敏）、`http_status`、`response_content_type`、`body_parse`（ok/malformed）、`finish_reason`（如存在）、`outcome_class`（transport / http-api-protocol / model-result-condition / success）、`retry_worthiness_guess`、`evidence_ref`。

### 5.5 成功指标

1. 7/7 场景在纯本地环境确定性复现，重复运行结果一致。
2. 每个场景得到明确且可解释的分类；相邻类别（如 2 与 3、1 与 7）不混淆。
3. client 零第三方依赖；全程无真实外部网络请求（可验证）。
4. 证据中无凭据泄漏。
5. 首批 Evaluation Cases 从这 6 个场景归档（满足 Week 1 ≥3–5 的最低目标）。

### 5.6 执行步骤（学习闭环）

1. **概念**（约 45 分钟）：画一次 chat-completion 请求的四层边界图；用自己的话写出三类失败的定义与各 1 个例子，并说明 HTTP success != model task success。
2. **定义**（约 15 分钟）：确认 H1 与本文件指标；列出 fixtures 清单。
3. **实现**（约 60 分钟，须先获确认）：本地 mock（标准库）+ 最小同步 client；每个场景一个 fixture。
4. **运行**（约 30 分钟）：按场景矩阵逐项执行，填写 5.4 观察表。
5. **解释**（约 20 分钟）：对照 H1 回答 Engineering Question；记录意外行为与失败。
6. **沉淀**（约 10 分钟）：归档首批 cases；更新 `PROGRESS.md` 为**实际结果**；按需创建当日 daily log。

## 6. 如何验证 / Definition of Done

沿用 ROADMAP §8：实验真实运行；验证证据已记录；学习者能解释 transport failure、HTTP / API protocol failure 与 model / result-level condition 的区别，并能说明 HTTP success != model task success；`PROGRESS.md` 更新为实际结果。**仅生成代码不算完成。**

## 7. Artifact 清单

- 最小 client + 本地 mock + 6 个场景 fixtures（含运行说明的 README）。
- 错误观察表（6 条记录）。
- M1.1 机制说明 note（含四层数据流边界图与三类失败解释）。
- 首批 Evaluation Cases（case schema：case_id / scenario / fixture / expected / actual / repeatable / evidence_ref）。
- 更新后的 `PROGRESS.md`。

## 8. 开工参数（已于 2026-08-30 确认）

1. 实现语言：Python 3.12；Day 1 只用标准库（不用官方 SDK、requests、httpx、Agent Framework）。
2. 协议 baseline：最小 OpenAI-compatible HTTP schema；仅作为协议样本，不与 OpenAI SDK 或任何 provider 强绑定。
3. 实验边界：仅本地 mock server；禁止调用真实 LLM API 与 CLIProxyAPI，不产生外部模型费用；真实 provider 另行授权。
4. 正式开始日期：2026-08-31（2026-08-30 保持 Day 0）。

## 9. 完成后动作

- `PROGRESS.md`：Active Task 推进记录 + 实际证据 + 未解决问题；M1.1 只有在验证完成且能解释机制后才可标记 Completed。
- 将稳定理解（三类失败模型与四层数据流）提炼到 `knowledge/`；意外发现转 `playground/` 后续实验。

---

## 10. 假设、Fixture Contract 与决策规则（概念步确认后更新，2026-08-30）

概念步已通过：学习者已用自己的话正确区分 timeout、200+畸形 JSON、200+`finish_reason="length"` 三类场景。本章把理解固化为可证伪假设与可执行契约；经用户确认后才开始实现。

### 10.1 假设（最终版）

**H1**：仅用 Python 3.12 标准库实现的最小同步 client，配合本地 mock server，对 7 个场景产生确定性、相互可区分的结果，并把每次运行唯一地归入四种 outcome class 之一。

- **H1a**：7 个场景的可观察信号可重复（同输入 → 同信号）。
- **H1b**：每次运行都能依据显式信号（状态码、body 解析、`finish_reason`）唯一分类为 `success / transport / http-api-protocol / model-result-condition`，不以内容语义猜测分类。
- **H1c**：全程仅 loopback 连接，零真实凭据。

### 10.2 Fixture Contract

Mock 只暴露一个真实路径 `POST /v1/chat/completions`；场景行为由请求头 `X-Mock-Scenario: s1..s7` 选择（仅测试机制，不改变单端点真实形状）。

| id | Mock 行为 | 关键 fixture |
|---|---|---|
| s1 | 200 + 合法 JSON + `finish_reason="stop"` | content 为完整短句 |
| s2 | 200 + `Content-Type: application/json` + 非法 JSON | 截断 body（如 `{"choices": [`） |
| s3 | 401 + JSON 错误体 | 认证失败语义 |
| s4 | 429 + JSON 错误体 | 附带 `Retry-After` 头供观察 |
| s5 | 500 + JSON 错误体 | 服务错误语义 |
| s6 | 延迟长于 client 读超时 | client 必须超时；记录发生在 connect 还是 read 阶段 |
| s7 | 200 + 合法 JSON + `finish_reason="length"` | content 为故意不完整的句子（可见截断） |

合法 JSON 最小字段集：`choices[0].message.content`（string）、`choices[0].finish_reason`（string）；`usage` 可选，存在则记录。

**预测分类（实验前写下，供运行后对照）**：s1 → `success`；s2 / s3 / s4 / s5 → `http-api-protocol`；s6 → `transport`；s7 → `model-result-condition`。

### 10.3 分类决策规则（按序评估，首中即止）

- **R1 Transport**：接收响应前/中抛出异常（连接失败、读超时）→ `transport`。此时无可用 HTTP status；记录异常发生在 connect 还是 read 阶段。
- **R2 HTTP 状态**：收到完整响应但 status 非 2xx → `http-api-protocol`。
- **R3 Payload 契约**：status 为 2xx 但 body 不是合法 JSON，或缺少最小字段/类型不符 → `http-api-protocol`。
- **R4 正常完成**：JSON 合法且 `finish_reason == "stop"` → `success`。
- **R5 其他结果条件**：JSON 合法但 `finish_reason != "stop"`（如 `length`）→ `model-result-condition`。

规则顺序就是层次顺序本身：收到响应前读不到 status，读 status 前取不到 body，解析 body 前查不了 `finish_reason`；分类自然级联，无歧义。

边界规则：

- JSON 合法但缺 `finish_reason` → 归 R3（契约违反），不归 R4/R5。
- `finish_reason` 为未知值 → 归 R5 并上报上层，client 不猜测。
- 分类只依据显式契约信号；**禁止**按内容自然语言启发式推断分类。

### 10.4 验证标准

1. 7/7 场景在 `127.0.0.1` 离线运行通过，零非 loopback 连接。
2. 每场景重复运行 3 次，三次 `outcome_class` 完全一致且与 10.2 预测一致。
3. 观察记录完整（5.4 全部字段）；证据中无真实凭据。
4. 7 个场景归档为首批 Evaluation Cases（case schema：case_id / scenario / fixture / expected / actual / repeatable / evidence_ref）。

### 10.5 实现决策（待用户确认）

1. HTTP client 用标准库 `http.client` 而非 `urllib.request`：前者把连接、响应状态、body 三个阶段分开暴露，与本项目「观察分层」的学习目标一致；`urllib` 把分层包得太深。
2. Mock 默认监听 `127.0.0.1:8931`，可用命令行参数覆盖。
3. Client 超时：connect 2s / read 2s；s6 睡眠 5s，保证必然触发读超时。
4. 实现顺序：mock server（可独立运行自验）→ 最小 client → 批量 runner 与观察表输出。每步可独立验证，不一次性生成完整实现。
