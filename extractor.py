"""
extractor.py
去重 + 清洗 + 正文抽取
- 对 RSS summary 做 HTML 标签清理
- 尝试通过 trafilatura 抓取原网页正文
- 提供降级方案（BeautifulSoup 提取段落）
"""
import html
import logging
import re
from typing import Dict, Any, Optional

import requests
import trafilatura
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def clean_html(raw: str) -> str:
    """移除 HTML 标签并还原实体字符。"""
    if not raw:
        return ""
    text = re.sub(r"<script[^>]*>.*?</script>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_url(url: str, timeout: int = 20) -> Optional[str]:
    """获取网页原始 HTML。"""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning("[fetch_url] 无法获取 %s: %s", url, e)
        return None


def extract_full_text(url: str, html_text: Optional[str] = None) -> str:
    """使用 trafilatura 抽取正文，失败则降级到 BeautifulSoup。"""
    if html_text is None:
        html_text = fetch_url(url)
    if not html_text:
        return ""

    try:
        # trafilatura 会过滤导航、广告等噪音
        text = trafilatura.extract(html_text, include_comments=False, include_tables=False)
        if text and len(text.strip()) > 100:
            return text.strip()
    except Exception as e:
        logger.warning("[trafilatura] 抽取失败: %s", e)

    # 降级：BeautifulSoup 提取段落
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        paragraphs = [p.get_text(strip=True) for p in soup.find_all(["p", "article", "section"])]
        text = "\n\n".join(p for p in paragraphs if len(p) > 20)
        return text.strip()
    except Exception as e:
        logger.warning("[bs4] 抽取失败: %s", e)
        return ""


def extract_item(item: Dict[str, Any], fetch_body: bool = True) -> Dict[str, Any]:
    """
    清洗 RSS 摘要，并可选择抓取原网页正文。
    返回新增字段：clean_summary, full_text, word_count
    """
    summary = clean_html(item.get("summary", ""))
    item["clean_summary"] = summary

    full_text = ""
    if fetch_body and item.get("link"):
        full_text = extract_full_text(item["link"])
    item["full_text"] = full_text

    # 优先使用正文，否则使用摘要作为后续分类/摘要的输入
    content = full_text if len(full_text) > len(summary) else summary
    item["content"] = content
    item["word_count"] = len(content.split())
    return item


if __name__ == "__main__":
    test = {
        "title": "Test",
        "link": "https://github.blog/2023-10-30-github-copilot-octoverse-2023/",
        "summary": "<p>GitHub Copilot 相关介绍。</p>",
    }
    print(extract_item(test, fetch_body=False)["clean_summary"])
