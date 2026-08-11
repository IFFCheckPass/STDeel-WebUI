import io
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="解题记录 · STDeel",
    page_icon="📝",
    layout="wide",
)

st.title("📝 解题记录浏览")

from db import query_df


@st.cache_data(ttl=30)
def load_all_solves():
    return query_df(
        "SELECT sr.id, sr.created_at, u.username, "
        "substr(sr.question, 1, 50) as question_summary, sr.question, "
        "sr.answer, sr.explanation, sr.knowledge_points, sr.image_path, "
        "sr.ai_model, sr.latency_ms, sr.user_feedback "
        "FROM solve_records sr LEFT JOIN users u ON u.id = sr.user_id "
        "ORDER BY sr.created_at DESC"
    )


solves_df = load_all_solves()

if solves_df.empty:
    st.info("暂无解题记录")
    st.stop()

st.sidebar.header("🔎 筛选条件")

all_usernames = solves_df["username"].dropna().unique().tolist()
selected_user = st.sidebar.selectbox(
    "👤 按用户", ["全部"] + sorted(all_usernames)
)

min_date = pd.to_datetime(solves_df["created_at"]).min().date()
max_date = pd.to_datetime(solves_df["created_at"]).max().date()
date_left, date_right = st.sidebar.date_input(
    "📅 日期范围", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

feedback_options = ["全部", "正确", "错误", "未反馈"]
feedback_map = {
    "正确": "correct",
    "错误": "wrong",
    "未反馈": None,
}
selected_feedback = st.sidebar.selectbox("✅ 反馈状态", feedback_options)

all_models = solves_df["ai_model"].dropna().unique().tolist()
selected_model = st.sidebar.selectbox(
    "🤖 AI 模型", ["全部"] + sorted(all_models)
)

df = solves_df.copy()

if selected_user != "全部":
    df = df[df["username"] == selected_user]

if isinstance(date_left, tuple):
    date_left, date_right = date_left

if date_left and date_right:
    dt_col = pd.to_datetime(df["created_at"])
    df = df[(dt_col.dt.date >= date_left) & (dt_col.dt.date <= date_right)]

if selected_feedback != "全部":
    fb_val = feedback_map[selected_feedback]
    if fb_val is None:
        df = df[df["user_feedback"].isna() | (df["user_feedback"] == "")]
    else:
        df = df[df["user_feedback"] == fb_val]

if selected_model != "全部":
    df = df[df["ai_model"] == selected_model]

st.caption(f"筛选结果：**{len(df)}** 条记录")

display_cols = ["created_at", "username", "question_summary",
                "ai_model", "latency_ms", "user_feedback"]
st.dataframe(
    df[display_cols].rename(columns={
        "created_at": "时间",
        "username": "用户",
        "question_summary": "题目摘要",
        "ai_model": "AI 模型",
        "latency_ms": "耗时(ms)",
        "user_feedback": "反馈",
    }),
    use_container_width=True,
    hide_index=True,
)

st.divider()
st.subheader("🔍 记录详情")

for _, row in df.iterrows():
    with st.expander(
        f"[{row['created_at']}] {row.get('username', '—')} · "
        f"{row.get('ai_model', '—')} · {row.get('user_feedback', '未反馈')}"
    ):
        st.markdown(f"**耗时：** {row.get('latency_ms', '—')} ms")
        st.markdown(f"**图片路径：** `{row.get('image_path', '')}`")
        st.markdown("**完整题目：**")
        st.write(row.get("question", ""))
        st.markdown("**完整答案：**")
        st.write(row.get("answer", ""))
        if row.get("explanation"):
            st.markdown("**解答过程：**")
            st.write(row["explanation"])
        if row.get("knowledge_points"):
            st.markdown("**知识点：**")
            st.write(row["knowledge_points"])

st.divider()

csv_buf = io.StringIO()
df.to_csv(csv_buf, index=False, encoding="utf-8-sig")
st.download_button(
    label="⬇️ 导出 CSV",
    data=csv_buf.getvalue(),
    file_name=f"solve_records_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
)
