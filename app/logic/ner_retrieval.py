"""Logic for Players and Teams Named Entity Recognition (NER), and the retrieval from the database."""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports
import difflib

from pydantic import BaseModel

from app.db.dao import get_player_names, get_team_names
from app.llm import query_llm

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
    return f"""
You are given a text that may contain some NBA players and players and teams.
Retrieve the list of players and teams from the text.
DO NOT MODIFY THE NAMES OF THE PLAYERS AND TEAMS.
Example n°1 :
Input: "How many rebounds did mike pietrus have in the 2018 playoffs?"
Output: {{'players': ['mike pietrus'], 'teams': []}}

Example n°2 :
Input: "How many points did Victor wembanyama have in the 2024 season for the spurs?"
Output: {{'players': ['Victor wembanyama'], 'teams': ['spurs]}}

Notice that the name of the player and team is not modified and no uppercase is added.

Retrieve the result in the following format:  {PlayersAndTeams.model_json_schema()}

Here is the text to process:

{text}.
"""


def get_closest_player_name(player_name: str) -> str:
    """Find the closest player name in the database from an input given name."""
    player_names = get_player_names()
    player_names_lowercase_to_original_case = {p.lower(): p for p in player_names}

    # Find the closest match, use lowercase to make the search case insensitive.
    closest_match_lower_case = difflib.get_close_matches(
        word=player_name.lower(), possibilities=[p.lower() for p in player_names], n=1, cutoff=0
    )[0]
    return player_names_lowercase_to_original_case[closest_match_lower_case]


def get_closest_team_name(team_name: str) -> str:
    """Find the closest team name in the database from an input given name."""
    team_names = get_team_names()
    team_names_lowercase_to_original_case = {p.lower(): p for p in team_names}

    # Find the closest match, use lowercase to make the search case insensitive.
    closest_match_lower_case = difflib.get_close_matches(
        word=team_name.lower(), possibilities=[p.lower() for p in team_names], n=1, cutoff=0
    )[0]
    return team_names_lowercase_to_original_case[closest_match_lower_case]


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

    for player_name in ner_result.players:
        text = text.replace(player_name, get_closest_player_name(player_name))
    for team_name in ner_result.teams:
        text = text.replace(team_name, get_closest_team_name(team_name))

    return text
