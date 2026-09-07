# Day 6 计划 — M1.6 Tool Registry / Dispatch

> 状态：**Day 6 进行中（2026-09-07）**。2026-09-05～06 无学习记录，不补写。
> 开工参数沿用 Day 1：Python 3.12、仅标准库、纯本地 fixture、禁止真实 API 与外部费用。预计约 3 小时。

## 1. 学什么

- **Tool Registry（工具注册表）**：集中保存 ToolSpec（名称、说明、参数 schema、权限 metadata、是否有副作用、执行函数）。
- **Dispatch（分派）**：收到 tool call 后按 name 查找 ToolSpec，并按统一顺序执行 lookup → authorization → args validation → invoke → normalize result/error。
- **Registration-time validation（注册期校验）**：重复名称或命名冲突在启动/注册时拒绝，不能静默覆盖原工具。
- **Permission metadata（权限元数据）**：描述调用工具需要什么权限；不仅执行时检查，工具 inventory 也应按调用者权限过滤。
- **执行异常**：参数合法且函数已进入，但内部抛错；与 selection / invocation validation 分开记录。

## 2. 为什么重要

M1.5 的 `name → function` allowlist 能保护两个工具，但工具增加后，schema、权限、说明和执行逻辑会散落在多处分支。Registry 把“发现、治理、分派”集中成唯一边界，避免 `if name == ...` 无限增长，也为 M1.7 Agent Loop 提供稳定工具接口。

## 3. Engineering Question

> Registry 比普通函数映射多提供了什么工程价值？权限、schema、执行错误为什么必须在同一 dispatch 边界内统一处理？

## 4. 假设（可证伪）

**H1**：一个最小 registry 能做到：注册与 inventory 确定；重复名称拒绝且不覆盖；未知 / 参数错误 / 未授权均零执行；合法调用正确执行；函数内部异常被归类为 execution failure；不同调用者看到的 inventory 符合权限。

## 5. 最小实验计划

### 5.1 ToolSpec

字段：`name`、`description`、`args_schema`、`required_permissions`、`side_effect`、`function`。

工具：

| name | 参数 | 权限 | 副作用 | 行为 |
|---|---|---|---|---|
| `add` | a/b: number | 无 | false | a+b |
| `divide` | a/b: number | 无 | false | a/b（b=0 时真实 execution exception） |
| `restricted_report` | name: string | `report:read` | false | 返回合成报告，不访问真实数据 |

### 5.2 Dispatch 顺序

1. lookup（未知工具拒绝）
2. authorization（先鉴权，避免向未授权者泄漏参数细节）
3. args validation（required / type / additionalProperties=false）
4. invoke（实际函数入口，计数器 +1）
5. normalize（统一 success / failure 结果）

### 5.3 场景矩阵

| # | 场景 | 预期 |
|---|---|---|
| r1 | 注册 3 工具；dispatch add(2,3) | success=5；add executed=1 |
| r2 | 用不同函数重复注册 name=add | registration:duplicate_name；原 add 不被覆盖 |
| r3 | dispatch unknown_tool | lookup:unknown_tool；总执行=0 |
| r4 | add(a="two") / 缺 b | validation:invalid_args；add executed=0 |
| r5 | 无 report:read 权限调用 restricted_report | authorization:denied；该工具 executed=0 |
| r6 | divide(10,0) | execution:tool_error；divide executed=1 |
| r7 | 普通用户 vs 有权限用户 inventory | 顺序稳定；普通用户看不到 restricted_report，有权限用户可见 |

### 5.4 成功指标

1. r1–r7 全部命中预期；重复运行结果一致。
2. r2 原工具行为仍是 add(2,3)=5，证明未被覆盖。
3. r3/r4/r5 执行计数均 0；r6 执行计数为 1。
4. inventory 按 name 排序且按权限过滤。
5. Evaluation 累计 ≥34（现 27 + 7）。

## 6. Definition of Done

- dispatch 确定且有测试；未知/未授权/参数非法不执行；执行异常可观察。
- 学习者能解释 Registry 相对普通 dict 的额外价值，以及 lookup / authorization / validation / execution 的边界。
- PROGRESS 更新为实际结果。仅生成代码不算完成。

## 7. Artifact

- `m1-6-tool-registry/`：ToolSpec、Registry、DispatchResult、fixtures/runner。
- 共享 `eval_cases.jsonl` 追加 m1.6-r1..r7。

## 8. 实现决策（待用户确认）

1. `ToolSpec` 用 frozen dataclass（注册后 metadata 不可变）。
2. 重复名称硬拒绝，绝不覆盖。
3. authorization 在参数校验之前，减少未授权调用者获得的 schema 细节。
4. inventory 按 name 排序并按调用者权限过滤；执行计数按 tool 记录。
