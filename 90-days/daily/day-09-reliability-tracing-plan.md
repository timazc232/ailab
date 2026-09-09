# Day 9 计划 — M1.9 Retry / Timeout / Error Recovery + Basic Tracing

> 状态：**Day 9 进行中（2026-09-09）**。
> 参数沿用：Python 3.12、仅标准库、本地 fixture、禁止真实 API。预计约 4 小时（本模块含故障注入矩阵与 trace schema，是 Phase 1 收尾）。

## 1. 学什么

- **Transient vs Permanent error**：暂时性错误（429、连接抖动、超时）可能自愈，值得重试；永久性错误（401/403、参数非法、schema 违约）重试无意义。
- **Retry policy**：哪些错误重试、重试几次、间隔多久；可靠性不能靠无限重试。
- **Timeout vs Deadline**：单次尝试的时间上限 vs 整个操作（含所有重试）的总时间预算；deadline 到期必须停止。
- **Backoff（退避）**：重试之间的等待时间，本实验用固定小间隔模拟指数退避（不真实 sleep 长时间）。
- **Idempotency（幂等性）**：同一操作执行多次与一次效果相同；副作用工具重试前必须先回答"重试安全吗"。
- **降级（fallback）**：主路径失败后的替代路径（如换工具、返回缓存、明确失败）。
- **Correlation ID / Trace**：为每次 run 分配唯一 ID，每个 step 产生带时间戳的事件；trace 必须足以重建一次运行。

## 2. 为什么重要

Agent 的调用链是 model → tool → model → …，任何一环都可能瞬时失败。没有分类的重试会：把永久错误重试到天荒地老；没有 deadline 的重试会拖垮上层；对非幂等副作用盲目重试会造成重复发送。Tracing 是事后回答"到底发生了什么"的唯一手段。

## 3. Engineering Questions

1. 哪些错误属于 transient，重试能修复？哪些属于 permanent，重试只是浪费？
2. 为什么"单次 timeout"不能代替"整体 deadline"？
3. 副作用工具失败后，什么条件下才允许重试？
4. 最小 trace 需要哪些字段才能重建一次运行？

## 4. 假设（可证伪）

**H1**：一个可靠性层能为 model 调用与 tool 调用提供分类重试、deadline、降级与 trace；429/超时按上限重试且间隔递增；永久错误不重试；deadline 到期停止；非幂等副作用工具失败后不自动重试；trace JSONL 可完整重建每次运行的 step 序列与结果。

## 5. 最小实验计划

### 5.1 故障注入矩阵（scripted，n1–n8）

| # | 场景 | 预期 |
|---|---|---|
| n1 | model 调用 429 → 第 2 次成功 | 成功；attempt=2；trace 含 2 个 model 事件 |
| n2 | model 429 × 3（超过 max_retries=2） | failed:retries_exhausted；尝试 3 次（1 原始 + 2 重试） |
| n3 | model 401（永久错误） | 立即 failed:permanent_error；尝试 1 次；不重试 |
| n4 | tool 超时（挂起模拟）→ 重试成功 | 成功；tool attempt=2 |
| n5 | deadline 到期（重试中总时间超预算） | failed:deadline_exceeded；不再发起下一次尝试 |
| n6 | 副作用工具（非幂等）失败 | 不自动重试；failed:tool_error；send 尝试 1 次或 0 次（取决于失败位置）；进入人工处理路径提示 |
| n7 | 主工具失败 → 降级到备用工具 | fallback_used=true；任务完成 |
| n8 | trace 重建 | 用 trace JSONL 重放，能推出与 observations 一致的 step 序列、attempt 数与最终状态 |

### 5.2 Retry Policy（分类决策表）

| 错误 | 分类 | 重试？ |
|---|---|---|
| HTTP 429 / 500 / 超时 | transient | 是（上限 2 次，间隔递增） |
| HTTP 401 / 403 / 404 | permanent | 否 |
| 参数非法 / schema 违约 | permanent | 否 |
| 副作用工具执行异常 | 需幂等性判断 | 非幂等 → 否（转人工） |

### 5.3 Trace schema（最小字段）

```json
{"ts": "...", "run_id": "...", "seq": 3, "kind": "model_call|tool_call|decision|fallback",
 "name": "add", "attempt": 2, "outcome": "ok|429|timeout|permanent_error|...",
 "detail": "...", "elapsed_ms": 12}
```

### 5.4 成功指标

1. n1–n8 全部命中预测；重复运行一致。
2. n2 尝试次数恰好 3（1+2），无第 4 次；n3 恰好 1 次。
3. n5 deadline 后零额外尝试。
4. n6 非幂等工具不被自动重试。
5. trace 重建（n8）与实际运行结果一致。
6. Evaluation 累计 ≥55（现 47 + 8）。

## 6. Definition of Done

- 重试有上限且只覆盖允许错误；timeout 能终止；永久失败有明确恢复/降级路径；trace 可重建一次运行。
- 学习者能解释 transient vs permanent、deadline vs timeout、幂等性与重试的关系。
- 累计至少 15 个有意义 Evaluation Cases（当前 47，已远超）。
- 仅生成代码不算完成。

## 7. Artifact

- `m1-9-reliability/`：retry policy、deadline、backoff、trace recorder、故障注入 fixtures、runner。
- 共享 `eval_cases.jsonl` 追加 m1.9-n1..n8。
- Phase 1（agent-lab）baseline 汇总。

## 8. 实现决策（待用户确认）

1. 时间用注入的虚拟时钟（可测试、不真实 sleep）；backoff 间隔记录进 trace 而不真实等待。
2. 429/超时/500 用 scripted flaky 函数模拟（前 N 次抛错，之后成功）。
3. 幂等性由 ToolSpec 新增 `idempotent` 字段表达（M1.6 metadata 扩展）。
4. trace 为 append-only JSONL，事件含 run_id + 单调 seq。
5. 降级路径显式声明（fallback tool 列表），不做隐式自动换工具。
