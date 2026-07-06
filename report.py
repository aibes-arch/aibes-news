"""
report.py
生成日报 / 周报
- 按分类聚合
- 输出 Markdown，便于邮件、微信或 Web 展示
"""
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

from storage import Storage

logger = logging.getLogger(__name__)

REPORT_DIR = os.path.join(os.getenv("DATA_DIR", "./data"), "reports")


def _load_summary(row: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if row.get("summary_json"):
            return json.loads(row["summary_json"])
    except Exception:
        pass
    return {}


def _render_item(row: Dict[str, Any]) -> str:
    summary = _load_summary(row)
    lines = [f"### [{row['title']}]({row['link']})"]
    lines.append(f"- 来源：{row['source']} | 分类：{row['category']} | 时间：{row['published'][:10]}")
    if summary.get("one_sentence"):
        lines.append(f"- **一句话**：{summary['one_sentence']}")
    if summary.get("key_points"):
        lines.append("- **要点**：")
        for p in summary["key_points"]:
            lines.append(f"  - {p}")
    if summary.get("impact"):
        lines.append(f"- **影响**：{summary['impact']}")
    if summary.get("audience"):
        lines.append(f"- **适合谁看**：{summary['audience']}")
    if not summary:
        lines.append(f"- {row.get('clean_summary', '')[:200]}")
    lines.append("")
    return "\n".join(lines)


def generate_report(items: List[Dict[str, Any]], title: str = "技术情报简报") -> str:
    """根据 items 生成 Markdown 报告。"""
    # 按分类分组
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        cat = item.get("category") or "其他"
        groups.setdefault(cat, []).append(item)

    lines = [f"# {title}", f"", f"生成时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", f"共收录 {len(items)} 条", ""]

    # 按预设顺序 + 动态分类
    order = ["AI/LLM", "AI Agent", "编程/工程", "云原生", "开源", "安全", "研究", "行业应用", "公司动态/投融资", "其他"]
    sorted_cats = sorted(groups.keys(), key=lambda c: (order.index(c) if c in order else 99, c))

    for cat in sorted_cats:
        lines.append(f"## {cat}（{len(groups[cat])} 条）")
        lines.append("")
        for item in groups[cat]:
            lines.append(_render_item(item))

    return "\n".join(lines)


def save_report(report_md: str, period: str = "daily") -> str:
    """保存报告到文件，返回路径。"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    now = datetime.utcnow().strftime("%Y%m%d_%H%M")
    filename = f"{period}_{now}.md"
    path = os.path.join(REPORT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_md)
    logger.info("[report] 报告已保存: %s", path)
    return path


def daily_report(storage: Storage, hours: int = 24) -> str:
    items = storage.get_recent(hours=hours)
    title = f"AI 与软件技术情报日报 ({datetime.utcnow().strftime('%Y-%m-%d')})"
    md = generate_report(items, title=title)
    return save_report(md, period="daily")


def weekly_report(storage: Storage) -> str:
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    items = storage.get_by_date_range(start, end)
    title = f"AI 与软件技术情报周报 ({start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')})"
    md = generate_report(items, title=title)
    return save_report(md, period="weekly")


if __name__ == "__main__":
    s = Storage()
    print(daily_report(s))
