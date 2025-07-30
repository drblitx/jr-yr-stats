"""
@name cleaning.py
@author drblitx
@created July 2025
"""

# module imports
import pandas as pd
import os

# merging datasets
def merge_season_stats(year_dir, output_dir='data/cleaned'):
    season_name = os.path.basename(os.path.normpath(year_dir))
    os.makedirs(output_dir, exist_ok=True)
    
    files = os.listdir(year_dir)
    csv_files = sorted([f for f in files if f.endswith('.csv')])
    dfs = []

    for file in csv_files:
        path = os.path.join(year_dir, file)
        df = pd.read_csv(path)

        df['match_number'] = df.groupby('date').cumcount() + 1

        cols = df.columns.tolist()
        if 'match_number' in cols:
            cols.remove('match_number')
            date_index = cols.index('date')
            cols.insert(date_index + 1, 'match_number')
            df = df[cols]

        if len(dfs) > 0 and 'result' in df.columns:
            df = df.drop(columns=['result'])

        dfs.append(df)
    
    if not dfs:
        raise ValueError(f"No CSV files found in {year_dir}")

    merge_keys = ['date', 'opponent', 'sets_played', 'match_number']
    merged = dfs[0]
    for df in dfs[1:]:
        merged = merged.merge(df, on=merge_keys, how='outer')

    merged = merged.sort_values(by=['date', 'match_number']).reset_index(drop=True)
    return merged

def add_derived_features(df, season_label, season_year):
    if 'result' in df.columns and 'set_result' not in df.columns:
        result_split = df['result'].str.extract(r'^(W|L|T)\s+(\d-\d)$')
        df['result'] = result_split[0]
        df['set_result'] = result_split[1]

    if 'set_result' not in df.columns:
        raise ValueError("Missing 'set_result' column — ensure result format like 'W 2-1'.")
    
    # normalize date format and make numeric
    df['date'] = pd.to_datetime(df['date'] + f'/{season_year}', errors='coerce')
    df = df.dropna(subset=['date'])  # drop rows w/ invalid dates
    
    # re-sort so match_number can be trusted
    df = df.sort_values(by=['date', 'match_number']).reset_index(drop=True)

    # add match_index (season sequential ID)
    df['match_index'] = range(1, len(df) + 1)

    # add weekday
    df['weekday'] = df['date'].dt.day_name()

    # reformat date as numeric string (yyyy-mm-dd)
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')

    # numeric result
    result_map = {'W': 1, 'T': 0, 'L': -1}
    df['numeric_result'] = df['result'].map(result_map)

    # ser count (e.g., 3-2 → 5)
    df['set_count'] = df['set_result'].str.extract(r'(\d)-(\d)').astype(float).sum(axis=1)

    # set diff (e.g., 3-2 → +1)
    df['set_diff'] = df['set_result'].str.extract(r'(\d)-(\d)').astype(float).apply(lambda x: x[0] - x[1], axis=1)

    # margin % (e.g., +1/5 = 0.2)
    df['margin_pct'] = df['set_diff'] / df['set_count']

    # setting 'Varsity Opponents' to unknown
    df['opponent_original'] = df['opponent']
    df['opponent_unknown'] = df['opponent'].str.lower() == 'varsity opponent'
    df['opponent_code'] = df['opponent'].str.lower().str.replace(' ', '_')

    # match ID
    df['match_id'] = (
        str(season_year)
        + '_' + df['date'].astype(str)
        + '_G' + df['match_number'].astype(str)
    )

    # duplicate opponent same day?
    df['is_duplicate_opponent_on_date'] = df.duplicated(subset=['date', 'opponent'], keep=False)

    # is tournament match?
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
    df['is_tournament'] = df['date'].isin(tournament_dates)

    # season metadata
    df['season_label'] = season_label
    df['season_year'] = season_year

    # key columns to the front
    important_cols = ['date', 'match_number', 'match_id', 'match_index', 'season_label', 'season_year',
                      'result', 'set_result', 'set_diff', 'set_count', 'margin_pct', 'numeric_result',
                      'opponent', 'weekday', 'is_duplicate_opponent_on_date', 'is_tournament']
    
    remaining_cols = [col for col in df.columns if col not in important_cols]
    df = df[important_cols + remaining_cols]

    return df

if __name__ == "__main__":
    dirs = ['freshman', 'sophomore', 'senior']
    years = [2016, 2017, 2019]
    all_seasons = []
    for dir, yr in zip(dirs, years):
        season_raw_path = f'data/raw/{dir}'
        merged = merge_season_stats(season_raw_path)
        merged = add_derived_features(merged, season_label=dir, season_year=yr)
        merged.to_csv(f'data/cleaned/{dir}_full.csv', index=False)
        all_seasons.append(merged)

    # combine all in one df
    df_all = pd.concat(all_seasons, ignore_index=True)
    df_all = df_all.sort_values(by=['date', 'match_number']).reset_index(drop=True)
    df_all['career_match_index'] = range(1, len(df_all) + 1)
    df_all = df_all[merged.columns.tolist() + ['career_match_index']]
    df_all.to_csv("data/cleaned/all_seasons.csv", index=False)
    