# Code Structure

## Module Overview

This document provides a comprehensive view of the code structure, including all modules, classes, and functions.

## Module Hierarchy

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

## Detailed Structure

### Modules (0)



### Classes (15)

- **PlayerUpdater** (api_updater)
- **MatchStatuses** (test_routers)
- **DatabaseManager** (manager)
- **MatchResult** (match_result)
- **Game** (game)
- **League** (league)
- **PlayerStats** (player_stats)
- **Team** (team)
- **Stream** (stream)
- **Player** (player)
- **Serie** (serie)
- **RoundScore** (round_score)
- **PlayerResult** (player_result)
- **Tournament** (tournament)
- **Match** (match)


### Functions (67)


#### api_updater

- `PlayerUpdater.__init__()` - Line N/A
- `PlayerUpdater.make_request()` - Line N/A
- `PlayerUpdater.get_upcoming_matches()` - Line N/A
- `PlayerUpdater.get_particular_team_url()` - Line N/A
- `PlayerUpdater.get_particular_player_stats_url()` - Line N/A
- `PlayerUpdater.get_particular_game_stats_url()` - Line N/A
- `PlayerUpdater.get_required_matches_for_particular_player()` - Line N/A
- `PlayerUpdater.compare_and_update()` - Line N/A
- `PlayerUpdater.fetch_last_games()` - Line N/A
- `PlayerUpdater.populate_leagues()` - Line N/A
- `PlayerUpdater.populate_series()` - Line N/A
- `PlayerUpdater.populate_tournament()` - Line N/A
- `PlayerUpdater.populate_team()` - Line N/A
- `PlayerUpdater.populate_player()` - Line N/A
- `PlayerUpdater.populate_match()` - Line N/A
- `PlayerUpdater.populate_game()` - Line N/A
- `PlayerUpdater.populate_match_result()` - Line N/A
- `PlayerUpdater.populate_round_score()` - Line N/A
- `PlayerUpdater.populate_player_result()` - Line N/A
- `PlayerUpdater.populate_player_stats()` - Line N/A
- `PlayerUpdater.populate_stream()` - Line N/A
- `PlayerUpdater.main_population()` - Line N/A
- `run_api_updater()` - Line N/A

#### env

- `run_migrations_offline()` - Line N/A
  - Run migrations in 'offline' mode.
- `run_migrations_online()` - Line N/A
  - Run migrations in 'online' mode.

#### funkcja

- `pp()` - Line N/A
- `dp()` - Line N/A
- `wynik()` - Line N/A

#### logger_config

- `setup_loggers()` - Line N/A

#### main

- `initialize_api()` - Line N/A

#### manager

- `DatabaseManager.__init__()` - Line N/A
- `DatabaseManager.create_tables()` - Line N/A
- `DatabaseManager.check_all_table_exists()` - Line N/A
- `DatabaseManager.get_session()` - Line N/A
- `DatabaseManager.add()` - Line N/A
  - Save an instance of a model to the database
- `DatabaseManager.get()` - Line N/A
  - Fetch a single instance of a model by its ID.
- `DatabaseManager.get_all()` - Line N/A
  - Fetch all instances of a model
- `DatabaseManager.update()` - Line N/A
  - Update a single instance of a model by its ID
- `DatabaseManager.delete()` - Line N/A
  - Delete a single instance of a model by its ID
- `DatabaseManager.clear_all_data()` - Line N/A
- `DatabaseManager.get_session()` - Line N/A
- `get_db()` - Line N/A

#### player_base

- `PlayerBase.serialize_birthday()` - Line N/A
- `PlayerBase.serialize_modified_at()` - Line N/A

#### roboczy

- `fetch_matches()` - Line N/A

#### router

- `get_margin()` - Line N/A
- `calculate_odds()` - Line N/A
- `poisson_probabilities()` - Line N/A
  - Pre-compute Poisson probabilities for the range of kills using numpy for efficiency.
- `create_probability_matrix()` - Line N/A
  - Use numpy to efficiently create a probability matrix for two players.
- `calculate_total_probabilities()` - Line N/A
  - Calculate total probabilities for A wins, draw, and B wins using numpy.
- `calculate_odds()` - Line N/A
  - Convert probabilities to odds.
- `fetch_upcoming_matches()` - Line N/A

#### routers

- `get_margin()` - Line N/A
- `calculate_odds_kill()` - Line N/A
- `poisson_probabilities()` - Line N/A
  - Pre-compute Poisson probabilities for the range of kills using numpy for efficiency.
- `create_probability_matrix()` - Line N/A
  - Use numpy to efficiently create a probability matrix for two players.
- `calculate_total_probabilities()` - Line N/A
  - Calculate total probabilities for A wins, draw, and B wins using numpy.
- `calculate_odds_h2h()` - Line N/A
  - Convert probabilities to odds.
- `fetch_upcoming_matches()` - Line N/A

#### test_routers

- `get_roster_url()` - Line N/A
- `fetch_rosters()` - Line N/A
- `get_player_avg_kills_data()` - Line N/A
- `fetch_match_info()` - Line N/A

#### tests_models

- `test_league_model()` - Line N/A
- `test_serie_model()` - Line N/A
- `test_team_model()` - Line N/A

#### tournaments

- `roster_url()` - Line N/A
