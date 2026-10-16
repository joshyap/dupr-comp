from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analysis import (
    DATA_DIR,
    SOURCE_DATE,
    calculate_percentile,
    get_rating_band,
    load_benchmarks,
    load_distribution,
    rating_gap_to_next_benchmark,
    summarize_distribution,
)


st.set_page_config(
    page_title="DUPR Comp | Doubles Rating Analysis",
    page_icon="🎾",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background: #f2f6fb; color: #182b42; }
    [data-testid="stHeader"] { background: rgba(242, 246, 251, .88); }
    .block-container { max-width: 1180px; padding-top: 4rem; padding-bottom: 3rem; }
    .hero-title { color: #182b42; font-size: clamp(2.5rem, 5vw, 4rem); font-weight: 780; letter-spacing: -.06em; line-height: 1.03; margin: .45rem 0 .65rem; }
    .hero-copy { color: #68798d; font-size: 1rem; line-height: 1.6; max-width: 660px; }
    .panel { background: white; border: 1px solid #dce6f0; border-radius: 16px; padding: 1.2rem 1.35rem; }
    .percentile-card { background: #174a7e; border-radius: 16px; color: white; min-height: 220px; padding: 1.5rem; }
    .percentile-label { color: #a8d4f8; font-size: .72rem; font-weight: 750; letter-spacing: .15em; text-transform: uppercase; }
    .percentile-value { color: #cfe8ff; font-size: clamp(3.5rem, 7vw, 5rem); font-weight: 780; letter-spacing: -.07em; line-height: 1.15; }
    .percentile-caption { color: #d8e7f5; font-size: .9rem; line-height: 1.55; }
    .section-title { color: #182b42; font-size: 1.3rem; font-weight: 740; letter-spacing: -.035em; }
    .section-copy { color: #68798d; font-size: .85rem; }
    .scope-box { background: #eaf3fc; border: 1px solid #c9dced; border-radius: 14px; padding: 1rem 1.25rem; color: #526b83; font-size: .84rem; line-height: 1.55; }
    .scope-box strong { color: #294d6d; }
    div[data-testid="stTextInput"] input {
        min-height: 3.25rem;
        border: 1px solid #8aaeca !important;
        border-radius: 10px;
        background: #ffffff !important;
        color: #182b42 !important;
        box-shadow: 0 0 0 1px rgb(57 125 182 / 12%) !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #174a7e !important;
        box-shadow: 0 0 0 3px rgb(23 74 126 / 20%) !important;
    }
    div[data-testid="stMetric"] { background: white; border: 1px solid #dce6f0; border-radius: 12px; padding: .85rem 1rem; }
    div[data-testid="stMetricLabel"] { color: #68798d; }
    .stButton > button, .stDownloadButton > button { border-radius: 9px; }
    a { color: #286da8; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_distribution(DATA_DIR / "doubles_distribution.csv"), load_benchmarks(
        DATA_DIR / "percentile_benchmarks.csv"
    )


distribution, benchmarks = get_data()
summary = summarize_distribution(distribution)


def ordinal(value: int) -> str:
    remainder = value % 100
    if 11 <= remainder <= 13:
        return f"{value}th"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


st.markdown("#### DUPR COMP · DATA ANALYSIS")
st.markdown('<div class="hero-title">Your rating,<br>in the bigger picture.</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-copy">Explore your doubles DUPR against the published active-player '
    'distribution, benchmark percentiles, and rating milestones.</div>',
    unsafe_allow_html=True,
)
st.write("")

with st.container(border=True):
    st.markdown("#### Important context about this data")
    scope_left, scope_right = st.columns(2)
    with scope_left:
        st.markdown(
            "- **Doubles only:** singles ratings are not included.\n"
            "- **Active players:** at least one result in the previous 12 months."
        )
    with scope_right:
        st.markdown(
            "- **DUPR participants, not everyone:** recreational players without logged "
            "results are not represented; rated players may skew more competitive.\n"
            "- **Rounded source figures:** percentages are approximate; values between "
            "published percentile benchmarks are estimates."
        )

st.write("")
input_col, result_col = st.columns([1, 1], gap="large")
with input_col:
    st.markdown('<div class="section-title">Check your standing</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">The rating is used for this session only; it is not stored.</div>', unsafe_allow_html=True)
    raw_rating = st.text_input(
        "Current doubles DUPR rating",
        placeholder="For example, 3.725",
        help="Enter a rating from 2.000 to 8.000.",
    )

rating: float | None = None
rating_error: str | None = None
if raw_rating.strip():
    try:
        rating = float(raw_rating.strip())
    except ValueError:
        rating_error = "Enter a numeric DUPR rating from 2.000 to 8.000."
    else:
        if not 2.0 <= rating <= 8.0:
            rating_error = "Rating must be between 2.000 and 8.000."
            rating = None

if rating_error:
    st.error(rating_error)

if rating is None:
    percentile = None
    band = None
    next_benchmark = None
else:
    percentile = calculate_percentile(rating, benchmarks)
    band = get_rating_band(rating, distribution)
    next_benchmark = rating_gap_to_next_benchmark(rating, benchmarks)

with result_col:
    if rating is None:
        st.markdown(
            '<div class="percentile-card"><div class="percentile-label">Your percentile</div>'
            '<div class="percentile-value">—</div><div class="percentile-caption">'
            'Enter a rating to see your estimated standing.</div></div>',
            unsafe_allow_html=True,
        )
    elif percentile.value is not None:
        rounded_percentile = int(percentile.value + 0.5)
        st.markdown(
            f'<div class="percentile-card"><div class="percentile-label">Estimated percentile</div>'
            f'<div class="percentile-value">{ordinal(rounded_percentile)}</div>'
            f'<div class="percentile-caption">Ahead of about {rounded_percentile}% of active '
            f'DUPR doubles players · approximately top {100 - rounded_percentile}%</div></div>',
            unsafe_allow_html=True,
        )
    else:
        range_label = "below the 3.0 benchmark" if rating < 3.0 else "above the 5.0 benchmark"
        st.markdown(
            f'<div class="percentile-card"><div class="percentile-label">Your percentile</div>'
            f'<div class="percentile-value">N/A</div><div class="percentile-caption">'
            f'Your rating is {range_label}. The source does not provide a precise percentile '
            f'outside 3.0–5.0.</div></div>',
            unsafe_allow_html=True,
        )

st.write("")
if rating is not None:
    metric_cols = st.columns(3)
    metric_cols[0].metric("Current rating", f"{rating:.3f}")
    metric_cols[1].metric("Rating band", band["label"] if band is not None else "—")
    if next_benchmark is not None:
        target, gap = next_benchmark
        metric_cols[2].metric(
            f"Next benchmark · {target:.1f}",
            f"{gap:.3f} points",
            help=f"Published benchmark: {benchmarks.loc[benchmarks['rating'].eq(target), 'percentile'].iloc[0]:.0f}th percentile.",
        )
    else:
        metric_cols[2].metric(
            "Published range",
            "Top benchmark reached" if rating == 5 else "Above source range",
        )

st.write("")
st.markdown('<div class="section-title">The doubles field</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="section-copy">Published distribution of active DUPR doubles players · source snapshot {SOURCE_DATE}.</div>',
    unsafe_allow_html=True,
)

chart_col, benchmark_col = st.columns([1, 1], gap="large")
with chart_col:
    selected_band = get_rating_band(rating, distribution) if rating is not None else None
    selected_band_label = selected_band["label"] if selected_band is not None else None
    distribution_chart = go.Figure(
        go.Bar(
            x=distribution["share_pct"],
            y=distribution["label"],
            orientation="h",
            marker_color=[
                "#174a7e" if band["label"] == selected_band_label
                else "#83aed1"
                for _, band in distribution.iterrows()
            ],
            text=[f"{value:.0f}%" for value in distribution["share_pct"]],
            textposition="outside",
            hovertemplate="%{y}<br>%{x:.0f}% of players<extra></extra>",
        )
    )
    distribution_chart.update_layout(
        title="Player share by rating band",
        xaxis={"title": "Share of active players (%)", "range": [0, 36], "gridcolor": "#e7edf4"},
        yaxis={"title": None, "autorange": "reversed"},
        height=370,
        margin={"l": 5, "r": 30, "t": 60, "b": 45},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#526b83"},
        showlegend=False,
    )
    st.plotly_chart(distribution_chart, width="stretch", config={"displayModeBar": False})
    st.caption(
        f"The 3.0–3.999 bands account for {summary['share_3s']:.0f}% of the published field; "
        f"{summary['share_4_plus']:.0f}% are rated 4.0 or higher."
    )

with benchmark_col:
    benchmark_chart = go.Figure()
    benchmark_chart.add_trace(
        go.Scatter(
            x=benchmarks["rating"],
            y=benchmarks["percentile"],
            mode="lines+markers",
            name="Published benchmarks",
            line={"color": "#397db6", "width": 3},
            marker={"color": "#174a7e", "size": 9},
            customdata=benchmarks["percentile"].map(lambda p: 100 - p),
            hovertemplate="Rating %{x:.1f}<br>%{y}th percentile<br>Top %{customdata}%<extra></extra>",
        )
    )
    if rating is not None and percentile.value is not None:
        benchmark_chart.add_trace(
            go.Scatter(
                x=[rating],
                y=[percentile.value],
                mode="markers",
                name="Your estimate",
                marker={"color": "#ee995e", "size": 14, "line": {"color": "white", "width": 2}},
                hovertemplate=f"Your rating {rating:.3f}<br>Estimated {percentile.value:.1f}th percentile<extra></extra>",
            )
        )
    benchmark_chart.update_layout(
        title="Published rating benchmarks",
        xaxis={"title": "Doubles DUPR rating", "range": [2.8, 5.2], "dtick": 0.5, "gridcolor": "#e7edf4"},
        yaxis={"title": "Percentile", "range": [20, 103], "ticksuffix": "%", "gridcolor": "#e7edf4"},
        height=370,
        margin={"l": 5, "r": 20, "t": 60, "b": 45},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#526b83"},
        showlegend=False,
    )
    st.plotly_chart(benchmark_chart, width="stretch", config={"displayModeBar": False})
    st.caption("Published points are solid markers; the connecting line is a linear interpolation, not a DUPR formula.")

st.markdown('<div class="section-title">Milestones ahead</div>', unsafe_allow_html=True)
st.markdown('<div class="section-copy">Each benchmark marks the bottom of its rating band.</div>', unsafe_allow_html=True)
milestone_view = benchmarks.copy()
milestone_view["Approx. share below"] = milestone_view["percentile"].map(
    lambda value: f"{100 - value:.0f}%"
)
milestone_view["DUPR rating"] = milestone_view["rating"].map(lambda value: f"{value:.1f}")
milestone_view["Percentile"] = milestone_view["percentile"].map(lambda value: f"{value:.0f}th")
display_milestones = milestone_view[["DUPR rating", "Percentile", "Approx. share below"]]
st.dataframe(display_milestones, hide_index=True, width="stretch")

st.markdown(
    f"""
    <div class="section-copy">
    Analysis in Python with pandas and Plotly. Distribution shares sum to
    {distribution["share_pct"].sum():.0f}% (rounded source values).
    Percentiles are interpolated only between published benchmarks.
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()
st.markdown(
    f"Source: [DUPR percentile article](https://www.dupr.com/post/dupr-rating-percentiles-see-how-your-rating-stacks-up-2) · "
    f"snapshot dated {SOURCE_DATE}. Estimates are informational and are not official DUPR calculations."
)
pdf_path = Path(__file__).parent / "source-reference.pdf"
if pdf_path.exists():
    st.download_button(
        "Download source data reference (PDF)",
        data=pdf_path.read_bytes(),
        file_name="dupr-source-data-reference.pdf",
        mime="application/pdf",
    )
