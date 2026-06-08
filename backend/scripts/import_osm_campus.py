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
from app.services.osm_import_service import (
    build_osmnx_payload,
    import_fixture_osm_payload,
    import_osm_feature_layers_to_db,
    import_osm_payload_to_db,
    import_osm_road_graph_to_db,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import campus map data from OSMnx or fixture payload.")
    parser.add_argument("--source", choices=["fixture", "osmnx"], default="fixture")
    parser.add_argument("--database-url", default=settings.dev_database_url)
    parser.add_argument("--place-name", default=settings.osm_default_place)
    parser.add_argument("--center-lng", type=float, default=settings.osm_fallback_lng)
    parser.add_argument("--center-lat", type=float, default=settings.osm_fallback_lat)
    parser.add_argument("--dist", type=int, default=settings.osm_fallback_dist)
    parser.add_argument("--scene-key", default="bupt_shahe")
    parser.add_argument("--keep-existing", action="store_true")
    parser.add_argument(
        "--features-only",
        action="store_true",
        help="Import only OSM buildings/amenities, remove demo polygons, and keep existing AMap POIs/route graph.",
    )
    parser.add_argument(
        "--graph-only",
        action="store_true",
        help="Import only OSM walking road graph, keep existing seed fallback graph and POI/building layers.",
    )
    parser.add_argument("--save-payload", type=Path, default=None, help="Write fetched OSMnx payload to JSON before import.")
    parser.add_argument("--load-payload", type=Path, default=None, help="Read an OSMnx payload JSON saved by --save-payload instead of fetching.")
    parser.add_argument("--download-only", action="store_true", help="Fetch and optionally save OSMnx payload without writing the database.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.source == "fixture":
        engine = create_app_engine(args.database_url)
        create_all(engine)
        with Session(engine) as session:
            summary = import_fixture_osm_payload(
                session,
                reset_existing=not args.keep_existing,
                scene_key=args.scene_key,
            )
    else:
        if args.load_payload:
            payload = json.loads(args.load_payload.read_text(encoding="utf-8"))
        else:
            payload = build_osmnx_payload(
                place_name=args.place_name,
                center_lng=args.center_lng,
                center_lat=args.center_lat,
                dist=args.dist,
            )
        if args.save_payload:
            args.save_payload.parent.mkdir(parents=True, exist_ok=True)
            args.save_payload.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if args.download_only:
            summary = {
                "source": payload.get("source", "osmnx-overpass"),
                "scene_key": args.scene_key,
                "place_name": payload.get("place_name"),
                "lookup_mode": payload.get("lookup_mode"),
                "nodes": len(payload.get("nodes", [])),
                "edges": len(payload.get("edges", [])),
                "buildings": len(payload.get("buildings", [])),
                "facilities": len(payload.get("facilities", [])),
                "download_only": True,
            }
        else:
            engine = create_app_engine(args.database_url)
            create_all(engine)
            with Session(engine) as session:
                if args.features_only:
                    summary = import_osm_feature_layers_to_db(
                        session,
                        payload,
                        remove_demo_layers=True,
                        replace_osm_layers=not args.keep_existing,
                        import_facilities=True,
                        scene_key=args.scene_key,
                    )
                elif args.graph_only:
                    summary = import_osm_road_graph_to_db(
                        session,
                        payload,
                        replace_osm_roads=not args.keep_existing,
                        rebind_facilities=True,
                        scene_key=args.scene_key,
                    )
                else:
                    summary = import_osm_payload_to_db(
                        session,
                        payload,
                        reset_existing=not args.keep_existing,
                        scene_key=args.scene_key,
                    )

    print("[osm-import] database:", args.database_url)
    for key, value in summary.items():
        if key != "algorithm_trace":
            print(f"[osm-import] {key}: {value}")


if __name__ == "__main__":
    main()
