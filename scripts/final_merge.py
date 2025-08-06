"""
@name final_merge.py
@created August 2025
"""

import pandas as pd
import os

SCHEDULE_PATH = "data/cleaned/cleaned_master_schedule.csv"
STATS_PATH = "data/cleaned/all_stats_merged.csv"

def load_data():
    print("Loading...")
    schedule_df = pd.read_csv(SCHEDULE_PATH)
    stats_df = pd.read_csv(STATS_PATH)
    print(f"Loaded {len(schedule_df)} rows from schedule")
    print(f"Loaded {len(stats_df)} rows from stats")
    print()
    return schedule_df, stats_df

def compare_match_keys(schedule_df, stats_df):
    schedule_keys = set(schedule_df["match_key"])
    stats_keys = set(stats_df["match_key"])

    only_in_schedule = sorted(schedule_keys - stats_keys)
    only_in_stats = sorted(stats_keys - schedule_keys)

    if not only_in_schedule and not only_in_stats:
        print("✅ All match_keys align perfectly between schedule and stats.")
    else:
        print("⚠️ Mismatch detected in match_keys!")

        if only_in_schedule:
            print(f"  🟡 {len(only_in_schedule)} match_keys only in schedule:")
            for key in only_in_schedule:
                print(f"    - {key}")

        if only_in_stats:
            print(f"  🔴 {len(only_in_stats)} match_keys only in stats:")
            for key in only_in_stats:
                print(f"    - {key}")

    return not only_in_schedule and not only_in_stats

def validate_stat_integrity(stats_df, cleaned_dir="data/cleaned"):
    print("\n🔍 Validating stat integrity...")

    seasons = {
        "FR": "freshman_stats_merged.csv",
        "SO": "sophomore_stats_merged.csv",
        "SR": "senior_stats_merged.csv"
    }

    all_good = True

    stats_df = stats_df[stats_df["result"].notna()]

    for season_code, filename in seasons.items():
        file_path = os.path.join(cleaned_dir, filename)
        if not os.path.exists(file_path):
            print(f"❌ Missing season stats file: {filename}")
            all_good = False
            continue

        season_df = pd.read_csv(file_path)
        merged_df = stats_df[stats_df["season"] == season_code]

        season_df = season_df.set_index("match_key")
        merged_df = merged_df.set_index("match_key")

        meta_cols = ["date", "result", "opponent", "season", "opponent_slug", "sets_played", "match_no"]
        season_df = season_df.drop(columns=[c for c in meta_cols if c in season_df.columns], errors="ignore")
        merged_df = merged_df.drop(columns=[c for c in meta_cols if c in merged_df.columns], errors="ignore")

        season_df.index = season_df.index.astype(str)
        merged_df.index = merged_df.index.astype(str)
        season_df.columns = season_df.columns.astype(str)
        merged_df.columns = merged_df.columns.astype(str)

        if season_df.index.duplicated().any():
            dupes = season_df.index[season_df.index.duplicated()].unique()
            print(f"❌ Duplicate match_keys in season_df for {season_code}: {list(dupes)}")
            all_good = False
            continue

        if merged_df.index.duplicated().any():
            dupes = merged_df.index[merged_df.index.duplicated()].unique()
            print(f"❌ Duplicate match_keys in merged_df for {season_code}: {list(dupes)}")
            all_good = False
            continue

        common_cols = sorted(season_df.columns.intersection(merged_df.columns))
        common_index = sorted(season_df.index.intersection(merged_df.index))

        season_df = season_df.reindex(index=common_index, columns=common_cols)
        merged_df = merged_df.reindex(index=common_index, columns=common_cols)

        for col in common_cols:
            try:
                merged_df[col] = merged_df[col].astype(season_df[col].dtype)
            except Exception:
                merged_df[col] = merged_df[col].astype(float)

        try:
            season_df = season_df[common_cols].sort_index()
            merged_df = merged_df[common_cols].sort_index()

            print(f"[{season_code}] comparing {season_df.shape} vs {merged_df.shape}")

            diffs = season_df.compare(merged_df, align_axis=0)
            if not diffs.empty:
                print(f"⚠️ Mismatch found in {season_code} stats! Showing up to 10 differences:")
                print(diffs.head(10))

                sample_key = diffs.index.get_level_values(0)[0]
                print("🧪 match_key:", sample_key)
                print("Season file:\n", season_df.loc[sample_key])
                print("All stats merged:\n", merged_df.loc[sample_key])

                all_good = False
            else:
                print(f"✅ Stats for {season_code} match exactly.")
        except ValueError as ve:
            print(f"❌ Comparison error in {season_code}: {ve}")
            print(f"  🟡 In {filename} only: {sorted(set(season_df.columns) - set(merged_df.columns))}")
            print(f"  🔴 In all_stats_merged only: {sorted(set(merged_df.columns) - set(season_df.columns))}")
            all_good = False

    return all_good

if __name__ == "__main__":
    schedule_df, stats_df = load_data()

    if not compare_match_keys(schedule_df, stats_df):
        print("❌ Halting due to match_key mismatch. Please fix before continuing.")
        exit(1)

    if not validate_stat_integrity(stats_df):
        print("❌ Stat mismatches found. Please resolve before proceeding.")
        exit(1)

    print("\n🎯 All checks passed. Proceeding to final merge...")
    # merge logic can go here
