"""Logic for Players and Teams Named Entity Recognition (NER), and the retrieval from the database."""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports
from pydantic import BaseModel

from app.db.dao import Player, Team, get_all_players, get_all_teams
from app.llm import query_llm
from app.logic.fuzzy_search import top_matches
from app.prompts import NER_RETRIEVAL

# -------------------------------------------------------------------------------------------------------------------- #
# Models


class PlayersAndTeams(BaseModel):
    "A list of players and a list of teams"

    players: list[str]
    teams: list[str]


# -------------------------------------------------------------------------------------------------------------------- #
# Functions


def get_ner_prompt(text: str) -> str:
    """Get a name entity retrieval prompt for the LLM to extract players and teams from a text."""
    return NER_RETRIEVAL.format(text=text, expected_json_schema=PlayersAndTeams.model_json_schema())


def get_closest_player_name(player_name: str, players: list[Player]) -> str:
    """Find the closest player name in the database from an input given name."""
    players_names = [p.player_name for p in players]
    return top_matches(player_name, players_names, limit=1)[0][0]


def get_closest_team_name(team_name: str, teams: list[Team]) -> str:
    """Find the closest team name in the database from an input given name."""
    teams_names = [t.team_name for t in teams]
    return top_matches(team_name, teams_names, limit=1)[0][0]


def replace_names_in_text(text: str) -> str:
    """Clean the text by replacing the players and teams names with the ones available in the db."""
    prompt_ner_players_teams = get_ner_prompt(text)
    ner_players_teams = query_llm(
        prompt=prompt_ner_players_teams, model_kind="light", structured_output=PlayersAndTeams
    )

    # Find exact name value in text because the LLM sometimes doesn't return the original case.
    q = text
    ner_result = PlayersAndTeams(
        players=[q[q.lower().find(p.lower()) : q.lower().find(p.lower()) + len(p)] for p in ner_players_teams.players],
        teams=[q[q.lower().find(p.lower()) : q.lower().find(p.lower()) + len(p)] for p in ner_players_teams.teams],
    )

    # Replace the names in the text with the ones available in the db.
    players = get_all_players()
    for player_name in ner_result.players:
        text = text.replace(
            player_name,
            get_closest_player_name(player_name=player_name, players=players),
        )

    teams = get_all_teams()
    for team_name in ner_result.teams:
        text = text.replace(
            team_name,
            get_closest_team_name(team_name=team_name, teams=teams),
        )

    return text
