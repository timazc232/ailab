# Day 5 计划 — M1.5 Tool Calling

> 状态：**Day 5 进行中（2026-09-04）**。开工参数沿用 Day 1。预计约 3 小时。
> 本日只做 M1.5（提出 / 校验 / 执行 / 回填）。Registry 治理留给 M1.6。

## 1. 学什么

- **模型提出 ≠ 已经执行**：`tool_calls` 只是一份请求；真正跑函数的是本地可信代码。
- **Tool call 是 untrusted input**：名称、参数 JSON、甚至“要不要调工具”都来自模型，必须当不可信输入。
- **三段失败边界**：
  - **Tool selection failure**：选了未知工具、未授权/危险工具。
  - **Invocation validation failure**（调用校验失败）：工具已知，但参数不合法；函数根本不执行。
  - **Tool execution failure**：参数合法且函数已进入执行，但内部抛错/超时（今天只解释，真实异常 fixture 留给 M1.6）。
- **回填下一轮**：执行结果变成 `role=tool` 的 message，再发给模型（接 M1.2：context 仍是你显式构造的）。

## 2. 为什么重要

Agent 一旦能调工具，失败从“说错话”变成“做错事”。没有执行边界，prompt injection 或幻觉出来的 `delete_all` 就会真跑。Simon Willison / Anthropic 的核心主张：工具设计与权限边界是安全问题，不是 DX 问题。

## 3. Engineering Question

> 把模型提出的动作视为 untrusted input，执行边界应防御哪些无效、危险与注入动作？selection / invocation validation / execution 为什么必须分开记录？

## 4. 假设（可证伪）

**H1**：仅用标准库的最小执行器，能对 scripted fixture 的 tool call 做到：合法调用执行并回填；未知 / 危险 / 参数错误一律拒绝且**不执行**；拒绝原因可分类为 selection vs invocation validation。

## 5. 最小实验计划

### 5.1 范围与非目标

- 范围：解析 OpenAI-compatible `tool_calls` → schema 校验参数 → allowlist 执行纯函数 → 组装 `tool` message。
- 非目标：Registry（M1.6）、完整 Agent Loop（M1.7）、有副作用工具、并行多 tool call、prompt injection 实弹（只做危险名称拒绝）。

### 5.2 允许的工具（纯函数）

| name | 参数 schema | 行为 |
|---|---|---|
| `add` | `{a: number, b: number}` | 返回 `a+b` |
| `abs_diff` | `{a: number, b: number}` | 返回 `abs(a-b)` |

不在表内的名称一律视为未知或危险，**不调用任何 Python 函数**。

### 5.3 场景矩阵

scripted model fixture（不调用真实模型），每条是一段含 `tool_calls` 的 assistant message。

| # | 场景 | fixture | 预期 |
|---|---|---|---|
| t1 | 合法调用 | `add(a=2, b=3)` | execute，result=5，产出 tool message |
| t2 | 未知工具 | `name=lookup_secret` | reject: `selection:unknown_tool`，零执行 |
| t3 | 参数错误 | `add(a="two")` 缺 b、类型错 | reject: `invocation:invalid_args`，零执行 |
| t4 | 危险工具 | `name=run_shell` | reject: `selection:denied_tool`，零执行 |
| t5 | 结果回填 | t1 的 tool message 追加进 messages | 序列化后可见 `role=tool` + `tool_call_id` + content=`5` |

“零执行”用执行计数器证明：拒绝路径 `calls_executed=0`。

### 5.4 成功指标

1. t1 执行 1 次且结果正确；t2/t3/t4 `calls_executed=0`。
2. t2 与 t4 的 error class 都是 selection，但原因码不同（unknown vs denied）。
3. t3 是 invocation validation，不是 selection，也不是 execution（函数未进入）。
4. t5 回填消息可被 M1.2 `serialize_payload` 稳定序列化。
5. 累计 Evaluation Cases ≥ 27（现 22 + 5）。

## 6. Definition of Done

- 非法调用被拒绝且可观察；合法结果能回填下一轮。
- 学习者能解释：提出 ≠ 执行；selection / invocation validation / execution 三段边界；为什么危险工具不能靠 prompt 禁止。
- `PROGRESS.md` 更新为实际结果。仅生成代码不算完成。

## 7. Artifact

- `m1-5-tool-calling/`：executor + fixtures + runner。
- 可选：mock s18–s21 返回 scripted `tool_calls`（若走 HTTP）；也允许纯本地 fixture，不强制 HTTP。
- `eval_cases.jsonl` 追加 m1.5-*。

## 8. 实现决策（待用户确认）

1. **scripted fixture 本地解析**，不经真实模型；可用 mock HTTP 包一层，但执行器不依赖网络。
2. **allowlist 硬编码两纯函数**；未知与明确危险名单（`run_shell`）分开记原因。
3. **参数用 M1.4 同款最小校验**（required + type），失败不执行。
4. **执行计数器**作为“零执行”的可观察证据，而不是只看返回字符串。
