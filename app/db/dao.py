import pandas as pd

from app.db.connection import con


def get_players_names() -> list[str]:
    """Retrieve list of player names available in the database."""
    return [e[0] for e in con.sql("select distinct player_name from player").fetchall()]


def get_teams_names() -> list[str]:
    """Retrieve list of team names available in the database."""
    return [e[0] for e in con.sql("select distinct team_name from team").fetchall()]


def get_table_columns(table_name: str) -> list[tuple[str, str]]:
    """Retrieve list of columns name and type for a given table."""
    return [
        e
        for e in con.sql(
            f"select column_name, data_type from information_schema.columns where table_name = '{table_name}'"
        ).fetchall()
    ]


def get_tables() -> list[str]:
    """Retrieve list of tables available in the database."""
    return [
        e[0]
        for e in con.sql("select table_name from information_schema.tables").fetchall()
        if not e[0].startswith("base_")  # These tables should not be in the final db
    ]


def sql_to_df(sql_query: str) -> pd.DataFrame:
    """Execute a SQL query and return the result as a pandas DataFrame."""
    return con.sql(sql_query).df()


def get_all_players() -> list[dict]:
    """Retrieve list of players with id and name."""
    return [
        {"id": e[0], "player_name": e[1]}
        for e in con.sql("SELECT id, player_name FROM player").fetchall()
    ]


def get_all_teams() -> list[dict]:
    """Retrieve list of teams with id and name."""
    return [
        {"id": e[0], "team_name": e[1]}
        for e in con.sql("SELECT id, team_name FROM team").fetchall()
    ]


def get_table_description(table_name: str) -> str:
    """Return a human-readable description of a table's columns."""
    table_description = f"Table: {table_name}"
    for column_name, data_type in get_table_columns(table_name):
        table_description += f"\n  - {column_name}: {data_type}"
    return table_description


def get_db_description() -> str:
    """Return a description of all tables in the database."""
    return "\n\n".join(get_table_description(t) for t in get_tables())
