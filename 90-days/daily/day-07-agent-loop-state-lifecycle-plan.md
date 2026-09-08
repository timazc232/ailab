# Day 7 计划 — M1.7 Agent Loop + State / Lifecycle

> 状态：**Day 7 进行中（2026-09-07，同一 UTC 日期的第二个学习单元）**。
> 参数沿用：Python 3.12、仅标准库、scripted model、纯本地 Registry、禁止真实 API。预计约 3–4 小时。

## 1. 学什么

- **Agent Loop**：重复执行 model decision → optional tool dispatch → observation → next model request，直到明确终止。
- **Explicit State（显式状态）**：运行进度不藏在局部变量或会话里；messages、step、status、终止原因、script cursor、trace 均可检查和序列化。
- **Lifecycle（生命周期）**：`created → running → completed/failed/cancelled/paused`；只有合法状态转换。
- **Termination reason（终止原因）**：退出循环必须说明 final answer / max steps / cancelled / interrupted / failure，而不是仅仅“停了”。
- **Checkpoint（检查点）**：在安全边界保存最小可恢复状态；恢复后不能重复执行已经完成的工具。
- **Resource cleanup（资源清理）**：完成、失败、取消、暂停都必须关闭本次运行资源；resume 创建新资源会话。

## 2. Agent 与固定 Workflow

- **Workflow**：步骤和分支预先确定，例如固定的 validate → transform → save；通常更简单、便宜、可预测。
- **Agent**：下一步依赖模型对当前 context 的动态决策；适合路径不能预先完整写死的任务。
- 如果任务本来可以用固定流程可靠完成，不应为了“智能”引入循环、额外调用与不可预测性。

## 3. Engineering Questions

1. 哪些任务不应该使用 Agent，而应使用固定 Workflow？
2. 为支持中断/恢复，checkpoint 最小必须保存什么？
3. 如何避免 max steps、取消或恢复时重复执行工具？

## 4. 假设（可证伪）

**H1**：一个 scripted Agent Runtime 能让直接回答、单工具、多工具、重复调用、max steps、取消、中断和恢复都以明确终止原因结束；state 可 JSON round-trip；恢复不重复已完成工具；每条路径资源都关闭。

## 5. 最小状态模型

`AgentState` 至少包含：

- `version`、`run_id`
- `status`、`termination_reason`
- `step_count`、`max_steps`
- `model_cursor`（scripted model 下一条 decision 的位置）
- `messages`（完整 context）
- `tool_trace`（已执行调用及结果）
- `final_answer`

不把 Registry、函数对象或打开的资源写入 checkpoint；这些是运行时依赖，resume 时重新注入。

## 6. Loop 与安全 checkpoint 边界

每个 step：

1. 检查 cancel / interrupt / max_steps。
2. 获取一个 scripted model decision，step +1、cursor +1。
3. 若 final answer：追加 assistant message并 completed。
4. 若 tool call：追加 assistant tool-call message → Registry dispatch → 追加 role=tool observation → 下一 step。
5. 用 `finally` 清理本次资源。

本日只在**完整 step 结束后**允许 pause/checkpoint；不处理中途正在执行的 tool。这样 resume 不会重放已完成动作。in-flight exactly-once 留给 reliability/lifecycle 后续实验。

## 7. 场景矩阵

| # | 场景 | 预期 |
|---|---|---|
| l1 | 直接回答 | completed:final_answer；0 tool execution |
| l2 | add → final | 2 steps；add 1 次；tool result 在 context 中 |
| l3 | add → divide → final | 3 steps；两工具各 1 次；context 顺序正确 |
| l4 | scripted model 持续重复 add | max_steps；有限结束；执行次数=max_steps |
| l5 | 第一工具 step 后请求 cancel | cancelled；已完成工具不回滚；资源关闭 |
| l6 | 第一工具 step 后 interrupt | paused:interrupted；checkpoint JSON round-trip；资源关闭 |
| l7 | 从 l6 checkpoint resume → final | completed；已完成 add 不重复执行；新资源关闭 |

## 8. 成功指标


1. l1–l7 全部命中预测，所有路径有 `termination_reason`。
2. l4 不超过 max_steps；l5/l6 在 step 边界停止。
3. checkpoint JSON serialize → deserialize 保持关键 state 相等。
4. l7 不重复 l6 已完成的工具；context 与 model cursor 连续。
5. 每次 runtime session 的 resource probe 均 `opened=1, closed=1`。
6. Evaluation 累计 ≥41（现 34 + 7）。

## 9. Definition of Done

- state 可序列化/检查；每条路径有终止原因；资源可清理；恢复不重复已完成工具。
- 学习者能画出状态转换并解释每次 context 更新，以及 Agent vs Workflow 的适用边界。
- 仅生成代码不算完成；必须运行、观察、解释、归档 Evaluation。

## 10. Artifact

- `m1-7-agent-loop/`：state model、scripted model、runtime、resource probe、runner。
- 状态转换图（README / plan 内 Mermaid 或文本图）。
- `eval_cases.jsonl` 追加 m1.7-l1..l7。

## 11. 实现决策（待用户确认）

1. 一个 step 定义为“一次 model decision + 该 decision 的可选 tool dispatch”。
2. pause/cancel 只发生在 step 边界，不中断正在运行的工具。
3. checkpoint 不保存函数/Registry/资源，只保存 JSON-safe state；resume 重新注入依赖。
4. scripted model cursor 存进 state，防止恢复后从第一条 decision 重播。
