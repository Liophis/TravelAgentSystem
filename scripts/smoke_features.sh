#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}

PYTHONPATH=backend ${PYTHON_CMD} - <<'PY'
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.v1.admin import admin_stats
from app.db.session import create_app_engine
from app.services.aigc_service import generate_diary_draft, generate_storyboard
from app.services.destination_service import list_destinations_from_db
from app.services.diary_service import list_diaries_from_db
from app.services.facility_service import get_nearby_facilities_from_db
from app.services.food_service import nearby_foods_from_db, recommend_foods_from_db
from app.services.indoor_service import plan_indoor_route_from_db
from app.services.map_data_service import get_map_stats_from_db
from app.services.recommendation_service import recommend_destinations_from_db
from app.services.route_service import plan_multi_point_route_from_db, plan_route_from_db
from app.services.search_service import search_places_from_db
from app.services.user_service import update_user_interests_from_db


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

    profile = update_user_interests_from_db(session, 1, ["sports", "study"])
    require("updated user interests", len(profile["interests"]) if profile else 0, 2)
    interest_recommendations = recommend_destinations_from_db(
        session=session,
        user_id=1,
        strategy="interest",
        limit=3,
        current_lng=116.28333,
        current_lat=40.15608,
    )
    require("interest recommendations", len(interest_recommendations["items"]))
    print(
        "[smoke] user interests: "
        f"{interest_recommendations['algorithm_trace']['interest_tags']}"
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

    multi_route = plan_multi_point_route_from_db(
        session,
        {
            "start_lng": 116.28333,
            "start_lat": 40.15608,
            "points": [
                {"name": "教学楼", "lng": 116.2842, "lat": 40.1567},
                {"name": "图书馆", "lng": 116.2862, "lat": 40.1582},
            ],
            "return_to_start": False,
            "strategy": "shortest_distance",
            "mode": "walk",
        },
    )
    require("multi-point route segments", len(multi_route["segments"]), 2)
    print(
        "[smoke] multi-point route: "
        f"distance={multi_route['distance']}m segments={len(multi_route['segments'])}"
    )

    indoor_route = plan_indoor_route_from_db(
        session,
        {
            "building_name": "综合教学楼",
            "start_name": "一层大门",
            "end_name": "305 教室",
        },
    )
    require("indoor route steps", len(indoor_route["steps"]), 2)
    print(
        "[smoke] indoor route: "
        f"distance={indoor_route['distance']}m floors={indoor_route['end']['floor']}"
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

    foods = recommend_foods_from_db(
        session=session,
        cuisine=None,
        user_id=1,
        current_lng=116.28333,
        current_lat=40.15608,
        limit=3,
    )
    require("food recommendations", len(foods["items"]))
    print(f"[smoke] foods: total={foods['total']} returned={len(foods['items'])}")

    nearby_foods = nearby_foods_from_db(
        session=session,
        current_lng=116.28333,
        current_lat=40.15608,
        cuisine=None,
        radius=5000,
        limit=3,
    )
    require("nearby foods", len(nearby_foods["items"]))
    print(f"[smoke] nearby foods: total={nearby_foods['total']} returned={len(nearby_foods['items'])}")

    stats_payload = admin_stats(session)
    require("admin food count", stats_payload["tables"]["foods"])
    print(f"[smoke] admin: tables={stats_payload['tables']}")

draft = generate_diary_draft({"topic": "沙河校区路线", "keywords": ["食堂", "图书馆"], "tone": "自然"})
storyboard = generate_storyboard({"text": draft["draft"], "scene_count": 3})
require("aigc scenes", len(storyboard["scenes"]), 3)
print(f"[smoke] aigc: title={draft['title']} scenes={len(storyboard['scenes'])}")

print(f"[smoke] OK using API_DATABASE_URL={settings.api_database_url}")
PY
