"""
@name add_advanced_tags.py
@created August 2025
"""

import pandas as pd
from scipy.stats import rankdata

# load in full merged dataset
df = pd.read_csv("data/full_merged_dataset.csv")

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

# flag JR season with having no stats
df['stats_available'] = df['season'] != 'JR'

# did i play all sets of that game?
df['played_all_sets'] = df['did_play'] & (df['sets_played'] == df['set_count'])

# personal performance score
df['personal_performance_score'] = df.apply(compute_performance_score, axis=1)

# track matches with 0 stats (doubt any will be flagged but still)
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

# performance per set
df.loc[df['did_play'] & df['stats_available'], 'personal_performance_per_set'] = (
    df['personal_performance_score'] / df['sets_played']
)

# season average performance
df['season_avg_performance_score'] = (
    df[df['did_play'] & df['stats_available']]
    .groupby('season')['personal_performance_score']
    .transform('mean')
)

# season ranking
def compute_percentile(group):
    return rankdata(group, method='average') / len(group) * 100

df['season_performance_percentile'] = (
    df[df['did_play'] & df['stats_available']]
    .groupby('season')['personal_performance_score']
    .transform(compute_percentile)
)

# below average performances
df['below_avg_performance'] = (
    df['personal_performance_score'] < df['season_avg_performance_score']
)

df['form_trend_label'] = (
    df[df['did_play'] & df['stats_available']]
    .groupby('season')['personal_performance_score']
    .transform(label_form_trend)
)

# efficiency score
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

# defensive focus score
df.loc[df['did_play'] & df['stats_available'], 'defensive_impact_score'] = (
    (df['digs_digging'] + df['receiving_serve_receiving']) / df['sets_played']
)

# save to csv
df.to_csv("data/enriched_matches.csv", index=False)
