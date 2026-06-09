#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}

PYTHONPATH=backend ${PYTHON_CMD} - <<'PY'
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.v1.admin import admin_stats
from app.db.session import create_app_engine
from app.services.aigc_agent_service import run_aigc_agent
from app.services.aigc_service import generate_diary_draft, generate_storyboard
from app.services.destination_service import list_destinations_from_db
from app.services.diary_service import list_diaries_from_db
from app.services.facility_service import get_nearby_facilities_from_db
from app.services.food_service import nearby_foods_from_db, recommend_foods_from_db
from app.services.food_service import search_foods_from_db
from app.services.indoor_service import plan_indoor_route_from_db
from app.services.map_data_service import get_map_stats_from_db
from app.services.recommendation_service import recommend_destinations_from_db
from app.services.route_service import plan_multi_point_route_from_db, plan_route_from_db
from app.services.search_service import search_places_from_db
from app.services.user_service import update_user_interests_from_db
from app.models import UserInterest
from sqlalchemy import select


def require(label: str, value: int, minimum: int = 1) -> None:
    if value < minimum:
        raise SystemExit(f"[smoke] {label} expected >= {minimum}, got {value}")


engine = create_app_engine(settings.api_database_url)

with Session(engine) as session:
    visible_stats = get_map_stats_from_db(session)
    raw_stats = get_map_stats_from_db(session, include_demo=True)
    require("map nodes", raw_stats["nodes"])
    require("route graph roads", raw_stats["roads"])
    print(f"[smoke] map visible: {visible_stats}")
    print(f"[smoke] map raw: {raw_stats}")

    destinations = list_destinations_from_db(session, None, None, "popularity", 3, 0)
    require("destinations", destinations["total"])
    print(f"[smoke] destinations: total={destinations['total']} returned={len(destinations['items'])}")

    search = search_places_from_db(session, "图书馆", None, 3)
    require("place search results", search["total"])
    print(f"[smoke] search: total={search['total']} returned={len(search['items'])}")
    origin_search = search_places_from_db(session, "图书馆", None, 1, scope="campus")
    require("nearby origin search", origin_search["total"])
    nearby_origin = origin_search["items"][0]

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

    original_interests = [
        interest.tag
        for interest in session.scalars(select(UserInterest).where(UserInterest.user_id == 1)).all()
    ]
    try:
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
    finally:
        update_user_interests_from_db(session, 1, original_interests)

    route = plan_route_from_db(
        session,
        {
            "start_lng": 116.28333,
            "start_lat": 40.15608,
            "end_lng": 116.2862,
            "end_lat": 40.1582,
            "strategy": "shortest_distance",
            "mode": "walk",
            "route_source": "local_graph",
        },
    )
    require("route path points", len(route["path"]), 2)
    print(
        "[smoke] route: "
        f"distance={route['distance']}m duration={route['duration']}s steps={len(route['steps'])}"
    )

    summer_stats = get_map_stats_from_db(session, scene_key="summer_palace")
    require("summer palace roads", summer_stats["roads"], 200)
    require("summer palace buildings", summer_stats["buildings"], 20)
    require("summer palace facilities", summer_stats["facilities"], 50)
    print(f"[smoke] summer palace map: {summer_stats}")
    summer_start_search = search_places_from_db(
        session,
        "仁寿殿",
        None,
        5,
        scope="scenic",
        scene_key="summer_palace",
    )
    summer_end_search = search_places_from_db(
        session,
        "佛香阁",
        None,
        5,
        scope="scenic",
        scene_key="summer_palace",
    )
    require("summer palace start search", summer_start_search["total"])
    require("summer palace end search", summer_end_search["total"])
    summer_route = plan_route_from_db(
        session,
        {
            "scene_key": "summer_palace",
            "start_place_id": summer_start_search["items"][0]["id"],
            "end_place_id": summer_end_search["items"][0]["id"],
            "strategy": "shortest_distance",
            "mode": "walk",
            "route_source": "local_graph",
        },
    )
    require("summer palace route path points", len(summer_route["path"]), 2)
    print(
        "[smoke] summer palace route: "
        f"distance={summer_route['distance']}m steps={len(summer_route['steps'])}"
    )
    summer_multi_route = plan_multi_point_route_from_db(
        session,
        {
            "scene_key": "summer_palace",
            "start_place_id": summer_start_search["items"][0]["id"],
            "points": [
                {"place_id": summer_end_search["items"][0]["id"]},
            ],
            "return_to_start": False,
            "strategy": "shortest_distance",
            "mode": "walk",
            "route_source": "local_graph",
        },
    )
    require("summer palace multi-point segments", len(summer_multi_route["segments"]))
    print(
        "[smoke] summer palace multi-point: "
        f"distance={summer_multi_route['distance']}m segments={len(summer_multi_route['segments'])}"
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
            "route_source": "local_graph",
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
    science_indoor_route = plan_indoor_route_from_db(
        session,
        {
            "building_name": "中国科学技术馆主展厅",
            "start_name": "西门入口",
            "end_name": "4F 挑战与未来 C 厅",
            "route_mode": "accessible",
        },
    )
    require("science museum indoor route steps", len(science_indoor_route["steps"]), 4)
    if science_indoor_route["end"]["floor"] != 4:
        raise SystemExit("[smoke] science museum indoor route did not reach 4F")
    if science_indoor_route["algorithm_trace"]["vertical_traffic"] != "elevator":
        raise SystemExit("[smoke] science museum accessible route should use elevator vertical traffic")
    if any(step["access_type"] in {"stairs", "escalator"} for step in science_indoor_route["steps"]):
        raise SystemExit("[smoke] science museum accessible route used stairs/escalator")
    print(
        "[smoke] science museum indoor route: "
        f"distance={science_indoor_route['distance']}m mode={science_indoor_route['route_mode']} "
        f"end={science_indoor_route['end']['floor_label']}"
    )

    facilities = get_nearby_facilities_from_db(
        session=session,
        origin_place_id=nearby_origin["id"],
        current_lng=0,
        current_lat=0,
        category="超市",
        radius=5000,
        limit=3,
    )
    require("nearby facilities", len(facilities["items"]))
    print(
        "[smoke] facilities: "
        f"origin={facilities['origin']['name']} category={facilities['category']} "
        f"total={facilities['total']} returned={len(facilities['items'])}"
    )

    summer_facilities = get_nearby_facilities_from_db(
        session=session,
        origin_place_id=summer_start_search["items"][0]["id"],
        current_lng=0,
        current_lat=0,
        category=None,
        radius=5000,
        limit=3,
        scene_key="summer_palace",
    )
    require("summer palace nearby facilities", len(summer_facilities["items"]))
    print(
        "[smoke] summer palace facilities: "
        f"origin={summer_facilities['origin']['name']} returned={len(summer_facilities['items'])}"
    )

    diaries = list_diaries_from_db(session, destination_id=None, q=None, sort="hot", limit=2, offset=0)
    require("diaries", diaries["total"])
    print(f"[smoke] diaries: total={diaries['total']} returned={len(diaries['items'])}")

    foods = recommend_foods_from_db(
        session=session,
        cuisine=None,
        destination_id=1,
        user_id=1,
        current_lng=116.28333,
        current_lat=40.15608,
        sort="composite",
        limit=3,
    )
    require("food recommendations", len(foods["items"]))
    require("food recommendation route preview", len(foods["items"][0].get("routePath", [])), 2)
    print(
        "[smoke] foods: "
        f"sort={foods['sort']} total={foods['total']} returned={len(foods['items'])}"
    )

    hot_foods = recommend_foods_from_db(
        session=session,
        cuisine=None,
        destination_id=1,
        user_id=1,
        current_lng=116.28333,
        current_lat=40.15608,
        sort="hot",
        limit=3,
    )
    require("hot food recommendations", len(hot_foods["items"]))
    if hot_foods["items"][0]["heat"] < hot_foods["items"][-1]["heat"]:
        raise SystemExit("[smoke] food hot recommendation order failed")

    distance_foods = recommend_foods_from_db(
        session=session,
        cuisine=None,
        destination_id=1,
        user_id=1,
        current_lng=116.28333,
        current_lat=40.15608,
        sort="distance",
        limit=3,
    )
    require("distance food recommendations", len(distance_foods["items"]))
    if distance_foods["items"][0]["distance"] > distance_foods["items"][-1]["distance"]:
        raise SystemExit("[smoke] food distance recommendation order failed")
    print(
        "[smoke] food recommendation sorts: "
        f"hot={hot_foods['sort']} distance={distance_foods['sort']}"
    )

    food_search = search_foods_from_db(
        session=session,
        q="饭",
        cuisine=None,
        destination_id=1,
        sort="distance",
        current_lng=116.28333,
        current_lat=40.15608,
        limit=3,
    )
    require("food distance search", len(food_search["items"]))
    print(
        "[smoke] food search: "
        f"sort={food_search['sort']} returned={len(food_search['items'])}"
    )

    restaurant_search = search_foods_from_db(
        session=session,
        q="南区食堂",
        cuisine=None,
        destination_id=1,
        sort="match",
        current_lng=116.28333,
        current_lat=40.15608,
        limit=3,
    )
    require("food restaurant/window search", len(restaurant_search["items"]))
    print(
        "[smoke] food restaurant search: "
        f"keyword={restaurant_search['keyword']} returned={len(restaurant_search['items'])}"
    )

    nearby_foods = nearby_foods_from_db(
        session=session,
        current_lng=116.28333,
        current_lat=40.15608,
        cuisine=None,
        destination_id=1,
        radius=5000,
        limit=3,
    )
    require("nearby foods", len(nearby_foods["items"]))
    print(f"[smoke] nearby foods: total={nearby_foods['total']} returned={len(nearby_foods['items'])}")

    stats_payload = admin_stats(session)
    require("admin food count", stats_payload["tables"]["foods"])
    print(f"[smoke] admin: tables={stats_payload['tables']}")

draft = generate_diary_draft({"topic": "颐和园半日游记", "keywords": ["昆明湖", "佛香阁"], "tone": "自然"})
storyboard = generate_storyboard({"text": draft["draft"], "scene_count": 3})
require("aigc scenes", len(storyboard["scenes"]), 3)
agent = run_aigc_agent(
    {
        "task": "diary_animation",
        "text": draft["draft"],
        "destination_name": "颐和园",
        "media_urls": ["/media/demo/scenic-photo.jpg"],
        "scene_count": 3,
    }
)
require("aigc agent steps", len(agent["agent_trace"]["steps"]), 4)
require("aigc agent scenes", len(agent["result"]["storyboard"]), 3)
print(
    "[smoke] aigc: "
    f"title={draft['title']} legacy_scenes={len(storyboard['scenes'])} "
    f"agent_steps={len(agent['agent_trace']['steps'])}"
)

print(f"[smoke] OK using API_DATABASE_URL={settings.api_database_url}")
PY
