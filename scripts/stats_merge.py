"""
@name stats_merge.py
@created July 2025
"""

import pandas as pd
import re
import os
from datetime import datetime

DATA_DIR = "data/raw"
OUTPUT_DIR = "data/cleaned"
SEASON_YEAR_MAP = {
    "freshman": (2016, "FR"),
    "sophomore": (2017, "SO"),
    "senior": (2019, "SR"),
}
STAT_CATEGORIES = ["attacking", "ball_handling", "blocking", "digging", "serve_receiving", "serving"]

opponent_name_corrections = {
    "Jackson-Reed": "Woodrow Wilson"
}

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

def create_junior_stat_rows_from_schedule():
    schedule_path = os.path.join("data/schedules/season", "junior_schedule.csv")
    if not os.path.exists(schedule_path):
        print("Missing junior schedule file!")
        return pd.DataFrame()

    schedule_df = pd.read_csv(schedule_path)
    year, season_code = 2018, "JR"

    schedule_df['opponent'] = schedule_df['opponent'].apply(clean_opponent_name)
    schedule_df['date'] = schedule_df['date'].apply(lambda d: format_date(d, year))
    schedule_df['opponent_slug'] = schedule_df['opponent'].apply(get_opponent_slug)
    schedule_df['season'] = season_code

    schedule_df["match_no"] = schedule_df.groupby("date").cumcount() + 1
    schedule_df["match_key"] = (
        schedule_df["season"]
        + "_" + schedule_df["date"].str[5:]
        + "_" + schedule_df["opponent_slug"].str.replace(r'\W+', '', regex=True)
        + "_" + schedule_df["match_no"].astype(str)
    )

    schedule_df['result'] = pd.NA
    schedule_df['sets_played'] = pd.NA

    return schedule_df

def clean_opponent_name(name):
    return opponent_name_corrections.get(name, name)

def format_date(date_str, year):
    if pd.isna(date_str):
        return None
    try:
        parsed = datetime.strptime(date_str.strip(), "%m/%d")
        return parsed.replace(year=year).strftime("%Y-%m-%d")
    except ValueError:
        return None

def get_opponent_slug(opponent):
    return opponent_slug_map.get(opponent, re.sub(r'[^A-Z]', '', opponent.upper())[:3])

SCHEDULE_CLEANED_PATH = os.path.join("data/cleaned", "cleaned_master_schedule.csv")

if os.path.exists(SCHEDULE_CLEANED_PATH):
    schedule_df = pd.read_csv(SCHEDULE_CLEANED_PATH)
    schedule_df["date"] = schedule_df["date"].astype(str)
    schedule_df["opponent"] = schedule_df["opponent"].apply(clean_opponent_name)
    schedule_match_keys = schedule_df[["season", "date", "opponent", "match_key", "opponent_slug"]].copy()
else:
    print(f"WARNING: {SCHEDULE_CLEANED_PATH} not found. Match key merge will fallback.")
    schedule_match_keys = pd.DataFrame()

def preprocess_stat_df(df, year, season_code, fill_zero=False):
    df = df.copy()
    df["season"] = season_code
    df["opponent"] = df["opponent"].apply(clean_opponent_name)
    df["date"] = df["date"].apply(lambda d: format_date(d, year))

    df = df.merge(
        schedule_match_keys,
        on=["season", "date", "opponent"],
        how="left",
        suffixes=("", "_schedule")
    )

    # if opponent_slug is missing, generate from scratch
    df["opponent_slug"] = df["opponent_slug"].fillna(df["opponent"].apply(get_opponent_slug)).astype(str)

    # helper columns for fallback match key generation
    df["match_no"] = df.groupby("date").cumcount() + 1
    df["total_matches_that_day"] = df.groupby("date")["date"].transform("count")
    df["same_day_opponent_seq"] = df.groupby(["date", "opponent"]).cumcount() + 1
    df["season_opponent_seq"] = df.groupby(["season", "opponent"]).cumcount() + 1
    df["is_repeat_opponent"] = df["season_opponent_seq"] > 1

    # fill match_key only if it's missing (e.g. not found in schedule)
    missing_keys = df["match_key"].isna()
    if missing_keys.any():
        print(f"WARNING: {missing_keys.sum()} match_keys missing — falling back to auto-generation.")
        df["match_no"] = df.groupby("date").cumcount() + 1
        df.loc[missing_keys, "match_key"] = (
            df.loc[missing_keys, "season"].astype(str)
            + "_" + df.loc[missing_keys, "date"].str[5:]
            + "_" + df.loc[missing_keys, "opponent_slug"].str.replace(r'\W+', '', regex=True)
            + "_" + df.loc[missing_keys, "match_no"].astype(str)
        )

    if fill_zero:
        meta_cols = ["date", "opponent", "result", "sets_played", "match_key", "season", "opponent_slug"]
        stat_cols = [col for col in df.columns if col not in meta_cols]
        df[stat_cols] = df[stat_cols].fillna(0)

    return df

def suffix_stat_columns(df, stat_category):
    meta_cols = ["match_key", "date", "opponent", "result", "sets_played", "season", "opponent_slug"]
    stat_cols = [col for col in df.columns if col not in meta_cols]
    df = df.rename(columns={col: f"{col}_{stat_category}" for col in stat_cols})
    return df

def merge_stats():
    all_seasons_merged = []

    for season_folder in SEASON_YEAR_MAP:
        year, season_code = SEASON_YEAR_MAP[season_folder]
        season_path = os.path.join(DATA_DIR, season_folder)
        print(f"processing {season_folder} ({season_code}, {year})...")

        merged_dfs = []

        for stat_category in STAT_CATEGORIES:
            file_path = os.path.join(season_path, f"{stat_category}.csv")
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                fill_zero = (season_folder == "junior")  # zero-fill for JR only
                df = preprocess_stat_df(df, year, season_code, fill_zero=fill_zero)
                df = suffix_stat_columns(df, stat_category)
                df = df.set_index("match_key")

                if merged_dfs:
                    meta_cols = ["date", "opponent", "result", "sets_played", "season", "opponent_slug"]
                    df = df.drop(columns=[col for col in meta_cols if col in df.columns])

                merged_dfs.append(df)
            else:
                print(f"missing: {file_path}")

        if merged_dfs:
            season_merged = pd.concat(merged_dfs, axis=1, join="outer").reset_index()
            all_seasons_merged.append(season_merged)

            out_path = os.path.join(OUTPUT_DIR, f"{season_folder}_stats_merged.csv")
            season_merged.to_csv(out_path, index=False)
            print(f"saved {out_path}")

        if all_seasons_merged:
            jr_df = create_junior_stat_rows_from_schedule()
            if not jr_df.empty:
                schedule_meta_cols = {
                    "set_scores", "set_result", "set_count", "set_diff", "location",
                    "is_conference", "is_playoffs", "is_tournament", "is_championship",
                    "maxpreps", "h_a_n"
                }
                jr_df = jr_df.drop(columns=[col for col in schedule_meta_cols if col in jr_df.columns])

                all_columns = set().union(*(df.columns for df in all_seasons_merged))
                for col in all_columns:
                    if col not in jr_df.columns:
                        if col not in {"match_key", "date", "opponent", "season", "opponent_slug", "result"}:
                            jr_df[col] = 0
                        else:
                            jr_df[col] = pd.NA

                all_seasons_merged.append(jr_df)
                print("added junior schedule-based placeholder stats")

            master_df = pd.concat(all_seasons_merged, ignore_index=True)

        # DNP games (6)
        dnp_entries = [
            ("2016-09-24", "Connelly School of the Holy Child", "FR"),
            ("2019-10-21", "McLean", "SR"),
            ("2016-09-27", "McLean", "FR"),
            ("2017-09-18", "Berman Hebrew Academy", "SO"),
            ("2017-11-07", "Bell", "SO"),
            ("2017-11-08", "Jackson-Reed", "SO")
        ]

        dnp_rows = []
        dnp_entries = [
            ("2016-09-24", "Connelly School of the Holy Child", "FR"),
            ("2019-10-21", "McLean", "SR"),
            ("2016-09-27", "McLean", "FR"),
            ("2017-09-18", "Berman Hebrew Academy", "SO"),
            ("2017-11-07", "Bell", "SO"),
            ("2017-11-08", "Jackson-Reed", "SO")
        ]

        stat_columns = [
            col for col in master_df.columns
            if col not in {"match_key", "date", "opponent", "season", "opponent_slug", "result"}
        ]

        dnp_rows = []
        for date_str, opponent, season_code in dnp_entries:
            opponent_clean = clean_opponent_name(opponent)
            opponent_slug = get_opponent_slug(opponent_clean)
            match_key = f"{season_code}_{date_str[5:]}_{opponent_slug}_1"

            row = {
                "match_key": match_key,
                "date": date_str,
                "opponent": opponent_clean,
                "season": season_code,
                "opponent_slug": opponent_slug,
                "result": pd.NA,
            }

            for col in stat_columns:
                row[col] = pd.NA

            dnp_rows.append(row)

        dnp_df = pd.DataFrame(dnp_rows)
        for col in master_df.columns:
            if col not in dnp_df.columns:
                dnp_df[col] = pd.NA
        dnp_df = dnp_df[master_df.columns]
        master_df = pd.concat([master_df, dnp_df], ignore_index=True)
        print(f"ADDED {len(dnp_df)} dnp placeholder rows")

        # sort by season then date
        SEASON_SORT_ORDER = {"FR": 1, "SO": 2, "JR": 3, "SR": 4}
        master_df["season_order"] = master_df["season"].map(SEASON_SORT_ORDER)
        master_df = master_df.sort_values(by=["season_order", "date"]).reset_index(drop=True)
        master_df = master_df.drop(columns=["season_order"])

        # drop schedule metadata columns that will come from schedule master
        schedule_cols_to_drop = {
            "sets_played", "set_scores", "set_result", "set_count", "set_diff",
            "location", "is_conference", "is_playoffs", "is_tournament", "is_championship",
            "maxpreps"
        }

        master_df = master_df.drop(columns=[col for col in schedule_cols_to_drop if col in master_df.columns])

        fixed_order = ["result", "date", "season", "opponent_slug", "opponent", "match_key"]
        stat_cols = sorted([col for col in master_df.columns if col not in fixed_order])
        final_cols = fixed_order + stat_cols
        master_df = master_df[final_cols]

        master_df = master_df.drop_duplicates(subset="match_key", keep="first")

        master_path = os.path.join(OUTPUT_DIR, "all_stats_merged.csv")
        master_df.to_csv(master_path, index=False)
        print(f"SAVED master file: {master_path}")

if __name__ == "__main__":
    merge_stats()
