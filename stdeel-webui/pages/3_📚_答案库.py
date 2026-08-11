import json
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="标准答案库 · STDeel",
    page_icon="📚",
    layout="wide",
)

st.title("📚 标准答案库")

from db import query_df


@st.cache_data(ttl=60)
def load_all_answers():
    return query_df(
        "SELECT id, question, answer, explanation, knowledge_points, "
        "source, created_at, image_path FROM answer_library ORDER BY created_at DESC"
    )


answers_df = load_all_answers()

search = st.text_input("🔍 全文检索题干", placeholder="输入关键词…")

all_kps = []
all_sources = []
if not answers_df.empty:
    for kp_str in answers_df["knowledge_points"].dropna():
        try:
            items = json.loads(kp_str) if isinstance(kp_str, str) else kp_str
            if isinstance(items, list):
                for it in items:
                    name = it.get("name") if isinstance(it, dict) else None
                    if name:
                        all_kps.append(name)
        except Exception:
            pass
    all_sources = sorted(answers_df["source"].dropna().unique().tolist())

col1, col2 = st.columns(2)
selected_kps = col1.multiselect("🏷️ 按知识点筛选", sorted(set(all_kps)))
selected_sources = col2.multiselect("📦 按来源筛选", all_sources)

PAGE_SIZE = 20
page = st.number_input("📄 页码", min_value=1, step=1, value=1)

df = answers_df.copy()

if search and not df.empty:
    mask = df["question"].str.contains(search, case=False, na=False)
    df = df[mask]

if selected_sources and not df.empty:
    df = df[df["source"].isin(selected_sources)]

if selected_kps and not df.empty:
    def kp_match(kp_str):
        try:
            items = json.loads(kp_str) if isinstance(kp_str, str) else kp_str
            if not isinstance(items, list):
                return False
            names = {it.get("name") for it in items if isinstance(it, dict)}
            return any(k in names for k in selected_kps)
        except Exception:
            return False

    df = df[df["knowledge_points"].apply(kp_match)]

total = len(df)
start = (page - 1) * PAGE_SIZE
end = start + PAGE_SIZE
page_df = df.iloc[start:end]

st.caption(f"共 **{total}** 条答案 · 第 {page} 页 / 共 {max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)} 页")

if page_df.empty:
    st.info("暂无匹配的答案")
else:
    for _, row in page_df.iterrows():
        q_summary = (row["question"] or "")[:100]
        with st.expander(
            f"[{row.get('source', '—')}] {q_summary}{'…' if len(row['question'] or '') > 100 else ''}"
        ):
            st.markdown(f"**ID：** `{row['id']}`  ")
            st.markdown(f"**来源：** {row.get('source', '—')}  ")
            st.markdown(f"**创建时间：** {row.get('created_at', '—')}")
            st.divider()
            st.markdown("**题干：**")
            st.write(row.get("question", ""))
            st.markdown("**标准答案：**")
            st.write(row.get("answer", ""))
            if row.get("explanation"):
                st.markdown("**解答过程：**")
                st.write(row["explanation"])
            if row.get("knowledge_points"):
                st.markdown("**知识点标签：**")
                st.write(row["knowledge_points"])
            if row.get("image_path"):
                st.markdown(f"**图片路径：** `{row['image_path']}`")
