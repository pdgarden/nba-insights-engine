"""Logic to generate a SQL query on the NBA database from a question in natural language."""
# -------------------------------------------------------------------------------------------------------------------- #
# Imports

from loguru import logger

from app.db.dao import get_table_columns, get_tables
from app.llm import query_llm

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


def build_prompt(question: str, db_description: str) -> str:
    """Build prompt to retrieve SQL query from LLM."""
    return f"""
    You are an expert in SQL and NBA data.
    A user asks you this question:

    {question}


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


def extract_sql_query(text: str) -> str:
    """Extract SQL query from a text. This assumes that the SQL query is enclosed in triple backticks."""
    sql_identifier = "```sql"
    if sql_identifier not in text:
        error_msg = "No SQL query found in text."
        raise ValueError(error_msg)
    start_index = text.find(sql_identifier)
    return text[start_index + len(sql_identifier) :].split("```")[0]


def generate_sql_query(question: str) -> str:
    """Generate SQL query from a question."""
    db_description = get_db_description()
    prompt = build_prompt(question, db_description)
    llm_response = query_llm(prompt=prompt, model_kind="heavy")
    logger.debug(f"llm_response: {llm_response}")
    sql_query = extract_sql_query(llm_response)
    return sql_query
