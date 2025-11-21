"""
Streamlit app
@created October 2025
"""

import streamlit as st
import pandas as pd
import altair as alt


# page configurations
st.set_page_config(page_title="MSSDVB", layout="wide")

st.html("<style>hr {border-color: white;}</style>")

def season_card(season):
    st.subheader(f"{season['season'].iloc[0]} season")
    st.markdown(f"""
    **Matches:** {len(season)}  
    **Record:** {season['result'].eq('W').sum()} -
                    {season['result'].eq('L').sum()} -
                    {season['result'].eq('T').sum()}  
    **Total Kills:** {int(season['kills'].sum())}  
    **Total Aces:** {int(season['aces'].sum())}  
    **Total Digs:** {int(season['digs'].sum())}  
    **Total Blocks:** {int(season['total_blocks'].sum())}  
    """)


# data
@st.cache_data
def load_data():
    df = pd.read_csv("data/NEW_enriched_matches.csv")
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df

df = load_data()
fr = df[df["season"] == "FR"]
so = df[df["season"] == "SO"]
jr = df[df["season"] == "JR"]
sr = df[df["season"] == "SR"]

print(fr.head())


# header
st.markdown("<h1 style='text-align: center;'>A MSSD Volleyball Career</h1>", unsafe_allow_html=True)


# opening "section"
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("<h2 style='text-align: center;'>2016</h2>", unsafe_allow_html=True)
    st.image("images/2016.jpg")

with col2:
    st.markdown("<h2 style='text-align: center;'>2017</h2>", unsafe_allow_html=True)
    st.image("images/2017.JPG")

with col3:
    st.markdown("<h2 style='text-align: center;'>2018</h2>", unsafe_allow_html=True)
    st.image("images/2018.JPG")

with col4:
    st.markdown("<h2 style='text-align: center;'>2019</h2>", unsafe_allow_html=True)
    st.image("images/2019.JPG")


st.divider()


st.markdown("<h2 style='text-align: center;'>2016: Freshman</h2>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>2017: Sophomore</h2>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>2018: Junior</h2>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>2019: Senior</h2>", unsafe_allow_html=True)


st.divider()


st.markdown("<h2 style='text-align: center;'>2016-2019: 4-Year Overview</h2>", unsafe_allow_html=True)
col5, col6, col7, col8 = st.columns(4)

with col5:
    season_card(fr)

with col6:
    season_card(so)

with col7:
    st.subheader(f"{jr['season'].iloc[0]} season")
    st.markdown(f"""
    **Matches:** {len(jr)}  
    **Record:** {jr['result'].eq('W').sum()} -
                    {jr['result'].eq('L').sum()} -
                    {jr['result'].eq('T').sum()}  
    **Total Kills:** {167}  
    **Total Aces:** {120}  
    **Total Digs:** {250}  
    **Total Blocks:** {8}  
    """)

with col8:
    season_card(sr)


st.divider()