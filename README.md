# 🏐 HS Volleyball Stats (jr-yr-stats)

A personal data project analyzing my performance in high school volleyball across three seasons:
- **Freshman season (2016)**
- **Sophomore season (2017)**
- **Senior season (2019)** 

My junior year season (2018) was under-reported due to poor record-keeping. I do have the schedules and results, but not the stats; so this project uses data science to estimate what my match-by-match and season-long stats should have been based on past performance (see junior_full.csv).

This project compiles and cleans individual match-level statistics from each season, producing a dataset that supports deeper analysis of trends, situational performance, and match outcomes. The final merged dataset is saved as finalized_data.csv.

---

## 🧾 Overview of Data Layers & Tags
To better organize the match and player context, I've designed several structured tag layers. Some are computed, some are manually curated, and others will be inferred from the merged dataset.

### 🧍‍♀️ Personal + Participation Flags
- `injured`, `sick`, `forfeited`
- `did_play`, `played_all_sets`
- `is_repeat_opponent`
- `milestone_flag` -- e.g. `"first MSSD match"`, `"first SO match"`

### 🏷️ Match Context Tags
- `match_type` (e.g., tournament, league)
- `game_importance`, `game_importance_score`
- `comeback_win`, `rivalry`, `revenge_match`, `redemption_game`
- `highlight_match` (default: `False`)
- `event_name`

### 🧮 Match Timeline + Scheduling
- `match_index`, `season_match_number`, `career_match_index`
- `week_of_season`, `days_since_last_match`, `is_back_to_back`
- `match_density_3days`, `multi_game_day`, `match_no`, `total_matches_that_day`
- `first_match_of_day`, `last_match_of_day`, `same_day_opponent_seq`
- `season_stage`, `total_sets_that_day`
- `team_needed_win`, `confidence_boost_game`, `momentum_swing`

### 🎂 Date & Opponent Details
- `birthday_match`
- `opponent_slug`, `deaf_school`
- `total_points_for`, `total_points_against`

### 📊 Stats-Based Calculations *(requires stat merge)*
- `did_play`, `played_all_sets`
- `personal_performance_score`, `personal_performance_per_set`
- `season_avg_performance_score`, `season_performance_percentile`
- `below_avg_performance`, `performance_trend`, `form_trend_label`
- `offensive_focus_score`, `defensive_impact_score`, `efficiency_score`
- `zero_stat_match`, `best_match_of_season`, `clutch_factor`
- `vs_last_time_same_opponent`, `game_rating`
- `offense_dominant_match`, `defense_dominant_match`, `balanced_match`, `low_error_game`

### 🏅 Career & Narrative Tags
- `career_match_index`, `career_stage`, `match_key`
- `result`, `set_scores`, `set_result`, `set_count`, `set_diff`
- `was_set_swept`, `swept_opponent`, `deciding_set_played`
- `milestone_flag`

### 📣 Storyline Tags *(some require stats + outcome)*
- `revenge_match`, `redemption_game`, `highlight_match`
- `momentum_swing`, `confidence_boost_game`, `clutch_performance_flag`
- `heartbreaker` (close loss + good performance)  
- `dominant_sweep` (strong win + good stats) 
- `record_breaker_flag` 
- `season_highs_flags`

### 🎮 Fun & Sim Tags
- `game_rating`
- `energy_boost_game`
- `high_impact_win`

### 🧠 Opponent Prediction & Categorization
- `predictable_match`
- `upset_victory`
- `opponent_strength_tier`

### 🧱 Team Dynamics Tags
- `team_needed_win`
- `high_margin_win` / `low_margin_loss` (calculated from `margin_pct`)

### 🧬 Skill Profile Analysis
- `offense_dominant_match`
- `defense_dominant_match`
- `balanced_match`
- `low_error_game`

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
