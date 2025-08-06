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
    "junior": (2018, "JR"),
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

    def combine_result(row):
        if pd.notna(row["result"]) and pd.notna(row["set_result"]):
            return f"{row['result']} {row['set_result']}"
        return pd.NA

    schedule_df["result"] = schedule_df.apply(combine_result, axis=1)

    # derive sets_played from set_result
    def extract_sets_played(set_result):
        try:
            if isinstance(set_result, str) and "-" in set_result:
                a, b = map(int, set_result.strip().split("-"))
                return a + b
        except:
            pass
        return pd.NA

    schedule_df["sets_played"] = schedule_df["set_result"].apply(extract_sets_played)

    # manual override - injured game (player twisted my ankle as i landed after a hit)
    schedule_df.loc[schedule_df["match_key"] == "JR_09-27_BOHS_1", "sets_played"] = 1

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

def suffix_stat_columns(df, stat_category):
    meta_cols = ["match_key", "date", "opponent", "result", "sets_played", "season", "opponent_slug"]
    stat_cols = [col for col in df.columns if col not in meta_cols]
    df = df.rename(columns={col: f"{col}_{stat_category}" for col in stat_cols})
    return df

def enforce_column_types(df):
    int_columns = [
        "sets_played", "kills_attacking", "kill_att_attacking", "kill_err_attacking",
        "assists_ball_handling", "ball_handling_att_ball_handling", "ball_handling_err_ball_handling",
        "solo_blks_blocking", "assisted_blks_blocking", "total_blks_blocking", "blk_err_blocking",
        "digs_digging", "dig_err_digging",
        "receiving_serve_receiving", "receiving_err_serve_receiving",
        "aces_serving", "serve_att_serving", "serve_err_serving", "points_serving"
    ]

    float_columns = [
        "kills_per_set_attacking", "kill_pct_attacking", "hit_pct_attacking",
        "assists_per_set_ball_handling",
        "blks_per_set_blocking",
        "digs_per_set_digging",
        "receiving_per_set_serve_receiving",
        "aces_per_set_serving", "ace_pct_serving",
        "serve_pct_serving"
    ]

    for col in int_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in float_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)

    return df

def merge_stats():
    all_seasons_merged = []

    # merge FR/SO/SR with match_key already in files
    for season_folder in SEASON_YEAR_MAP:
        year, season_code = SEASON_YEAR_MAP[season_folder]
        season_path = os.path.join(DATA_DIR, season_folder)
        print(f"Processing {season_folder} ({season_code}, {year})...")

        merged_dfs = []

        for stat_category in STAT_CATEGORIES:
            file_path = os.path.join(season_path, f"{stat_category}.csv")
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)

                if "match_key" not in df.columns:
                    print(f"ERROR: {file_path} missing 'match_key' column.")
                    continue

                df["season"] = season_code
                df = suffix_stat_columns(df, stat_category)
                df = df.set_index("match_key")

                if merged_dfs:
                    meta_cols = {"date", "opponent", "result", "sets_played", "season", "opponent_slug"}
                    df = df.drop(columns=[col for col in meta_cols if col in df.columns], errors="ignore")

                merged_dfs.append(df)
            else:
                print(f"Missing: {file_path}")

        if merged_dfs:
            season_merged = pd.concat(merged_dfs, axis=1, join="outer").reset_index()
            all_seasons_merged.append(season_merged)

            out_path = os.path.join(OUTPUT_DIR, f"{season_folder}_stats_merged.csv")

            def fix_date_with_year_row(row):
                year_map = {"FR": 2016, "SO": 2017, "JR": 2018, "SR": 2019}
                try:
                    date_str = row["date"]
                    year = year_map.get(row["season"])
                    if pd.isna(date_str) or pd.isna(year):
                        return pd.NA
                    dt = datetime.strptime(date_str.strip(), "%m/%d") if len(date_str.strip()) <= 5 else datetime.strptime(date_str.strip(), "%Y-%m-%d")
                    return dt.replace(year=year).strftime("%Y-%m-%d")
                except Exception:
                    return pd.NA

            season_merged["date"] = season_merged.apply(fix_date_with_year_row, axis=1)

            final_cols = [
                "match_key", "date", "result", "opponent", "sets_played",
                "kills_attacking", "kills_per_set_attacking", "kill_pct_attacking", 
                "kill_att_attacking", "kill_err_attacking", "hit_pct_attacking",
                "season",
                "assists_ball_handling", "assists_per_set_ball_handling", 
                "ball_handling_att_ball_handling", "ball_handling_err_ball_handling",
                "solo_blks_blocking", "assisted_blks_blocking", "total_blks_blocking", 
                "blks_per_set_blocking", "blk_err_blocking",
                "digs_digging", "dig_err_digging", "digs_per_set_digging",
                "receiving_serve_receiving", "receiving_err_serve_receiving", 
                "receiving_per_set_serve_receiving",
                "aces_serving", "aces_per_set_serving", "ace_pct_serving", 
                "serve_att_serving", "serve_err_serving", "serve_pct_serving", 
                "points_serving",
            ]

            for col in final_cols:
                if col not in season_merged.columns:
                    season_merged[col] = pd.NA
            season_merged = season_merged[[col for col in final_cols if col in season_merged.columns]]
            season_merged = enforce_column_types(season_merged)

            season_merged.to_csv(out_path, index=False)
            print(f"Saved: {out_path}")

    # JR placeholder rows (no stats)
    jr_df = create_junior_stat_rows_from_schedule()
    if not jr_df.empty:
        schedule_meta_cols = {
            "set_scores", "set_result", "set_count", "set_diff", "location",
            "is_conference", "is_playoffs", "is_tournament", "is_championship",
            "maxpreps", "h_a_n"
        }
        jr_df = jr_df.drop(columns=[col for col in schedule_meta_cols if col in jr_df.columns], errors="ignore")
        jr_df = jr_df.drop(columns=["match_no"], errors="ignore")

        # fill stat columns w/ 0 or NA
        all_columns = set().union(*(df.columns for df in all_seasons_merged))
        for col in all_columns:
            if col not in jr_df.columns:
                jr_df[col] = 0 if col.endswith(tuple(STAT_CATEGORIES)) else pd.NA

        all_seasons_merged.append(jr_df)
        print("Added junior schedule-based placeholder stats")

    # combine all into master_df
    master_df = pd.concat(all_seasons_merged, ignore_index=True)

    # DNP placeholders
    dnp_entries = [
        ("2016-09-24", "Connelly School of the Holy Child", "FR"),
        ("2019-10-21", "McLean", "SR"),
        ("2016-09-27", "McLean", "FR"),
        ("2017-09-18", "Berman Hebrew Academy", "SO"),
        ("2017-11-07", "Bell", "SO"),
        ("2017-11-08", "Jackson-Reed", "SO"),
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
    print(f"ADDED {len(dnp_df)} DNP placeholder rows")

    SEASON_SORT_ORDER = {"FR": 1, "SO": 2, "JR": 3, "SR": 4}
    master_df["season_order"] = master_df["season"].map(SEASON_SORT_ORDER)
    master_df = master_df.sort_values(by=["season_order", "date"]).drop(columns=["season_order"])

    final_cols = [
        "match_key", "date", "result", "opponent", "sets_played",

        "kills_attacking", "kills_per_set_attacking", "kill_pct_attacking", 
        "kill_att_attacking", "kill_err_attacking", "hit_pct_attacking",

        "season",

        "assists_ball_handling", "assists_per_set_ball_handling", 
        "ball_handling_att_ball_handling", "ball_handling_err_ball_handling",

        "solo_blks_blocking", "assisted_blks_blocking", "total_blks_blocking", 
        "blks_per_set_blocking", "blk_err_blocking",

        "digs_digging", "dig_err_digging", "digs_per_set_digging",

        "receiving_serve_receiving", "receiving_err_serve_receiving", 
        "receiving_per_set_serve_receiving",

        "aces_serving", "aces_per_set_serving", "ace_pct_serving", 
        "serve_att_serving", "serve_err_serving", "serve_pct_serving", 
        "points_serving",
    ]

    for col in final_cols:
        if col not in master_df.columns:
            master_df[col] = pd.NA

    master_df = master_df[[col for col in final_cols if col in master_df.columns]]
    master_df = enforce_column_types(master_df)

    master_df = master_df.drop_duplicates(subset="match_key", keep="first")

    master_path = os.path.join(OUTPUT_DIR, "all_stats_merged.csv")
    master_df.to_csv(master_path, index=False)
    print(f"SAVED master file: {master_path}")

if __name__ == "__main__":
    merge_stats()
