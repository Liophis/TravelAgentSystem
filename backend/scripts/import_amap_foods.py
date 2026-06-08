import argparse
import json
import sys
from pathlib import Path

from sqlalchemy.orm import Session

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.init_db import create_all
from app.db.session import create_app_engine
from app.services.amap_food_import_service import (
    AMAP_FOOD_KEYWORDS,
    fetch_amap_food_pois,
    import_amap_food_items_to_db,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import real destination-nearby restaurant POIs from AMap.")
    parser.add_argument("--database-url", default=settings.dev_database_url)
    parser.add_argument("--destination-id", type=int, required=True)
    parser.add_argument("--center-lng", type=float, default=None)
    parser.add_argument("--center-lat", type=float, default=None)
    parser.add_argument("--radius", type=int, default=3000)
    parser.add_argument("--keyword", action="append", dest="keywords")
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--request-interval", type=float, default=0.3)
    parser.add_argument("--reset-destination", action="store_true")
    parser.add_argument("--save-raw", type=Path, default=None)
    parser.add_argument("--load-raw", type=Path, default=None)
    parser.add_argument("--download-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    keywords = args.keywords or AMAP_FOOD_KEYWORDS

    if args.load_raw:
        raw_payload = json.loads(args.load_raw.read_text(encoding="utf-8"))
        pois = list(raw_payload.get("pois") or [])
        fetch_trace = raw_payload.get("fetch") or {"source_file": str(args.load_raw)}
        center = raw_payload.get("center") or []
        center_lng = args.center_lng if args.center_lng is not None else (center[0] if len(center) >= 2 else None)
        center_lat = args.center_lat if args.center_lat is not None else (center[1] if len(center) >= 2 else None)
    else:
        if args.center_lng is None or args.center_lat is None:
            center_lng, center_lat = _load_destination_center(args.database_url, args.destination_id)
        else:
            center_lng, center_lat = args.center_lng, args.center_lat
        pois, fetch_trace = fetch_amap_food_pois(
            api_key=settings.amap_web_api_key or "",
            center_lng=center_lng,
            center_lat=center_lat,
            radius=args.radius,
            keywords=keywords,
            max_pages=args.max_pages,
            request_interval=args.request_interval,
        )

    if args.save_raw:
        args.save_raw.parent.mkdir(parents=True, exist_ok=True)
        args.save_raw.write_text(
            json.dumps(
                {
                    "source": "amap-place-around-food",
                    "destination_id": args.destination_id,
                    "center": [center_lng, center_lat],
                    "radius": args.radius,
                    "keywords": keywords,
                    "fetch": fetch_trace,
                    "pois": pois,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    if args.download_only:
        summary = {
            "source": "amap-place-around-food",
            "destination_id": args.destination_id,
            "center": [center_lng, center_lat],
            "radius": args.radius,
            "raw_pois": len(pois),
            "download_only": True,
        }
    else:
        engine = create_app_engine(args.database_url)
        create_all(engine)
        with Session(engine) as session:
            summary = import_amap_food_items_to_db(
                session=session,
                pois=pois,
                destination_id=args.destination_id,
                center_lng=center_lng,
                center_lat=center_lat,
                radius=args.radius,
                reset_destination=args.reset_destination,
                fetch_trace=fetch_trace,
            )

    print("[amap-food-import] database:", args.database_url)
    for key, value in summary.items():
        if key != "algorithm_trace":
            print(f"[amap-food-import] {key}: {value}")


def _load_destination_center(database_url: str, destination_id: int) -> tuple[float, float]:
    from app.models import Destination

    engine = create_app_engine(database_url)
    create_all(engine)
    with Session(engine) as session:
        destination = session.get(Destination, destination_id)
        if destination is None:
            raise SystemExit(f"Destination {destination_id} was not found.")
        return destination.lng, destination.lat


if __name__ == "__main__":
    main()
