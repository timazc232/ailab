# AI Lab

`~/ai-lab` 是一个长期的 **AI Agent Engineering 学习、实验与作品开发工作区**。这里把系统学习、知识沉淀、可控实验和作品工程串成一条可追溯路径，而不是单纯收集教程或框架示例。

> 开始任何工作前，请先阅读 [`AGENTS.md`](AGENTS.md)。它定义了目录边界、实验纪律、可复现性、安全和完成标准。

## 工作区目标

- 建立对 agent loop、tool use、memory、RAG、MCP、evaluation、observability 与 safety 的系统理解。
- 用小实验验证概念，而不是仅凭文档或直觉形成结论。
- 将成熟实验升级为可运行、可测试、可演示的作品项目。
- 保留决策、失败、指标和复盘，使学习过程可以复用与审计。

## 目录地图

| 路径 | 说明 |
|---|---|
| [`90-days/`](90-days/) | 90 天学习路线、每日记录和阶段复盘 |
| [`knowledge/`](knowledge/) | 长期有效的知识笔记与主题索引 |
| [`playground/`](playground/) | evals、MCP、memory、RAG 等方向的小型实验 |
| [`projects/`](projects/) | 面向作品集的长期项目及项目模板 |
| [`templates/`](templates/) | 日志、知识笔记、复盘和 ADR 模板 |
| [`AGENTS.md`](AGENTS.md) | 人类与 AI agents 的根级工作规则 |

## 推荐闭环

```text
学习目标（90-days）
        ↓
概念提炼（knowledge）
        ↓
单点验证（playground）
        ↓
工程化与展示（projects）
        ↓
评测、复盘，再回写知识与计划
```

同一主题不必机械地复制四份内容：计划记录“为什么现在学”，知识库记录“长期成立的理解”，实验记录“如何验证”，项目记录“如何交付”。

## 快速开始

1. 阅读 [`AGENTS.md`](AGENTS.md)。
2. 在 [`90-days/ROADMAP.md`](90-days/ROADMAP.md) 选择当前阶段并定义本周输出。
3. 学习记录使用 [`templates/daily-log.md`](templates/daily-log.md)。
4. 新知识使用 [`templates/knowledge-note.md`](templates/knowledge-note.md)，并登记到 [`knowledge/INDEX.md`](knowledge/INDEX.md)。
5. 新实验复制 [`playground/_template/`](playground/_template/)，建立独立目录。
6. 成熟方向复制 [`projects/_template/`](projects/_template/)，补齐运行、测试、评测和演示说明。

示例：

```bash
cp templates/daily-log.md 90-days/daily/2026-01-15.md
cp -R playground/_template playground/evals/2026-01-15-tool-selection-baseline
cp -R projects/_template projects/my-agent-project
```

复制模板后，立即替换所有占位符，并删除不适用章节。

## 全局约定

- 文档说明默认中文；代码标识符、命令和配置键使用英文。
- 日期使用 `YYYY-MM-DD`，普通目录和文档名使用 `kebab-case`。
- 每个可运行单元维护自己的依赖、配置、README 和测试入口。
- 凭据只保存在未追踪的本地 `.env` 中；仓库只保留 `.env.example`。
- 结论必须能追溯到来源、代码、数据或评测结果；负面结果同样有价值。
- 先做最小闭环，确认价值后再抽象、扩展或引入框架。

## 当前状态

- [x] 初始化根级协作规则与版本控制
- [x] 建立学习、知识、实验、项目和模板的基础结构
- [ ] 确定首个 90 天周期的开始日期与每周可投入时间
- [ ] 选择第一个基线实验
- [ ] 定义第一个作品项目的用户问题与验收指标
