"""Logic to generate a SQL query on the NBA database from a question in natural language."""
# -------------------------------------------------------------------------------------------------------------------- #
# Imports

from loguru import logger

from app.db.dao import get_table_columns, get_tables
from app.llm import query_llm
from app.prompts import QUESTION_TO_SQL

# -------------------------------------------------------------------------------------------------------------------- #
# Functions


def get_table_description(table_name: str) -> str:
    """Generate the description of a table in natural language to be used by the LLM."""
    table_description = f"Table: {table_name}"
    for column_name, data_type in get_table_columns(table_name):
        table_description += f"\n  - {column_name}: {data_type}"

    return table_description


def get_db_description() -> str:
    """Generate the description of a database in natural language to be used by the LLM."""
    tables_names = get_tables()
    tables_desc = {table: get_table_description(table) for table in tables_names}
    return "\n\n".join(tables_desc.values())


def build_prompt(question: str, db_description: str, thinking_mode: bool) -> str:
    """Build prompt to retrieve SQL query from LLM."""
    prompt = QUESTION_TO_SQL["THINKING"] if thinking_mode else QUESTION_TO_SQL["NO_THINKING"]
    return prompt.format(question=question, db_description=db_description)


def extract_sql_query(text: str) -> str:
    """Extract SQL query from a text. This assumes that the SQL query is enclosed in triple backticks."""
    sql_identifier = "```sql"
    if sql_identifier not in text:
        error_msg = "No SQL query found in text."
        raise ValueError(error_msg)
    start_index = text.find(sql_identifier)
    return text[start_index + len(sql_identifier) :].split("```")[0]


def generate_sql_query(question: str, thinking_mode: bool) -> str:
    """Generate SQL query from a question."""
    db_description = get_db_description()
    prompt = build_prompt(question=question, db_description=db_description, thinking_mode=thinking_mode)
    llm_response = query_llm(prompt=prompt, model_kind="heavy")
    logger.debug(f"llm_response: {llm_response}")
    sql_query = extract_sql_query(llm_response)
    return sql_query
