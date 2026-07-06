# 数据模型设计

## SQLite 表结构

### items 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT PRIMARY KEY | MD5(title\|link)，全局唯一 |
| `title` | TEXT | 文章标题 |
| `link` | TEXT | 原文链接 |
| `summary` | TEXT | 原始摘要（兼容字段） |
| `clean_summary` | TEXT | 清洗后的摘要 |
| `content` | TEXT | 用于分类/摘要的最终内容 |
| `published` | TEXT | 发布时间（ISO 格式） |
| `source` | TEXT | 源名称 |
| `source_category` | TEXT | 源分组名称 |
| `category` | TEXT | 主分类 |
| `confidence` | REAL | 分类置信度 |
| `tags` | TEXT | JSON 数组，命中标签 |
| `summary_json` | TEXT | JSON 结构化摘要 |
| `collected_at` | TEXT | 采集时间（ISO 格式） |
| `vectorized` | INTEGER | 是否已向量化（0/1） |

### 索引

```sql
CREATE INDEX idx_items_published ON items(published);
CREATE INDEX idx_items_category ON items(category);
```

### 建表 SQL

```sql
CREATE TABLE IF NOT EXISTS items (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    summary TEXT,
    clean_summary TEXT,
    content TEXT,
    published TEXT,
    source TEXT,
    source_category TEXT,
    category TEXT,
    confidence REAL,
    tags TEXT,
    summary_json TEXT,
    collected_at TEXT,
    vectorized INTEGER DEFAULT 0
);
```

## Chroma 向量库设计

### Collection

- **名称**：`news`
- **向量维度**：取决于 Embedding 模型
  - 当前使用 `paraphrase-multilingual-MiniLM-L12-v2`，维度为 **384**。

### 存储内容

| 字段 | 说明 |
|------|------|
| `ids` | 与 SQLite `id` 一致 |
| `documents` | `title + clean_summary + content` 拼接文本（截断 2000 字符） |
| `embeddings` | 句子向量 |
| `metadatas` | `{title, source}` |

### 向量化流程

1. `main.py` 写入 SQLite 后，调用 `storage.vectorize_unvectorized()`。
2. 查询 `vectorized=0` 的记录。
3. 使用 `sentence-transformers` 批量编码。
4. 写入 Chroma Collection。
5. 更新 SQLite `vectorized=1`。

## 数据流向

```text
RSS/网页
  → crawler.py (item dict)
  → extractor.py (增加 clean_summary, content)
  → classifier.py (增加 category, confidence, tags)
  → summarizer.py (增加 summary_json)
  → storage.py
      ├── SQLite 写入元数据
      └── Chroma 写入向量
  → report.py / app.py 读取展示
```

## 数据保留策略

当前版本不做自动清理，所有数据永久保留。后续可在 `scheduler.py` 中增加：

- 按时间清理旧数据。
- 按分类保留 Top N。
- 归档机制。

## 备份建议

定期备份 `data/` 目录即可：

```bash
tar czvf tech-intel-backup-$(date +%Y%m%d).tar.gz data/
```
