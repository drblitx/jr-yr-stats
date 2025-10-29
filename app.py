"""
Streamlit app
@created October 2025
"""

import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="MSSDVB", layout="wide")

# data
@st.cache_data
def load_data():
    df = pd.read_csv("data/NEW_enriched_matches.csv")
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df

df = load_data()

# header
st.title("A MSSD Volleyball Career")
st.markdown("Let's take a look at my volleyball career at MSSD! Scroll down to go through the years.")

def show_season(season, color):
    season_df = df[df["season"] == season]
    st.header(f"{season_df['season_stage'].iloc[0].capitalize()} Year ({season})")
    st.caption(f"Matches played: {len(season_df)} | Wins: {season_df['result'].eq('W').sum()} | Losses: {season_df['result'].eq('L').sum()}")

    # Plot match results
    chart = alt.Chart(season_df).mark_circle(size=100).encode(
        x=alt.X("career_match_index", title="Career Match #"),
        y=alt.Y("margin_pct", title="Win Margin %"),
        color=alt.Color("result", scale=alt.Scale(domain=["W","L"], range=["#2ecc71","#e74c3c"])),
        tooltip=["date", "opponent", "set_scores", "result", "margin_pct"]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

    # Highlight milestones
    milestones = season_df[season_df["milestone_flag"].notna()]
    if not milestones.empty:
        st.subheader("Milestone Matches")
        for _, row in milestones.iterrows():
            st.markdown(f"- **{row['event_name']}** on {row['date'].strftime('%b %d, %Y')} vs {row['opponent']}")
    else:
        st.info("No milestone matches recorded this season.")

    # Show a few highlights
    st.subheader("Season Highlights")
    st.dataframe(season_df[[
        "date","opponent","result","set_scores","kills","aces","digs","total_blocks","points"
    ]].sort_values("date"))

    st.markdown("---")

# 2016
st.header("2016: Freshman")
show_season("FR", "#3498db")

# 2017
st.header("2017: Sophomore")
show_season("SO", "#9b59b6")

# 2018
st.header("2018: Junior")
show_season("JR", "#f39c12")

# 2019
st.header("2019: Senior")
show_season("SR", "#e74c3c")