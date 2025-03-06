from app.logic.ner_retrieval import get_closest_player_name, get_closest_team_name


def test_get_closest_player_name() -> None:
    players_names = ["LeBron James", "Stephen Curry", "Kevin Durant", "James Harden"]

    # Test exact match
    assert get_closest_player_name("LeBron James", players_names) == "LeBron James"

    # Test case insensitivity
    assert get_closest_player_name("lebron james", players_names) == "LeBron James"

    # Test closest match
    assert get_closest_player_name("Lebron Jame", players_names) == "LeBron James"
    assert get_closest_player_name("Stephen Cur", players_names) == "Stephen Curry"
    assert get_closest_player_name("Kevin Duran", players_names) == "Kevin Durant"
    assert get_closest_player_name("James Hard", players_names) == "James Harden"


def test_get_closest_team_name() -> None:
    teams_names = ["Los Angeles Lakers", "Golden State Warriors", "Brooklyn Nets", "Miami Heat"]

    # Test exact match
    assert get_closest_team_name("Los Angeles Lakers", teams_names) == "Los Angeles Lakers"

    # Test case insensitivity
    assert get_closest_team_name("los angeles lakers", teams_names) == "Los Angeles Lakers"

    # Test closest match
    assert get_closest_team_name("Lakers", teams_names) == "Los Angeles Lakers"
    assert get_closest_team_name("Warriors", teams_names) == "Golden State Warriors"
    assert get_closest_team_name("Brooklyn Net", teams_names) == "Brooklyn Nets"
    assert get_closest_team_name("Miami Hea", teams_names) == "Miami Heat"
