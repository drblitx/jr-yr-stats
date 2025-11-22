"""
Streamlit app
@created October 2025
"""

import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px


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


# header
st.markdown("<h1 style='text-align: center;'>A MSSD Volleyball Career</h1>", unsafe_allow_html=True)


# opening "section"
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("<h2 style='text-align: center;'>2016</h2>", unsafe_allow_html=True)
    st.image("images/2016.jpg", "SpikeOut XVIII @ Indiana")

with col2:
    st.markdown("<h2 style='text-align: center;'>2017</h2>", unsafe_allow_html=True)
    st.image("images/2017.JPG", "SpikeOut XIX @ Maryland")

with col3:
    st.markdown("<h2 style='text-align: center;'>2018</h2>", unsafe_allow_html=True)
    st.image("images/2018.JPG", "SpikeOut XX @ Model Secondary")

with col4:
    st.markdown("<h2 style='text-align: center;'>2019</h2>", unsafe_allow_html=True)
    st.image("images/2019.JPG", "SpikeOut XXI @ Riverside")


st.divider()


# at a glance section
st.markdown("<h2 style='text-align: center;'>At a Glance: 2016-2019</h2>", unsafe_allow_html=True)
df_nojr = df[df['career_stage'].notna() & (df['season'] != 'JR')]
year_colors = {
    'early': "#0c6cb1",
    'mid': "#ffffff",
    'late': "#e83717"
}

# k/s
st.subheader("Kills Per Set")
col9, col10, col11 = st.columns(3)
with col9:
    st.metric("Average Kills/Set", round(df_nojr["kills_per_set"].mean(), 2))

with col10:
    st.metric("Highest Kills/Set", df_nojr["kills_per_set"].max())

with col11:
    st.metric("Most Consistent Stretch", round(df_nojr["kills_per_set"].rolling(5).std().min(), 2))

chart = (
    alt.Chart(df_nojr)
    .mark_line(point=True)
    .encode(
        x=alt.X('career_match_index:Q', title='Career Match Index'),
        y=alt.Y('kills_per_set:Q', title='Kills Per Set'),
        color=alt.Color(
            'career_stage:N',
            scale=alt.Scale(domain=list(year_colors.keys()), range=list(year_colors.values())),
            title='Year'
        ),
        tooltip=['opponent', 'career_match_index', 'kills_per_set']
    )
    .properties(width=700, height=400)
)

st.altair_chart(chart, use_container_width=True)

# d/s
st.subheader("Digs Per Set")
col9, col10, col11 = st.columns(3)
with col9:
    st.metric("Average Digs/Set", round(df_nojr["digs_per_set"].mean(), 2))

with col10:
    st.metric("Highest Digs/Set", df_nojr["digs_per_set"].max())

with col11:
    st.metric("Most Consistent Stretch", round(df_nojr["digs_per_set"].rolling(5).std().min(), 2))

chart = (
    alt.Chart(df_nojr)
    .mark_line(point=True)
    .encode(
        x=alt.X('career_match_index:Q', title='Career Match Index'),
        y=alt.Y('digs_per_set:Q', title='Digs Per Set'),
        color=alt.Color(
            'career_stage:N',
            scale=alt.Scale(domain=list(year_colors.keys()), range=list(year_colors.values())),
            title='Year'
        ),
        tooltip=['opponent', 'career_match_index', 'digs_per_set']
    )
    .properties(width=700, height=400)
)

st.altair_chart(chart, use_container_width=True)

# a/s
st.subheader("Aces Per Set")
col9, col10, col11 = st.columns(3)
with col9:
    st.metric("Average Aces/Set", round(df_nojr["aces_per_set"].mean(), 2))

with col10:
    st.metric("Highest Aces/Set", df_nojr["aces_per_set"].max())

with col11:
    st.metric("Most Consistent Stretch", round(df_nojr["aces_per_set"].rolling(5).std().min(), 2))

chart = (
    alt.Chart(df_nojr)
    .mark_line(point=True)
    .encode(
        x=alt.X('career_match_index:Q', title='Career Match Index'),
        y=alt.Y('aces_per_set:Q', title='Aces Per Set'),
        color=alt.Color(
            'career_stage:N',
            scale=alt.Scale(domain=list(year_colors.keys()), range=list(year_colors.values())),
            title='Year'
        ),
        tooltip=['opponent', 'career_match_index', 'aces_per_set']
    )
    .properties(width=700, height=400)
)

st.altair_chart(chart, use_container_width=True)


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

# retrospective section
st.markdown("<h2 style='text-align: center;'>In Retrospective</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center;'>Four years went by in a blink. Looking back almost 10 years after I started, I had an incredible " \
    "career. None of this would have been possible without the people who saw me through from day one to " \
    "the very last one. You know who you are -- thank you. Here's my career in retrospective with all the photos, honors, "
    "awards, and things learned below.</p>", unsafe_allow_html=True
)

st.subheader("Awards & Honors")
st.markdown("""
    - 2016-2017 MSSD Female Rookie of the Year  
    - 2017 SpikeOut XIX All-Tournament Team  
    - 2017 MSSD Volleyball Most Outstanding Player  
    - 2017 Potomac Valley Athletic Conference Volleyball 1st Team All-Conference Selection  
    - 2017 National Deaf Interscholastic Athletic Association Volleyball First Team All-American  
    - 2017-2018 MSSD Female Student-Athlete of the Year  
    - 2018 Spikeout XX All-Tournament Team  
    - 2018 DeafDigest Volleyball All-American  
    - 2018 Potomac Valley Athletic Conference Volleyball 1st Team All-Conference Selection  
    - 2018-2019 MSSD Female Student-Athlete of the Year  
    - 2019 Deaf Elite Volleyball Camp Best Pepper Award  
    - 2019 Deaf Elite Volleyball Camp Believe & Achieve Award  
    - 2019 Oriole Volleyball Classic All-Star  
    - 2019 Model Volleyball Invitational Tournament All-Star  
    - 2019 SpikeOut XXI All-Tournament Team  
    - 2019 Wilson Tiger Paws Volleyball Tournament All-Star  
    - 2019 Potomac Valley Athletic Conference Volleyball 1st Team All-Conference Selection  
    - 2019 Potomac Valley Athletic Conference Volleyball Most Valuable Player  
    - 2019 District of Columbia State Athletica Association Volleyball All-Star  
    - 2019 National Deaf Interscholastic Athletic Association Volleyball First Team All-American  
    - 2019 District of Columbia State Athletic Association Fall All-State (Volleyball)
"""
)

st.subheader("What I Learned")
st.markdown("To be added later.")

st.subheader("Photo Gallery")
items = [
    ("images/2018_allstar.jpg", "SpikeOut XX All-Star"),
    ("images/2019_allstar1.jpg", "2019 Oriole Classic All-Star"),
    ("images/2019_dcsaa.jpg", "DCSAA All-Star 2019"),
    ("images/champ.jpg", "2019 PVAC Champs... finally!"),
    ("images/hc2019.jpg", "Homecoming 2019"),
    ("images/mvp.jpg", "2019 PVAC MVP"),
    ("images/team.jpg", "2017 DCSAA Runner-Ups"),
    ("images/lastsrgame.jpg", "Last-ever MSSD postgame circle, 2019"),
    ("images/pvacrunners.jpg", "2017 PVAC Runner-Ups")
]

cols = st.columns(3)

for i, (img_path, caption) in enumerate(items):
    with cols[i % 3]:
        st.image(img_path, caption=caption, use_container_width=True)
