from app.db.dao import Player, Team
from app.logic.ner_retrieval import get_closest_player_name, get_closest_team_name


def test_get_closest_player_name() -> None:
    players = [
        Player(id=1, player_name="LeBron James"),
        Player(id=2, player_name="Stephen Curry"),
        Player(id=3, player_name="Kevin Durant"),
        Player(id=4, player_name="James Harden"),
    ]

    # Test exact match
    assert get_closest_player_name("LeBron James", players) == "LeBron James"

    # Test case insensitivity
    assert get_closest_player_name("lebron james", players) == "LeBron James"

    # Test closest match
    assert get_closest_player_name("Lebron Jame", players) == "LeBron James"
    assert get_closest_player_name("Stephen Cur", players) == "Stephen Curry"
    assert get_closest_player_name("Kevin Duran", players) == "Kevin Durant"
    assert get_closest_player_name("James Hard", players) == "James Harden"


def test_get_closest_team_name() -> None:
    teams = [
        Team(id=1, team_name="Los Angeles Lakers"),
        Team(id=2, team_name="Golden State Warriors"),
        Team(id=3, team_name="Brooklyn Nets"),
        Team(id=4, team_name="Miami Heat"),
    ]

    # Test exact match
    assert get_closest_team_name("Los Angeles Lakers", teams) == "Los Angeles Lakers"

    # Test case insensitivity
    assert get_closest_team_name("los angeles lakers", teams) == "Los Angeles Lakers"

    # Test closest match
    assert get_closest_team_name("Lakers", teams) == "Los Angeles Lakers"
    assert get_closest_team_name("Warriors", teams) == "Golden State Warriors"
    assert get_closest_team_name("Brooklyn Net", teams) == "Brooklyn Nets"
    assert get_closest_team_name("Miami Hea", teams) == "Miami Heat"
