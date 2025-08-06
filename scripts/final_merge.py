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

if __name__ == "__main__":
    schedule_df, stats_df = load_data()