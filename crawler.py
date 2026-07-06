"""
crawler.py
RSS/API/网页 定时采集器
统一输出字段：id, title, link, summary, published, source, source_category, raw
"""
import hashlib
import logging
from datetime import datetime
from typing import Iterator, Dict, Any, List

import feedparser
import requests
import yaml
from dateutil import parser as date_parser

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def load_feeds(path: str = "feeds.yaml") -> Dict[str, Any]:
    """加载 feeds.yaml，返回按分组组织的源配置。"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _norm_date(entry: Dict[str, Any]) -> datetime:
    """从 feed entry 中提取标准化时间。"""
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        if key in entry and entry[key]:
            try:
                return datetime(*entry[key][:6])
            except Exception:
                pass
    for key in ("published", "updated", "created"):
        if key in entry and entry[key]:
            try:
                return date_parser.parse(entry[key])
            except Exception:
                pass
    return datetime.utcnow()


def _item_id(title: str, link: str) -> str:
    return hashlib.md5(f"{title.strip()}|{link.strip()}".encode("utf-8")).hexdigest()


def _fetch_feed(source: Dict[str, Any], group_name: str) -> List[Dict[str, Any]]:
    """抓取单个 RSS/Atom 源。"""
    name = source["name"]
    url = source["url"]
    max_items = source.get("max_items", 10)
    enabled = source.get("enabled", True)

    if not enabled:
        logger.info("[跳过] %s 已禁用", name)
        return []

    logger.info("[采集] %s -> %s", name, url)
    try:
        # feedparser 支持直接解析 URL，但 requests 可自定义 UA/超时
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        logger.error("[失败] %s 请求异常: %s", name, e)
        return []

    items = []
    for entry in feed.entries[:max_items]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        if not link:
            continue
        summary = entry.get("summary", entry.get("description", "")).strip()
        # 某些源 summary 是完整 HTML，这里保留原始内容给 extractor 清洗
        published = _norm_date(entry)

        items.append({
            "id": _item_id(title, link),
            "title": title,
            "link": link,
            "summary": summary,
            "published": published,
            "source": name,
            "source_category": group_name,
            "raw": dict(entry),
        })

    logger.info("[完成] %s 获取 %d 条", name, len(items))
    return items


def crawl(feeds_path: str = "feeds.yaml") -> Iterator[Dict[str, Any]]:
    """
    主入口：读取配置并逐个源采集。
    返回去重后的 item 字典迭代器（按源顺序保留首次出现）。
    """
    groups = load_feeds(feeds_path)
    seen = set()
    for group_key, group in groups.items():
        group_name = group.get("name", group_key)
        for source in group.get("sources", []):
            for item in _fetch_feed(source, group_name):
                if item["id"] in seen:
                    continue
                seen.add(item["id"])
                yield item


def crawl_to_list(feeds_path: str = "feeds.yaml") -> List[Dict[str, Any]]:
    return list(crawl(feeds_path))


if __name__ == "__main__":
    for it in crawl():
        print(f"[{it['source_category']}] {it['source']}: {it['title'][:60]}")
