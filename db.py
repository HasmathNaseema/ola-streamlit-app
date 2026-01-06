import pandas as pd
from sqlalchemy import create_engine, text

# ✅ CHANGE THESE
DB_USER = "root"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_NAME = "ola_ride"   # your database name

engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)

def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    params = params or {}
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn, params=params)
    return df
