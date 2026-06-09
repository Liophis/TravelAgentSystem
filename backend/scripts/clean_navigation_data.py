import argparse
import sys
from pathlib import Path

from sqlalchemy.orm import Session

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.session import create_app_engine
from app.services.navigation_data_cleaning_service import clean_all_navigation_scenes, clean_navigation_scene_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean BUPT/Summer Palace internal navigation data.")
    parser.add_argument("--database-url", default=settings.dev_database_url)
    parser.add_argument("--scene-key", default="all", help="all, bupt_shahe, or summer_palace")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engine = create_app_engine(args.database_url)
    with Session(engine) as session:
        if args.scene_key == "all":
            summary = clean_all_navigation_scenes(session)
        else:
            summary = clean_navigation_scene_data(session, args.scene_key)
    print("[navigation-clean] database:", args.database_url)
    _print_summary(summary)


def _print_summary(summary: dict) -> None:
    for key, value in summary.items():
        if key == "algorithm_trace":
            continue
        if key == "scenes":
            for item in value:
                print(
                    "[navigation-clean] scene={scene_key} removed_blocked={removed_blocked_facilities} "
                    "normalized={normalized_facilities} invalid_edges={removed_invalid_edges} "
                    "orphan_nodes={removed_orphan_import_nodes}".format(**item)
                )
            continue
        print(f"[navigation-clean] {key}: {value}")


if __name__ == "__main__":
    main()
