"""
main.py
一次完整运行：采集 -> 抽取 -> 分类 -> 摘要 -> 存储 -> 向量化 -> 生成日报
"""
import argparse
import logging
import os
from datetime import datetime

from crawler import crawl_to_list
from extractor import extract_item
from classifier import classify_item
from summarizer import summarize
from storage import Storage
from report import daily_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_once(feeds_path: str = "feeds.yaml",
             fetch_body: bool = True,
             summarize_items: bool = True,
             skip_summary: bool = False) -> dict:
    logger.info("[main] 开始采集: %s", datetime.utcnow().isoformat())

    storage = Storage()
    total_new = 0

    items = crawl_to_list(feeds_path)
    logger.info("[main] 采集到 %d 条（去重后）", len(items))

    for item in items:
        try:
            extract_item(item, fetch_body=fetch_body)
            classify_item(item)
            if summarize_items and not skip_summary:
                summarize(item)
            if storage.upsert(item):
                total_new += 1
        except Exception as e:
            logger.error("[main] 处理 %s 失败: %s", item.get("link"), e)

    logger.info("[main] 新增 %d 条", total_new)

    # 向量化
    storage.vectorize_unvectorized()

    # 生成日报
    report_path = daily_report(storage)

    storage.close()
    return {"total": len(items), "new": total_new, "report": report_path}


def main():
    parser = argparse.ArgumentParser(description="AI 技术情报 Agent 运行入口")
    parser.add_argument("--feeds", default="feeds.yaml", help="源配置文件路径")
    parser.add_argument("--no-body", action="store_true", help="不抓取原网页正文")
    parser.add_argument("--no-summary", action="store_true", help="不使用 LLM 摘要")
    args = parser.parse_args()

    result = run_once(
        feeds_path=args.feeds,
        fetch_body=not args.no_body,
        skip_summary=args.no_summary,
    )
    print("运行结果:", result)


if __name__ == "__main__":
    main()
