# 🏐 HS Volleyball Stats (jr-yr-stats)

This is a personal data project analyzing my performance in high school volleyball across 3 seasons:
- **Freshman (2016)**
- **Sophomore (2017)**
- **Senior (2019)**

My junior season (2018) was not per-match-tracked for statistics due to poor record-keeping. There's the schedule and results, but not the stats. Hence, this project will use data science to estimate what my match-by-match and season-long stas would've been based on past performance (see junior_full.csv). 

This project compiles and cleans individual match-level statistics from each season, which produces a dataset that supports analysis of trends, performance, and outcomes of matches. The final merged dataset is saved as PLACEHOLDER csv.

---

## 🧾 Overview of Data Layers & Tags
The full merged dataset contains these fields -- some are computed, some are manually curated, and others will be inferred from the merged dataset. 

- `match_key`
- `career_match_index`
- `career_stage`
- `season`
- `season_match_number`
- `season_stage`
- `date`
- `day_of_week`
- `week_of_season`
- `days_since_last_match`
- `is_back_to_back`
- `match_density_3days`
- `match_no`
- `total_matches_that_day`
- `multi_game_day`
- `first_match_of_day`
- `last_match_of_day`
- `same_day_opponent_seq`
- `opponent`
- `opponent_slug`
- `season_opponent_seq`
- `is_repeat_opponent`
- `rivalry`
- `deaf_school`
- `match_type`
- `game_importance`
- `game_importance_score`
- `event_name`
- `milestone_flag` -- e.g. `"first MSSD match"`, `"first SO match"`
- `set_scores`
- `set_count`
- `set_result`
- `set_diff`
- `location`
- `forfeited`
- `injured`
- `sick`
- `comeback_win`
- `revenge_match`
- `redemption_game`
- `birthday_match`
- `is_conference`
- `is_playoffs`
- `is_tournament`
- `is_championship`
- `total_points_for`
- `total_points_against`
- `margin_pct`
- `high_margin_win`
- `low_margin_loss`
- `did_play`
- `played_all_sets`
- `favorite_match`
- `stats_available`
- `season_highs_flags`
- `career_highs_flags`
- `record_breaker_flag`
- `deciding_set_win`
- `deciding_set_loss`
- `low_error_game`
- `win_streak`
- `loss_streak`
- `prev_result`
- `prev_win_streak`
- `prev_loss_streak`
- `was_set_swept`
- `swept_opponent`
- `deciding_set_played`
- `sets_played`
- `kills`
- `kills_per_set`
- `kill_pct`
- `kill_attempts`
- `kill_errors`
- `hit_pct`
- `assists`
- `assists_per_set`
- `ball_handling_attempts`
- `ball_handling_errors`
- `solo_blocks`
- `assisted_blocks`
- `total_blocks`
- `blocks_per_set`
- `block_errors`
- `digs`
- `dig_errors`
- `digs_per_set`
- `receiving`
- `receiving_errors`
- `receiving_per_set`
- `aces`
- `aces_per_set`
- `ace_pct`
- `serve_attempts`
- `serve_errors`
- `serve_pct`
- `points`
- `highlight_match`
- `maxpreps`

---

## 📊 Key Columns in `finalized_data.csv`
- `date`: Match date (YYYY-MM-DD)
- `match_number`: Order of the match on that day
- `match_id`: Unique identifier (season + date + match number)
- `match_index`: Match number within the season
- `career_match_index`: Match number across all seasons
- `season_label`: e.g., freshman, sophomore, senior
- `season_year`: Numeric year of the season
- `result`: W (win), L (loss), or T (tie)
- `set_result`: Final set score (e.g., 2-1, 0-2)
- `set_diff`: Difference in sets won vs lost
- `set_count`: Total sets played
- `margin_pct`: Set margin divided by total sets
- `numeric_result`: +1 for win, -1 for loss, 0 for tie
- `opponent`: Name of opponent team
- `weekday`: Day of week of the match
- `is_duplicate_opponent_on_date`: Flag if opponent played twice in one day
- `is_tournament`: Flag for tournament matches
- `opponent_code`: Lowercased, underscored version of opponent name
- `kills`, `hit_pct`, `points`, `serve_pct`, `aces`, etc.: Game performance stats

If you're curious about how certain labels are generated or how performance scores are computed, dig into the notebooks or check junior_full.csv for the prediction logic.
