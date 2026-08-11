import plotly.graph_objects as go
import plotly.express as px

CHART_COLORS = {
    'primary': '#5b9fff',
    'success': '#4fd1a5',
    'warning': '#f0b24b',
    'danger': '#f06565',
    'purple': '#b794f4',
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#e4e7ee', size=13),
    margin=dict(l=40, r=20, t=40, b=40),
)


def registration_trend(df):
    fig = go.Figure(go.Scatter(
        x=df['date'], y=df['cumulative'],
        mode='lines+markers', line=dict(color=CHART_COLORS['primary'], width=2),
        fill='tozeroy', fillcolor='rgba(91,159,255,0.1)',
    ))
    fig.update_layout(title='注册人数趋势', **PLOTLY_LAYOUT)
    return fig


def knowledge_radar(labels, values):
    if not labels or not values:
        fig = go.Figure()
        fig.update_layout(title='知识点掌握度', **PLOTLY_LAYOUT)
        return fig
    closed_theta = labels + [labels[0]]
    closed_r = values + [values[0]]
    fig = go.Figure(go.Scatterpolar(
        r=closed_r,
        theta=closed_theta,
        fill='toself',
        line=dict(color=CHART_COLORS['success']),
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 100])),
        title='知识点掌握度',
        **PLOTLY_LAYOUT,
    )
    return fig


def mastery_bar(df):
    fig = px.bar(
        df, x='knowledge_point', y='correct_rate',
        color_discrete_sequence=[CHART_COLORS['primary']],
    )
    fig.update_layout(title='各知识点正确率', **PLOTLY_LAYOUT)
    return fig


def solve_timeline(df):
    fig = px.bar(
        df, x='date', y='count',
        color_discrete_sequence=[CHART_COLORS['purple']],
    )
    fig.update_layout(title='每日解题数', **PLOTLY_LAYOUT)
    return fig


def weak_points_bar(df):
    fig = px.bar(
        df, x='knowledge_point', y='error_rate',
        color_discrete_sequence=[CHART_COLORS['danger']],
    )
    fig.update_layout(title='薄弱知识点（按错误率）', **PLOTLY_LAYOUT)
    return fig


def heatmap(df):
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title='知识点掌握度热力图', **PLOTLY_LAYOUT)
        return fig
    pivot = df.pivot_table(
        index='username', columns='knowledge_point',
        values='correct_rate', aggfunc='mean',
    ).sort_index().sort_index(axis=1)
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale='RdYlGn',
        zmin=0, zmax=100,
    ))
    fig.update_layout(title='用户 × 知识点 掌握度热力图', **PLOTLY_LAYOUT)
    return fig
