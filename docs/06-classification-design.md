# 分类算法设计

## 分类目标

将每篇文章自动归入以下 9 个主分类之一，并给出置信度和命中标签：

1. AI/LLM
2. AI Agent
3. 编程/工程
4. 云原生
5. 开源
6. 安全
7. 研究
8. 行业应用
9. 公司动态/投融资
10. 其他（未命中任何关键词时）

## 算法流程

```text
输入：item（title, clean_summary, content, source_category）
  │
  ▼
拼接文本 text = title + clean_summary + content[:2000]
  │
  ▼
对每个分类 C：
  score[C] = Σ (关键词出现次数 × 分类权重)
  │
  ▼
源类别加权：
  score[C] *= SOURCE_BIAS[source_category][C]（如有）
  │
  ▼
主分类 = argmax(score)
置信度 = max(score) / sum(score)
标签 = {C | score[C] > 0}
```

## 分类规则示例

### AI/LLM

```python
{
    "weight": 1.0,
    "keywords": [
        "LLM", "large language model", "大模型", "大语言模型",
        "GPT", "ChatGPT", "OpenAI", "Claude", "Anthropic",
        "Transformer", "fine-tuning", "RLHF", "多模态",
        "generative AI", "NLP", "自然语言处理"
    ]
}
```

### AI Agent

```python
{
    "weight": 1.0,
    "keywords": [
        "agent", "agents", "AI agent", "智能体",
        "langchain", "RAG", "retrieval", "vector database",
        "tool use", "function calling", "multi-agent"
    ]
}
```

### 云原生

```python
{
    "weight": 1.0,
    "keywords": [
        "AWS", "Azure", "GCP", "Kubernetes", "Docker",
        "serverless", "microservices", "observability", "云计算"
    ]
}
```

## 源类别加权

```python
SOURCE_BIAS = {
    "研究源": {"研究": 1.5, "AI/LLM": 1.2},
    "官方源": {"公司动态/投融资": 1.3, "AI/LLM": 1.2},
    "工程源": {"编程/工程": 1.5, "开源": 1.2},
    "云厂商源": {"云原生": 1.8, "AI/LLM": 1.1},
    "安全与开源": {"安全": 1.8, "开源": 1.3},
    "中文源": {"AI/LLM": 1.2, "行业应用": 1.2},
}
```

## 匹配策略

- 采用子串匹配（`text.lower().count(kw.lower())`）。
- 原因：
  - 实现简单，无需分词。
  - 对英文大小写不敏感。
  - 对中文词组也能有效命中（如"大语言模型"）。
- 缺点：可能误匹配部分边界，后续可优化为词边界或正则。

## 置信度解释

- `confidence = 1.0`：文章只命中一个分类。
- `confidence < 0.5`：文章跨多个分类，主分类优势不明显。
- 可作为人工复核或排序的依据。

## 可优化方向

1. **LLM 二次分类**：对置信度低的文章调用 LLM 重新判定。
2. **TF-IDF 加权**：根据关键词在语料中的分布调整权重。
3. **机器学习分类器**：积累标注数据后训练 FastText/BERT 分类器。
4. **实体识别**：识别公司名、产品名，提升公司动态分类准确率。
