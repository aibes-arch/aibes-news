"""
summarizer.py
大模型摘要：一句话、要点、影响、适合谁看
- 优先使用 OpenAI API（或其他兼容 OpenAI 接口的服务）
- 未配置 API 时使用本地降级摘要（标题+首段+关键句）
"""
import logging
import os
import re
from typing import Dict, Any

from dotenv import load_dotenv

try:
    import openai
except ImportError:
    openai = None

load_dotenv()
logger = logging.getLogger(__name__)

SUMMARY_LANGUAGE = os.getenv("SUMMARY_LANGUAGE", "zh")
MAX_CONTENT_TOKENS = int(os.getenv("MAX_CONTENT_TOKENS", "3000"))

SYSTEM_PROMPT_ZH = """你是一位资深技术编辑，负责为 AI 与软件工程领域的新闻生成中文简报。
请对用户提供的新闻标题和正文，用中文输出如下 JSON 结构（不要包含 markdown 代码块）：
{
  "one_sentence": "一句话总结全文核心信息",
  "key_points": ["要点1", "要点2", "要点3"],
  "impact": "对行业、开发者或公司的潜在影响",
  "audience": "适合谁看，例如后端工程师、AI 研究者、创业者、安全工程师等"
}
只输出 JSON，不要解释。"""

SYSTEM_PROMPT_EN = """You are a senior tech editor. Summarize the provided article in JSON:
{
  "one_sentence": "one-sentence summary",
  "key_points": ["point1", "point2", "point3"],
  "impact": "potential impact",
  "audience": "target audience"
}
Output JSON only."""


def _trim_content(text: str, max_tokens: int = MAX_CONTENT_TOKENS) -> str:
    """按空格分割的单词数做简单截断；英文约 1 token ≈ 0.75 词，中文按字处理。"""
    if not text:
        return ""
    # 粗略按字符截断，兼顾中英文
    if len(text) > max_tokens * 3:
        text = text[: max_tokens * 3]
    return text.strip()


def _llm_client():
    if openai is None:
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base_url = os.getenv("OPENAI_BASE_URL")
    client = openai.OpenAI(api_key=api_key, base_url=base_url or None)
    return client


def _parse_json(text: str) -> Dict[str, Any]:
    """简单提取 JSON 内容，容错处理。"""
    import json
    text = text.strip()
    # 去掉可能的 markdown 代码块
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception as e:
        logger.warning("[summarizer] JSON 解析失败: %s", e)
        return {}


def _fallback_summary(title: str, content: str) -> Dict[str, Any]:
    """无 LLM 时的降级摘要：标题 + 首段 + 关键句。"""
    sentences = re.split(r"(?<=[。\.\n])\s+", content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    one_sentence = f"{title}：{sentences[0]}" if sentences else title
    key_points = sentences[1:4] if len(sentences) > 1 else ["（内容较短，未抽取更多要点）"]
    return {
        "one_sentence": one_sentence[:300],
        "key_points": [p[:300] for p in key_points],
        "impact": "（未启用大模型，请配置 OPENAI_API_KEY 以生成影响分析）",
        "audience": "（未启用大模型）",
    }


def summarize(item: Dict[str, Any], force_llm: bool = False) -> Dict[str, Any]:
    """为 item 生成摘要，写回 item 的 summary 字段。"""
    title = item.get("title", "")
    content = _trim_content(item.get("content", ""))

    client = _llm_client()
    if client and (force_llm or os.getenv("OPENAI_API_KEY")):
        try:
            system = SYSTEM_PROMPT_ZH if SUMMARY_LANGUAGE == "zh" else SYSTEM_PROMPT_EN
            user = f"标题：{title}\n\n正文：\n{content}"
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.3,
                max_tokens=800,
            )
            raw = resp.choices[0].message.content
            parsed = _parse_json(raw)
            if parsed and "one_sentence" in parsed:
                item["summary"] = parsed
                return item
        except Exception as e:
            logger.warning("[summarizer] LLM 调用失败，使用降级摘要: %s", e)

    item["summary"] = _fallback_summary(title, content)
    return item


if __name__ == "__main__":
    test_item = {
        "title": "LangChain 0.1 发布：更模块化的 Agent 框架",
        "content": "LangChain 0.1 带来了全新的 LCEL 表达语言，使得构建 Agent 工作流更加简单。"
                   "开发者可以更灵活地组合工具调用、记忆和输出解析。",
    }
    print(summarize(test_item)["summary"])
