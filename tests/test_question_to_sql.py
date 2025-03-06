# -------------------------------------------------------------------------------------------------------------------- #
# Imports

import pytest

from app.logic.question_to_sql import extract_sql_query

# -------------------------------------------------------------------------------------------------------------------- #
# Tests


# test_extract_sql


def test_extract_sql_query_success() -> None:
    text = """Here is your SQL query:
```sql
SELECT * FROM players WHERE points_per_game > 20
```
"""
    expected_query = "\nSELECT * FROM players WHERE points_per_game > 20\n"
    assert extract_sql_query(text) == expected_query


def test_extract_sql_query_no_sql_identifier() -> None:
    text = """Here is your SQL query:
SELECT * FROM players WHERE points_per_game > 20
"""
    with pytest.raises(ValueError, match="No SQL query found in text."):
        extract_sql_query(text)


def test_extract_sql_query_multiple_sql_blocks() -> None:
    text = """Here is your first SQL query:
```sql
SELECT * FROM players WHERE points_per_game > 20
```
And here is another one:
```sql
SELECT * FROM teams WHERE wins > 50
```
"""
    expected_query = "\nSELECT * FROM players WHERE points_per_game > 20\n"
    assert extract_sql_query(text) == expected_query
