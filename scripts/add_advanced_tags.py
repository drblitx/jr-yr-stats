"""
@name add_advanced_tags.py
@created August 2025
"""

import pandas as pd
from scipy.stats import rankdata

# load in full merged dataset
df = pd.read_csv("data/full_merged_dataset.csv")

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

def label_narrative_score(score):
    if pd.isna(score):
        return ''
    elif score >= 9:
        return 'ICONIC'
    elif score >= 7:
        return 'MEMORABLE'
    elif score >= 5:
        return 'SOLID'
    else:
        return 'QUIET GAME'
    
def classify_opponent_tier(row):
    if not pd.notna(row['game_importance_score']):
        return 'Unknown'
    if row['game_importance_score'] >= 0.75:
        return 'High'
    elif row['game_importance_score'] >= 0.5:
        return 'Medium'
    else:
        return 'Low'


# --------------------------------------------------------------
# 1. personal & participation flags
# --------------------------------------------------------------
df['stats_available'] = df['season'] != 'JR'  # flag JR season with having no stats
df['played_all_sets'] = df['did_play'] & (df['sets_played'] == df['set_count'])
df['personal_performance_score'] = df.apply(compute_performance_score, axis=1)


# --------------------------------------------------------------
# 2. match context flags
# --------------------------------------------------------------
df['clutch_factor'] = df['personal_performance_score'] * df['game_importance_score']

df['clutch_performance_flag'] = (
    (df['game_importance_score'] >= 0.7) &
    (df['season_performance_percentile'] >= 75)
)


# --------------------------------------------------------------
# 3. match timeline & scheduling
# --------------------------------------------------------------
df['prev_result'] = df['result'].shift(1)
df['prev_percentile'] = df['season_performance_percentile'].shift(1)
df['prev_loss_streak'] = df['loss_streak'].shift(1)


# --------------------------------------------------------------
# 4. date & opponent details
# --------------------------------------------------------------
df['was_set_swept'] = df['set_result'] == "0–3"
df['swept_opponent'] = df['set_result'] == "3–0"
df['deciding_set_played'] = df['set_result'].isin(['2–1', '1–2', '3–2', '2–3'])


# --------------------------------------------------------------
# 5. stats-based calculations
# --------------------------------------------------------------
df.loc[df['did_play'] & df['stats_available'], 'personal_performance_per_set'] = (
    df['personal_performance_score'] / df['sets_played']
)

df['season_avg_performance_score'] = (
    df[df['did_play'] & df['stats_available']]
    .groupby('season')['personal_performance_score']
    .transform('mean')
)

df['season_performance_percentile'] = (
    df[df['did_play'] & df['stats_available']]
    .groupby('season')['personal_performance_score']
    .transform(compute_percentile)
)

df['below_avg_performance'] = (
    df['personal_performance_score'] < df['season_avg_performance_score']
)

df['form_trend_label'] = (
    df[df['did_play'] & df['stats_available']]
    .groupby('season')['personal_performance_score']
    .transform(label_form_trend)
)

df.loc[df['did_play'] & df['stats_available'], 'efficiency_score'] = (
    df['personal_performance_score'] /
    (
        df['serve_err_serving'] +
        df['kill_err_attacking'] +
        df['receiving_err_serve_receiving'] +
        1  # avoid divide-by-zero
    )
)

# offensive focus score
offensive_terms = (
    df['kills_attacking'] * 1.5 +
    df['kill_pct_attacking'] * 10 +
    df['aces_serving'] * 1.3 +
    df['ace_pct_serving'] * 8
)

df.loc[df['did_play'] & df['stats_available'], 'offensive_focus_score'] = (
    offensive_terms / df['personal_performance_score']
)

df.loc[df['did_play'] & df['stats_available'], 'defensive_impact_score'] = (
    (df['digs_digging'] + df['receiving_serve_receiving']) / df['sets_played']
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

season_max = df.groupby('season')[stats_high_fields].transform('max')

df['season_highs_flags'] = df.apply(get_season_high_flags, axis=1)
df['career_highs_flags'] = df.apply(get_career_high_flags, axis=1)
df['record_breaker_flag'] = df['career_highs_flags'].ne('')

df['best_match_of_season'] = (
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
    (df['result'] == 'W') &
    (df['set_count'] == 3) &
    (df['personal_performance_percentile'] >= 80)
)

df['momentum_swing'] = (  # streak breaker + performance swing
    (
        (df['loss_streak'] >= 2) &
        (df['result'] == 'W') &
        (df['personal_performance_percentile'] >= 70)
    ) |
    (
        (df['win_streak'] >= 2) &
        (df['result'] == 'L') &
        (df['personal_performance_percentile'] <= 40)
    )
)

df['deciding_set_win'] = (  # tight win in final deciding set
    df['did_play'] &
    df['result'] == 'W' &
    df['set_result'].isin(['2–1', '3-2']) & 
    df['set_scores'].str.contains(r"(15–(13|14)|16–14)$", na=False)
)

df['deciding_set_loss'] = (  # tight loss in final deciding set
    df['did_play'] &
    df['result'] == 'L' &
    df['set_result'].isin(['2–1', '3–2']) &
    df['set_scores'].str.contains(r"(13–15|14–16)$", na=False)
)

df['bounceback_win'] = (
    (df['prev_loss_streak'] >= 2) &
    (df['result'] == 'W') &
    (df['personal_performance_score'] >= df['season_avg_performance_score'])
)

df['highlight_match'] = (
    df['highlight_match'] |
    (
        (df['personal_performance_percentile'] >= 90) & (
            (df['game_importance_score'] >= 0.7) |
            df['is_playoffs'] |
            df['rivalry'] |
            df['redemption_game'] |
            df['comeback_win']
        )
    )
)


# --------------------------------------------------------------
# 8. narrative & rating scores
# --------------------------------------------------------------
df['emotional_drama_score'] = (
    df['comeback_win'].astype(int) * 2 +
    df['redemption_game'].astype(int) * 2 +
    df['revenge_match'].astype(int) * 1 +
    df['rivalry'].astype(int) * 2 +
    df['birthday_match'].astype(int) * 1 +
    df['highlight_match'].astype(int) * 1 +
    df['is_playoffs'].astype(int) * 3 +
    df['is_championship'].astype(int) * 4 +
    df['is_tournament'].astype(int) * 1 +
    df['milestone_flag'].notna().astype(int) * 1 +
    df['game_importance_score'].clip(upper=2)  # give 0–2 points from importance
)

df['performance_brilliance_score'] = (
    df['record_breaker_flag'].astype(int) * 3 +
    df['season_highs_flags'].ne('').astype(int) * 2 +
    df['career_highs_flags'].ne('').astype(int) * 3 +
    df['clutch_performance_flag'].astype(int) * 2 +
    df['dominant_sweep'].astype(int) * 1 +
    df['heartbreaker'].astype(int) * 1 +
    (df['season_performance_percentile'] >= 85).astype(int) * 2 +
    (df['efficiency_score'] >= 5.0).astype(int) * 1
)

df['match_narrative_score'] = (  # 0-10 scale
    (df['emotional_drama_score'] / 20 * 10) * 0.5 +
    (df['performance_brilliance_score'] / 15 * 10) * 0.5
).round(1)

df['match_narrative_label'] = df['match_narrative_score'].apply(label_narrative_score)

df['fan_rating'] = (
    df['match_narrative_score'] * 0.6 +  # base drama/performance
    df['comeback_win'].astype(int) * 1.0 +
    df['dominant_sweep'].astype(int) * 0.7 +
    df['highlight_match'].astype(int) * 1.0 +
    df['rivalry'].astype(int) * 0.5 +
    df['redemption_game'].astype(int) * 0.5 +
    df['milestone_flag'].notna().astype(int) * 0.5 +
    df['birthday_match'].astype(int) * 0.3 +
    df['deciding_set_played'].astype(int) * 0.4 +
    df['buzzer_beater'].astype(int) * 0.4
).clip(upper=10).round(1)


# --------------------------------------------------------------
# 9. opponent categorization & simulation tags
# --------------------------------------------------------------
df['opponent_strength_tier'] = df.apply(classify_opponent_tier, axis=1)

df['upset_victory'] = (
    (df['result'] == 'W') &
    (df['opponent_strength_tier'] == 'High') &
    (df['season_performance_percentile'] < 50)
)

df['predictable_match'] = (  # repeat opponent + similar margin trend
    df['is_repeat_opponent'] &
    (df['margin_pct'].abs() <= 0.1)  # close match again
)


# --------------------------------------------------------------
# 10. team dynamics tags
# --------------------------------------------------------------
df['team_needed_win'] = (
    (df['loss_streak'] >= 2) &
    (df['result'] == 'W')
)

df['energy_boost_game'] = (
    (df['prev_result'] == 'L') &
    (df['result'] == 'W') &
    (df['season_performance_percentile'] >= 75)
)

df['confidence_boost_game'] = (  # bounceback after poor game
    (df['prev_percentile'] <= 40) &
    (df['season_performance_percentile'] >= 70)
)

df['high_impact_win'] = (  # high-stakes win with great performance
    (df['result'] == 'W') &
    (
        df['is_playoffs'] |
        df['is_championship'] |
        df['clutch_performance_flag'] |
        (df['match_narrative_score'] >= 8.5)
    )
)

# --------------------------------------------------------------
# 11. skill profile tags
# --------------------------------------------------------------
df['best_match_of_season'] = (
    df.groupby('season')['match_narrative_score']
    .transform('max') == df['match_narrative_score']
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
df.to_csv("data/enriched_matches.csv", index=False)
