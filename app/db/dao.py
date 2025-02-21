from app.db.connection import con


def get_player_names() -> list[str]:
    """Retrieve list of player names available in the database."""
    return [e[0] for e in con.sql("select distinct player_name from player").fetchall()]


def get_team_names() -> list[str]:
    """Retrieve list of team names available in the database."""
    return [e[0] for e in con.sql("select distinct team_name from team").fetchall()]
