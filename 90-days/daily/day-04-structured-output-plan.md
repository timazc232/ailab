# Day 4 计划 — M1.4 Structured Output

> 状态：**Day 4 进行中（2026-09-03）**。开工参数沿用 Day 1。预计约 3 小时。

## 1. 学什么

- **Prompt 不是契约**：在 prompt 里写“请返回 JSON”不能保证得到可解析、可校验的数据。
- **Schema contract**：用显式 schema（类型、必填、枚举、是否允许额外字段）定义机器可验证的输出形状。
- **Schema validation vs semantic validation**：前者检查形状（缺字段、错类型、非法 JSON）；后者检查含义（severity=3 是否真的“高危”——今天不做，只划清边界）。
- **拒绝边界**：校验失败的输出**不得进入下游**。
- **一次受控重试**：失败后最多再请求一次修复；第二次仍失败则拒绝，禁止无限 repair loop。

## 2. 为什么重要

Agent 下游（tool dispatch、状态机、评测）吃的是数据不是散文。把“看起来像 JSON 的自然语言”当成功，会把错误静默送进下一层——比 Streaming 的半截结果更危险，因为它**看起来合法**。

## 3. Engineering Question

> Prompt 要求能否替代 schema 校验？一次受控重试在什么条件下值得做，什么条件下只是在烧调用次数？

## 4. 假设（可证伪）

**H1**：仅用标准库的最小 schema 校验器，能把 5 类失败（无效 JSON / 缺字段 / 错类型 / 额外字段 / 合法）稳定分类；非法输出永不进入下游；一次受控重试只在“可修复的契约失败”时触发，第二次失败则拒绝。

## 5. 最小实验计划

### 5.1 范围与非目标

- 范围：最小 JSON Schema 子集（object / required / type / enum / additionalProperties=false）+ 一次 retry 策略 + mock 场景。
- 非目标：完整 JSON Schema 实现、semantic validation、JSON Schema 第三方库、无限 repair。

### 5.2 场景矩阵

目标 schema（运维诊断最小记录）：

```json
{
  "status": "ok | degraded | down",
  "severity": "integer 0-5",
  "summary": "non-empty string"
}
```

不允许额外字段。

| # | 场景 | 输入 | 预期 |
|---|---|---|---|
| g1 | 合法 | 三字段齐全、类型正确 | accept，无 retry |
| g2 | 无效 JSON | `{oops` | reject: invalid_json，无 retry（无法修复形状未知的垃圾） |
| g3 | 缺字段 | 缺 `severity` | retry 一次；第二次仍缺 → reject: missing_field |
| g4 | 错类型 | `severity: "high"` | retry 一次；修复成功 → accept（记 retried=true） |
| g5 | 额外字段 | 多 `comment` | reject: extra_field（策略：额外字段不修，直接拒绝） |

Retry 策略（显式 Policy，待确认）：
- **可 retry**：缺字段、错类型（形状可描述，修复 prompt 有意义）。
- **不可 retry**：无效 JSON、额外字段（前者无法定位；后者是契约违规，修了也改变不了“模型爱加字段”的根因，今天选择拒绝以便观察）。

### 5.3 成功指标

1. g1–g5 分类与上表一致；非法输出零泄漏到 `accepted` 通道。
2. g4 恰好 retry 1 次后 accept；不会出现第 3 次请求。
3. g2/g5 请求次数 = 1（不触发 retry）。
4. 累计 Evaluation Cases ≥ 22（现 17 + 5）。

## 6. Definition of Done

- 实验真实运行；无效输出不得进入下游；错误分类与重试条件明确。
- 学习者能解释 schema validation 与 semantic validation 的差异，以及“一次受控重试”为什么必须有上限。
- `PROGRESS.md` 更新为实际结果。仅生成代码不算完成。

## 7. Artifact

- `m1-4-structured-output/`：schema 校验器 + retry 策略 + runner。
- mock 扩展 s12–s16（合法 / 非法 JSON / 缺字段 / 错类型 / 额外字段）及 s17（错类型修复后的合法响应）。
- `eval_cases.jsonl` 追加 m1.4-*。

## 8. 实现决策（待用户确认）

1. **最小 schema 子集自实现**（标准库 `json`），不引入 `jsonschema` 库。
2. **额外字段 = 拒绝且不 retry**（保守：契约违规直接可见）。
3. **无效 JSON = 拒绝且不 retry**。
4. **缺字段 / 错类型 = 最多 1 次 retry**；第二次仍失败则拒绝。
