# Projects

本目录保存需要长期维护、可运行、可测试、可评测和可演示的 AI Agent Engineering 作品。

## 项目准入标准

一个方向进入 `projects/` 前，至少应具备：

- 明确的目标用户与真实问题，而不是“使用某框架”的技术演示。
- 可观察的成功标准、非目标和主要风险。
- 至少一个来自 `playground/` 或等价证据支持的核心方案。
- 可以独立安装与运行的边界，不直接依赖实验目录内部代码。

## 项目最低要求

- 项目级 README：问题、能力、架构、setup、run、test、eval、demo、限制。
- 独立依赖清单与 lockfile（工具支持时）。
- `.env.example`（仅在需要环境变量时）。
- 对关键行为、失败恢复和已修复 bug 的测试。
- 可重复的评测与至少一个 baseline。
- 涉及重要取舍时，在 `docs/decisions/` 记录 ADR。
- 清楚的状态：`idea`、`prototype`、`active`、`stable` 或 `archived`。

## 新建项目

```bash
cp -R projects/_template projects/<project-name>
```

复制后替换所有占位内容，并在下方项目清单登记。

## 项目清单

| Project | Status | User problem | Demo | Last updated |
|---|---|---|---|---|
| _暂无_ | — | — | — | — |
