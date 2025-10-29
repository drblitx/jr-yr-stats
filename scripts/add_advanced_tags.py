"""
@name add_advanced_tags.py
@created August 2025
"""

import numpy as np
import pandas as pd
from scipy.stats import rankdata

# load in full merged dataset
df = pd.read_csv("data/NEW_full_merged_dataset.csv")
original_cols = df.columns.tolist() 

# set ordering list for correct dates
season_order = pd.CategoricalDtype(categories=['FR','SO','JR','SR'], ordered=True)
df['season'] = df['season'].astype(season_order)
df = df.sort_values(['season','date','match_no'], kind='mergesort').reset_index(drop=True)

# set up cols for boolean flags
bool_cols = [
    'did_play',
    'is_playoffs',
    'is_championship',
    'is_tournament',
    'rivalry',
    'redemption_game',
    'comeback_win',
    'revenge_match',
    'birthday_match',
    'is_repeat_opponent'
]
for c in bool_cols:
    if c in df.columns:
        df[c] = df[c].fillna(False).astype(bool)

# --------------------------------------------------------------
# functions
# --------------------------------------------------------------
def get_season_high_flags(row):
    if not row['did_play'] or not row['stats_available']:
        return ''
    highs = [field for field in stats_high_fields if pd.notna(row[field]) and row[field] == season_max.loc[row.name, field]]
    return ';'.join(highs)

def get_career_high_flags(row):
    if not row['did_play'] or not row['stats_available']:
        return ''
    return ';'.join([
        field for field in stats_high_fields
        if pd.notna(row[field]) and row[field] == df[field].max()
    ])

def _streak(series, want='W'):
    out, c = [], 0
    for v in series:
        c = c + 1 if v == want else 0
        out.append(c)
    return pd.Series(out, index=series.index)


# --------------------------------------------------------------
# personal & participation flags
# --------------------------------------------------------------
df['stats_available'] = df['season'] != 'JR'  # flag JR season with having no stats
df['played_all_sets'] = df['did_play'] & (df['sets_played'] == df['set_count'])

# win/loss streaks
df['win_streak'] = (
    df.groupby('season', group_keys=False, observed=False)['result']
      .apply(lambda s: _streak(s, 'W'))
)

df['loss_streak'] = (
    df.groupby('season', group_keys=False, observed=False)['result']
      .apply(lambda s: _streak(s, 'L'))
)


# --------------------------------------------------------------
# match timeline & scheduling
# --------------------------------------------------------------
df['prev_result'] = df['result'].shift(1)
df['prev_win_streak']  = df['win_streak'].shift(1)
df['prev_loss_streak'] = df['loss_streak'].shift(1)


# --------------------------------------------------------------
# date & opponent details
# --------------------------------------------------------------
df['was_set_swept'] = df['set_result'].isin(["0-3","0-2"])
df['swept_opponent'] = df['set_result'].isin(["3-0","2-0"])
df['deciding_set_played'] = df['set_result'].isin(['2-1', '1-2', '3-2', '2-3'])


# --------------------------------------------------------------
# career & narrative tags
# --------------------------------------------------------------
stats_high_fields = ['kills', 'aces', 'points', 'digs', 'receiving', 
                     'assists', 'total_blocks']

season_max = df.groupby('season', observed=False)[stats_high_fields].transform('max')

df['season_highs_flags'] = df.apply(get_season_high_flags, axis=1)
df['career_highs_flags'] = df.apply(get_career_high_flags, axis=1)
df['record_breaker_flag'] = df['career_highs_flags'].ne('')


# --------------------------------------------------------------
# storyline tags
# --------------------------------------------------------------
df['set_scores'] = df['set_scores'].fillna('').astype(str)

df['deciding_set_win'] = (  # tight win in final deciding set
    df['did_play'].fillna(False).astype(bool)
    & (df['result'] == 'W')
    & df['set_result'].isin(['2-1', '3-2'])
    & (
        df['set_scores']
        .str.extract(r'\s*(\d+)\s*-\s*(\d+)\s*$')
        .apply(pd.to_numeric, errors='coerce')
        .pipe(lambda s: (s[0] - s[1]).abs() == 2)
    )
)

df['deciding_set_loss'] = (  # tight loss in final deciding set
    df['did_play'].fillna(False).astype(bool)
    & (df['result'] == 'L')
    & df['set_result'].isin(['1-2', '2-3'])
    & (
        df['set_scores']
        .str.extract(r'\s*(\d+)\s*-\s*(\d+)\s*$')
        .apply(pd.to_numeric, errors='coerce')
        .pipe(lambda s: (s[0] - s[1]).abs() == 2)
    )
)


# --------------------------------------------------------------
# narrative & rating scores
# --------------------------------------------------------------
tight_sets   = (df['set_diff'].abs() == 1).fillna(False)
close_margin = (df['margin_pct'].abs() <= 0.12).fillna(False)


# --------------------------------------------------------------
# skill profile tags
# --------------------------------------------------------------
df['low_error_game'] = (
    (
        df['serve_errors'] +
        df['kill_errors'] +
        df['receiving_errors']
    ) <= 2
)


# --------------------------------------------------------------
# save to CSV
# --------------------------------------------------------------
col_order = [
    # --- match info ---
    "match_key", "career_match_index", "career_stage", "season",
    "season_match_number", "season_stage", "date", "day_of_week",
    "week_of_season",

    # --- match context/scheduling ---
    "days_since_last_match", "is_back_to_back", "match_density_3days",
    "match_no", "total_matches_that_day", "multi_game_day",
    "first_match_of_day", "last_match_of_day", "same_day_opponent_seq",

    # --- opponent/match details ---
    "opponent", "opponent_slug", "season_opponent_seq",
    "is_repeat_opponent", "rivalry", "deaf_school", "match_type",
    "game_importance", "game_importance_score", "event_name",
    "milestone_flag", "set_scores", "set_count", "set_result", "set_diff",

    # --- outcome/location ---
    "result", "location", "forfeited", "injured", "sick",

    # --- narrative/storyline tags ---
    "comeback_win", "revenge_match", "redemption_game",
    "birthday_match", "is_conference", "is_playoffs", "is_tournament",
    "is_championship",

    # --- scoring/margins ---
    "total_points_for", "total_points_against", "margin_pct",
    "high_margin_win", "low_margin_loss",

    # --- participation ---
    "did_play", "played_all_sets", "favorite_match", "stats_available",

    # --- achievements/records ---
    "season_highs_flags", "career_highs_flags", "record_breaker_flag",

    # --- storyline ---
    "deciding_set_win", "deciding_set_loss",

    # --- skill profiles ---
    "low_error_game",

    # --- match flow ---
    "win_streak", "loss_streak", "prev_result",
    "prev_win_streak", "prev_loss_streak", "was_set_swept",
    "swept_opponent", "deciding_set_played",

    # --- stat lines ---
    "sets_played",

    # attacking
    "kills", "kills_per_set", "kill_pct",
    "kill_attempts", "kill_errors", "hit_pct",

    # ball handling
    "assists", "assists_per_set",
    "ball_handling_attempts", "ball_handling_errors",

    # blocking
    "solo_blocks", "assisted_blocks", "total_blocks", "blocks_per_set", "block_errors",

    # digging
    "digs", "dig_errors", "digs_per_set",

    # serve receiving
    "receiving", "receiving_errors",
    "receiving_per_set",

    # serving
    "aces", "aces_per_set", "ace_pct",
    "serve_attempts", "serve_errors", "serve_pct", "points",

    # maxpreps
    "maxpreps"
    ]

missing_from_order = [c for c in original_cols if c not in col_order]
if missing_from_order:
    try:
        max_idx = col_order.index("maxpreps")
    except ValueError:
        max_idx = len(col_order)
    col_order = col_order[:max_idx] + [c for c in missing_from_order if c != "maxpreps"] + col_order[max_idx:]

missing_still = [c for c in original_cols if c not in col_order]
assert not missing_still, f"Missing OG columns in export: {missing_still}"

df = df[col_order]

df.to_csv("data/NEW_enriched_matches.csv", index=False)
