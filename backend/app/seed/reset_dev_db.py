import os
import sys
from pathlib import Path

from sqlalchemy.orm import Session

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.config import settings
from app.db.init_db import create_all, drop_all
from app.db.session import create_app_engine
from app.seed.seed_all import seed_demo_data


def resolve_reset_database_url() -> str:
    return os.getenv("SEED_DATABASE_URL") or os.getenv("DEV_DATABASE_URL") or settings.dev_database_url


def main() -> None:
    database_url = resolve_reset_database_url()
    engine = create_app_engine(database_url)
    drop_all(engine)
    create_all(engine)
    with Session(engine) as session:
        counts = seed_demo_data(session)
    print("[db] reset database:", database_url)
    for name, count in counts.items():
        print(f"[db] {name}: {count}")


if __name__ == "__main__":
    main()
