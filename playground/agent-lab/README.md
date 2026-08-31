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
- **状态**：mock server、client、runner 已实现；runner 实测 21/21 通过（7 场景 × 3 次全部一致且命中预测）；Evaluation 归档待用户解释观察结果。

#### 运行（mock server）

```bash
cd m1-1-llm-client
python3 mock_server.py                # 前台运行，监听 127.0.0.1:8931
python3 mock_server.py --self-test    # 逐场景自检 fixture contract
python3 run_scenarios.py              # 进程内自动启动 mock，7 场景 × 3 次，写 observations.jsonl
```

#### 验证

- `--self-test` 应输出 `PASS: 7/7 fixtures match the contract`：
  s1/s2/s6/s7 → 200，s3 → 401，s4 → 429，s5 → 500；s6 延迟约 5s。
- `run_scenarios.py` 应输出 `PASS`：21 条观察 outcome 一致且全部命中 §10.2 预测（退出码 0）。
- 场景由请求头 `X-Mock-Scenario: s1..s7` 选择；无此头或未知值返回 400。

#### 已知限制

- mock 只覆盖 Day 1 的 7 个固定场景；无 TLS、无 chunked 编码、无流式。
- 不校验 Authorization 头（Day 1 client 使用占位假 key，真实认证不属于本模块）。
- s6 会占用工作线程 5s；仅适合单人本地实验。

#### 下一步

用户解释观察结果（学习闭环「解释」步）→ 归档首批 7 个 Evaluation Cases → M1.1 Definition of Done 检查。
