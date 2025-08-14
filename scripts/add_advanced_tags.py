"""
@name add_advanced_tags.py
@created August 2025
"""

import numpy as np
import pandas as pd
from scipy.stats import rankdata

# load in full merged dataset
df = pd.read_csv("data/full_merged_dataset.csv")
original_cols = df.columns.tolist() 
season_order = pd.CategoricalDtype(categories=['FR','SO','JR','SR'], ordered=True)
df['season'] = df['season'].astype(season_order)
df = df.sort_values(['season','date','match_no'], kind='mergesort').reset_index(drop=True)

bool_cols = [
    'did_play','is_playoffs','is_championship','is_tournament','rivalry',
    'redemption_game','comeback_win','highlight_match','revenge_match',
    'birthday_match','is_repeat_opponent'
]
for c in bool_cols:
    if c in df.columns:
        df[c] = df[c].fillna(False).astype(bool)

# --------------------------------------------------------------
# functions
# --------------------------------------------------------------
def compute_performance_score(row):
    """
    creates a personalized performance score for an outside hitter (me!)
    who consistently plays full matches and contributes across multiple skills.

    row must have all relevant stat fields and `played_all_sets` already computed.
    """
    if not row.get('did_play') or not row.get('stats_available'):
        return None

    # attacking
    score = row['kills_attacking'] * 1.5                     # primary point contribution
    score += row['kill_pct_attacking'] * 10                 # efficiency bonus for clean hitting

    # serving
    score += row['aces_serving'] * 1.3                      # direct service points
    score += row['ace_pct_serving'] * 8                    # efficiency reward for precision

    # defensive & support stats
    score += row['digs_digging'] * 1.0                      # back-row defense
    score += row['assists_ball_handling'] * 0.5             # out-of-system assists

    # serve receive (positive)
    score += row['receiving_serve_receiving'] * 0.8         # handling first contact

    # negative contributions (errors)
    score -= row['receiving_err_serve_receiving'] * 1.3     # receiving errors hurt possession
    score -= row['kill_err_attacking'] * 1.0                # missed attacks
    score -= row['serve_err_serving'] * 1.0                 # missed serves = free points

    # full-match presence
    if row.get('played_all_sets'):
        score += 1.0  # reward consistency and leadership

    return score

def label_form_trend(values):
    values = list(values)  
    if len(values) < 3:
        return ['FLAT'] * len(values)
    result = ['FLAT'] * len(values)
    for i in range(2, len(values)):
        window = values[i-2:i+1]
        if all(x < window[-1] for x in window[:2]):
            result[i] = 'UP'
        elif all(x > window[-1] for x in window[:2]):
            result[i] = 'DOWN'
        else:
            result[i] = 'FLAT'
    return result

def compute_percentile(group):
    return rankdata(group, method='average') / len(group) * 100  # season ranking

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

def label_performance(x, did_play):
    if not did_play or pd.isna(x):
        return ''
    if x >= 8.5:   return 'ICONIC'
    if x >= 7.0:   return 'MEMORABLE'
    if x >= 5.0:   return 'SOLID'
    return 'QUIET'
    
def classify_opponent_tier(row):
    if not pd.notna(row['game_importance_score']):
        return 'Unknown'
    if row['game_importance_score'] >= 0.75:
        return 'High'
    elif row['game_importance_score'] >= 0.5:
        return 'Medium'
    else:
        return 'Low'
    
def _streak(series, want='W'):
    out, c = [], 0
    for v in series:
        c = c + 1 if v == want else 0
        out.append(c)
    return pd.Series(out, index=series.index)


# --------------------------------------------------------------
# 1. personal & participation flags
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

df['personal_performance_score'] = df.apply(compute_performance_score, axis=1)


# --------------------------------------------------------------
# 2. stats-based calculations (early, required for later tags)
# --------------------------------------------------------------
df.loc[df['did_play'] & df['stats_available'], 'personal_performance_per_set'] = (
    df['personal_performance_score'] / df['sets_played']
)

df['season_avg_performance_score'] = (
    df[df['did_play'] & df['stats_available']]
    .groupby('season', observed=False)['personal_performance_score']
    .transform('mean')
)

df['personal_performance_percentile'] = (
    df[df['did_play'] & df['stats_available']]
    .groupby('season', observed=False)['personal_performance_score']
    .transform(compute_percentile)
)


# --------------------------------------------------------------
# 3. match context flags
# --------------------------------------------------------------
df['clutch_factor'] = df['personal_performance_score'] * df['game_importance_score']

df['clutch_performance_flag'] = (
    (df['game_importance_score'] >= 0.7) &
    (df['personal_performance_percentile'] >= 75)
)


# --------------------------------------------------------------
# 4. match timeline & scheduling
# --------------------------------------------------------------
df['prev_result'] = df['result'].shift(1)
df['prev_percentile'] = df['personal_performance_percentile'].shift(1)
df['prev_win_streak']  = df['win_streak'].shift(1)
df['prev_loss_streak'] = df['loss_streak'].shift(1)


# --------------------------------------------------------------
# 5. date & opponent details
# --------------------------------------------------------------
df['was_set_swept'] = df['set_result'].isin(["0-3","0-2"])
df['swept_opponent'] = df['set_result'].isin(["3-0","2-0"])
df['deciding_set_played'] = df['set_result'].isin(['2-1', '1-2', '3-2', '2-3'])


# --------------------------------------------------------------
# 6. extended stats-based calculations
# --------------------------------------------------------------
df['below_avg_performance'] = (
    df['personal_performance_score'] < df['season_avg_performance_score']
)

df['form_trend_label'] = (
    df[df['did_play'] & df['stats_available']]
    .groupby('season', observed=False)['personal_performance_score']
    .transform(label_form_trend)
)

# efficiency score
err_total = (
    df['serve_err_serving'].fillna(0).astype(float) +
    df['kill_err_attacking'].fillna(0).astype(float) +
    df['receiving_err_serve_receiving'].fillna(0).astype(float)
)
valid_mask = df['did_play'] & df['stats_available']
df.loc[valid_mask, 'efficiency_score'] = (
    df.loc[valid_mask, 'personal_performance_score'].astype(float) / (err_total.loc[valid_mask] + 1.0)
)
df['efficiency_score'] = df['efficiency_score'].replace([np.inf, -np.inf], np.nan)

# offensive focus score
offensive_terms = (
    df['kills_attacking'].fillna(0).astype(float) * 1.5 +
    df['kill_pct_attacking'].fillna(0).astype(float) * 10.0 +
    df['aces_serving'].fillna(0).astype(float) * 1.3 +
    df['ace_pct_serving'].fillna(0).astype(float) * 8.0
)
den = df['personal_performance_score'].astype(float)
mask_focus = valid_mask & den.notna() & (den != 0)
df.loc[mask_focus, 'offensive_focus_score'] = offensive_terms.loc[mask_focus] / den.loc[mask_focus]
df.loc[valid_mask & ~mask_focus, 'offensive_focus_score'] = np.nan

# defensive impact score
den_sets = df['sets_played'].astype(float)
mask_di = df['did_play'] & df['stats_available'] & den_sets.gt(0)
df.loc[mask_di, 'defensive_impact_score'] = (
    (df.loc[mask_di, 'digs_digging'].fillna(0) + df.loc[mask_di, 'receiving_serve_receiving'].fillna(0))
    / den_sets.loc[mask_di]
)

df['zero_stat_match'] = (
    df['did_play'] &
    df['stats_available'] &
    (df['kills_attacking'] == 0) &
    (df['assists_ball_handling'] == 0) &
    (df['digs_digging'] == 0) &
    (df['aces_serving'] == 0) &
    (df['solo_blks_blocking'] == 0) &
    (df['assisted_blks_blocking'] == 0)
)

df['game_rating'] = (
    df['personal_performance_score'] / df['season_avg_performance_score']
).round(2)


# --------------------------------------------------------------
# 6. career & narrative tags
# --------------------------------------------------------------
stats_high_fields = ['kills_attacking', 'aces_serving', 'points_serving', 'digs_digging', 'receiving_serve_receiving', 
                     'assists_ball_handling', 'total_blks_blocking', 'personal_performance_score', 'personal_performance_per_set']

season_max = df.groupby('season', observed=False)[stats_high_fields].transform('max')

df['season_highs_flags'] = df.apply(get_season_high_flags, axis=1)
df['career_highs_flags'] = df.apply(get_career_high_flags, axis=1)
df['record_breaker_flag'] = df['career_highs_flags'].ne('')

df['best_performance_of_season'] = (
    df['personal_performance_score'] == season_max['personal_performance_score']
)


# --------------------------------------------------------------
# 7. storyline tags
# --------------------------------------------------------------
df['heartbreaker'] = (  # strong performance in a close loss
    (df['result'] == 'L') &
    (df['set_diff'] == -1) &
    (df['personal_performance_percentile'] >= 70)
)

df['dominant_sweep'] = (  # 3-0 win + strong stats
    (df['result'] == 'W')
    & df['set_result'].isin(['3-0','2-0'])
    & (df['personal_performance_percentile'] >= 80)
)

df['momentum_swing'] = (  # streak breaker + performance swing
    ((df['prev_loss_streak'] >= 2) & (df['result'] == 'W') & (df['personal_performance_percentile'] >= 70))
    |
    ((df['prev_win_streak']  >= 2) & (df['result'] == 'L') & (df['personal_performance_percentile'] <= 40))
)

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

df['bounceback_win'] = (
    (df['prev_loss_streak'] >= 2) &
    (df['result'] == 'W') &
    (df['personal_performance_score'] >= df['season_avg_performance_score'])
)

df['highlight_match'] = (
    df['highlight_match'].fillna(False).astype(bool)
    | (
        (df['personal_performance_percentile'] >= 90)
        & (
            (df['game_importance_score'] >= 0.7)
            | df['is_playoffs'].fillna(False).astype(bool)
            | df['rivalry'].fillna(False).astype(bool)
            | df['redemption_game'].fillna(False).astype(bool)
            | df['comeback_win'].fillna(False).astype(bool)
        )
    )
)


# --------------------------------------------------------------
# 8. narrative & rating scores
# --------------------------------------------------------------
tight_sets   = (df['set_diff'].abs() == 1).fillna(False)
close_margin = (df['margin_pct'].abs() <= 0.12).fillna(False)

# weights for each storyline element (booleans are 0/1; importance is 0–1)
w = {
    'playoffs': 2.5,
    'championship': 3.0,
    'tournament': 1.0,
    'rivalry': 1.2,
    'redemption': 1.2,
    'revenge': 0.8,
    'comeback': 1.6,
    'deciding_played': 1.2,
    'deciding_win': 0.6,
    'highlight': 0.6,
    'milestone': 0.6,
    'birthday': 0.3,
    'importance': 2.0,     # scales with game_importance_score (0–1)
    'tight_sets': 0.4,     # 2–1 or 3–2 match
    'close_margin': 0.3,   # overall margin close
}

df['performance_brilliance_score'] = (
    df['record_breaker_flag'].astype(int) * 3 +
    df['season_highs_flags'].ne('').astype(int) * 2 +
    df['career_highs_flags'].ne('').astype(int) * 3 +
    df['clutch_performance_flag'].astype(int) * 2 +
    df['dominant_sweep'].astype(int) * 1 +
    df['heartbreaker'].astype(int) * 1 +
    (df['personal_performance_percentile'] >= 85).astype(int) * 2 +
    (df['efficiency_score'] >= 5.0).astype(int) * 1
)


df['performance_label'] = df.apply(
    lambda r: label_performance(r['performance_brilliance_score'], r['did_play']),
    axis=1
)

raw_excitement = (
    df['is_playoffs'].astype(int)         * w['playoffs'] +
    df['is_championship'].astype(int)     * w['championship'] +
    df['is_tournament'].astype(int)       * w['tournament'] +
    df['rivalry'].astype(int)             * w['rivalry'] +
    df['redemption_game'].astype(int)     * w['redemption'] +
    df['revenge_match'].astype(int)       * w['revenge'] +
    df['comeback_win'].astype(int)        * w['comeback'] +
    df['deciding_set_played'].astype(int) * w['deciding_played'] +
    df['deciding_set_win'].astype(int)    * w['deciding_win'] +
    df['highlight_match'].astype(int)     * w['highlight'] +
    df['milestone_flag'].notna().astype(int) * w['milestone'] +
    df['birthday_match'].astype(int)      * w['birthday'] +
    df['game_importance_score'].fillna(0) * w['importance'] +
    tight_sets.astype(int)                * w['tight_sets'] +
    close_margin.astype(int)              * w['close_margin']
)

max_excitement = sum(w.values())
df['fan_excitement'] = (raw_excitement / max_excitement * 10).clip(0, 10).round(1)


# --------------------------------------------------------------
# 9. opponent categorization & simulation tags
# --------------------------------------------------------------
df['opponent_strength_tier'] = df.apply(classify_opponent_tier, axis=1)

df['upset_victory'] = (
    (df['result'] == 'W') &
    (df['opponent_strength_tier'] == 'High') &
    (df['personal_performance_percentile'] < 50)
)

df['predictable_match'] = (  # repeat opponent + similar margin trend
    df['is_repeat_opponent'] &
    (df['margin_pct'].abs() <= 0.1)  # close match again
)


# --------------------------------------------------------------
# 10. team dynamics tags
# --------------------------------------------------------------
df['confidence_boost_game'] = (  # bounceback after poor game
    (df['prev_percentile'] <= 40) &
    (df['personal_performance_percentile'] >= 70)
)

df['high_impact_win'] = (  # high-stakes win with great performance
    (df['result'] == 'W') &
    (
        df['is_playoffs'] |
        df['is_championship'] |
        df['clutch_performance_flag'] |
        (df['performance_brilliance_score'] >= 8.5)
    )
)


# --------------------------------------------------------------
# 11. skill profile tags
# --------------------------------------------------------------
df['best_match_of_season'] = (
    df.groupby('season', observed=False)['performance_brilliance_score']
      .transform('max') == df['performance_brilliance_score']
)

df['offense_dominant_match'] = df['offensive_focus_score'] >= 0.7
df['defense_dominant_match'] = df['defensive_impact_score'] >= 4.0
df['balanced_match'] = (
    df['offense_dominant_match'] &
    df['defense_dominant_match']
)

df['low_error_game'] = (
    (
        df['serve_err_serving'] +
        df['kill_err_attacking'] +
        df['receiving_err_serve_receiving']
    ) <= 2
)

# --------------------------------------------------------------
# save to CSV
# --------------------------------------------------------------
# rounding numbers so no LONG floats
adv_round_map = {
    'personal_performance_score': 1,
    'personal_performance_percentile': 1,
    'personal_performance_per_set': 2,
    'season_avg_performance_score': 2,
    'clutch_factor': 2,
    'efficiency_score': 2,
    'offensive_focus_score': 3,
    'defensive_impact_score': 2,
    'game_rating': 2,
    'performance_brilliance_score': 1,
    'fan_excitement': 1,
    'margin_pct': 3
}

adv_round_map.update({
    'personal_performance_score_norm100': 1,
    'personal_performance_per_set_norm100': 1,
    'season_avg_performance_score_norm100': 1,
    'performance_brilliance_score_norm100': 1,

    'personal_performance_score_norm01': 3,
    'personal_performance_per_set_norm01': 3,
    'season_avg_performance_score_norm01': 3,
    'performance_brilliance_score_norm01': 3,

    'personal_performance_percentile_norm01': 3,
    'prev_percentile': 3,
})

for col, nd in adv_round_map.items():
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').round(nd)

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
    "comeback_win", "revenge_match", "redemption_game", "highlight_match",
    "birthday_match", "is_conference", "is_playoffs", "is_tournament",
    "is_championship",

    # --- scoring/margins ---
    "total_points_for", "total_points_against", "margin_pct",
    "high_margin_win", "low_margin_loss",

    # --- participation ---
    "did_play", "played_all_sets", "favorite_match", "stats_available",

    # --- core metrics ---
    "personal_performance_score", "personal_performance_score_norm100", "personal_performance_score_norm01",
    "personal_performance_per_set", "personal_performance_per_set_norm100", "personal_performance_per_set_norm01",
    "season_avg_performance_score", "season_avg_performance_score_norm100", "season_avg_performance_score_norm01",
    "personal_performance_percentile", "personal_performance_percentile_norm01",
    "performance_brilliance_score", "performance_brilliance_score_norm100", "performance_brilliance_score_norm01",
    "performance_label", "fan_excitement", "game_rating",

    # --- performance breakdown ---
    "clutch_factor", "clutch_performance_flag", "below_avg_performance",
    "form_trend_label", "efficiency_score", "offensive_focus_score",
    "defensive_impact_score", "zero_stat_match",

    # --- achievements/records ---
    "season_highs_flags", "career_highs_flags", "record_breaker_flag",
    "best_performance_of_season", "best_match_of_season",

    # --- storyline ---
    "heartbreaker", "dominant_sweep", "momentum_swing", "deciding_set_win",
    "deciding_set_loss", "bounceback_win",

    # --- opponent tier/match type ---
    "opponent_strength_tier", "upset_victory", "predictable_match",

    # --- team dynamics ---
    "team_needed_win", "energy_boost_game", "confidence_boost_game",
    "high_impact_win",

    # --- skill profiles ---
    "offense_dominant_match", "defense_dominant_match", "balanced_match",
    "low_error_game",

    # --- match flow ---
    "win_streak", "loss_streak", "prev_result", "prev_percentile",
    "prev_win_streak", "prev_loss_streak", "was_set_swept",
    "swept_opponent", "deciding_set_played",

    # --- stat lines ---
    "sets_played",

    # attacking
    "kills_attacking", "kills_per_set_attacking", "kill_pct_attacking",
    "kill_att_attacking", "kill_err_attacking", "hit_pct_attacking",

    # ball handling
    "assists_ball_handling", "assists_per_set_ball_handling",
    "ball_handling_att_ball_handling", "ball_handling_err_ball_handling",

    # blocking
    "solo_blks_blocking", "assisted_blks_blocking", "total_blks_blocking",
    "blks_per_set_blocking", "blk_err_blocking",

    # digging
    "digs_digging", "dig_err_digging", "digs_per_set_digging",

    # serve receiving
    "receiving_serve_receiving", "receiving_err_serve_receiving",
    "receiving_per_set_serve_receiving",

    # serving
    "aces_serving", "aces_per_set_serving", "ace_pct_serving",
    "serve_att_serving", "serve_err_serving", "serve_pct_serving",
    "points_serving",


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

nan_sus = df[
    (df['season'] != 'JR')
    & df['did_play'].fillna(False)
    & (
        df['personal_performance_score'].isna()
        | df['personal_performance_percentile'].isna()
        | df['personal_performance_per_set'].isna()
    )
][['season','date','opponent','did_play','stats_available','personal_performance_score']]
if not nan_sus.empty:
    print("⚠️ Unexpected NaNs in non-JR played matches:\n", nan_sus.to_string(index=False))

df.to_csv("data/enriched_matches.csv", index=False)
