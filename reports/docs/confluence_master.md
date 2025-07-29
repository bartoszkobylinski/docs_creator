# API Documentation Documentation

> **Generated**: 2025-07-29 09:52:34  
> **Coverage**: 11.0%  
> **Total Items**: 145

---

## 📋 Overview

API Documentation is an automated documentation system that analyzes Python code and generates comprehensive documentation.

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Items | 145 |
| Documented | 16 |
| Coverage | 11.0% |
| Modules | 0 |
| Classes | 15 |
| Functions | 67 |

---

## 🏗️ Architecture

### Module Structure

```
├── api_updater
│   ├── PlayerUpdater (CLASS)
│   ├── PlayerUpdater.__init__ (FUNCTION)
│   ├── PlayerUpdater.make_request (FUNCTION)
│   ├── PlayerUpdater.get_upcoming_matches (FUNCTION)
│   ├── PlayerUpdater.get_particular_team_url (FUNCTION)
│   ├── PlayerUpdater.get_particular_player_stats_url (FUNCTION)
│   ├── PlayerUpdater.get_particular_game_stats_url (FUNCTION)
│   ├── PlayerUpdater.get_required_matches_for_particular_player (FUNCTION)
│   ├── PlayerUpdater.compare_and_update (FUNCTION)
│   ├── PlayerUpdater.fetch_last_games (FUNCTION)
│   ├── PlayerUpdater.populate_leagues (FUNCTION)
│   ├── PlayerUpdater.populate_series (FUNCTION)
│   ├── PlayerUpdater.populate_tournament (FUNCTION)
│   ├── PlayerUpdater.populate_team (FUNCTION)
│   ├── PlayerUpdater.populate_player (FUNCTION)
│   ├── PlayerUpdater.populate_match (FUNCTION)
│   ├── PlayerUpdater.populate_game (FUNCTION)
│   ├── PlayerUpdater.populate_match_result (FUNCTION)
│   ├── PlayerUpdater.populate_round_score (FUNCTION)
│   ├── PlayerUpdater.populate_player_result (FUNCTION)
│   ├── PlayerUpdater.populate_player_stats (FUNCTION)
│   ├── PlayerUpdater.populate_stream (FUNCTION)
│   ├── PlayerUpdater.main_population (FUNCTION)
│   └── run_api_updater (FUNCTION)
├── env
│   ├── run_migrations_offline (FUNCTION)
│   └── run_migrations_online (FUNCTION)
├── funkcja
│   ├── pp (FUNCTION)
│   ├── dp (FUNCTION)
│   └── wynik (FUNCTION)
├── game
│   └── Game (CLASS)
├── game_base
│   └── GameBase (PYDANTIC_MODEL)
├── league
│   └── League (CLASS)
├── league_base
│   └── LeagueBase (PYDANTIC_MODEL)
├── logger_config
│   └── setup_loggers (FUNCTION)
├── main
│   ├── app.middleware (MIDDLEWARE)
│   ├── app.router_inclusion (ROUTER_INCLUSION)
│   ├── app.router_inclusion (ROUTER_INCLUSION)
│   ├── initialize_api (FUNCTION)
│   ├── app (METADATA)
│   ├── app.middleware (MIDDLEWARE)
│   └── app.router_inclusion (ROUTER_INCLUSION)
├── manager
│   ├── DatabaseManager (CLASS)
│   ├── DatabaseManager.__init__ (FUNCTION)
│   ├── DatabaseManager.create_tables (FUNCTION)
│   ├── DatabaseManager.check_all_table_exists (FUNCTION)
│   ├── DatabaseManager.get_session (FUNCTION)
│   ├── DatabaseManager.add (FUNCTION)
│   ├── DatabaseManager.get (FUNCTION)
│   ├── DatabaseManager.get_all (FUNCTION)
│   ├── DatabaseManager.update (FUNCTION)
│   ├── DatabaseManager.delete (FUNCTION)
│   ├── DatabaseManager.clear_all_data (FUNCTION)
│   ├── DatabaseManager.get_session (FUNCTION)
│   └── get_db (FUNCTION)
├── match
│   └── Match (CLASS)
├── match_base
│   └── MatchBase (PYDANTIC_MODEL)
├── match_result
│   └── MatchResult (CLASS)
├── match_result_base
│   └── MatchResultBase (PYDANTIC_MODEL)
├── player
│   └── Player (CLASS)
├── player_base
│   ├── PlayerBase (PYDANTIC_MODEL)
│   ├── PlayerBase.serialize_birthday (FUNCTION)
│   ├── PlayerBase.serialize_modified_at (FUNCTION)
│   └── PlayerBase.from_orm (CLASSMETHOD)
├── player_result
│   └── PlayerResult (CLASS)
├── player_result_base
│   └── PlayerResultBase (PYDANTIC_MODEL)
├── player_stats
│   └── PlayerStats (CLASS)
├── player_stats_base
│   └── PlayerStatsBase (PYDANTIC_MODEL)
├── pydantic_models
│   ├── LeagueBase (PYDANTIC_MODEL)
│   ├── SerieBase (PYDANTIC_MODEL)
│   ├── GameBase (PYDANTIC_MODEL)
│   ├── PlayerBase (PYDANTIC_MODEL)
│   ├── PlayerStatsBase (PYDANTIC_MODEL)
│   ├── PlayerResultBase (PYDANTIC_MODEL)
│   ├── StreamBase (PYDANTIC_MODEL)
│   ├── RoundScoreBase (PYDANTIC_MODEL)
│   ├── MatchResultBase (PYDANTIC_MODEL)
│   ├── MatchBase (PYDANTIC_MODEL)
│   ├── TeamBase (PYDANTIC_MODEL)
│   └── TournamentBase (PYDANTIC_MODEL)
├── roboczy
│   └── fetch_matches (FUNCTION)
├── round_score
│   └── RoundScore (CLASS)
├── round_score_base
│   └── RoundScoreBase (PYDANTIC_MODEL)
├── router
│   ├── get_margin (FUNCTION)
│   ├── calculate_odds (FUNCTION)
│   ├── poisson_probabilities (FUNCTION)
│   ├── create_probability_matrix (FUNCTION)
│   ├── calculate_total_probabilities (FUNCTION)
│   ├── calculate_odds (FUNCTION)
│   ├── fetch_upcoming_matches (FUNCTION)
│   ├── upcoming_matches (ASYNC_FUNCTION)
│   ├── upcoming_matches (GET)
│   ├── optimized_fetch_and_aggregate (ASYNC_FUNCTION)
│   ├── optimized_fetch_and_aggregate (GET)
│   ├── predict_stats (ASYNC_FUNCTION)
│   ├── predict_stats (POST)
│   ├── generate_h2h_data (ASYNC_FUNCTION)
│   ├── generate_h2h_data (POST)
│   ├── generate_over_under_data (ASYNC_FUNCTION)
│   └── generate_over_under_data (POST)
├── routers
│   ├── get_margin (FUNCTION)
│   ├── calculate_odds_kill (FUNCTION)
│   ├── poisson_probabilities (FUNCTION)
│   ├── create_probability_matrix (FUNCTION)
│   ├── calculate_total_probabilities (FUNCTION)
│   ├── calculate_odds_h2h (FUNCTION)
│   ├── fetch_upcoming_matches (FUNCTION)
│   ├── upcoming_matches (ASYNC_FUNCTION)
│   ├── upcoming_matches (GET)
│   ├── optimized_fetch_and_aggregate (ASYNC_FUNCTION)
│   ├── optimized_fetch_and_aggregate (GET)
│   ├── predict_stats (ASYNC_FUNCTION)
│   ├── predict_stats (POST)
│   ├── generate_h2h_data (ASYNC_FUNCTION)
│   ├── generate_h2h_data (POST)
│   ├── generate_over_under_data (ASYNC_FUNCTION)
│   └── generate_over_under_data (POST)
├── serie
│   └── Serie (CLASS)
├── serie_base
│   └── SerieBase (PYDANTIC_MODEL)
├── stream
│   └── Stream (CLASS)
├── stream_base
│   └── StreamBase (PYDANTIC_MODEL)
├── team
│   └── Team (CLASS)
├── team_base
│   └── TeamBase (PYDANTIC_MODEL)
├── test_routers
│   ├── MatchStatuses (CLASS)
│   ├── upcoming_matches (ASYNC_FUNCTION)
│   ├── upcoming_matches (GET)
│   ├── all_players_list (ASYNC_FUNCTION)
│   ├── all_players_list (GET)
│   ├── add_player_to_team (ASYNC_FUNCTION)
│   ├── add_player_to_team (POST)
│   ├── remove_player_from_team (ASYNC_FUNCTION)
│   ├── remove_player_from_team (DELETE)
│   ├── get_roster_url (FUNCTION)
│   ├── fetch_rosters (FUNCTION)
│   ├── get_player_avg_kills_data (FUNCTION)
│   ├── fetch_match_info (FUNCTION)
│   ├── upcoming_matches_with_rosters_and_stats (ASYNC_FUNCTION)
│   ├── upcoming_matches_with_rosters_and_stats (GET)
│   ├── match_players_stats (ASYNC_FUNCTION)
│   └── match_players_stats (GET)
├── tests_models
│   ├── test_league_model (FUNCTION)
│   ├── test_serie_model (FUNCTION)
│   └── test_team_model (FUNCTION)
├── tournament
│   └── Tournament (CLASS)
├── tournament_base
│   └── TournamentBase (PYDANTIC_MODEL)
└── tournaments
    └── roster_url (FUNCTION)
```

---

## 📊 Documentation Coverage

### Summary
- ✅ Documented: 16 items
- ❌ Missing: 129 items
- 📈 Coverage: 11.0%

### Items Needing Documentation

- `setup_loggers` (logger_config) - Line N/A
- `PlayerUpdater` (api_updater) - Line N/A
- `PlayerUpdater.__init__` (api_updater) - Line N/A
- `PlayerUpdater.make_request` (api_updater) - Line N/A
- `PlayerUpdater.get_upcoming_matches` (api_updater) - Line N/A
- `PlayerUpdater.get_particular_team_url` (api_updater) - Line N/A
- `PlayerUpdater.get_particular_player_stats_url` (api_updater) - Line N/A
- `PlayerUpdater.get_particular_game_stats_url` (api_updater) - Line N/A
- `PlayerUpdater.get_required_matches_for_particular_player` (api_updater) - Line N/A
- `PlayerUpdater.compare_and_update` (api_updater) - Line N/A

*... and 119 more items*


---

## 🚀 Quick Start

1. **Install dependencies**: `poetry install`
2. **Start server**: `poetry run python main.py`
3. **Open dashboard**: http://localhost:8200
4. **Scan project**: Enter path and click "Scan"

---

## 📡 API Endpoints

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scan-local` | POST | Scan a local project |
| `/api/report/data` | GET | Get current report data |
| `/api/docs/latex` | POST | Generate PDF documentation |
| `/api/confluence/publish` | POST | Publish to Confluence |

---

## 🔗 Links

- [View Dashboard](http://localhost:8200)
- [API Documentation](http://localhost:8200/docs)
- [Download PDF Report](../latex/documentation.pdf)

---

*This document was automatically generated. For the latest version, regenerate from the dashboard.*
