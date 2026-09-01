# Day 2 计划 — M1.2 Messages / Context

> 状态：**Day 2 进行中（2026-09-01）**，M1.1 已于 2026-08-31 完成。
> 开工参数沿用 Day 1 确认值：Python 3.12、仅标准库、最小 OpenAI-compatible schema、仅本地 mock、禁止真实 API 与外部费用。
> 预计投入：约 3 小时（Week 1 共 10–12 小时的一部分）。
> 按需创建当日日志：`2026-09-01.md`。

## 1. 学什么

Module：**M1.2 Messages / Context**（ROADMAP Week 1）。

- **Message 的结构**：`{role, content}` 有序数组；OpenAI-compatible 最小角色集 `system / user / assistant`（`tool` 角色留到 Tool Calling 模块）。
- **顺序即语义**：模型按数组顺序读取；同样的消息不同排列 = 不同输入 = 可能不同输出。
- **Context window 是输入预算**：一次调用能"看到"的内容有上限；超出会导致报错或静默截断（因 provider 而异）。上层必须自己管理预算：估算 → 显式截断策略。
- **截断是有损决策**：丢弃的信息不可恢复；策略（保 system、从最新往回保留等）必须是显式 Policy，不是隐式字符串切片。
- **Context ≠ memory**：context 是本次请求显式发送的内容，请求结束即消失；memory 是跨请求持久化状态，需要显式存储、检索、再注入。
- **序列化确定性**：相同结构 → 字节一致的 payload；这是后续缓存、测试与 hash 的前提。

## 2. 为什么重要

Agent 的全部"状态连续性"都来自你显式重发的历史。不理解 messages 是唯一事实来源，就会把 context 误当 memory，在多步 Agent Runtime（M1.7）里出现状态漂移。预算与截断策略则是 Cost / Latency Engineering（M3.3）的地基。

## 3. Engineering Question（本次要回答的）

> 显式构造与截断策略是否足以支撑多步 Agent Runtime，而不把 context 误当 memory？

对应 ROADMAP 思想地图 M1.2（Karpathy / Anthropic：context 是显式、有界的输入）。答案以 echo 实验为证据。

## 4. 假设（可证伪）

**H1**：仅用标准库实现的 messages 模块，能对合法输入产生**字节确定**的序列化，并在构造期拒绝非法输入；配合显式字符预算（proxy），能把超预算对话截断为符合 Policy 的可验证 payload。

- **H1a**：同一 messages 列表两次序列化结果字节一致。
- **H1b**：空内容 / 非法 role 在**构造期**被拒绝（fail fast，不产生网络请求）。
- **H1c**：重排消息产生字节不同的 payload；echo mock 证明"模型看到的顺序 = 发送顺序"。
- **H1d**：超预算对话按 Policy 截断后，payload 字节预算内，且 echo 回显与策略产出一致。

## 5. 最小实验计划

### 5.1 范围与非目标

- 范围：messages 构造/校验/序列化模块 + 字符预算截断 Policy + echo 场景验证。
- 非目标：真 token 计数（需 tokenizer，留待授权后）、memory 存储、多轮状态持久化、tool 角色、内容语义质量。

### 5.2 环境与安全边界

- 沿用 Day 1：`playground/agent-lab/m1-1-llm-client/` 中的 client/mock 模式；Day 2 新增 `m1-2-messages/`，mock 扩展一个 echo 场景（`s8`），保持向后兼容。
- 仅 loopback；无凭据；占位假 key。

### 5.3 场景矩阵

| # | 场景 | 输入/操作 | 预期结果（实验时对照） |
|---|---|---|---|
| e1 | 确定性序列化 | 同一 3 条消息序列化 2 次 | 两次字节一致 |
| e2 | 顺序即语义 | 同 3 条消息两种顺序，经 `s8` echo 发送 | payload 字节不同；回显顺序 = 发送顺序 |
| e3 | 空内容 | `content=""` | 构造期拒绝，无网络请求 |
| e4 | 非法 role | `role="boss"` | 构造期拒绝，无网络请求 |
| e5 | 超预算截断 | 6 条消息 vs 字符预算 120 | 截断后 ≤ 预算；保 system + 最新轮次；echo 验证一致 |

### 5.4 观察字段（每个 case 一条记录）

`case_id`、`operation`（serialize/send/reject/truncate）、`input_summary`（消息数、总字符）、`budget_chars`（如适用）、`result`（ok / rejected:<原因> / bytes）、`payload_sha256`（前 12 位）、`echo_match`（如适用）、`evidence_ref`。

### 5.5 成功指标

1. e1 两次序列化字节一致；重复运行结果稳定。
2. e2 两种顺序 payload 字节不同，且 echo 回显顺序与发送一致（3/3）。
3. e3/e4 在构造期被拒绝且错误信息明确；全程零网络请求。
4. e5 截断后 payload ≤ 预算，echo 回显与策略产出字节一致。
5. 首批 M1.2 Evaluation Cases（≥5）归档到 `eval_cases.jsonl`（累计 ≥12）。

### 5.6 执行步骤（学习闭环）

1. **概念**（约 40 分钟）：四问讲解 + 用户复述确认（见当日对话）。
2. **定义**（约 15 分钟）：确认 H1、场景矩阵与决策点（§8）。
3. **实现**（约 60 分钟）：messages 模块（构造/校验/序列化/截断）→ mock 增加 `s8` echo → runner。
4. **运行**（约 25 分钟）：按场景矩阵执行，填写观察记录。
5. **解释**（约 20 分钟）：对照 H1 回答 Engineering Question；记录意外行为。
6. **沉淀**（约 20 分钟）：归档 M1.2 cases；更新 `PROGRESS.md`；提炼机制说明 note。

## 6. 如何验证 / Definition of Done

- 实验真实运行；序列化可重复（字节级）；边界行为有证据。
- 学习者能解释 **message history、context window、persistent memory** 三者的区别。
- `PROGRESS.md` 更新为实际结果。**仅生成代码不算完成。**

## 7. Artifact 清单

- `m1-2-messages/`：messages 模块 + echo runner + 运行说明（README 更新）。
- mock `s8` echo 场景（向后兼容扩展）。
- 机制说明 note（四层概念图 + 三概念区分表）。
- `eval_cases.jsonl` 追加 m1.2-* cases；`PROGRESS.md`、当日日志更新。

## 8. 实现决策（待用户确认）

1. **预算 proxy 用字符数**：标准库可测、确定性强；注明"字符 ≠ token"，真 token 计数留到可用 tokenizer 时。
2. **截断 Policy**：保 system 消息 + 从最新轮次向回保留，直到预算用尽（drop-oldest-except-system）。
3. **拒绝语义**：构造期 raise（fail fast），让非法状态不可表示。
4. **mock 扩展**：`s8` echo——把收到的 `messages` 原样回显在 `choices[0].message.content`（JSON 字符串），`finish_reason="stop"`。

## 9. 完成后动作

- `PROGRESS.md`：M1.2 完成状态 + 证据 + 下一步（Week 1 收尾复盘或提前进入 M1.3 视进度）。
- 稳定理解提炼到 `knowledge/`：context window vs memory 概念表。
