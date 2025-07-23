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

    for i, file in enumerate(csv_files):
        path = os.path.join(year_dir, file)
        df = pd.read_csv(path)

        if 'result' in df.columns:
            result_split = df['result'].str.extract(r'^(W|L|T)\s+(\d-\d)$')
            df['result'] = result_split[0]
            df['set_result'] = result_split[1]
            df['set_diff'] = (
                df['set_result']
                .str.extract(r'(\d)-(\d)')
                .astype(float)
                .apply(lambda x: x[0] - x[1], axis=1)
            )

        df['match_number'] = df.groupby('date').cumcount() + 1
        cols = df.columns.tolist()

        for col in ['match_number', 'result', 'set_result', 'set_diff']:
            if col in cols:
                cols.remove(col)
                date_index = cols.index('date')
                cols.insert(date_index + 1, col)

        df = df[cols]

        if i != 0 and 'result' in df.columns:
            df = df.drop(columns=['result'])
        dfs.append(df)
    
    if not dfs:
        raise ValueError(f"No CSV files found in {year_dir}")

    merged = dfs[0]
    for df in dfs[1:]:
        merged = merged.merge(df, on=['date', 'opponent', 'sets_played', 'match_number'], how='outer')

    merged = merged.sort_values(by=['date', 'match_number']).reset_index(drop=True)
    output_path = os.path.join(output_dir, f"{season_name}_full.csv")
    merged.to_csv(output_path, index=False)
    print(f"Saved merged file to {output_path}")

def add_derived_features(df, season_label, season_year):
    pass


dirs = ['freshman', 'sophomore', 'senior']
for dir in dirs:
    merge_season_stats(f"data/raw/{dir}")
