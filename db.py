# db.py
import os
from pathlib import Path
from sqlmodel import create_engine, SQLModel, Session

def get_database_url() -> str:
    # 1) Gebruik DATABASE_URL uit env
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # 2) Standaardpad naar D-schijf
    return "sqlite:///D:/wrsafe-data/wrsafe.db"

DATABASE_URL = get_database_url()

# SQLite connect args
CONNECT_ARGS = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Zorg dat de map voor SQLite bestaat (alleen voor file-URL's)
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

# Eventueel query logging inschakelen via env (DEBUG_SQL=1)
ECHO = os.getenv("DEBUG_SQL", "0") == "1"

engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS, echo=ECHO)

def init_db():
    # Import binnen functie, zodat modellen geregistreerd zijn
    import models  # noqa: F401
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    """Handige helper voor context-managed sessions:
       with get_session() as s: ..."""
    return Session(engine)
