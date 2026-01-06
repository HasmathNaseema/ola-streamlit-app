import pandas as pd
from sqlalchemy import text

DATA_PATH = "data/ola_clean.csv"

def _load_df():
    return pd.read_csv(DATA_PATH)

def run_query(sql: str, params: dict | None = None):
    """
    Runs a SQL query on the CSV using pandas + sqlite in-memory.
    Supports simple SELECT queries.
    """
    df = _load_df()

    import sqlite3
    conn = sqlite3.connect(":memory:")
    df.to_sql("ola_clean", conn, index=False, if_exists="replace")

    if params is None:
        params = {}

    out = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return out
