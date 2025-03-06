import pandas as pd

from app.db.connection import con


def get_players_names() -> list[str]:
    """Retrieve list of player names available in the database."""
    return [e[0] for e in con.sql("select distinct player_name from player").fetchall()]


def get_teams_names() -> list[str]:
    """Retrieve list of team names available in the database."""
    return [e[0] for e in con.sql("select distinct team_name from team").fetchall()]


def get_table_columns(table_name: str) -> list[str, str]:
    """Retrieve list of columns name and type for a given table."""
    return [
        e
        for e in con.sql(
            f"select column_name, data_type from information_schema.columns where table_name = '{table_name}'"
        ).fetchall()
    ]


def get_tables() -> list[str]:
    """Retrieve list of tables available in the database."""
    return [e[0] for e in con.sql("select table_name from information_schema.tables").fetchall()]


def sql_to_df(sql_query: str) -> pd.DataFrame:
    """Execute a SQL query and return the result as a pandas DataFrame."""
    return con.sql(sql_query).df()
