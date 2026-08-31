# <Project Name>

> 用一句话说明：为哪类用户解决什么问题，以及核心差异。

## Status

- **Lifecycle**：idea | prototype | active | stable | archived
- **Last updated**：YYYY-MM-DD
- **Owner**：TBD

## Problem

### Target user

TBD

### Problem statement

TBD

### Success criteria

- TBD

### Non-goals

- TBD

## Capabilities

- TBD

## Demo

```bash
# 最短演示命令
```

补充预期输入、输出、截图或录屏位置。演示不得依赖未说明的本机状态。

## Architecture

```text
Input → Agent/Workflow → Tools/Knowledge → Validation → Output
```

说明关键组件、状态边界、外部依赖和失败恢复策略。重大决策写入 [`docs/decisions/`](docs/decisions/)。

## Repository Layout

```text
.
├── README.md
├── src/          # 按实际语言调整
├── tests/
└── docs/
```

只保留实际存在的目录，避免空架构。

## Prerequisites

- TBD

## Setup

```bash
# 安装依赖
```

如果需要环境变量，提供 `.env.example` 并逐项说明用途；不要提交真实凭据。

## Run

```bash
# 启动或执行
```

## Test

```bash
# 单元/集成测试
```

## Evaluation

### Dataset and baseline

TBD

### Metrics

- Task success：TBD
- Quality：TBD
- Latency：TBD
- Token / cost：TBD
- Safety / failure rate：TBD

```bash
# 可重复执行的评测命令
```

## Results

| Version | Dataset | Quality | Latency | Cost | Notes |
|---|---|---:|---:|---:|---|
| baseline | TBD | TBD | TBD | TBD | TBD |

## Safety and Privacy

说明工具权限、数据处理、审批点、日志脱敏和删除策略。

## Known Limitations

- TBD

## Roadmap

- [ ] 最小端到端闭环
- [ ] 自动测试
- [ ] 基线评测
- [ ] 失败分析
- [ ] 可复现演示

## References

- TBD
