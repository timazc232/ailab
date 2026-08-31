# Evaluation Playground

本目录用于验证 agent 评测方法，包括 dataset/fixture 设计、确定性检查、rubric、LLM-as-judge、人工校准和回归测试。

每个实验应至少说明：被评对象、基线、数据划分、指标、judge 配置、重复次数和失败分类。避免用开发样例同时充当最终测试集；使用 LLM judge 时记录模型、prompt、随机参数，并尽可能用人工样本校准。

从 [`../_template/`](../_template/) 复制新实验。
