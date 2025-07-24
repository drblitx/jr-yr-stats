# 🏐 Junior Year Volleyball Stats (jr-yr-stats)

A personal data project analyzing my performance in high school volleyball across three seasons:
- **Freshman (2016)**
- **Sophomore (2017)**
- **Senior (2019)**

Then uses these analyses to predict what my stats would have been match-by-match and season during my junior year (see `junior_full.csv` for what I mean). My junior year was under-reported; so I'm using data science to estimate what should've been.

This project compiles and cleans individual match-level statistics from each season, producing a dataset that supports analysis. Examples include trends, situational performance, and match outcomes. The final dataset is saved as `all_seasons.csv`.

---

## 📊 Key Columns in `all_seasons.csv`
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
- `opponent_unknown`: Flag if opponent was listed as “Varsity Opponent”
- `opponent_code`: Lowercased, underscored version of opponent name
- `kills`, `hit_pct`, `points`, `serve_pct`, `aces`, etc.: Game performance stats
