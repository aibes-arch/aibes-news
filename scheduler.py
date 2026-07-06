"""
scheduler.py
定时任务入口：每隔 N 小时运行一次 main.run_once
也可交给系统 cron / Windows 计划任务调用 main.py
"""
import argparse
import logging
import time

import schedule

from main import run_once

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def job(args):
    logger.info("[scheduler] 触发定时任务")
    try:
        run_once(
            feeds_path=args.feeds,
            fetch_body=not args.no_body,
            skip_summary=args.no_summary,
        )
    except Exception as e:
        logger.error("[scheduler] 运行失败: %s", e)


def main():
    parser = argparse.ArgumentParser(description="定时运行 AI 技术情报 Agent")
    parser.add_argument("--feeds", default="feeds.yaml")
    parser.add_argument("--no-body", action="store_true")
    parser.add_argument("--no-summary", action="store_true")
    parser.add_argument("--interval", type=int, default=4, help="运行间隔（小时）")
    args = parser.parse_args()

    schedule.every(args.interval).hours.do(job, args)
    logger.info("[scheduler] 已启动，每 %d 小时运行一次", args.interval)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
