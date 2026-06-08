import argparse
import sys
from pathlib import Path

from sqlalchemy.orm import Session

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.init_db import create_all
from app.db.session import create_app_engine
from app.services.reference_campus_import_service import (
    DEFAULT_SOURCE_DIR,
    import_reference_campus_to_db,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import WGS84 BUPT Shahe reference campus topology.")
    parser.add_argument("--database-url", default=settings.dev_database_url)
    parser.add_argument("--source", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--replace-campus-layers", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engine = create_app_engine(args.database_url)
    create_all(engine)
    with Session(engine) as session:
        summary = import_reference_campus_to_db(
            session=session,
            source_dir=args.source,
            replace_campus_layers=args.replace_campus_layers,
        )
    print("[reference-campus-import] database:", args.database_url)
    for key, value in summary.items():
        if key != "algorithm_trace":
            print(f"[reference-campus-import] {key}: {value}")


if __name__ == "__main__":
    main()
