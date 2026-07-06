# AI 与软件技术情报 Agent

自动聚合 AI / LLM / Agent / 编程 / 云原生 / 开源 / 安全 等领域最新动态，自动分类、摘要并生成中文技术简报。

## 项目结构

```text
tech-intel-agent/
├── feeds.yaml          # 新闻源配置（6 大类源）
├── crawler.py          # RSS/API 采集
├── extractor.py        # 去重、清洗、正文抽取
├── classifier.py       # 关键词分类打标签
├── summarizer.py       # 大模型摘要（LLM + 本地降级）
├── storage.py          # SQLite + Chroma 向量库
├── report.py           # 日报 / 周报生成
├── app.py              # Streamlit Web 看板
├── main.py             # 单次完整运行入口
├── scheduler.py        # 定时任务
├── requirements.txt
└── .env.example
```

## 快速开始

### 1. 安装依赖

建议使用虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

首次运行会向量化模型会自动下载 `sentence-transformers` 模型。

### 2. 配置环境变量

```bash
cp .env.example .env
```

按需填写：

```env
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
SUMMARY_LANGUAGE=zh
MAX_CONTENT_TOKENS=3000
DATA_DIR=./data
```

未配置 `OPENAI_API_KEY` 时，摘要模块会使用本地降级摘要（标题 + 首段 + 关键句）。

### 3. 单次运行

```bash
python main.py
```

可选参数：

```bash
python main.py --no-body      # 不抓取原网页正文，仅使用 RSS 摘要
python main.py --no-summary   # 不调用 LLM 摘要
```

### 4. 定时采集

```bash
python scheduler.py --interval 4
```

或交给系统 cron（Linux/macOS）：

```cron
0 */4 * * * cd /path/to/tech-intel-agent && python main.py >> /tmp/tech_intel.log 2>&1
```

### 5. 启动 Web 看板

```bash
streamlit run app.py
```

打开浏览器访问 `http://localhost:8501`。

## 分类体系

| 分类 | 说明 |
|------|------|
| AI/LLM | 大模型、NLP、Transformer、多模态等 |
| AI Agent | Agent、RAG、工具调用、工作流编排 |
| 编程/工程 | 编程语言、框架、开发工具、软件工程 |
| 云原生 | 云计算、K8s、Serverless、可观测性 |
| 开源 | 开源项目、协议、社区动态 |
| 安全 | 漏洞、攻击、隐私、安全公告 |
| 研究 | 论文、数据集、基准、SOTA |
| 行业应用 | 医疗、金融、教育、机器人等落地场景 |
| 公司动态/投融资 | 产品发布、融资、合作、财报 |

## 自定义源

编辑 `feeds.yaml`，按以下格式新增源：

```yaml
engineering:
  name: 工程源
  sources:
    - name: 我的源
      url: https://example.com/feed.xml
      type: rss
      enabled: true
      max_items: 10
```

## 数据存储

- `data/news.db`：SQLite，保存标题、链接、分类、摘要、时间等元数据
- `data/chroma/`：向量库，支持语义搜索
- `data/reports/`：生成的日报 / 周报 Markdown

## 常见问题

**Q：没有 OpenAI API Key 能用吗？**
A：可以。未配置时会使用本地降级摘要，功能完整，只是摘要质量取决于原文。

**Q：如何降低 LLM 调用成本？**
A：调低 `.env` 中的 `MAX_CONTENT_TOKENS`，或添加 `--no-body` 不抓取全文。

**Q：如何增加分类？**
A：修改 `classifier.py` 中的 `CATEGORY_RULES` 和 `SOURCE_BIAS`。

## 设计文档

详细分析与设计文档见 `docs/` 目录：

- [docs/index.md](./docs/index.md) - 文档索引
- [docs/01-overview.md](./docs/01-overview.md) - 项目概述
- [docs/02-architecture.md](./docs/02-architecture.md) - 系统架构
- [docs/03-data-sources.md](./docs/03-data-sources.md) - 数据源分析
- [docs/04-modules.md](./docs/04-modules.md) - 模块设计
- [docs/05-data-model.md](./docs/05-data-model.md) - 数据模型
- [docs/06-classification-design.md](./docs/06-classification-design.md) - 分类算法
- [docs/07-summarization-design.md](./docs/07-summarization-design.md) - 摘要设计
- [docs/08-deployment.md](./docs/08-deployment.md) - 部署运维
- [docs/09-roadmap.md](./docs/09-roadmap.md) - 路线图

## License

MIT
