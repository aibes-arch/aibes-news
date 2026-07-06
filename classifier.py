"""
classifier.py
关键词分类：AI / LLM / Agent / 编程 / 云 / 开源 / 安全 / 研究 / 行业应用
- 基于关键词权重匹配
- 支持 source_category 加权（如 arXiv 默认更偏研究）
- 返回主分类、置信度、标签列表
"""
import logging
import re
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

CATEGORY_RULES = {
    "AI/LLM": {
        "weight": 1.0,
        "keywords": [
            "LLM", "large language model", "大模型", "大语言模型", "GPT", "ChatGPT",
            "OpenAI", "Claude", "Anthropic", "Gemini", "PaLM", "Llama", "Mistral",
            "Transformer", "attention", "fine-tuning", "fine tuning", "微调",
            "prompt", "prompting", "对齐", "alignment", "RLHF", "多模态", "multimodal",
            "generative AI", "生成式 AI", "AIGC", "NLP", "自然语言处理",
        ],
    },
    "AI Agent": {
        "weight": 1.0,
        "keywords": [
            "agent", "agents", "AI agent", "智能体", "autonomous", "auto-gpt", "AutoGPT",
            "langchain", "crewai", "tool use", "function calling", "RAG", "retrieval",
            "向量库", "vector database", "embedding", "workflow", "编排", "orchestration",
            "multi-agent", "多智能体",
        ],
    },
    "编程/工程": {
        "weight": 1.0,
        "keywords": [
            "Python", "JavaScript", "TypeScript", "Rust", "Go", "Java", "C++",
            "programming", "coding", "developer", "API", "SDK", "framework",
            "testing", "CI/CD", "DevOps", "database", "backend", "frontend",
            "代码", "编程", "开发", "工程师", "软件工程", "架构",
        ],
    },
    "云原生": {
        "weight": 1.0,
        "keywords": [
            "AWS", "Azure", "GCP", "Google Cloud", "Cloudflare", "云",
            "Kubernetes", "K8s", "Docker", "container", "serverless", "无服务器",
            "microservices", "微服务", "observability", "可观测性", "SRE",
            "terraform", "IaC", "云计算", "云原生",
        ],
    },
    "开源": {
        "weight": 1.0,
        "keywords": [
            "open source", "开源", "GitHub", "GitLab", "repository", "repo",
            "license", "Apache", "MIT", "GPL", "Linux Foundation", "CNCF",
            "community", "贡献", "fork", "pull request", "release", "版本发布",
        ],
    },
    "安全": {
        "weight": 1.0,
        "keywords": [
            "security", "vulnerability", "CVE", "exploit", "attack", "breach",
            "malware", "ransomware", "phishing", "CISA", "Krebs", "零日",
            "漏洞", "攻击", "安全", "网络安全", "信息安全", "隐私", "privacy",
        ],
    },
    "研究": {
        "weight": 1.0,
        "keywords": [
            "paper", "arxiv", "research", "survey", "benchmark", "dataset",
            "实验", "论文", "研究", "综述", "基准", "数据集", "SOTA", "state of the art",
        ],
    },
    "行业应用": {
        "weight": 1.0,
        "keywords": [
            "healthcare", "finance", "education", "robotics", "自动驾驶",
            "医疗", "金融", "教育", "机器人", "制造", "零售", "电商", "游戏",
            "application", "场景", "落地", "产业化", "行业",
        ],
    },
    "公司动态/投融资": {
        "weight": 1.0,
        "keywords": [
            "funding", "investment", "IPO", "acquisition", "收购", "融资",
            "投资", "估值", "startup", "独角兽", "财报", "earnings", "revenue",
            "公司", "发布", "新品", "合作", "战略合作", "partnership",
        ],
    },
}

SOURCE_BIAS = {
    "研究源": {"研究": 1.5, "AI/LLM": 1.2},
    "官方源": {"公司动态/投融资": 1.3, "AI/LLM": 1.2},
    "工程源": {"编程/工程": 1.5, "开源": 1.2},
    "云厂商源": {"云原生": 1.8, "AI/LLM": 1.1},
    "安全与开源": {"安全": 1.8, "开源": 1.3},
    "中文源": {"AI/LLM": 1.2, "行业应用": 1.2},
}


def _score(text: str, rules: Dict[str, Any]) -> Dict[str, float]:
    """对文本按规则打分。"""
    text_lower = text.lower()
    scores = {}
    for category, cfg in rules.items():
        score = 0.0
        for kw in cfg["keywords"]:
            # 简单词频匹配，单词边界对中文不友好，这里使用子串匹配
            count = text_lower.count(kw.lower())
            score += count * cfg["weight"]
        scores[category] = score
    return scores


def classify(item: Dict[str, Any]) -> Tuple[str, float, List[str]]:
    """
    对单条 item 进行分类。
    返回：(主分类, 置信度, 所有命中标签)
    """
    text = " ".join([
        item.get("title", ""),
        item.get("clean_summary", ""),
        item.get("content", "")[:2000],
    ])
    if not text.strip():
        return "其他", 0.0, []

    scores = _score(text, CATEGORY_RULES)

    # 源类别加权
    source_cat = item.get("source_category", "")
    if source_cat in SOURCE_BIAS:
        for cat, factor in SOURCE_BIAS[source_cat].items():
            scores[cat] = scores.get(cat, 0) * factor

    # 提取命中的标签（出现分数大于 0 的分类）
    tags = [cat for cat, s in scores.items() if s > 0]

    if not scores or max(scores.values()) <= 0:
        return "其他", 0.0, tags

    top_category = max(scores, key=scores.get)
    top_score = scores[top_category]
    total = sum(scores.values()) or 1.0
    confidence = round(top_score / total, 3)

    return top_category, confidence, tags


def classify_item(item: Dict[str, Any]) -> Dict[str, Any]:
    category, confidence, tags = classify(item)
    item["category"] = category
    item["confidence"] = confidence
    item["tags"] = tags
    return item


if __name__ == "__main__":
    sample = {
        "title": "OpenAI releases new GPT-5 with improved agent capabilities",
        "clean_summary": "The latest model supports multi-agent workflows and tool use.",
        "content": "",
        "source_category": "官方源",
    }
    print(classify_item(sample))
