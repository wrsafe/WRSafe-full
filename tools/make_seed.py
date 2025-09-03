import sqlite3, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "wrsafe_demo_seed.db"
SEED.parent.mkdir(parents=True, exist_ok=True)

if SEED.exists():
    SEED.unlink()

con = sqlite3.connect(SEED)
cur = con.cursor()

# PAS DIT AAN NAAR JOUW TABBELLEN (minimaal die je in de demo toont)
cur.executescript("""
CREATE TABLE IF NOT EXISTS permits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  omschrijving TEXT NOT NULL,
  datum TEXT,
  status TEXT DEFAULT 'Aangevraagd',
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS risk_classes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  naam TEXT UNIQUE NOT NULL,
  toelichting TEXT
);
""")

cur.executemany(
  "INSERT INTO permits (omschrijving, datum, status) VALUES (?,?,?)",
  [
    ("Werkzaamheden machine 12", "2025-09-01", "Aangevraagd"),
    ("Inspectie ketelhuis",      "2025-09-03", "Goedgekeurd"),
    ("Vloercoating hal B",       "2025-09-10", "In uitvoering"),
  ]
)
cur.executemany(
  "INSERT INTO risk_classes (naam, toelichting) VALUES (?,?)",
  [
    ("Laag", "Beperkte kans/impact"),
    ("Midden", "Kans of impact merkbaar"),
    ("Hoog", "Verhoogd risico; aanvullende maatregelen vereist"),
  ]
)

con.commit()
con.close()
print(f"Seed DB gemaakt: {SEED}")
