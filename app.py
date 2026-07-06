"""
app.py
Streamlit Web 看板
- 浏览 / 搜索 / 筛选
- 查看摘要与原文链接
"""
import json
import os

import streamlit as st

from storage import Storage

st.set_page_config(page_title="AI 技术情报 Agent", layout="wide")

DATA_DIR = os.getenv("DATA_DIR", "./data")


@st.cache_resource
def get_storage():
    return Storage()


def load_summary_json(summary_json: str):
    try:
        return json.loads(summary_json)
    except Exception:
        return {}


def main():
    st.title("🤖 AI 与软件技术情报 Agent")
    st.markdown("自动聚合、分类、摘要，追踪 AI/LLM/Agent/云原生/开源/安全等领域动态。")

    storage = get_storage()

    # 侧边栏筛选
    st.sidebar.header("筛选")
    categories = ["全部"] + storage.get_categories()
    selected_category = st.sidebar.selectbox("分类", categories)

    hours = st.sidebar.slider("最近 N 小时", min_value=1, max_value=168, value=48)
    search_query = st.sidebar.text_input("语义搜索", placeholder="输入关键词或句子")

    # 获取数据
    if search_query:
        items = storage.search(search_query, top_k=20)
    else:
        cat = None if selected_category == "全部" else selected_category
        items = storage.get_recent(hours=hours, category=cat)

    st.sidebar.markdown(f"**当前展示：{len(items)} 条**")

    # 统计
    cols = st.columns(4)
    stats = storage.get_stats()
    cols[0].metric("总收录", stats["total"])
    cols[1].metric("已向量化", stats["vectorized"])
    cols[2].metric("当前展示", len(items))
    cols[3].metric("分类数", len(categories) - 1)

    # 列表
    for item in items:
        summary = load_summary_json(item.get("summary_json", "{}"))
        with st.container():
            st.subheader(item["title"])
            st.caption(
                f"📰 {item['source']} | 🏷️ {item['category']} | "
                f"🕒 {item['published'][:19]} | 🔗 [阅读原文]({item['link']})"
            )

            if summary.get("one_sentence"):
                st.markdown(f"**一句话：** {summary['one_sentence']}")
            if summary.get("key_points"):
                with st.expander("要点"):
                    for p in summary["key_points"]:
                        st.markdown(f"- {p}")
            if summary.get("impact"):
                st.markdown(f"**影响：** {summary['impact']}")
            if summary.get("audience"):
                st.markdown(f"**适合谁看：** {summary['audience']}")

            st.divider()


if __name__ == "__main__":
    main()
