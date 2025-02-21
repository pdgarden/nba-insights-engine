"""Logic to generate a SQL query on the NBA database from a question in natural language."""
# -------------------------------------------------------------------------------------------------------------------- #
# Imports

from app.db.dao import get_table_columns, get_tables

# -------------------------------------------------------------------------------------------------------------------- #
# Models

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
