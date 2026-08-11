import json
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="知识点统计 · STDeel",
    page_icon="📊",
    layout="wide",
)

st.title("📊 知识点掌握度统计")

from db import query_df
from charts import mastery_bar, weak_points_bar, heatmap


@st.cache_data(ttl=60)
def load_knowledge_mastery():
    return query_df(
        "SELECT knowledge_point, total_count, correct_count, "
        "wrong_count, correct_rate FROM knowledge_mastery ORDER BY correct_rate DESC"
    )


@st.cache_data(ttl=60)
def load_answers_knowledge():
    return query_df("SELECT knowledge_points FROM answer_library")


@st.cache_data(ttl=60)
def load_top_users():
    return query_df(
        "SELECT u.id, u.username, COUNT(sr.id) as cnt "
        "FROM users u JOIN solve_records sr ON sr.user_id = u.id "
        "GROUP BY u.id ORDER BY cnt DESC LIMIT 10"
    )


@st.cache_data(ttl=60)
def load_all_solves():
    return query_df(
        "SELECT u.username, sr.knowledge_points, sr.user_feedback "
        "FROM solve_records sr JOIN users u ON u.id = sr.user_id "
    )


st.subheader("📈 全局知识点掌握度")
km_df = load_knowledge_mastery()
if km_df.empty:
    st.info("knowledge_mastery 表暂无数据")
else:
    st.plotly_chart(mastery_bar(km_df), use_container_width=True)

st.divider()

st.subheader("⚠️ 薄弱知识点排行（错误率 > 50%）")
if not km_df.empty:
    km_df["error_rate"] = (100 - km_df["correct_rate"]).round(1)
    weak = km_df[km_df["error_rate"] > 50].sort_values("error_rate", ascending=False)
    if weak.empty:
        st.success("无错误率超过 50% 的薄弱点 🎉")
    else:
        display = weak[["knowledge_point", "total_count", "correct_count",
                        "wrong_count", "error_rate"]].rename(columns={
            "knowledge_point": "知识点",
            "total_count": "总题数",
            "correct_count": "正确数",
            "wrong_count": "错误数",
            "error_rate": "错误率(%)",
        })
        st.dataframe(display, use_container_width=True, hide_index=True)
        st.plotly_chart(weak_points_bar(weak), use_container_width=True)
else:
    st.info("暂无数据")

st.divider()

st.subheader("📚 知识点关联题目数统计")
answers_df = load_answers_knowledge()
if not answers_df.empty:
    kp_counts = {}
    for kp_str in answers_df["knowledge_points"].dropna():
        try:
            items = json.loads(kp_str) if isinstance(kp_str, str) else kp_str
            if not isinstance(items, list):
                continue
            for it in items:
                name = it.get("name") if isinstance(it, dict) else None
                if name:
                    kp_counts[name] = kp_counts.get(name, 0) + 1
        except Exception:
            continue
    if kp_counts:
        kp_count_df = pd.DataFrame(
            {"knowledge_point": list(kp_counts.keys()),
             "count": list(kp_counts.values())}
        ).sort_values("count", ascending=False)
        fig = px.bar(
            kp_count_df, x="knowledge_point", y="count",
            color_discrete_sequence=["#5b9fff"],
        )
        fig.update_layout(
            title="各知识点的标准答案数量",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e4e7ee', size=13),
            margin=dict(l=40, r=20, t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("答案库中暂无知识点数据")
else:
    st.info("答案库为空")

st.divider()

st.subheader("🔥 全局知识点掌握度热力图（Top 10 活跃用户）")
top_users = load_top_users()
all_solves = load_all_solves()
if top_users.empty or all_solves.empty:
    st.info("暂无足够数据生成热力图")
else:
    top_usernames = top_users["username"].tolist()
    heat_rows = []
    for _, row in all_solves.iterrows():
        if row["username"] not in top_usernames:
            continue
        fb = row.get("user_feedback")
        if fb not in ("correct", "wrong"):
            continue
        kp_str = row.get("knowledge_points")
        if not kp_str:
            continue
        try:
            items = json.loads(kp_str) if isinstance(kp_str, str) else kp_str
            if not isinstance(items, list):
                continue
        except Exception:
            continue
        for it in items:
            name = it.get("name") if isinstance(it, dict) else None
            if not name:
                continue
            heat_rows.append({
                "username": row["username"],
                "knowledge_point": name,
                "feedback": fb,
            })

    if heat_rows:
        heat_df = pd.DataFrame(heat_rows)
        agg = heat_df.groupby(["username", "knowledge_point"]).agg(
            total=("feedback", "count"),
            correct=("feedback", lambda s: (s == "correct").sum()),
        ).reset_index()
        agg["correct_rate"] = (agg["correct"] / agg["total"] * 100).round(1)
        st.plotly_chart(heatmap(agg), use_container_width=True)
    else:
        st.info("暂无足够的反馈数据")
