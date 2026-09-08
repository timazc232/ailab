# Day 8 计划 — M1.8 Planning + Reflection + Human-in-the-loop

> 状态：**Day 8 进行中（2026-09-08）**。
> 参数沿用：Python 3.12、仅标准库、scripted model、本地 Registry、禁止真实 API。预计约 3–4 小时。

## 1. 学什么

- **Reactive（反应式）**：走一步看一步，每步根据当前 context 决定下一步；M1.7 的默认策略。
- **Plan-first（先规划）**：先让模型产出显式计划，再逐步执行；计划本身也是 context 的一部分。
- **Reflection（反思）**：让模型检查自己的中间结果或失败原因并改进；必须有次数上限，否则成本与循环风险失控。
- **Human-in-the-loop**：在不可逆/有副作用的动作前插入人工审批点；审批前暂停（复用 M1.7 paused 状态），批准后恢复。

## 2. 为什么重要

这些机制可能提升复杂任务的质量，但每一个都增加 Model Calls、Latency 和 Cost。核心工程问题不是"能不能加"，而是"加了对成功率有没有可测量的收益"。Andrew Ng 的 agentic workflow 与 LangGraph 的 human-in-the-loop 生产实践都强调：机制引入要有条件、有上限、可测量。

## 3. Engineering Questions

1. 在相同 task / 模型 / 工具 / 预算下，Reflection 是否提高任务成功率？
2. 增加的 Model Calls / Latency / Cost 是否值得？
3. Multi-agent patterns 在此阶段是否必要？（预设：不必要，先不引入）

## 4. 假设（可证伪）

**H1**：在同一 scripted task 上，用统一 Runtime 可以实现 reactive baseline、plan-first、失败后一次 Reflection、副作用前 approval 四种策略；每种策略的 Model Calls、steps、termination reason 可测量；策略选择条件明确；Reflection 有硬上限；approval 可暂停/恢复且未批准时不执行副作用工具。

## 5. 实验设计

### 5.1 任务与策略

同一个 scripted task（含一次工具计算），比较四种策略：

| # | 策略 | scripted 行为 | 预期 |
|---|---|---|---|
| p1 | Reactive baseline | 决策→工具→final | 完成；2 steps；2 model decisions |
| p2 | Plan-first | 先输出 plan（一条 assistant message），再执行 | 完成；3 steps；计划消息在 context 中 |
| p3 | Reflection | 第一次 final 被内建 checker 判错 → 一次 Reflection → 修正 final | 完成；Reflection 恰好 1 次；修正后正确 |
| p4 | Reflection 上限 | checker 永远判错 | max_reflections=1 后停止；Reflection 不超过 1 次；有限结束 |
| p5 | Human approval | 决策含副作用工具（新工具 `send_report`，side_effect=true） | 未批准前 paused:awaiting_approval；批准后执行并完成；拒绝则 cancelled |

### 5.2 测量指标

- model decisions 次数（proxy for Model Calls / Cost）
- steps、tool executions
- termination reason
- Reflection 次数（p3=1，p4≤1）
- approval 前副作用工具执行次数（必须为 0）

### 5.3 成功指标

1. p1–p5 全部命中预测；重复运行一致。
2. p4 证明 Reflection 上限生效，无无限循环。
3. p5 未批准时 `send_report` 执行 0 次；批准后恰好 1 次。
4. Evaluation 累计 ≥46（现 41 + 5）。

## 6. Definition of Done

- 策略使用条件明确；Reflection 有次数上限；审批可暂停/恢复。
- 学习者能解释质量收益是否值得额外 Model Calls、Latency 与 Cost。
- 仅生成代码不算完成；必须运行、观察、解释、归档。

## 7. Artifact

- `m1-8-control-strategies/`：策略配置、checker、approval 钩子、runner。
- 共享 `eval_cases.jsonl` 追加 m1.8-p1..p5。

## 8. 实现决策（待用户确认）

1. 复用 M1.7 Runtime 与 AgentState，不 fork；策略通过 decision script 与钩子组合表达。
2. Reflection 由本地确定性 checker 触发（scripted 场景中"质量判断"无法来自真实模型；checker 模拟 ground truth 判断）。
3. 副作用工具 `send_report` 只记录调用意图，不产生真实副作用。
4. approval 复用 paused 状态：`termination_reason=awaiting_approval`；批准后 resume。
5. Multi-agent 不做，记录为明确非目标。
