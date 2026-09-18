"""Heuristic chart-type selection over a query result + Plotly rendering."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Validated categorical palette (blue, orange, aqua, yellow, magenta, green,
# violet, red) - fixed order, never cycled/reassigned by rank.
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SEQUENTIAL_BLUE = "#2a78d6"
GRIDLINE = "#e1e0d9"
AXIS = "#c3c2b7"
MUTED = "#898781"
INK = "#0b0b0b"

_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK),
    plot_bgcolor="#fcfcfb",
    paper_bgcolor="#fcfcfb",
    margin=dict(l=40, r=20, t=30, b=40),
)


def _is_datelike(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    name = str(series.name).lower()
    return any(k in name for k in ("date", "time", "month", "year", "day"))


def _style_axes(fig):
    fig.update_xaxes(showgrid=False, showline=True, linecolor=AXIS, tickfont=dict(color=MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, zeroline=False, tickfont=dict(color=MUTED))
    return fig


def build_chart(df: pd.DataFrame):
    """Returns a Plotly figure, or None if no sensible chart applies."""
    if df is None or df.empty:
        return None

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    other_cols = [c for c in df.columns if c not in numeric_cols]

    # 1x1 scalar result: no chart, caller should render a metric instead.
    if df.shape[0] == 1 and df.shape[1] <= 2:
        return None

    date_cols = [c for c in other_cols if _is_datelike(df[c])] + [
        c for c in numeric_cols if _is_datelike(df[c])
    ]

    # date-like + numeric -> line chart
    if date_cols and numeric_cols:
        x = date_cols[0]
        y = numeric_cols[0] if numeric_cols[0] != x else (numeric_cols[1] if len(numeric_cols) > 1 else None)
        if y is None:
            return None
        plot_df = df.sort_values(x)
        fig = px.line(plot_df, x=x, y=y, markers=True, color_discrete_sequence=[SEQUENTIAL_BLUE])
        fig.update_traces(line=dict(width=2))
        fig.update_layout(**_LAYOUT)
        return _style_axes(fig)

    categorical_cols = [c for c in other_cols if c not in date_cols and df[c].nunique() <= 30]

    # low-cardinality categorical + numeric -> bar chart
    if categorical_cols and numeric_cols:
        x, y = categorical_cols[0], numeric_cols[0]
        plot_df = df[[x, y]].sort_values(y, ascending=False)
        fig = px.bar(plot_df, x=x, y=y, color_discrete_sequence=[SEQUENTIAL_BLUE])
        fig.update_traces(marker_line_width=0)
        fig.update_layout(**_LAYOUT)
        return _style_axes(fig)

    # two numeric columns, no date/category -> scatter
    if len(numeric_cols) >= 2:
        x, y = numeric_cols[0], numeric_cols[1]
        fig = px.scatter(df, x=x, y=y, color_discrete_sequence=[SEQUENTIAL_BLUE])
        fig.update_traces(marker=dict(size=9))
        fig.update_layout(**_LAYOUT)
        return _style_axes(fig)

    return None
