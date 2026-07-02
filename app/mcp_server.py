import json

from mcp.server.fastmcp import FastMCP

from app.db import dao
from app.db.dao import get_db_description, sql_to_df
from app.logic.fuzzy_search import top_matches

mcp = FastMCP(
    "nba",
    instructions=(
        "This server provides access to an NBA statistics database. "
        "Workflow: always call `get_nba_database_schema` first to discover "
        "available tables and their columns, then use `query_database` to run SQL. "
        "Never call `query_database` without first knowing the schema."
    ),
)


@mcp.tool()
async def get_nba_database_schema() -> str:
    """Return the full schema of the NBA database.

    Call this before `query_database` to discover table names and column
    definitions. The schema is required to write correct SQL.
    """
    return get_db_description()


@mcp.tool()
async def query_database(sql: str, limit: int = 100) -> str:
    """Execute a SQL query against the NBA database and return the results.

    Prerequisite: call `get_nba_database_schema` first. Queries referencing
    unknown tables or columns will fail.

    Args:
        sql: A valid SQL SELECT statement.
        limit: Maximum number of rows to return (default 100).
    """
    try:
        limited_sql = f"SELECT * FROM ({sql}) AS __q LIMIT {limit}"
        frame = sql_to_df(limited_sql)
        if frame.empty:
            return "Query returned no results."
        result = frame.to_string(index=False)
        if len(frame) == limit:
            result += f"\n\n[Results truncated to {limit} rows. Pass a higher limit if needed.]"
    except Exception as e:
        return f"Error executing query: {e}"
    else:
        return result


def _search_by_name(query: str, items: list[dict], name_field: str) -> str:
    """Fuzzy-search `items` (each a dict with an `id` and `name_field` key) and return the top 10 matches as JSON."""
    names = [item[name_field] for item in items]
    id_by_name = {item[name_field]: item["id"] for item in items}
    matches = top_matches(query, names, limit=10)
    results = [{"id": id_by_name[m[0]], name_field: m[0], "score": round(m[1], 1)} for m in matches]
    return json.dumps(results, indent=2)


@mcp.tool()
async def search_player_by_name(player_name: str) -> str:
    """Find the top 10 closest player names in the database for a given query.

    Use this before querying player stats to get the correct player id.

    Args:
        player_name: A partial or approximate player name to search for.
    """
    return _search_by_name(player_name, dao.get_all_players(), "player_name")


@mcp.tool()
async def search_team_by_name(team_name: str) -> str:
    """Find the top 10 closest team names in the database for a given query.

    Use this before querying team stats to get the correct team id.

    Args:
        team_name: A partial or approximate team name to search for.
    """
    return _search_by_name(team_name, dao.get_all_teams(), "team_name")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
