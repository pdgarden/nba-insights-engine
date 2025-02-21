import duckdb

from app.constants import DB_PATH

# TODO: Encapsulate
con = duckdb.connect(database=DB_PATH, read_only=True)
