import sqlite3, pandas as pd, pathlib
db = pathlib.Path("data/wrsafe_demo_seed.db")
assert db.exists(), f"DB ontbreekt: {db}"
con = sqlite3.connect(db)
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", con)
print("Tabel(l)en:", tables["name"].tolist())
for t in tables["name"]:
    df = pd.read_sql(f"SELECT * FROM {t} LIMIT 5", con)
    print(f"\n=== {t} (5 rijen) ==="); print(df)
con.close()
