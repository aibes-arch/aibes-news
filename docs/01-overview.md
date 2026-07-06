# 项目概述

## 项目定位

本项目是一个 **AI 与软件技术情报 Agent**，目标是通过自动化的方式持续追踪 AI、大语言模型（LLM）、智能体（Agent）、编程工程、云原生、开源、安全等领域的技术动态，并将这些内容去重、分类、摘要后，生成中文技术简报，最终通过 Web 看板、日报/周报等形式呈现。

## 核心目标

1. **自动化采集**：每天定时从 6 大类技术源抓取最新内容。
2. **智能分类**：将文章自动归类到 AI/LLM、Agent、编程/工程、云原生、开源、安全、研究、行业应用、公司动态/投融资等类别。
3. **结构化摘要**：为每篇文章生成一句话总结、核心要点、潜在影响、目标受众。
4. **可检索存储**：使用 SQLite 保存元数据，使用 Chroma 向量库存储 Embedding，支持语义搜索。
5. **多形态输出**：生成 Markdown 日报/周报，并提供 Streamlit Web 看板。

## 适用场景

- 个人技术雷达：快速了解当日技术热点。
- 团队晨会材料：自动生成简报分享。
- 投资/研究人员：追踪 AI 公司与产品动态。
- 开发者社区运营：持续产出精选内容。

## 技术栈

| 层级 | 技术 |
|------|------|
| 采集 | `feedparser`、`requests` |
| 正文抽取 | `trafilatura`、`BeautifulSoup` |
| 分类 | 关键词加权规则 + 源类别加权 |
| 摘要 | OpenAI API / 本地降级摘要 |
| 向量库 | `Chroma` + `sentence-transformers` |
| 存储 | `SQLite` |
| 看板 | `Streamlit` |
| 调度 | `schedule` / 系统 Cron |

## 项目目录

```text
tech-intel-agent/
├── feeds.yaml          # 源配置
├── crawler.py          # 采集器
├── extractor.py        # 正文抽取与清洗
├── classifier.py       # 分类器
├── summarizer.py       # 摘要器
├── storage.py          # 存储层
├── report.py           # 报告生成
├── app.py              # Web 看板
├── main.py             # 单次运行入口
├── scheduler.py        # 定时调度
├── requirements.txt
├── .env.example
├── README.md
└── docs/               # 本文档
```

## 设计原则

- **最小可用**：第一版先跑通 RSS 采集 → 分类 → 摘要 → 存储 → 报告的全流程。
- **可扩展**：`feeds.yaml`、分类规则、摘要 Prompt 均可独立配置。
- **成本可控**：支持无 API Key 的降级摘要，支持按 token 截断正文以控制 LLM 成本。
- **本地优先**：数据、向量库、报告均存储在本地 `data/` 目录。
