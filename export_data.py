import os
from db import run_query

os.makedirs("data", exist_ok=True)

df = run_query("SELECT * FROM ola_clean;")
df.to_csv("data/ola_clean.csv", index=False)

print("✅ Exported:", df.shape, "to data/ola_clean.csv")
