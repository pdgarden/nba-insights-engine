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


# -------------------------------------------------------------------------------------------------------------------- #
# Constants

DATA_FOLDER = Path("data")
DB_PATH = DATA_FOLDER / "db" / "nba_dwh.duckdb"
DB_CONNECTOR = duckdb.connect(DB_PATH)

# Create LLM client
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


INPUT_BENCHMARK_PATH = DATA_FOLDER / "benchmark" / "test_dataset" / "dataset_request_to_sql.json"
OUTPUT_BENCHMARK_PATH = DATA_FOLDER / "benchmark" / "results" / "dataset_request_to_sql_results.json"

LLM_MODELS = [
    "mistralai/mistral-small-24b-instruct-2501:free",
    "nvidia/llama-3.1-nemotron-70b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-chat:free",
]

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
    tables_names = [e[0] for e in DB_CONNECTOR.sql("select table_name from information_schema.tables").fetchall()]
    tables_desc = {table: get_table_description(table) for table in tables_names}
    return "\n\n".join(tables_desc.values())


@retry_on_null(nb_retry=3, delay=10)
def query_llm(prompt: str, llm_model: str) -> str:
    """Send query to the LLM."""
    completion = LLM_CLIENT.chat.completions.create(
        model=llm_model,
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


def build_prompt(nba_data_query: str, db_description: str) -> str:
    """Build prompt to retrieve SQL query from LLM."""
    return f"""
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
    """


def execute_query(query: str) -> list[Any]:
    return DB_CONNECTOR.sql(query).df().to_dict(orient="records")


def test_single_case(test_case: TestCase, llm_model: str, db_description: str) -> TestCaseResult:
    try:
        prompt = build_prompt(nba_data_query=test_case.question, db_description=db_description)
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
        logger.info(f"Test: {llm_model}")

        # Test each test case for a given LLM
        test_cases_results = []
        for test_case in benchmark_test_cases:
            test_cases_results.append(
                test_single_case(test_case=test_case, llm_model=llm_model, db_description=db_description)
            )
            time.sleep(1)

        benchmark_results = BenchmarkTestResults(
            llm_model=llm_model,
            test_cases_results=test_cases_results,
        )
        llm_models_results[llm_model] = benchmark_results
        logger.info(f"    Accuracy: {benchmark_results.accuracy:.1%}")

    with OUTPUT_BENCHMARK_PATH.open("w") as f:
        json.dump([llm_model_result.model_dump() for llm_model_result in llm_models_results.values()], f, indent=4)
    logger.info("Done")
