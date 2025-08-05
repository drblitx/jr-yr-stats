"""
@name schedule_cleaning.py
@created July 2025
"""

import pandas as pd

def detect_comeback(set_scores, result):
    if pd.isna(set_scores) or pd.isna(result):
        return False
    try:
        sets = [int(s.split("-")[0]) < int(s.split("-")[1]) for s in set_scores.split(",")]
        return sets[0] and result == "W"
    except:
        return False

# load in raw master schedule
df = pd.read_csv("data/schedules/master_schedule.csv")

# parse/standardize dates of matches
df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")
df["day_of_week"] = df["date"].dt.day_name()

# changing Jackson-Reed back to Woodrow Wilson
df["opponent"] = df["opponent"].replace("Jackson-Reed", "Woodrow Wilson")

# labeling seasons
year_to_season = {
    2016: "FR",
    2017: "SO",
    2018: "JR",
    2019: "SR"
}
df["season"] = df["date"].dt.year.map(year_to_season)

# slugs of opponents; using abbreviations dict
opponent_slug_map = {
    "Alabama School for the Deaf": "AIDB",
    "Atlanta Area School for the Deaf": "AASD",
    "Barrie": "BARRIE",
    "Bell": "BELL",
    "Berman Hebrew Academy": "BHA",
    "Bishop Ireton": "BIHS",
    "Bishop O'Connell": "BOHS",
    "Brookewood": "BW",
    "Bullis": "BULLIS",
    "Burke": "BURKE",
    "California School for the Deaf": "CSDF",
    "California School for the Deaf-Riverside": "CSDR",
    "Clinton Grace Christian": "CGC",
    "Connelly School of the Holy Child": "CSHC",
    "Covenant Life": "CL",
    "DC International": "DCI",
    "E.L. Haynes": "HAYNES",
    "Episcopal": "EPISCOPAL",
    "Field": "FIELD",
    "Florida School for the Deaf & Blind": "FSDB",
    "Fredericksburg Christian": "FCHS",
    "Friends": "FRIENDS",
    "Georgetown Day": "GTD",
    "Grace Christian": "GC",
    "Grace Christian Academy": "GCA",
    "Highland": "HIGHLAND",
    "Indiana School for the Deaf": "ISD",
    "Interlachen": "INTERLACHEN",
    "Islamic Saudi Academy": "ISA",
    "King Abdullah Academy": "KAA",
    "Maret": "MARET",
    "Maryland School for the Deaf": "MSD",
    "McLean": "MCLEAN",
    "Mississippi School for the Deaf": "MISD",
    "Mount Airy Christian Academy": "MACA",
    "Oakcrest": "OAKCREST",
    "Pallotti": "PALLOTTI",
    "Parkside": "PARKSIDE",
    "Princess Anne": "PA",
    "River City Science Academy": "RCSA",
    "Riverdale Baptist": "RB",
    "Roosevelt": "ROOSEVELT",
    "Sandy Spring Friends": "SSFS",
    "School Without Walls": "SWW",
    "Seton School": "SETON",
    "Shalom Christian Academy": "SCA",
    "Sidwell Friends": "SIDWELL",
    "Smith Jewish Day School": "SJDS",
    "Spencerville Adventist Academy": "SAA",
    "St. John's": "SJ",
    "St. John's Catholic Prep": "SJCP",
    "Stone Ridge School of the Sacred Heart": "SRSSH",
    "StoneBridge": "SB",
    "Takoma Academy": "TA",
    "Texas School for the Deaf": "TSD",
    "Varsity Opponent": "VO",
    "Washington Christian Academy": "WCA",
    "Washington International": "WIS",
    "Woodrow Wilson": "WILSON",
}
df["opponent_slug"] = df["opponent"].map(opponent_slug_map)

# rivalries
rival_opponents = ["MSD", "WIS", "CL"] # deaf, pvac, general rivals
df["rivalry"] = df["opponent_slug"].isin(rival_opponents)

# check for any unmapped opponents
unmapped = df[df["opponent_slug"].isnull()]["opponent"].unique()
if len(unmapped) > 0:
    print("WARNING: Unmapped opponents found. Please update your slug map:")
    for opponent in unmapped:
        print(f'    "{opponent}": "",')
    raise ValueError("STOP: unmapped opponents need to be filled in.")

# forfeited, out sick, out injured matches
forfeited_matches = [
    ("2016-09-24", "Connelly School of the Holy Child"),
    ("2019-10-21", "McLean")]
sick_dates = pd.to_datetime(['2016-09-27', '2017-09-18'])
injured_dates = pd.to_datetime(['2017-11-07', '2017-11-08'])

df["forfeited"] = df.apply(
    lambda row: (row["date"].strftime("%Y-%m-%d"), row["opponent"]) in forfeited_matches,
    axis=1
)
df["sick"] = df["date"].isin((sick_dates))
df["injured"] = df["date"].isin((injured_dates))

# count of matches per day
df["match_no"] = df.groupby("date").cumcount() + 1
df["total_matches_that_day"] = df.groupby("date")["date"].transform("count")
df["same_day_opponent_seq"] = df.groupby(["date", "opponent"]).cumcount() + 1
df["season_opponent_seq"] = df.groupby(["season", "opponent"]).cumcount() + 1
df["is_repeat_opponent"] = df["season_opponent_seq"] > 1

# match key
df["match_key"] = (
    df["season"].astype(str)
    + "_" + df["date"].dt.strftime("%m-%d")
    + "_" + df["opponent_slug"].str.replace(r'\W+', '', regex=True)
    + "_" + df["match_no"].astype(str)
)

# game importances
tournament_dates = ['2016-09-09', # FSDB Invitational 2016
                    '2016-09-24', # Model Invitational 2016
                    '2016-10-07', # SpikeOut 2016 @ Indiana
                    '2016-10-08', # SpikeOut 2016 @ Indiana
                    '2017-09-23', # Model Invitational 2017
                    '2017-10-06', # SpikeOut 2017 @ Maryland
                    '2017-10-07', # SpikeOut 2017 @ Maryland
                    '2018-09-08', # Fredericksburg Inviational 2018
                    '2018-09-22', # Model Invitational 2018
                    '2018-10-05', # Spikeout 2018 @ Model
                    '2018-10-06', # Spikeout 2018 @ Model
                    '2019-09-07', # Fredericksburg Invitational 2019
                    '2019-09-14', # MSD's Oriole Classic 2019
                    '2019-09-21', # Model Invitational 2019
                    '2019-10-04', # Spikeout 2019 @ Riverside
                    '2019-10-05', # Spikeout 2019 @ Riverside
                    '2019-10-12', # Wilson Tiger Paws Invitational 2019
                    ]

pvac_champs = ['2017-10-30', '2018-10-29', '2019-10-30']
dcsaa_champs = ['2016-11-11']
spikeout_champ_keys = ["senior_10-05_TSD_2"]

df["is_championship"] = (
    df["date"].isin(pd.to_datetime(pvac_champs + dcsaa_champs)) |
    df["match_key"].isin(spikeout_champ_keys)
)

def infer_match_type(row):
    if row["forfeited"]:
        return "forfeit"
    if row["injured"]:
        return "injured"
    if row["sick"]:
        return "sick"
    if row["is_championship"]:
        return "championship"
    if row["is_playoffs"]:
        return "playoff"
    if row["date"] in tournament_dates:
        return "tournament_pool"  # will upgrade some manually to "tournament_bracket"
    if row["is_conference"]:
        return "regular"
    return "regular"

df["match_type"] = df.apply(infer_match_type, axis=1)

importance_map = {
    "regular": ("low", 0),
    "tournament_pool": ("normal", 1),
    "tournament_bracket": ("normal", 1),
    "playoff": ("high", 2),
    "championship": ("high", 3),
    "forfeit": ("low", 0),
    "injured": ("low", 0),
    "sick": ("low", 0)
}
df["game_importance"] = df["match_type"].map(lambda x: importance_map.get(x, ("low", 0))[0])
df["game_importance_score"] = df["match_type"].map(lambda x: importance_map.get(x, ("low", 0))[1])

# event names
event_name_map = {
    '2016-09-09': "FSDB Invitational 2016",
    '2016-09-24': "Model Invitational 2016",
    '2016-10-07': "SpikeOut 2016 @ Indiana",
    '2016-10-08': "SpikeOut 2016 @ Indiana",
    '2016-11-09': "DCSAA State Tournament Quarterfinals",
    '2016-11-10': "DCSAA State Tournament Semifinals",
    '2016-11-11': "DCSAA State Tournament Championship",
    '2017-09-23': "Model Invitational 2017",
    '2017-10-06': "SpikeOut 2017 @ Maryland",
    '2017-10-07': "SpikeOut 2017 @ Maryland",
    '2017-10-23': "PVAC Tournament Quarterfinals",
    '2017-10-25': "PVAC Tournament Semifinals",
    '2017-10-30': "PVAC Tournament Championship",
    '2017-11-07': "DCSAA State Tournament First Round",
    '2017-11-08': "DCSAA State Tournament Quarterfinals",
    '2018-09-08': "Fredericksburg Invitational 2018",
    '2018-09-22': "Model Invitational 2018",
    '2018-10-05': "SpikeOut 2018 @ Model",
    '2018-10-06': "SpikeOut 2018 @ Model",
    '2018-10-22': "PVAC Tournament Quarterfinals",
    '2018-10-29': "PVAC Tournament Championship",
    '2018-11-06': "DCSAA State Tournament First Round",
    '2019-09-07': "Fredericksburg Invitational 2019",
    '2019-09-14': "Oriole Classic 2019 @ Maryland",
    '2019-09-21': "Model Invitational 2019",
    '2019-10-04': "SpikeOut 2019 @ Riverside",
    '2019-10-05': "SpikeOut 2019 @ Riverside",
    '2019-10-12': "Tiger Paws Invitational 2019 @ Wilson",
    '2019-10-23': "PVAC Tournament Quarterfinals",
    '2019-10-28': "PVAC Tournament Semifinals",
    '2019-10-30': "PVAC Tournament Championship",
    '2019-11-05': "DCSAA State Tournament First Round",
    '2019-11-06': "DCSAA State Tournament Quarterfinals"
}
df["event_name"] = df["date"].dt.strftime("%Y-%m-%d").map(event_name_map)

# revenge matches (lost game, won next one against same team)
df = df.sort_values(by="date").copy()
df["prev_result_vs_opponent"] = (
    df.groupby(["season", "opponent"])["result"].shift(1)
)
df["revenge_match"] = (df["prev_result_vs_opponent"] == "L") & (df["result"] == "W")

# comeback wins
df["comeback_win"] = df.apply(lambda row: detect_comeback(row["set_scores"], row["result"]), axis=1)

# redemption games (lost last season, won next season)
df["previous_season"] = df["season"].map({"SO": "FR", "JR": "SO", "SR": "JR"})

prior_season_results = (
    df.sort_values("date")
      .groupby(["season", "opponent"])
      .last()
      .reset_index()[["season", "opponent", "result"]]
)
prior_season_results.columns = ["previous_season", "opponent", "prev_season_result"]

df = df.merge(prior_season_results, on=["previous_season", "opponent"], how="left")
df["redemption_game"] = (
    (df["prev_season_result"] == "L") &
    (df["result"] == "W")
)

# add favorite match & birthday match flags
df["favorite_match"] = False
df["birthday_match"] = df["date"].dt.strftime("%m-%d") == "09-21"

# career match index
df = df.sort_values(by="date").reset_index(drop=True)
df["career_match_index"] = df.index + 1

# season match #
df["season_match_number"] = df.groupby("season").cumcount() + 1

# week of season #
df["week_of_season"] = (
    df["date"] - df.groupby("season")["date"].transform("min")
).dt.days // 7 + 1

# days since last match
df["days_since_last_match"] = df["date"].diff().dt.days.fillna(0).astype(int)

# back to back?
df["is_back_to_back"] = df["days_since_last_match"] == 1

# match density
df["match_density_3days"] = df["date"].apply(
    lambda d: ((df["date"] >= d - pd.Timedelta(days=2)) & (df["date"] <= d)).sum()
)

# 1st/last match of day
df["first_match_of_day"] = df.apply(
    lambda row: True if row["match_no"] == 1 and row["total_matches_that_day"] > 1 else (
        False if row["match_no"] != 1 and row["total_matches_that_day"] > 1 else pd.NA
    ),
    axis=1
)
df["last_match_of_day"] = df.apply(
    lambda row: True if row["match_no"] == row["total_matches_that_day"] and row["total_matches_that_day"] > 1 else (
        False if row["match_no"] != row["total_matches_that_day"] and row["total_matches_that_day"] > 1 else pd.NA
    ),
    axis=1
)

# season stage
df["season_stage"] = (
    df.groupby("season")["season_match_number"]
    .transform(lambda x: pd.qcut(x, q=3, labels=["early", "mid", "late"]))
)

# career stage (25, 50, 75)
df["career_stage"] = pd.qcut(
    df["career_match_index"],
    q=[0, 0.25, 0.75, 1.0],
    labels=["early", "mid", "late"]
)

# multi match day
df["multi_game_day"] = df["total_matches_that_day"] > 1

# milestone flags
df["milestone_flag"] = ""

df.loc[df["career_match_index"] == 1, "milestone_flag"] = "first MSSD match"

first_season_match = df.groupby("season")["season_match_number"].idxmin()
df.loc[first_season_match, "milestone_flag"] = df.loc[first_season_match, "milestone_flag"].apply(
    lambda x: x + "; " if x else ""
) + df.loc[first_season_match, "season"].map(lambda s: f"first {s} match")

last_season_match = df.groupby("season")["season_match_number"].idxmax()
df.loc[last_season_match, "milestone_flag"] = df.loc[last_season_match, "milestone_flag"].apply(
    lambda x: x + "; " if x else ""
) + df.loc[last_season_match, "season"].map(lambda s: f"last {s} match")

df.loc[df["career_match_index"] == df["career_match_index"].max(), "milestone_flag"] = df.loc[
    df["career_match_index"] == df["career_match_index"].max(), "milestone_flag"
].apply(lambda x: x + "; " if x else "") + "last MSSD match"

# set info
df["was_set_swept"] = (df["result"] == "L") & (df["set_diff"] < 0) & (df["set_result"].str.startswith("0-"))
df["swept_opponent"] = (df["result"] == "W") & (df["set_diff"] > 0) & (df["set_result"].str.endswith("-0"))
df["deciding_set_played"] = df["set_count"].apply(
    lambda x: x in [3, 5]
)

# scheduling info
df["total_sets_that_day"] = df.groupby("date")["set_count"].transform("sum")

# win/loss streaks
df["win_streak"] = 0
df["loss_streak"] = 0

current_win = 0
current_loss = 0
streaks_win = []
streaks_loss = []

for res in df["result"]:
    if res == "W":
        current_win += 1
        current_loss = 0
    elif res == "L":
        current_loss += 1
        current_win = 0
    else:
        current_win = 0
        current_loss = 0
    streaks_win.append(current_win)
    streaks_loss.append(current_loss)

df["win_streak"] = streaks_win
df["loss_streak"] = streaks_loss

# psychological
df["team_needed_win"] = df["loss_streak"] >= 2
df["confidence_boost_game"] = (
    (df["loss_streak"] >= 2) &
    (df["result"] == "W")
)
df["confidence_boost_game"] = (
    (df["loss_streak"] >= 2) &
    (df["result"] == "W")
)

# highlight match
df["highlight_match"] = False

# total points for/against
def get_total_points(row):
    if pd.isna(row["set_scores"]):
        return pd.Series([0, 0])
    team_total, opp_total = 0, 0
    for score in row["set_scores"].split(","):
        try:
            a, b = map(int, score.strip().split("-"))
            if row["result"] == "W":
                team_total += a
                opp_total += b
            else:
                team_total += b
                opp_total += a
        except:
            continue
    return pd.Series([team_total, opp_total])

df[["total_points_for", "total_points_against"]] = df.apply(get_total_points, axis=1)

# margin %
df["margin_pct"] = (
    (df["total_points_for"] - df["total_points_against"]) /
    (df["total_points_for"] + df["total_points_against"]).replace(0, pd.NA)
)
df["high_margin_win"] = (df["result"] == "W") & (df["margin_pct"] >= 0.6)
df["low_margin_loss"] = (df["result"] == "L") & (df["margin_pct"] >= -0.1)

# deaf schools
deaf_schools = ["AIDB", "AASD", "CSDF", "CSDR", "FSDB", "ISD", "MSD", "MISD", "TSD"]
df["deaf_school"] = df["opponent_slug"].isin(deaf_schools)

# reorder columns
desired_order = [
    # match identity & ordering
    "match_key",
    "career_match_index",
    "career_stage",
    "season",
    "season_match_number",
    "season_stage",
    "date",
    "day_of_week",
    "week_of_season",
    "days_since_last_match",
    "is_back_to_back",
    "match_density_3days",

    # same-day match context
    "match_no",
    "total_matches_that_day",
    "multi_game_day",
    "first_match_of_day",
    "last_match_of_day",
    "same_day_opponent_seq",

    # opponent context
    "opponent",
    "opponent_slug",
    "season_opponent_seq",
    "is_repeat_opponent",
    "rivalry",
    "deaf_school",

    # match classification
    "match_type",
    "game_importance",
    "game_importance_score",
    "event_name",
    "milestone_flag",

    # outcome and storyline tags
    "result",
    "set_scores",
    "set_result",
    "set_count",
    "set_diff",
    "comeback_win",
    "revenge_match",
    "redemption_game",

    # scoring & margin
    "total_points_for",
    "total_points_against",
    "margin_pct",
    "high_margin_win",
    "low_margin_loss",

    # meta and manual flags
    "location",
    "injured",
    "sick",
    "forfeited",
    "favorite_match",
    "birthday_match",
    "highlight_match",

    # imported flags from source data
    "is_conference",
    "is_playoffs",
    "is_tournament",
    "is_championship",

    # external link
    "maxpreps"
]
df = df[[col for col in desired_order if col in df.columns]]

# save csv
df.to_csv("data/schedules/cleaned_master_schedule.csv", index=False)
print("✅ Schedule cleaned and saved as 'cleaned_master_schedule.csv'")