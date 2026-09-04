# agent-lab

90 天路线 Stage 1 的底层 Agent mechanism 实验区（规划见 [90-days/ROADMAP.md](../../90-days/ROADMAP.md)）。
每个实验自带运行说明；不引入大型 Agent Framework，优先标准库。

## 当前实验

### m1-1-llm-client — Day 1 / M1.1 LLM API Fundamentals / LLM Client

- **目标**：验证仅用 Python 3.12 标准库的同步 client，能否仅凭显式契约信号把每次请求归入
  `success / transport / http-api-protocol / model-result-condition` 之一，
  并解释 HTTP success != model task success。
- **契约与计划**：[90-days/daily/day-01-llm-api-fundamentals-plan.md](../../90-days/daily/day-01-llm-api-fundamentals-plan.md) §10。
- **前置条件**：Python 3.12（仅标准库）；无外部依赖；无真实网络访问（仅 loopback）。
- **状态**：M1.1 Day 1 闭环完成（2026-08-31）：self-test 7/7、runner 21/21、用户解释确认、首批 7 个 Evaluation Cases 归档（共享日志 [`eval_cases.jsonl`](../eval_cases.jsonl)）。
- 2026-09-01：client 新增向后兼容参数 `request_body` 与记录字段 `response_content`（M1.2 复用）；mock 新增 `s8` echo 场景；Day 1 回归 21/21 通过。

#### 运行（mock server）

```bash
cd m1-1-llm-client
python3 mock_server.py                # 前台运行，监听 127.0.0.1:8931
python3 mock_server.py --self-test    # 逐场景自检 fixture contract
python3 run_scenarios.py              # 进程内自动启动 mock，7 场景 × 3 次，写 observations.jsonl
```

#### 验证

- `--self-test` 应输出 `PASS: 17/17 fixtures match the contract`（含 s8 echo、s9–s11 流式、s12–s17 结构化输出）。
- `run_scenarios.py` 应输出 `PASS`：21 条观察 outcome 一致且全部命中 §10.2 预测（退出码 0）。
- 场景由请求头 `X-Mock-Scenario: s1..s17` 选择；无此头或未知值返回 400。Day 1 runner 仍固定跑 s1–s7。

#### 已知限制

- Day 1 范围仍是 s1–s7；s8–s11 为后续模块扩展。无 TLS。
- 不校验 Authorization 头（Day 1 client 使用占位假 key，真实认证不属于本模块）。
- s6 会占用工作线程 5s；仅适合单人本地实验。

#### 下一步

已由 M1.2 接续（见下）。

### m1-2-messages — Day 2 / M1.2 Messages / Context

- **目标**：显式构造 + 字节确定序列化 + 预算截断 Policy；用 `s8` echo 实验证「模型看到的 = 你发送的」，并区分 context 与 memory。
- **契约与计划**：[90-days/daily/day-02-messages-context-plan.md](../../90-days/daily/day-02-messages-context-plan.md)。
- **运行**：

  ```bash
  cd m1-2-messages
  python3 run_context_scenarios.py   # 进程内启动 mock（端口 8932），跑 e1–e5
  ```

- **验证**：输出 `PASS`（5/5）；原始观察 `observations.jsonl` 仅本地保留；Evaluation 追加至共享 [`eval_cases.jsonl`](../eval_cases.jsonl)（m1.2-e1..e5）。
- **已知限制**：字符预算是 proxy 非 token；截断 Policy 是确定性 baseline（语义去噪留给 M4.2/M4.4）。
- **状态**：M1.2 闭环完成（2026-09-01）：runner 5/5、用户解释确认。

### m1-3-streaming — Day 3 / M1.3 Streaming

- **目标**：增量 SSE parser 在任意分块（含跨 chunk UTF-8）下重组结果与非流式一致；断流/取消绝不静默完整。
- **契约与计划**：[90-days/daily/day-03-streaming-plan.md](../../90-days/daily/day-03-streaming-plan.md)。
- **运行**：

  ```bash
  cd m1-3-streaming
  python3 run_stream_scenarios.py   # 进程内启动 mock（端口 8933），跑 f1–f5
  ```

- **验证**：输出 `PASS`（5/5）；原始观察 `observations.jsonl` 仅本地保留；Evaluation 追加至共享 [`eval_cases.jsonl`](../eval_cases.jsonl)（m1.3-f1..f5）。
- **已知限制**：无主动 backpressure 控制；无 tool-call 流式事件；mock 用 Connection: close 而非 chunked transfer。
- **状态**：M1.3 闭环完成（2026-09-02）：runner 5/5、用户解释确认。

### m1-4-structured-output — Day 4 / M1.4 Structured Output

- **目标**：最小 schema 校验；非法输出不得进入下游；缺字段/错类型最多 1 次受控重试。
- **契约与计划**：[90-days/daily/day-04-structured-output-plan.md](../../90-days/daily/day-04-structured-output-plan.md)。
- **运行**：

  ```bash
  cd m1-4-structured-output
  python3 run_schema_scenarios.py   # 进程内启动 mock（端口 8934），跑 g1–g5
  ```

- **验证**：输出 `PASS`（5/5）；Evaluation 追加至共享 [`eval_cases.jsonl`](../eval_cases.jsonl)（m1.4-g1..g5）。
- **已知限制**：schema 子集仅 object/required/type/enum/additionalProperties=false；无 semantic validation。
- **状态**：M1.4 闭环完成（2026-09-03）：runner 5/5、用户解释确认。

### m1-5-tool-calling — Day 5 / M1.5 Tool Calling

- **目标**：模型仅提出动作；本地可信执行器按 selection → invocation validation → execution 分层处理，拒绝路径零执行。
- **契约与计划**：[90-days/daily/day-05-tool-calling-plan.md](../../90-days/daily/day-05-tool-calling-plan.md)。
- **运行**：

  ```bash
  cd m1-5-tool-calling
  python3 run_tool_scenarios.py   # 跑 t1–t5，仅本地 scripted fixtures
  ```

- **验证**：输出 `PASS`（5/5）；t2/t3/t4 `calls_executed=0`；Evaluation 追加至共享 [`eval_cases.jsonl`](../eval_cases.jsonl)（m1.5-t1..t5）。
- **已知限制**：只支持单 tool call；allowlist 硬编码；工具为纯函数；真实执行异常留到 M1.6。
- **状态**：M1.5 闭环完成（2026-09-04）：runner 5/5、拒绝路径零执行、用户解释确认。
