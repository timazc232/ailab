# RAG Playground

本目录用于 retrieval-augmented generation 的可控实验，包括 ingestion、chunking、embedding、retrieval、reranking、context assembly、grounding 和 citation。

每个实验应保留无检索或简单检索 baseline，并分别衡量 retrieval 与 generation；记录语料版本、切分策略、top-k、过滤条件、模型配置和失败样例。不要只用主观“回答看起来更好”作为结论。

从 [`../_template/`](../_template/) 复制新实验。
