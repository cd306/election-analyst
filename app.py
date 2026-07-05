"""Streamlit web UI for Election Analyst.

Run with: streamlit run app.py
"""

import matplotlib.pyplot as plt
import streamlit as st

import map as mapviz
import pipeline
import report
from contests import CONTESTS, DISTRICT_TYPES, ContestConfig, DistrictType


@st.cache_resource
def cached_run_analysis(contest: ContestConfig, district: DistrictType):
    """Cache pipeline results so re-selecting the same contest skips the work."""
    return pipeline.run_analysis(contest, district)


st.set_page_config(page_title="Election Analyst", page_icon="🗳️", layout="wide")

st.title("🗳️ Election Analyst")
st.caption(
    "Stratify any election result by political subdivision — "
    "San Diego County, Nov 2024 · "
    "[Source code](https://github.com/cd306/election-analyst)"
)

col1, col2 = st.columns(2)
with col1:
    contest = st.selectbox(
        "Contest",
        CONTESTS,
        format_func=lambda c: c.label,
    )
with col2:
    district = st.selectbox(
        "District type",
        DISTRICT_TYPES,
        format_func=lambda d: d.label,
    )

if st.button("Run Analysis", type="primary"):
    with st.spinner("Running pipeline (downloads cached after first run)..."):
        results, districts = cached_run_analysis(contest, district)

    title = f"{contest.label} · by {district.label}"
    st.subheader(title)

    tab_table, tab_map = st.tabs(["Table", "Map"])

    with tab_table:
        display = results[
            ["district_num", "yes_votes", "no_votes", "total_votes",
             "yes_pct", "no_pct", "margin_pct", "passed"]
        ].rename(columns={
            "district_num": "District",
            "yes_votes": f"{contest.choice_a_label} Votes",
            "no_votes": f"{contest.choice_b_label} Votes",
            "total_votes": "Total Votes",
            "yes_pct": f"{contest.choice_a_label} %",
            "no_pct": f"{contest.choice_b_label} %",
            "margin_pct": "Margin %",
            "passed": "Passed",
        })
        st.dataframe(display, use_container_width=True, hide_index=True)

        st.download_button(
            "Download CSV",
            results.to_csv(index=False),
            file_name=f"{contest.name}-by-{district.name}.csv",
            mime="text/csv",
        )

    with tab_map:
        fig = mapviz.make_choropleth(
            results,
            districts,
            value_col="yes_pct",
            title=title,
            cmap_colors=contest.cmap_colors,
            legend_label=contest.legend_label,
        )
        st.pyplot(fig)
        plt.close(fig)
