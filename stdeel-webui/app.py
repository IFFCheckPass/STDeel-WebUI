import streamlit as st
import pandas as pd

from db import query_df, query_one
from charts import registration_trend

st.set_page_config(
    page_title="思谛 STDeel · 管理后台",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧠 思谛 STDeel · 管理后台")
st.caption("内网管理面板 · 只读模式 · 数据直接来自 app.db")


@st.cache_data(ttl=60)
def load_metrics():
    users_total = query_one("SELECT COUNT(*) FROM users") or 0
    users_today = query_one(
        "SELECT COUNT(*) FROM users WHERE date(created_at) = date('now')"
    ) or 0
    solves_total = query_one("SELECT COUNT(*) FROM solve_records") or 0
    answers_total = query_one("SELECT COUNT(*) FROM answer_library") or 0
    return users_total, users_today, solves_total, answers_total


@st.cache_data(ttl=60)
def load_registration_trend():
    df = query_df(
        "SELECT date(created_at) as date, COUNT(*) as count "
        "FROM users GROUP BY date(created_at) ORDER BY date"
    )
    if df.empty:
        return df
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df['cumulative'] = df['count'].cumsum()
    return df


@st.cache_data(ttl=30)
def load_recent_solves(n=10):
    return query_df(
        "SELECT sr.id, sr.created_at, u.username, "
        "substr(sr.question, 1, 60) as question_summary, "
        "sr.ai_model, sr.user_feedback "
        "FROM solve_records sr LEFT JOIN users u ON u.id = sr.user_id "
        "ORDER BY sr.created_at DESC LIMIT ?",
        params=[n],
    )


@st.cache_data(ttl=30)
def load_recent_answers(n=5):
    return query_df(
        "SELECT id, substr(question, 1, 60) as question_summary, "
        "source, created_at FROM answer_library "
        "ORDER BY created_at DESC LIMIT ?",
        params=[n],
    )


with st.spinner("正在加载数据…"):
    users_total, users_today, solves_total, answers_total = load_metrics()

col1, col2, col3, col4 = st.columns(4)
col1.metric("注册总人数", f"{users_total:,}")
col2.metric("今日新增用户", f"{users_today:,}")
col3.metric("解题总数", f"{solves_total:,}")
col4.metric("答案库题量", f"{answers_total:,}")

st.divider()

st.subheader("📈 注册人数趋势")
trend_df = load_registration_trend()
if trend_df.empty:
    st.info("暂无注册数据")
else:
    st.plotly_chart(registration_trend(trend_df), use_container_width=True)

st.divider()

left, right = st.columns(2)
with left:
    st.subheader("🕐 最近解题记录")
    recent_solves = load_recent_solves()
    if recent_solves.empty:
        st.info("暂无解题记录")
    else:
        st.dataframe(recent_solves, use_container_width=True, hide_index=True)

with right:
    st.subheader("📚 最近新增答案")
    recent_answers = load_recent_answers()
    if recent_answers.empty:
        st.info("暂无答案数据")
    else:
        st.dataframe(recent_answers, use_container_width=True, hide_index=True)

st.divider()
st.caption("思谛 STDeel WebUI · 仅内网访问 · 所有查询均为只读")
