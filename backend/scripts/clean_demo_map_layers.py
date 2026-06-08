import argparse
import sys
from pathlib import Path

from sqlalchemy.orm import Session

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.init_db import create_all
from app.db.session import create_app_engine
from app.services.map_data_service import cleanup_demo_map_layers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remove old offline demo map layers from the dev database.")
    parser.add_argument("--database-url", default=settings.dev_database_url)
    parser.add_argument("--keep-demo-facilities", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engine = create_app_engine(args.database_url)
    create_all(engine)
    with Session(engine) as session:
        summary = cleanup_demo_map_layers(
            session,
            remove_buildings=True,
            remove_facilities=not args.keep_demo_facilities,
        )

    print("[map-cleanup] database:", args.database_url)
    for key, value in summary.items():
        if key != "algorithm_trace":
            print(f"[map-cleanup] {key}: {value}")


if __name__ == "__main__":
    main()
