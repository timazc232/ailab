# Phase 1 复盘（Day 30 Checkpoint）— agent-lab

> 日期：2026-09-09。学习者综合复述已验证通过（9 Module 失败模式、串联边界、可观察信号、失败记录价值、Phase 2 继承层）。

## 1. 验收对照（ROADMAP 通过条件）

| 条件 | 结果 |
|---|---|
| 原生 HTTP baseline 覆盖全部核心机制 | ✅ M1.1–M1.9，Python 标准库，零第三方依赖，无 Agent Framework |
| ≥15 个有意义可重复 Evaluation Cases | ✅ 55 条（`playground/agent-lab/eval_cases.jsonl`），含失败样例 |
| 学习者能说明每层为什么存在、失败模式与可观察信号 | ✅ 2026-09-09 综合复述通过（含纠偏） |
| 没有用大型框架隐藏核心机制 | ✅ |
| 代码已运行、有 Evaluation 与机制解释 | ✅ 每个 Module 均 runner 实测 + 用户解释后关闭 |

**判定：Phase 1（Days 1–30）通过。**

## 2. 各层防住的失败（学习者复述 + 纠偏后）

| Module | 防住的失败 | 核心机制 | 可观察信号 |
|---|---|---|---|
| M1.1 | HTTP 错误 / 模型错误 / 超时混为一谈；HTTP 200 ≠ 任务成功 | 分类重试、finish_reason 检查 | outcome 分类、retry 计数 |
| M1.2 | 以为模型记得历史（连续性是重发历史造出的）；截断后误用 | 确定性序列化、fail-fast、显式截断 Policy | 序列化字节稳定 |
| M1.3 | 不完整流 / 跨块 UTF-8 / 异常 EOF 当成完整结果 | 增量解码、finish_reason + [DONE] 双条件 | 重组结果与非流式一致 |
| M1.4 | 输出不符 schema；无条件反复重试 | 硬契约校验、分类重试、拒绝可见 | ValidationResult 分类 |
| M1.5 | 把"模型提出调用"当成"工具已执行" | allowlist、参数校验、执行计数器 | calls_executed=0 证据 |
| M1.6 | 工具未注册、权限越界、分发规则散落 | ToolSpec metadata、lookup→auth→validation→execution | 零执行 + 权限过滤 inventory |
| M1.7 | 死循环、恢复时重复副作用、状态漂移 | 终止原因、checkpoint（逻辑状态）、resume 零重放 | termination_reason、资源 opened/closed |
| M1.8 | 规划/反思无限消耗；高风险动作绕过审批 | 策略成本对比、Reflection 上限、审批门 | model decisions 数、审批前副作用=0 |
| M1.9 | 错误重试失控、超 deadline、重复副作用、无法还原过程 | 分类重试、deadline 前置检查、幂等门控、trace | trace JSONL（run_id/seq/attempt） |

## 3. 跨模块串联（复述确认）

```text
HTTP 接入 → 请求解析校验 → 构造 messages/context（M1.2）
  → 模型调用（M1.1/M1.3 包裹 retry/deadline）→ 解析输出（M1.4 schema）
  → 识别 tool call（M1.5 提出≠执行）
  → Registry lookup → authorization → validation（M1.6）
  → Agent 状态机判断下一步（M1.7，终止原因）
  → Planning/Reflection（M1.8，上限与成本）
  → HITL 审批（M1.8，副作用前暂停）
  → 幂等检查 + Dispatch 执行（M1.9 + M1.6 执行计数）
  → 写入 trace 与最终状态（M1.9）→ 返回结果
```

纠偏记录：Registry 内部先 authorization 后 validation（防 schema 泄漏）；retry/deadline 是包裹模型与工具调用的横切层，不是末端单点。

## 4. 失败教训（真实 runner_error，均已修复并保留记录）

1. **Day 8**：三个非法状态转换（created→completed、running 重复启动、paused→cancelled 未定义）——生命周期扩展必须同步更新状态机定义。
2. **Day 9**：打印格式化 bug（outcome=None）——runner 输出契约也要防 None。
3. **Day 7（实现中）**：runner 导入路径缺 sys.path 插入——目录间依赖要显式。
4. **Day 2-9 多次**：edit 工具 oldText 匹配失败导致整批回滚——文档更新前先读当前文本。

价值：失败暴露真实边界；是回归测试依据（Day 8 状态机改动后重跑 M1.6/M1.7）；AGENTS.md 要求不得静默覆盖不利结果。

## 5. 已知限制清单（带入 Phase 2 视野）

- 虚拟时钟 / scripted model：无真实时延与真实模型质量数据。
- in-flight tool 的 exactly-once、幂等键机制未实现（只做了门控）。
- trace 未与 M1.7 loop 集成；无持久化存储。
- schema 子集小；semantic validation 未做（留 M3.2）。
- multi-agent 明确非目标；approval 超时未实现。
- 并发注册、动态卸载、checkpoint schema migration 未覆盖。

## 6. Phase 2 继承（学习者判断 + 补充）

- **M1.9（首选）**：故障诊断必须保留完整证据链、区分暂时/永久故障、控制重试与修复动作、避免重复副作用。
- 补充：M1.6 权限边界 + M1.8 审批门在运维环境同等关键——高风险动作（重启/删除服务）强制审批，且只作用于隔离 Docker Test Lab（AGENTS.md 硬约束）。

## 7. Phase 2 前置确认（已于 2026-09-09 确认）

1. **首批用户**：作者本人。目标环境：当前服务器上搭建隔离 Docker Test Lab（参照真实拓扑复刻，宿主机服务不是注入对象）；远端 grok bot 机器作为后期扩展目标（需先提供其服务清单）。
2. **技术栈优先级**：① Linux 进程 / Docker / Logs（M2.3 基础层）→ ② Nginx（Web 层）→ ③ PostgreSQL（DB 层，备选 MySQL）。
3. **许可证**：Apache-2.0（专利授权 + 运维工具主流选择）。
4. **模型**：DeepSeek 官方 API，最新 `deepseek-chat`；Phase 2 全程 scripted 零真实调用；Phase 3 接入时另定预算上限与 per-run cost 记录。
