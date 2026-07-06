# 摘要设计

## 摘要目标

将长文转化为结构化中文简报，包含四个维度：

1. **一句话总结**：快速了解核心信息。
2. **核心要点**：3-5 条关键信息。
3. **潜在影响**：对行业、开发者、公司的影响。
4. **适合谁看**：目标读者群体。

## 摘要流程

```text
输入：item（title, content）
  │
  ▼
内容截断（MAX_CONTENT_TOKENS ≈ 3000 tokens）
  │
  ▼
检查 OPENAI_API_KEY
  │
  ├── 有 Key ──► 调用 OpenAI ChatCompletion
  │              输出 JSON 结构
  │
  └── 无 Key ──► 本地降级摘要
                 标题 + 首段 + 关键句
```

## LLM Prompt 设计

### System Prompt（中文）

```text
你是一位资深技术编辑，负责为 AI 与软件工程领域的新闻生成中文简报。
请对用户提供的新闻标题和正文，用中文输出如下 JSON 结构（不要包含 markdown 代码块）：
{
  "one_sentence": "一句话总结全文核心信息",
  "key_points": ["要点1", "要点2", "要点3"],
  "impact": "对行业、开发者或公司的潜在影响",
  "audience": "适合谁看，例如后端工程师、AI 研究者、创业者、安全工程师等"
}
只输出 JSON，不要解释。
```

### User Prompt

```text
标题：{title}

正文：
{content}
```

### 模型参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `model` | gpt-3.5-turbo | 默认模型，可配置 |
| `temperature` | 0.3 | 降低随机性 |
| `max_tokens` | 800 | 控制输出长度 |

## 内容截断策略

```python
def _trim_content(text, max_tokens=3000):
    # 按字符粗略截断
    if len(text) > max_tokens * 3:
        text = text[:max_tokens * 3]
    return text
```

- 英文约 1 token ≈ 0.75 词，中文约 1 token ≈ 1 字。
- 乘以 3 作为安全阈值，避免超过模型上下文。

## 本地降级摘要

当未配置 API Key 或调用失败时：

```python
{
    "one_sentence": f"{title}：{首句}",
    "key_points": ["第2句", "第3句", "第4句"],
    "impact": "（未启用大模型...）",
    "audience": "（未启用大模型）"
}
```

- 保证无 API 时仍可运行完整流程。
- 提示用户配置 Key 以提升摘要质量。

## 成本优化

1. **减少抓取正文**：使用 `--no-body`，仅基于 RSS 摘要生成摘要。
2. **降低 token 上限**：调小 `.env` 中的 `MAX_CONTENT_TOKENS`。
3. **缓存摘要**：对已摘要的文章不再重复调用。
4. **按分类选择性摘要**：仅对高价值分类调用 LLM。

## 可优化方向

1. **本地模型**：使用 Ollama / llama.cpp 运行本地模型，零成本。
2. **摘要缓存策略**：将摘要结果写入 Redis/Memcached。
3. **多语言摘要**：根据文章内容自动判断中英文输出。
4. **标题优化**：为社交媒体生成更吸引眼球的标题。
