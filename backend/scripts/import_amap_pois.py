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
from app.services.amap_import_service import fetch_amap_pois, import_amap_poi_items_to_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import real campus POIs from AMap Place Around Web Service.")
    parser.add_argument("--database-url", default=settings.dev_database_url)
    parser.add_argument("--center-lng", type=float, default=settings.osm_fallback_lng)
    parser.add_argument("--center-lat", type=float, default=settings.osm_fallback_lat)
    parser.add_argument("--radius", type=int, default=settings.osm_fallback_dist)
    parser.add_argument("--scene-key", default="bupt_shahe")
    parser.add_argument("--keyword", action="append", dest="keywords")
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--request-interval", type=float, default=0.3)
    parser.add_argument("--reset-facilities", action="store_true")
    parser.add_argument("--reset-dataset", action="store_true")
    parser.add_argument(
        "--dataset",
        choices=["nearby_facilities", "campus_navigation", "scenic_navigation"],
        default="nearby_facilities",
        help="Logical POI dataset written into facility descriptions.",
    )
    parser.add_argument(
        "--campus-only",
        action="store_true",
        help="Keep only POIs inside the BUPT Shahe campus boundary after GCJ-02 to WGS84 conversion.",
    )
    parser.add_argument("--save-raw", type=Path, default=None, help="Write raw AMap POI response items and fetch trace to JSON.")
    parser.add_argument("--load-raw", type=Path, default=None, help="Read raw AMap POI JSON saved by --save-raw instead of fetching.")
    parser.add_argument("--download-only", action="store_true", help="Fetch and optionally save raw POIs without writing the database.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.load_raw:
        raw_payload = json.loads(args.load_raw.read_text(encoding="utf-8"))
        pois = list(raw_payload.get("pois") or [])
        fetch_trace = raw_payload.get("fetch") or {"source_file": str(args.load_raw)}
    else:
        pois, fetch_trace = fetch_amap_pois(
            api_key=settings.amap_web_api_key or "",
            center_lng=args.center_lng,
            center_lat=args.center_lat,
            radius=args.radius,
            keywords=args.keywords,
            max_pages=args.max_pages,
            request_interval=args.request_interval,
        )
    if args.save_raw:
        args.save_raw.parent.mkdir(parents=True, exist_ok=True)
        args.save_raw.write_text(
            json.dumps(
                {
                    "source": "amap-place-around",
                    "scene_key": args.scene_key,
                    "dataset": args.dataset,
                    "center": [args.center_lng, args.center_lat],
                    "radius": args.radius,
                    "campus_only": args.campus_only,
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
            "source": "amap-place-around",
            "scene_key": args.scene_key,
            "dataset": args.dataset,
            "center": [args.center_lng, args.center_lat],
            "radius": args.radius,
            "campus_only": args.campus_only,
            "raw_pois": len(pois),
            "download_only": True,
        }
    else:
        engine = create_app_engine(args.database_url)
        create_all(engine)
        with Session(engine) as session:
            summary = import_amap_poi_items_to_db(
                session=session,
                pois=pois,
                center_lng=args.center_lng,
                center_lat=args.center_lat,
                radius=args.radius,
                reset_facilities=args.reset_facilities,
                reset_dataset=args.reset_dataset,
                dataset=args.dataset,
                campus_only=args.campus_only,
                scene_key=args.scene_key,
                fetch_trace=fetch_trace,
            )

    print("[amap-poi-import] database:", args.database_url)
    for key, value in summary.items():
        if key != "algorithm_trace":
            print(f"[amap-poi-import] {key}: {value}")


if __name__ == "__main__":
    main()
