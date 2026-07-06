# 模块设计

## 1. crawler.py

### 职责
- 读取 `feeds.yaml` 配置。
- 使用 `feedparser` + `requests` 抓取 RSS/Atom 源。
- 标准化输出字段。
- 基于 `title + link` 的 MD5 做去重。

### 核心函数

| 函数 | 说明 |
|------|------|
| `load_feeds(path)` | 加载 YAML 源配置 |
| `_fetch_feed(source, group_name)` | 抓取单个源 |
| `crawl(feeds_path)` | 主入口，返回去重后的 item 迭代器 |
| `crawl_to_list(feeds_path)` | 返回 item 列表 |

### 输出字段

```python
{
    "id": "md5(title|link)",
    "title": "文章标题",
    "link": "文章链接",
    "summary": "RSS 原始摘要（可能含 HTML）",
    "published": datetime,
    "source": "源名称",
    "source_category": "分组名称",
    "raw": { ... }  # feedparser 原始 entry
}
```

### 设计要点
- 使用自定义 `User-Agent` 避免被部分源拦截。
- 时间解析优先使用 `published_parsed`，降级解析字符串。
- 每个源单独捕获异常，避免单点失败影响整体流程。

---

## 2. extractor.py

### 职责
- 清洗 RSS 摘要中的 HTML 标签和实体字符。
- 抓取原网页正文。
- 控制内容长度，为后续分类和摘要提供干净文本。

### 核心函数

| 函数 | 说明 |
|------|------|
| `clean_html(raw)` | 移除 HTML 标签、还原实体 |
| `fetch_url(url)` | 获取网页 HTML |
| `extract_full_text(url, html_text)` | 抽取正文 |
| `extract_item(item, fetch_body)` | 处理单个 item |

### 正文抽取策略

1. **主策略**：`trafilatura.extract()`
   - 优势：自动过滤导航、广告、评论等噪音。
   - 条件：抽取结果长度 > 100 字符才使用。
2. **降级策略**：BeautifulSoup 提取 `<p>` / `<article>` / `<section>` 段落。
3. **内容选择**：优先使用 `full_text`，否则使用 `clean_summary`。

### 输出字段

```python
{
    "clean_summary": "清洗后的摘要",
    "full_text": "原网页正文",
    "content": "最终用于分类/摘要的内容",
    "word_count": 1234
}
```

---

## 3. classifier.py

### 职责
- 基于关键词权重对文章进行分类。
- 输出主分类、置信度、命中标签。

### 核心函数

| 函数 | 说明 |
|------|------|
| `_score(text, rules)` | 按规则打分 |
| `classify(item)` | 对 item 分类 |
| `classify_item(item)` | 将分类结果写回 item |

### 设计要点
- 每个分类有独立的关键词列表和权重系数。
- 支持源类别加权（如 arXiv 更偏研究）。
- 匹配采用子串匹配，兼顾中英文。
- 置信度 = 最高分类得分 / 总得分。

---

## 4. summarizer.py

### 职责
- 生成结构化中文摘要：一句话、要点、影响、适合谁看。
- 支持 OpenAI API，无 Key 时自动降级。

### 核心函数

| 函数 | 说明 |
|------|------|
| `_llm_client()` | 创建 OpenAI 客户端 |
| `_trim_content(text)` | 截断正文以控制 token |
| `_parse_json(text)` | 解析 LLM 返回的 JSON |
| `_fallback_summary(...)` | 本地降级摘要 |
| `summarize(item)` | 生成摘要 |

### Prompt 设计

```text
System: 你是一位资深技术编辑...
请输出如下 JSON 结构：
{
  "one_sentence": "...",
  "key_points": ["...", "..."],
  "impact": "...",
  "audience": "..."
}
```

### 降级摘要

未配置 API Key 或调用失败时：
- 一句话：标题 + 首句
- 要点：正文前几句
- 影响/受众：提示未启用 LLM

---

## 5. storage.py

### 职责
- SQLite 持久化。
- Chroma 向量库存储与语义检索。
- 管理 Embedding 模型。

### 核心函数

| 函数 | 说明 |
|------|------|
| `upsert(item)` | 插入或跳过已存在记录 |
| `vectorize_unvectorized()` | 对未向量化的记录生成 Embedding |
| `get_recent(hours, category)` | 查询最近 N 小时记录 |
| `get_by_date_range(start, end)` | 按发布时间范围查询 |
| `search(query, top_k)` | 语义搜索 |
| `get_categories()` | 获取所有分类 |
| `get_stats()` | 统计信息 |

### 数据目录

```text
data/
├── news.db       # SQLite
├── chroma/       # Chroma 向量库
└── reports/      # Markdown 报告
```

---

## 6. report.py

### 职责
- 按分类聚合文章。
- 生成 Markdown 日报/周报。

### 核心函数

| 函数 | 说明 |
|------|------|
| `generate_report(items, title)` | 生成 Markdown 文本 |
| `daily_report(storage, hours)` | 生成日报 |
| `weekly_report(storage)` | 生成周报 |

### 报告结构

```markdown
# AI 与软件技术情报日报 (YYYY-MM-DD)

## AI/LLM（N 条）
### [标题](链接)
- 来源：... | 分类：... | 时间：...
- 一句话：...
- 要点：...
- 影响：...
- 适合谁看：...

## AI Agent（N 条）
...
```

---

## 7. app.py

### 职责
- Streamlit Web 看板。
- 支持分类筛选、时间范围筛选、语义搜索。

### 页面结构

1. **顶部**：标题、简介、统计卡片。
2. **侧边栏**：分类选择、时间范围、搜索框。
3. **主区域**：文章卡片列表，可展开要点。

### 交互

- 选择分类后只显示该分类文章。
- 输入搜索词后使用 Chroma 向量检索。
- 每条文章提供原文链接。

---

## 8. main.py

### 职责
- 编排完整流程：采集 → 抽取 → 分类 → 摘要 → 存储 → 向量化 → 日报。

### 运行参数

| 参数 | 说明 |
|------|------|
| `--feeds` | 指定源配置文件 |
| `--no-body` | 不抓取原网页正文 |
| `--no-summary` | 不调用 LLM 摘要 |

---

## 9. scheduler.py

### 职责
- 定时触发 `main.run_once()`。
- 支持命令行指定间隔小时数。

### 使用方式

```bash
python scheduler.py --interval 4
```
