# Memory Playground

本目录用于 agent memory 实验，包括 working、episodic、semantic memory，以及写入、检索、压缩、遗忘和冲突处理策略。

实验应区分“上下文中的状态”和“跨会话持久记忆”，定义写入条件、检索指标、时间范围、隐私策略和删除方式。评测不仅看召回，还要关注错误记忆、过期信息、污染和 token/延迟成本。

从 [`../_template/`](../_template/) 复制新实验。
