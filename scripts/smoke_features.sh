#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}

PYTHONPATH=backend ${PYTHON_CMD} - <<'PY'
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import create_app_engine
from app.services.destination_service import list_destinations_from_db
from app.services.diary_service import list_diaries_from_db
from app.services.facility_service import get_nearby_facilities_from_db
from app.services.map_data_service import get_map_stats_from_db
from app.services.recommendation_service import recommend_destinations_from_db
from app.services.route_service import plan_route_from_db
from app.services.search_service import search_places_from_db


def require(label: str, value: int, minimum: int = 1) -> None:
    if value < minimum:
        raise SystemExit(f"[smoke] {label} expected >= {minimum}, got {value}")


engine = create_app_engine(settings.api_database_url)

with Session(engine) as session:
    stats = get_map_stats_from_db(session)
    require("map nodes", stats["nodes"])
    require("map roads", stats["roads"])
    print(f"[smoke] map: {stats}")

    destinations = list_destinations_from_db(session, None, None, "popularity", 3, 0)
    require("destinations", destinations["total"])
    print(f"[smoke] destinations: total={destinations['total']} returned={len(destinations['items'])}")

    search = search_places_from_db(session, "厕所", None, 3)
    require("place search results", search["total"])
    print(f"[smoke] search: total={search['total']} returned={len(search['items'])}")

    recommendations = recommend_destinations_from_db(
        session=session,
        user_id=1,
        strategy="composite",
        limit=3,
        current_lng=116.28333,
        current_lat=40.15608,
    )
    require("recommendations", len(recommendations["items"]))
    print(
        "[smoke] recommendations: "
        f"total={recommendations['total']} returned={len(recommendations['items'])}"
    )

    route = plan_route_from_db(
        session,
        {
            "start_lng": 116.28333,
            "start_lat": 40.15608,
            "end_lng": 116.2862,
            "end_lat": 40.1582,
            "strategy": "shortest_distance",
            "mode": "walk",
        },
    )
    require("route path points", len(route["path"]), 2)
    print(
        "[smoke] route: "
        f"distance={route['distance']}m duration={route['duration']}s steps={len(route['steps'])}"
    )

    facilities = get_nearby_facilities_from_db(
        session=session,
        current_lng=116.28333,
        current_lat=40.15608,
        category=None,
        radius=5000,
        limit=3,
    )
    require("nearby facilities", len(facilities["items"]))
    print(f"[smoke] facilities: total={facilities['total']} returned={len(facilities['items'])}")

    diaries = list_diaries_from_db(session, destination_id=None, q=None, sort="hot", limit=2, offset=0)
    require("diaries", diaries["total"])
    print(f"[smoke] diaries: total={diaries['total']} returned={len(diaries['items'])}")

print(f"[smoke] OK using API_DATABASE_URL={settings.api_database_url}")
PY
