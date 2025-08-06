"""
@name final_merge.py
@created August 2025
"""

import pandas as pd
import os

SCHEDULE_PATH = "data/cleaned/cleaned_master_schedule.csv"
STATS_PATH = "data/cleaned/all_stats_merged.csv"

def load_data():
    schedule_df = pd.read_csv(SCHEDULE_PATH)
    stats_df = pd.read_csv(STATS_PATH)
    
    print(f"Loaded {len(schedule_df)} rows from schedule")
    print(f"Loaded {len(stats_df)} rows from stats")

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

if __name__ == "__main__":
    schedule_df, stats_df = load_data()
    keys_match = compare_match_keys(schedule_df, stats_df)

    if not keys_match:
        print("❌ Halting before merge due to mismatched keys. Please resolve and try again.")
    else:
        print("🎉 Ready to proceed with merge!")