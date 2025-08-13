"""Simple benchmark of the request to SQL pipeline. Can test different models and save the results."""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports

import functools
import json
import os
import time
from pathlib import Path
from typing import Any, Callable

import duckdb
from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, computed_field

# -------------------------------------------------------------------------------------------------------------------- #
# Models


class TestCase(BaseModel):
    question: str
    expected_result: Any


class TestCaseResult(BaseModel):
    question: str
    expected_result: Any
    computed_result: Any
    llm_response: str
    computed_sql_query: str

    @computed_field
    def is_correct(self) -> bool:
        return self.expected_result == self.computed_result


class BenchmarkTestResults(BaseModel):
    llm_model: str
    test_cases_results: list[TestCaseResult]

    @computed_field
    def accuracy(self) -> float:
        return sum([result.is_correct for result in self.test_cases_results]) / len(self.test_cases_results)


class LLMConnection(BaseModel):
    model_id: str
    base_url: str
    api_key: str


# -------------------------------------------------------------------------------------------------------------------- #
# Constants

PROMPT_ID = "THINKING"

# Paths
DATA_FOLDER = Path("data")
DB_PATH = DATA_FOLDER / "db" / "nba_dwh.duckdb"
DB_CONNECTOR = duckdb.connect(DB_PATH)

INPUT_BENCHMARK_PATH = DATA_FOLDER / "benchmark" / "test_dataset" / "dataset_request_to_sql.json"
OUTPUT_BENCHMARK_PATH = (
    DATA_FOLDER / "benchmark" / "results" / f"dataset_request_to_sql_results_prompt_{PROMPT_ID.lower()}.json"
)


# Credentials
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# Models
LLM_MODELS = [
    # LLMConnection(
    #     model_id="mistralai/mistral-small-24b-instruct-2501:free",
    #     base_url="https://openrouter.ai/api/v1",
    #     api_key=OPENROUTER_API_KEY,
    # ),
    # LLMConnection(
    #     model_id="nvidia/llama-3.1-nemotron-70b-instruct:free",
    #     base_url="https://openrouter.ai/api/v1",
    #     api_key=OPENROUTER_API_KEY,
    # ),
    # LLMConnection(
    #     model_id="meta-llama/llama-3.3-70b-instruct:free",
    #     base_url="https://openrouter.ai/api/v1",
    #     api_key=OPENROUTER_API_KEY,
    # ),
    # LLMConnection(
    #     model_id="deepseek/deepseek-chat:free",
    #     base_url="https://openrouter.ai/api/v1",
    #     api_key=OPENROUTER_API_KEY,
    # ),
    LLMConnection(
        model_id="hf.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF:UD-Q4_K_XL",
        base_url="http://localhost:11434/v1",
        api_key=OPENROUTER_API_KEY,
    ),
    LLMConnection(
        model_id="hf.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF:UD-Q4_K_XL",
        base_url="http://localhost:11434/v1",
        api_key=OPENROUTER_API_KEY,
    ),

]


# Other
NB_RETRY = 3
DELAY_BETWEEN_RETRY = 20
DELAY_BETWEEN_REQUESTS = 20


# -------------------------------------------------------------------------------------------------------------------- #
# Prompts


PROMPT_CATALOG = {
    "NO_THINKING": """
    You are an expert in SQL and NBA data.
    A user asks you this question:

    {nba_data_query}


    Generate a valid SQL query which will answer his question.
    Be concise. Only retrieve the SQL query an nothing else.

    Example of expected return:
    ```sql
    select t.column1, t.column2
    from table t
    where t.column3 = 'value'
    ```

    To answer, you have access to a PostgreSQL database with the following tables:
    {db_description}
    """,
    "THINKING": """
# Persona

You are data analyst specialized in BasketBall and NBA analytics.
Your main job is to receive questions from users and convert it into SQL queries.


# Instructions

A user asks you this question:

    {nba_data_query}

Your task is to generate a valid SQL query which answers his question.
Start by thinking about the question and break it down step by step to figure out which tables you should use, how to join them, and so on.

# Output format

- You will start to think in a thinking tag following this format: <thinking>your-thoughts...</thinking>
- You wil then put the sql query in a sql query tag following this format: <>```sql select ...```</sql_query>


# Example of expected return:

## User query: What is the name of the player who played the most minutes in the 2010 calendar year ? How many minutes did he play during this year?

## Your response:

<thinking>
In order to answer this question:

I need to extract the following informations:
- player name: in `player.player_name`
- number of minutes per games: in `game_boxscore.minute_played`
- game date: in `game_summary.date`

I then need to find the matching keys between these tables:
- (player, game_boxscore): (id, player_id)
- (game_boxscore, game_summary): (game_id, game_summary.id)

I then need to filter the data: where game_summary.date in calendar year 2010
I then need to aggregate the data: By player_id, to compute the sum of minute_played
I then need to order the result by sum of minute_played by descending order
I then need to limit the result to 1
</thinking>

<sql_query>
```sql
select p.player_name, sum(gb.minute_played) sum_minutes_played
from player p
inner join game_boxscore gb on gb.player_id = p.id
inner join game_summary gs on gs.id = gb.game_id
where extract(year from gs.date = 2010
order by 2 desc
limit 1
```
</sql_query>

# Data

To answer, you have access to a PostgreSQL database with the following tables:
{db_description}

The SQL request that you'll generate will need to work effectively with the datbase, thus respecting the schema, keys, tables names, columns names and so on.
""",  # noqa: E501
}


# -------------------------------------------------------------------------------------------------------------------- #
# Functions


def retry_on_null(nb_retry: int, delay: int = 1) -> Callable:
    """Retries a function n if it returns None or an empty string."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            attempts = 0
            while attempts < nb_retry:
                result = func(*args, **kwargs)
                if result not in (None, ""):
                    return result
                attempts += 1
                logger.error(f"Function: {func.__name__} retrieved None. Retrying ({attempts}/{nb_retry})...")
                time.sleep(delay)
            logger.error(f"Function: {func.__name__} still retrieved None after {nb_retry} attempts. Returning None.")
            return None  # If all attempts fail, return None

        return wrapper

    return decorator


def get_table_columns(table_name: str) -> list[tuple[str, str]]:
    return DB_CONNECTOR.sql(
        f"select column_name, data_type from information_schema.columns where table_name = '{table_name}'"
    ).fetchall()


def get_table_description(table_name: str) -> str:
    table_description = f"Table: {table_name}"

    for column_name, data_type in DB_CONNECTOR.sql(
        f"select column_name, data_type from information_schema.columns where table_name = '{table_name}'"
    ).fetchall():
        table_description += f"\n  - {column_name}: {data_type}"

    return table_description


def get_db_description() -> str:
    """Database description in natural language to be used by the LLM."""
    tables_names = [
        e[0]
        for e in DB_CONNECTOR.sql("select table_name from information_schema.tables").fetchall()
        if not e[0].startswith("base_")  # These tables should not be in the final db
    ]
    tables_desc = {table: get_table_description(table) for table in tables_names}
    return "\n\n".join(tables_desc.values())


@retry_on_null(nb_retry=NB_RETRY, delay=DELAY_BETWEEN_RETRY)
def query_llm(prompt: str, llm_model: LLMConnection) -> str:
    """Send query to the LLM."""
    llm_client = OpenAI(
        base_url=llm_model.base_url,
        api_key=llm_model.api_key,
    )

    completion = llm_client.chat.completions.create(
        model=llm_model.model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    llm_response = completion.choices[0].message.content
    return llm_response


def extract_sql_query_from_response(response: str) -> str:
    """Extract SQL query from LLM response."""
    sql_identifier = "```sql"
    if sql_identifier not in response:
        error_msg = "No SQL query found in response."
        raise ValueError(error_msg)
    start_index = response.find(sql_identifier)
    return response[start_index + len(sql_identifier) :].split("```")[0]


def build_prompt(prompt_id: str, nba_data_query: str, db_description: str) -> str:
    """Build prompt to retrieve SQL query from LLM."""
    return PROMPT_CATALOG[prompt_id].format(db_description=db_description, nba_data_query=nba_data_query)


def execute_query(query: str) -> list[Any]:
    return DB_CONNECTOR.sql(query).df().to_dict(orient="records")


def test_single_case(test_case: TestCase, llm_model: LLMConnection, db_description: str) -> TestCaseResult:
    try:
        prompt = build_prompt(nba_data_query=test_case.question, db_description=db_description, prompt_id=PROMPT_ID)
        llm_response = query_llm(prompt=prompt, llm_model=llm_model)
        sql_query = extract_sql_query_from_response(response=llm_response)
        sql_result = execute_query(query=sql_query)
        result = TestCaseResult(
            question=test_case.question,
            expected_result=test_case.expected_result,
            computed_result=sql_result,
            llm_response=llm_response,
            computed_sql_query=sql_query,
        )
    except Exception as exc:
        logger.error(f"Error: {exc}")
        result = TestCaseResult(
            question=test_case.question,
            expected_result=test_case.expected_result,
            computed_result=f"ERROR: {exc}",
            llm_response=f"ERROR: {exc}",
            computed_sql_query="",
        )

    return result


# -------------------------------------------------------------------------------------------------------------------- #
# Main

if __name__ == "__main__":
    # Retrieve db description
    db_description = get_db_description()

    # Retrieve benchmark test cases
    with INPUT_BENCHMARK_PATH.open("r", encoding="utf-8") as f:
        benchmark_test_cases = [TestCase(**e) for e in json.load(f)]

    llm_models_results = {}
    for llm_model in LLM_MODELS:
        logger.info(f"Test: {llm_model.model_id}")

        # Test each test case for a given LLM
        test_cases_results = []
        for i, test_case in enumerate(benchmark_test_cases):
            test_case_result = test_single_case(test_case=test_case, llm_model=llm_model, db_description=db_description)
            test_cases_results.append(test_case_result)
            logger.debug(f"{i + 1} / {len(benchmark_test_cases)} - Correct: {test_case_result.is_correct}")
            time.sleep(DELAY_BETWEEN_REQUESTS)

        benchmark_results = BenchmarkTestResults(
            llm_model=llm_model.model_id,
            test_cases_results=test_cases_results,
        )
        llm_models_results[llm_model.model_id] = benchmark_results
        logger.info(f"Accuracy: {benchmark_results.accuracy:.1%}")

    with OUTPUT_BENCHMARK_PATH.open("w") as f:
        json.dump([llm_model_result.model_dump() for llm_model_result in llm_models_results.values()], f, indent=4)
    logger.info("Done")
