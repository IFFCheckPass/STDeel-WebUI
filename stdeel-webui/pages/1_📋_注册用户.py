import streamlit as st

st.set_page_config(
    page_title="注册用户管理 · STDeel",
    page_icon="📋",
    layout="wide",
)

st.title("📋 注册用户管理")

from db import query_df


@st.cache_data(ttl=30)
def load_users():
    return query_df(
        "SELECT u.id, u.username, u.device_id, u.created_at, u.last_active_at, "
        "COUNT(sr.id) as solve_count, "
        "SUM(CASE WHEN sr.user_feedback = 'correct' THEN 1 ELSE 0 END) as correct_count, "
        "SUM(CASE WHEN sr.user_feedback = 'wrong' THEN 1 ELSE 0 END) as wrong_count "
        "FROM users u "
        "LEFT JOIN solve_records sr ON sr.user_id = u.id "
        "GROUP BY u.id"
    )


users_df = load_users()

search = st.text_input("🔍 按用户名搜索", placeholder="输入用户名关键字…")
sort_by = st.selectbox(
    "排序方式",
    ["注册时间", "解题数", "最后活跃时间"],
)

df = users_df.copy()

if search and not df.empty:
    df = df[df['username'].str.contains(search, case=False, na=False)]

if sort_by == "注册时间":
    df = df.sort_values("created_at", ascending=False)
elif sort_by == "解题数":
    df = df.sort_values("solve_count", ascending=False)
elif sort_by == "最后活跃时间":
    df = df.sort_values("last_active_at", ascending=False)

st.write(f"共 **{len(df)}** 位注册用户")

if df.empty:
    st.info("暂无用户数据")
else:
    display_cols = ["username", "device_id", "created_at", "last_active_at",
                    "solve_count", "correct_count", "wrong_count"]
    st.dataframe(
        df[display_cols].rename(columns={
            "username": "用户名",
            "device_id": "设备ID",
            "created_at": "注册时间",
            "last_active_at": "最后活跃时间",
            "solve_count": "解题总数",
            "correct_count": "正确数",
            "wrong_count": "错误数",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.subheader("🔗 查看用户学习账本")
    selected = st.selectbox(
        "选择用户",
        df["username"].tolist(),
    )
    if st.button("前往学习账本 →"):
        user_row = df[df["username"] == selected].iloc[0]
        st.query_params["user_id"] = str(int(user_row["id"]))
        st.switch_page("pages/2_📒_学习账本.py")
