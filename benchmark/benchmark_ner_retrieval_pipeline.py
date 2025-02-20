"""Simple benchmark of the NER and Retrieval pipeline. Can test different models and save the results."""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports

import difflib
import json
from pathlib import Path

import duckdb
from openai import OpenAI
from pydantic import BaseModel, computed_field

# -------------------------------------------------------------------------------------------------------------------- #
# Models


class PlayersAndTeams(BaseModel):
    "A list of players and a list of teams"

    players: list[str]
    teams: list[str]


class TestCase(BaseModel):
    """Model of a single test for the NER and retrieval pipeline."""

    request: str

    # Expected values
    expected_raw_teams: list[str]
    expected_raw_players: list[str]
    expected_db_teams: dict[str, str]
    expected_db_players: dict[str, str]


class TestCaseResult(BaseModel):
    """Model of a single test and corresponding result for the NER and retrieval pipeline."""

    request: str

    # Expected values
    expected_raw_teams: list[str]
    expected_raw_players: list[str]
    expected_db_teams: dict[str, str]
    expected_db_players: dict[str, str]

    # Values computed by the pipeline
    computed_raw_teams: list[str]
    computed_raw_players: list[str]
    computed_db_teams: dict[str, str]
    computed_db_players: dict[str, str]

    @computed_field
    def is_correct(self) -> bool:
        return (self.expected_db_teams == self.computed_db_teams) and (
            self.expected_db_players == self.computed_db_players
        )


class BenchmarkTestResults(BaseModel):
    """Model of the result of a benchmark for the NER and retrieval pipeline for a given LLM."""

    llm_model: str
    test_results: list[TestCaseResult]

    @computed_field
    def accuracy(self) -> float:
        return sum([result.is_correct for result in self.test_results]) / len(self.test_results)


# -------------------------------------------------------------------------------------------------------------------- #
# Constants


DATA_FOLDER = Path("data")
DB_PATH = DATA_FOLDER / "db" / "nba_dwh.duckdb"
DB_CONNECTOR = duckdb.connect(DB_PATH)
LLM_CLIENT = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


INPUT_BENCHMARK_PATH = DATA_FOLDER / "benchmark" / "test_dataset" / "dataset_ner_retrieval.json"
OUTPUT_BENCHMARK_PATH = DATA_FOLDER / "benchmark" / "results" / "dataset_ner_retrieval_results.json"


RAW_PLAYER_NAMES = [e[0] for e in DB_CONNECTOR.sql("select distinct player_name from player").fetchall()]
PLAYER_NAMES = [p.lower() for p in RAW_PLAYER_NAMES]
PLAYER_NAMES_LOWERCASE = [p.lower() for p in RAW_PLAYER_NAMES]
PLAYER_NAMES_LOWERCASE_TO_NORMAL_CASE = {p.lower(): p for p in RAW_PLAYER_NAMES}

RAW_TEAM_NAMES = [e[0] for e in DB_CONNECTOR.sql("select distinct team_name from team").fetchall()]
TEAM_NAMES = [p.lower() for p in RAW_TEAM_NAMES]
TEAM_NAMES_LOWERCASE = [p.lower() for p in RAW_TEAM_NAMES]
TEAM_NAMES_LOWERCASE_TO_NORMAL_CASE = {p.lower(): p for p in RAW_TEAM_NAMES}

LLM_MODELS = [
    "smollm2:360m",
    "llama3.2:3b",
    "mistral:7b",
    "qwen2.5:7b",
]


# -------------------------------------------------------------------------------------------------------------------- #
# Functions


def make_ner_prompt(text: str) -> str:
    """Make a ner prompt for the LLM to extract players and teams from a text."""
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


def query_llm(ner_prompt: str, llm_model: str) -> PlayersAndTeams:
    """Query the LLM by using OpenAI API to retrieve players and teams from a text."""
    completion = LLM_CLIENT.beta.chat.completions.parse(
        model=llm_model,
        messages=[{"role": "user", "content": ner_prompt}],
        temperature=0,
        response_format=PlayersAndTeams,
        max_completion_tokens=500,
    )  # TODO: Add error handling
    llm_response = completion.choices[0].message

    return llm_response.parsed


def get_closest_player(player_name: str) -> str:
    """Find the closest player name in the database from an input given name."""
    closest_match = difflib.get_close_matches(
        word=player_name.lower(), possibilities=PLAYER_NAMES_LOWERCASE, n=1, cutoff=0
    )[0]
    return PLAYER_NAMES_LOWERCASE_TO_NORMAL_CASE[closest_match]


def get_closest_team(team_name: str) -> str:
    """Find the closest team name in the database from an input given name."""
    closest_match = difflib.get_close_matches(
        word=team_name.lower(), possibilities=TEAM_NAMES_LOWERCASE, n=1, cutoff=0
    )[0]
    return TEAM_NAMES_LOWERCASE_TO_NORMAL_CASE[closest_match]


def test_single_case(test_case: TestCase, llm_model: str) -> TestCaseResult:
    """Take a single test case, run it though the NER and retrieval pipeline. Then return the result."""

    ner_result = query_llm(
        ner_prompt=make_ner_prompt(text=test_case.request),
        llm_model=llm_model,
    )

    # Find exact name value in text as the LLM sometimes doesn't return the original case.
    r = test_case.request
    ner_result = PlayersAndTeams(
        players=[r[r.lower().find(p.lower()) : r.lower().find(p.lower()) + len(p)] for p in ner_result.players],
        teams=[r[r.lower().find(p.lower()) : r.lower().find(p.lower()) + len(p)] for p in ner_result.teams],
    )

    ner_db_result_players = {player_name: get_closest_player(player_name) for player_name in ner_result.players}
    ner_db_result_teams = {team_name: get_closest_team(team_name) for team_name in ner_result.teams}

    return TestCaseResult(
        request=test_case.request,
        expected_raw_teams=test_case.expected_raw_teams,
        expected_raw_players=test_case.expected_raw_players,
        expected_db_teams=test_case.expected_db_teams,
        expected_db_players=test_case.expected_db_players,
        computed_raw_teams=ner_result.teams,
        computed_raw_players=ner_result.players,
        computed_db_teams=ner_db_result_teams,
        computed_db_players=ner_db_result_players,
    )


# -------------------------------------------------------------------------------------------------------------------- #
# Main

if __name__ == "__main__":
    with INPUT_BENCHMARK_PATH.open("r") as f:
        benchmark_test_set = [TestCase(**test_case) for test_case in json.load(f)]

    llm_models_results = {}
    for llm_model in LLM_MODELS:
        print(f"Test: {llm_model}")

        benchmark_result = BenchmarkTestResults(
            llm_model=llm_model,
            test_results=[
                test_single_case(test_case=test_case, llm_model=llm_model) for test_case in benchmark_test_set
            ],
        )
        llm_models_results[llm_model] = benchmark_result
        print(f"    Accuracy: {benchmark_result.accuracy:.1%}")

    with OUTPUT_BENCHMARK_PATH.open("w") as f:
        json.dump([llm_model_result.model_dump() for llm_model_result in llm_models_results.values()], f, indent=4)
    print("Done")
