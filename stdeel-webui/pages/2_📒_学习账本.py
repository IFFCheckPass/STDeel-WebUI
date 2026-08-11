import json
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="个人学习账本 · STDeel",
    page_icon="📒",
    layout="wide",
)

st.title("📒 个人学习账本")

from db import query_df, query_one
from charts import knowledge_radar, solve_timeline


@st.cache_data(ttl=30)
def load_all_users():
    return query_df("SELECT id, username FROM users ORDER BY created_at DESC")


all_users = load_all_users()
if all_users.empty:
    st.warning("暂无注册用户")
    st.stop()

url_user_id = st.query_params.get("user_id", None)
default_idx = 0
if url_user_id:
    target = str(url_user_id)
    for i, uid in enumerate(all_users["id"].astype(str)):
        if uid == target:
            default_idx = i
            break

selected_user = st.selectbox(
    "👤 选择用户",
    all_users["username"].tolist(),
    index=default_idx,
)
user_id = int(all_users[all_users["username"] == selected_user].iloc[0]["id"])


@st.cache_data(ttl=30)
def load_user_overview(uid):
    total = query_one("SELECT COUNT(*) FROM solve_records WHERE user_id = ?", [uid]) or 0
    correct = query_one(
        "SELECT COUNT(*) FROM solve_records WHERE user_id = ? AND user_feedback = 'correct'",
        [uid],
    ) or 0
    wrong = query_one(
        "SELECT COUNT(*) FROM solve_records WHERE user_id = ? AND user_feedback = 'wrong'",
        [uid],
    ) or 0
    avg_latency = query_one(
        "SELECT AVG(latency_ms) FROM solve_records WHERE user_id = ?", [uid]
    )
    top_model = query_one(
        "SELECT ai_model FROM solve_records WHERE user_id = ? AND ai_model IS NOT NULL "
        "GROUP BY ai_model ORDER BY COUNT(*) DESC LIMIT 1",
        [uid],
    )
    return total, correct, wrong, avg_latency, top_model


@st.cache_data(ttl=30)
def load_solves(uid):
    return query_df(
        "SELECT id, created_at, question, answer, explanation, "
        "knowledge_points, ai_model, latency_ms, user_feedback "
        "FROM solve_records WHERE user_id = ? ORDER BY created_at DESC",
        [uid],
    )


@st.cache_data(ttl=30)
def load_timeline(uid):
    return query_df(
        "SELECT date(created_at) as date, COUNT(*) as count "
        "FROM solve_records WHERE user_id = ? GROUP BY date(created_at) ORDER BY date",
        [uid],
    )


total, correct, wrong, avg_latency, top_model = load_user_overview(user_id)

col1, col2, col3, col4 = st.columns(4)
col1.metric("总解题数", f"{total}")
feedback_total = correct + wrong
rate = round(correct / feedback_total * 100, 1) if feedback_total else 0.0
col2.metric("正确率", f"{rate}%")
col3.metric("平均响应耗时", f"{avg_latency:.0f} ms" if avg_latency else "—")
col4.metric("常用 AI 模型", top_model or "—")

st.divider()

solves_df = load_solves(user_id)

st.subheader("📡 知识点掌握度雷达图")
radar_placeholder = st.empty()

radar_placeholder.info("正在解析知识点数据…")
if not solves_df.empty and "knowledge_points" in solves_df.columns:
    kp_rows = []
    for kp_str in solves_df["knowledge_points"].dropna():
        try:
            items = json.loads(kp_str) if isinstance(kp_str, str) else kp_str
            if isinstance(items, list):
                kp_rows.extend(items)
        except (json.JSONDecodeError, TypeError):
            continue

    if kp_rows:
        kp_df = pd.DataFrame(kp_rows)
        if "name" in kp_df.columns and "mastery" in kp_df.columns:
            agg = kp_df.groupby("name", as_index=False)["mastery"].mean()
            labels = agg["name"].tolist()
            values = agg["mastery"].clip(0, 100).tolist()
            radar_placeholder.plotly_chart(
                knowledge_radar(labels, values), use_container_width=True
            )
        else:
            radar_placeholder.info("知识点数据格式不符合预期")
    else:
        radar_placeholder.info("暂无知识点数据")
else:
    radar_placeholder.info("该用户暂无解题记录")

st.divider()

st.subheader("📅 解题时间线")
timeline_df = load_timeline(user_id)
if timeline_df.empty:
    st.info("暂无解题时间数据")
else:
    st.plotly_chart(solve_timeline(timeline_df), use_container_width=True)

st.divider()

st.subheader("⚠️ 薄弱知识点列表")
if not solves_df.empty and "knowledge_points" in solves_df.columns:
    weak_rows = []
    for _, row in solves_df.iterrows():
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
        except (json.JSONDecodeError, TypeError):
            continue
        for item in items:
            name = item.get("name") if isinstance(item, dict) else None
            if not name:
                continue
            weak_rows.append({"knowledge_point": name, "feedback": fb})

    if weak_rows:
        weak_df = pd.DataFrame(weak_rows)
        agg = weak_df.groupby("knowledge_point").agg(
            total=("feedback", "count"),
            wrong=("feedback", lambda s: (s == "wrong").sum()),
        ).reset_index()
        agg["error_rate"] = (agg["wrong"] / agg["total"] * 100).round(1)
        weak = agg[agg["error_rate"] > 50].sort_values("error_rate", ascending=False)

        if weak.empty:
            st.success("暂无错误率超过 50% 的薄弱点 🎉")
        else:
            styled = weak.style.background_gradient(
                subset=["error_rate"], cmap="Reds", vmin=50, vmax=100
            ).format({"error_rate": "{:.1f}%"})
            st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.info("暂无足够的反馈数据")
else:
    st.info("该用户暂无解题记录")

st.divider()

st.subheader("📝 最近解题记录")
recent = solves_df.head(20)
if recent.empty:
    st.info("暂无解题记录")
else:
    for _, row in recent.iterrows():
        with st.expander(
            f"[{row['created_at']}] {row.get('ai_model', '—')} · "
            f"反馈: {row.get('user_feedback', '未反馈')}"
        ):
            st.markdown("**题目：**")
            st.write(row.get("question", ""))
            st.markdown("**答案：**")
            st.write(row.get("answer", ""))
            if row.get("explanation"):
                st.markdown("**解答过程：**")
                st.write(row["explanation"])
            if row.get("knowledge_points"):
                st.markdown("**知识点：**")
                st.write(row["knowledge_points"])
