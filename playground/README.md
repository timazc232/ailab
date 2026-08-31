# Playground

`playground/` 用于低成本、短周期、围绕单一问题的实验。这里允许探索和失败，但不允许无法运行、没有问题定义或没有结论的代码堆积。

## 主题目录

- [`evals/`](evals/)：评测数据、指标、judge 与回归实验
- [`mcp/`](mcp/)：MCP client/server、transport 与互操作实验
- [`memory/`](memory/)：working / episodic / semantic memory 实验
- [`rag/`](rag/)：ingestion、retrieval、reranking 与 grounding 实验

出现新主题时，仅在有真实实验后创建对应目录。

## 新建实验

```bash
cp -R playground/_template playground/<topic>/YYYY-MM-DD-<short-name>
```

随后：

1. 在实验 README 中写清问题、假设、基线和成功指标。
2. 保持依赖与命令独立，不引用其他实验内部代码。
3. 先用 fixture/mock 跑通，再决定是否调用真实服务。
4. 保存小型可审查结果，记录环境、模型和配置。
5. 完成后标记状态并写结论；失败也必须说明学到了什么。

## 升级与归档

当实验解决了稳定的用户问题、需要持续维护，或已有明确工程化价值时，将其升级到 `projects/`：重新建立清晰边界、测试、文档和依赖，不让项目直接依赖实验路径。

长期没有验证价值的实验可标记为 `archived`。删除前先确认其中没有尚未沉淀的结论。
