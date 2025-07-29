# Documentation Coverage Report

Generated on: 2025-07-29 10:05:23

## Summary

- **Total Items**: 145
- **Documented**: 16 (11.0%)
- **Missing Documentation**: 129

## Coverage Visualization

```
[█░░░░░░░░░] 11.0%
```

## Items Missing Documentation

The following items are missing documentation:


### api_updater

- `PlayerUpdater` (CLASS) - Line N/A
- `PlayerUpdater.__init__` (FUNCTION) - Line N/A
- `PlayerUpdater.make_request` (FUNCTION) - Line N/A
- `PlayerUpdater.get_upcoming_matches` (FUNCTION) - Line N/A
- `PlayerUpdater.get_particular_team_url` (FUNCTION) - Line N/A
- `PlayerUpdater.get_particular_player_stats_url` (FUNCTION) - Line N/A
- `PlayerUpdater.get_particular_game_stats_url` (FUNCTION) - Line N/A
- `PlayerUpdater.get_required_matches_for_particular_player` (FUNCTION) - Line N/A
- `PlayerUpdater.compare_and_update` (FUNCTION) - Line N/A
- `PlayerUpdater.fetch_last_games` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_leagues` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_series` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_tournament` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_team` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_player` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_match` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_game` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_match_result` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_round_score` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_player_result` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_player_stats` (FUNCTION) - Line N/A
- `PlayerUpdater.populate_stream` (FUNCTION) - Line N/A
- `PlayerUpdater.main_population` (FUNCTION) - Line N/A
- `run_api_updater` (FUNCTION) - Line N/A

### funkcja

- `pp` (FUNCTION) - Line N/A
- `dp` (FUNCTION) - Line N/A
- `wynik` (FUNCTION) - Line N/A

### game

- `Game` (CLASS) - Line N/A

### game_base

- `GameBase` (PYDANTIC_MODEL) - Line N/A

### league

- `League` (CLASS) - Line N/A

### league_base

- `LeagueBase` (PYDANTIC_MODEL) - Line N/A

### logger_config

- `setup_loggers` (FUNCTION) - Line N/A

### main

- `app.middleware` (MIDDLEWARE) - Line N/A
- `app.router_inclusion` (ROUTER_INCLUSION) - Line N/A
- `app.router_inclusion` (ROUTER_INCLUSION) - Line N/A
- `initialize_api` (FUNCTION) - Line N/A
- `app.middleware` (MIDDLEWARE) - Line N/A
- `app.router_inclusion` (ROUTER_INCLUSION) - Line N/A

### manager

- `DatabaseManager` (CLASS) - Line N/A
- `DatabaseManager.__init__` (FUNCTION) - Line N/A
- `DatabaseManager.create_tables` (FUNCTION) - Line N/A
- `DatabaseManager.check_all_table_exists` (FUNCTION) - Line N/A
- `DatabaseManager.get_session` (FUNCTION) - Line N/A
- `DatabaseManager.clear_all_data` (FUNCTION) - Line N/A
- `DatabaseManager.get_session` (FUNCTION) - Line N/A
- `get_db` (FUNCTION) - Line N/A

### match

- `Match` (CLASS) - Line N/A

### match_base

- `MatchBase` (PYDANTIC_MODEL) - Line N/A

### match_result

- `MatchResult` (CLASS) - Line N/A

### match_result_base

- `MatchResultBase` (PYDANTIC_MODEL) - Line N/A

### player

- `Player` (CLASS) - Line N/A

### player_base

- `PlayerBase` (PYDANTIC_MODEL) - Line N/A
- `PlayerBase.serialize_birthday` (FUNCTION) - Line N/A
- `PlayerBase.serialize_modified_at` (FUNCTION) - Line N/A
- `PlayerBase.from_orm` (CLASSMETHOD) - Line N/A

### player_result

- `PlayerResult` (CLASS) - Line N/A

### player_result_base

- `PlayerResultBase` (PYDANTIC_MODEL) - Line N/A

### player_stats

- `PlayerStats` (CLASS) - Line N/A

### player_stats_base

- `PlayerStatsBase` (PYDANTIC_MODEL) - Line N/A

### pydantic_models

- `LeagueBase` (PYDANTIC_MODEL) - Line N/A
- `SerieBase` (PYDANTIC_MODEL) - Line N/A
- `GameBase` (PYDANTIC_MODEL) - Line N/A
- `PlayerBase` (PYDANTIC_MODEL) - Line N/A
- `PlayerStatsBase` (PYDANTIC_MODEL) - Line N/A
- `PlayerResultBase` (PYDANTIC_MODEL) - Line N/A
- `StreamBase` (PYDANTIC_MODEL) - Line N/A
- `RoundScoreBase` (PYDANTIC_MODEL) - Line N/A
- `MatchResultBase` (PYDANTIC_MODEL) - Line N/A
- `MatchBase` (PYDANTIC_MODEL) - Line N/A
- `TeamBase` (PYDANTIC_MODEL) - Line N/A
- `TournamentBase` (PYDANTIC_MODEL) - Line N/A

### roboczy

- `fetch_matches` (FUNCTION) - Line N/A

### round_score

- `RoundScore` (CLASS) - Line N/A

### round_score_base

- `RoundScoreBase` (PYDANTIC_MODEL) - Line N/A

### router

- `get_margin` (FUNCTION) - Line N/A
- `calculate_odds` (FUNCTION) - Line N/A
- `fetch_upcoming_matches` (FUNCTION) - Line N/A
- `upcoming_matches` (ASYNC_FUNCTION) - Line N/A
- `upcoming_matches` (GET) - Line N/A
- `optimized_fetch_and_aggregate` (ASYNC_FUNCTION) - Line N/A
- `optimized_fetch_and_aggregate` (GET) - Line N/A
- `predict_stats` (ASYNC_FUNCTION) - Line N/A
- `predict_stats` (POST) - Line N/A
- `generate_h2h_data` (ASYNC_FUNCTION) - Line N/A
- `generate_h2h_data` (POST) - Line N/A
- `generate_over_under_data` (ASYNC_FUNCTION) - Line N/A
- `generate_over_under_data` (POST) - Line N/A

### routers

- `get_margin` (FUNCTION) - Line N/A
- `calculate_odds_kill` (FUNCTION) - Line N/A
- `fetch_upcoming_matches` (FUNCTION) - Line N/A
- `upcoming_matches` (ASYNC_FUNCTION) - Line N/A
- `upcoming_matches` (GET) - Line N/A
- `optimized_fetch_and_aggregate` (ASYNC_FUNCTION) - Line N/A
- `optimized_fetch_and_aggregate` (GET) - Line N/A
- `predict_stats` (ASYNC_FUNCTION) - Line N/A
- `predict_stats` (POST) - Line N/A
- `generate_h2h_data` (ASYNC_FUNCTION) - Line N/A
- `generate_h2h_data` (POST) - Line N/A
- `generate_over_under_data` (ASYNC_FUNCTION) - Line N/A
- `generate_over_under_data` (POST) - Line N/A

### serie

- `Serie` (CLASS) - Line N/A

### serie_base

- `SerieBase` (PYDANTIC_MODEL) - Line N/A

### stream

- `Stream` (CLASS) - Line N/A

### stream_base

- `StreamBase` (PYDANTIC_MODEL) - Line N/A

### team

- `Team` (CLASS) - Line N/A

### team_base

- `TeamBase` (PYDANTIC_MODEL) - Line N/A

### test_routers

- `MatchStatuses` (CLASS) - Line N/A
- `upcoming_matches` (ASYNC_FUNCTION) - Line N/A
- `upcoming_matches` (GET) - Line N/A
- `all_players_list` (ASYNC_FUNCTION) - Line N/A
- `all_players_list` (GET) - Line N/A
- `add_player_to_team` (ASYNC_FUNCTION) - Line N/A
- `add_player_to_team` (POST) - Line N/A
- `remove_player_from_team` (ASYNC_FUNCTION) - Line N/A
- `remove_player_from_team` (DELETE) - Line N/A
- `get_roster_url` (FUNCTION) - Line N/A
- `fetch_rosters` (FUNCTION) - Line N/A
- `get_player_avg_kills_data` (FUNCTION) - Line N/A
- `fetch_match_info` (FUNCTION) - Line N/A
- `upcoming_matches_with_rosters_and_stats` (ASYNC_FUNCTION) - Line N/A
- `upcoming_matches_with_rosters_and_stats` (GET) - Line N/A
- `match_players_stats` (ASYNC_FUNCTION) - Line N/A
- `match_players_stats` (GET) - Line N/A

### tests_models

- `test_league_model` (FUNCTION) - Line N/A
- `test_serie_model` (FUNCTION) - Line N/A
- `test_team_model` (FUNCTION) - Line N/A

### tournament

- `Tournament` (CLASS) - Line N/A

### tournament_base

- `TournamentBase` (PYDANTIC_MODEL) - Line N/A

### tournaments

- `roster_url` (FUNCTION) - Line N/A


## Well-Documented Items

The following items have comprehensive documentation:

- `run_migrations_offline` (env) - 297 characters
- `run_migrations_online` (env) - 124 characters
