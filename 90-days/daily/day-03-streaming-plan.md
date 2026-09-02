# Day 3 计划 — M1.3 Streaming

> 状态：**Day 3 进行中（2026-09-02）**，M1.1 / M1.2 已完成。Week 1 复盘顺延至 Week 2 末统一做。
> 开工参数沿用 Day 1 确认值：Python 3.12、仅标准库、最小 OpenAI-compatible schema、仅本地 mock、禁止真实 API 与外部费用。
> 预计投入：约 3 小时。

## 1. 学什么

- **流式的线缆形态**（OpenAI-compatible）：`stream: true` 时，响应 body 不再是一个 JSON，而是 SSE（Server-Sent Events）文本流：每事件形如 `data: {...}\n\n`，delta 增量片段需累积，终止信号为 `data: [DONE]`。
- **分块边界不可假设**：TCP 不保证 chunk 边界 = 事件边界；一行 JSON、甚至一个 UTF-8 多字节字符都可能被切在两个 chunk 中间 → parser 必须增量、带缓冲。
- **完整性只有 finish signal 能证明**：`finish_reason`（事件内）与 `[DONE]`（流末）是权威完成信号；断流时手里只有半截结果，**不得静默当作完整结果**——这是 Day 1 "model/result-level condition" 概念在流式下的延伸。
- **取消边界**：客户端可主动断开（用户点停止）；已收到的部分可展示，但必须标记为不完整。
- **Streaming 改变什么/不改变什么**：改变传输与体验（首 token 延迟、渐进显示）；不改变答案本身——流式重组结果应与非流式一致（本模块 DoD 的核心验证）。
- **Backpressure**（新词：反压）——消费速率跟不上生产速率时的"顶回去"机制；HTTP/TCP 的窗口与 socket 缓冲天然提供基础形态，应用层表现为"读不过来就积压"。

## 2. 为什么重要

真实 Agent 的交互几乎都是流式；且流式把"完整结果"从默认变成需要证明的命题——没有 finish signal 就宣称完成，是流式系统最常见的一类静默错误。增量解析也是后续 Tool Calling 事件流（M1.5+）的地基。

## 3. Engineering Question（本次要回答的）

> 流式重组结果能否与非流式完全一致？任意分块、跨 chunk 字符、畸形事件、中途断流下，parser 的失败边界在哪里？

## 4. 假设（可证伪）

**H1**：仅用标准库实现的增量 stream parser，能把任意分块（含跨 chunk 的 UTF-8 字符）的 SSE 流重组成与非流式完全一致的结果；且在畸形事件、中途断流、主动取消时，能明确报告不完整，绝不静默输出完整结果。

- H1a：f1/f2 重组文本与非流式 fixture 一致。
- H1b：分块大小不影响重组结果（逐 3 字节切与整块切等价）。
- H1c：畸形事件被记录为 protocol error，不崩溃、不产出完整结果。
- H1d：断流/取消 → 状态明确为 incomplete，已收部分与"完整性判定"分离。

## 5. 最小实验计划

### 5.1 范围与非目标

- 范围：增量 SSE parser（缓冲 + 增量 UTF-8 解码）+ mock 流式场景 + 5 个边界 case。
- 非目标：真 token/延迟测量、并发多路复用、tool-call 流式事件、UI 渲染、backpressure 的主动控制（只要求能解释）。

### 5.2 环境与安全边界

- 沿用 agent-lab：mock 流式响应用 `Connection: close` + 小块写入（模拟任意分块）；仅 loopback；占位假 key。

### 5.3 场景矩阵

| # | 场景 | mock 行为 | 预期（实验时对照） |
|---|---|---|---|
| f1 | 正常流 | 4 个 delta 事件 + finish_reason=stop + [DONE] | 重组文本 == 非流式参考；complete |
| f2 | 任意分块 + 跨 chunk 字符 | 同一事件流按 3 字节粒度写出（含中文字符被切开） | 重组结果与 f1 一致 |
| f3 | 畸形事件 | 流中夹一行 `data: {oops` | parser 记录 protocol error，不崩溃、不判 complete |
| f4 | 中途断流 | 写 2 个事件后直接断开连接，无 finish/[DONE] | 状态 incomplete；已收部分单独报告 |
| f5 | 主动取消 | 正常流；client 收到 2 个事件后主动断开 | 状态 cancelled-by-client；已收部分单独报告 |

### 5.4 观察字段

`case_id`、`chunk_strategy`（whole/3-byte）、`events_received`、`deltas_assembled`（重组文本）、`finish_reason`、`done_received`、`completeness`（complete / incomplete / cancelled / protocol_error）、`errors`（畸形事件列表）、`text_matches_nonstream`（与参考答案比对）、`evidence_ref`。

### 5.5 成功指标

1. f1/f2 重组文本与非流式参考**完全一致**，completeness=complete。
2. f2 与 f1 结果字节一致（分块不影响）。
3. f3 errors 非空且 completeness ≠ complete。
4. f4/f5 completeness 分别为 incomplete / cancelled，且已收 delta 明确保存。
5. 首批 M1.3 cases（≥5）归档 `eval_cases.jsonl`（累计 ≥17）。

### 5.6 执行步骤

1. **概念**（约 40 分钟）：四问讲解 + 用户复述确认。
2. **定义**（约 15 分钟）：确认 H1 与决策点（§8）。
3. **实现**（约 60 分钟）：stream parser → mock s9–s11 → runner。
4. **运行**（约 25 分钟）：场景矩阵执行 + 观察记录。
5. **解释**（约 20 分钟）：对照 H1 回答 Engineering Question。
6. **沉淀**（约 20 分钟）：cases 归档、PROGRESS/日志更新、机制 note。

## 6. 如何验证 / Definition of Done

- 实验真实运行；重组结果与非流式 fixture 一致；中断可观察且不静默完整。
- 学习者能解释：delta 与完整 message 的关系、为什么 finish signal 是唯一完整性证明、backpressure 与取消边界。
- `PROGRESS.md` 更新为实际结果。**仅生成代码不算完成。**

## 7. Artifact 清单

- `m1-3-streaming/`：stream parser + runner；mock 新增 s9–s11（向后兼容）。
- 机制说明 note（SSE 形态图 + 完整性判定规则）。
- `eval_cases.jsonl` 追加 m1.3-* cases；PROGRESS / 当日日志更新。

## 8. 实现决策（待用户确认）

1. **协议样本**：SSE 按 OpenAI-compatible 形态（`data: {json}\n\n`，`data: [DONE]` 终止）。
2. **增量 UTF-8 解码**：用标准库 `codecs.getincrementaldecoder("utf-8")` 处理跨 chunk 字符。
3. **完整性判定**：事件内出现 `finish_reason` **且**收到 `[DONE]` 才算 complete；两者缺一 = incomplete。
4. **mock 流式实现**：`Connection: close` + 小粒度 `wfile.write`（f2 按 3 字节切）模拟任意分块；f4 直接 close 模拟断流。
