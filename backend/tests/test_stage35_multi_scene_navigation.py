from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.algorithms.route_planning import RouteNotFoundError
from app.core.scenes import DEFAULT_SCENE_KEY, SUMMER_PALACE_SCENE_KEY
from app.db.init_db import create_all
from app.models import Building, Facility, FacilityCategory, MapEdge, MapNode
from app.seed.seed_all import seed_demo_data
from app.services.map_data_service import get_map_payload_from_db, get_map_stats_from_db
from app.services.route_service import plan_route_from_db
from app.services.search_service import search_places_from_db


def test_scene_key_filters_map_search_and_routes() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        _add_tiny_summer_palace_scene(session)

        bupt_stats = get_map_stats_from_db(session, include_demo=True)
        summer_payload = get_map_payload_from_db(
            session,
            include_demo=True,
            scene_key=SUMMER_PALACE_SCENE_KEY,
        )
        scenic_search = search_places_from_db(
            session,
            keyword="东宫门",
            category=None,
            limit=10,
            scope="scenic",
            scene_key=SUMMER_PALACE_SCENE_KEY,
        )
        campus_search = search_places_from_db(
            session,
            keyword="东宫门",
            category=None,
            limit=10,
            scope="campus",
            scene_key=DEFAULT_SCENE_KEY,
        )
        start = next(item for item in scenic_search["items"] if item["source"] == "facility")
        end = search_places_from_db(
            session,
            keyword="仁寿殿",
            category=None,
            limit=10,
            scope="scenic",
            scene_key=SUMMER_PALACE_SCENE_KEY,
        )["items"][0]
        route = plan_route_from_db(
            session,
            {
                "scene_key": SUMMER_PALACE_SCENE_KEY,
                "start_place_id": start["id"],
                "end_place_id": end["id"],
                "route_source": "local_graph",
            },
        )

    assert bupt_stats["roads"] == 641
    assert summer_payload["scene_key"] == SUMMER_PALACE_SCENE_KEY
    assert len(summer_payload["roads"]) == 1
    assert len(summer_payload["buildings"]) == 1
    assert len(summer_payload["facilities"]) == 1
    assert scenic_search["total"] >= 1
    assert campus_search["total"] == 0
    assert route["scene_key"] == SUMMER_PALACE_SCENE_KEY
    assert route["algorithm_trace"]["scene_key"] == SUMMER_PALACE_SCENE_KEY
    assert route["distance"] > 0


def test_route_place_ids_cannot_cross_scenes() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        _add_tiny_summer_palace_scene(session)
        summer_facility = session.scalar(select(Facility).where(Facility.scene_key == SUMMER_PALACE_SCENE_KEY))
        assert summer_facility is not None
        try:
            plan_route_from_db(
                session,
                {
                    "scene_key": DEFAULT_SCENE_KEY,
                    "start_place_id": f"facility-{summer_facility.id}",
                    "end_lng": 116.28333,
                    "end_lat": 40.15608,
                    "route_source": "local_graph",
                },
            )
        except RouteNotFoundError as exc:
            error = str(exc)
        else:
            error = ""

    assert "belongs to scene summer_palace" in error


def _add_tiny_summer_palace_scene(session: Session) -> None:
    category = session.scalar(select(FacilityCategory).where(FacilityCategory.code == "gate"))
    assert category is not None
    node_a = MapNode(
        scene_key=SUMMER_PALACE_SCENE_KEY,
        external_id="test-summer-palace-node-a",
        name="东宫门",
        lng=116.2752,
        lat=39.9995,
    )
    node_b = MapNode(
        scene_key=SUMMER_PALACE_SCENE_KEY,
        external_id="test-summer-palace-node-b",
        name="仁寿殿",
        lng=116.2761,
        lat=39.9998,
    )
    session.add_all([node_a, node_b])
    session.flush()
    session.add(
        MapEdge(
            scene_key=SUMMER_PALACE_SCENE_KEY,
            from_node_id=node_a.id,
            to_node_id=node_b.id,
            distance=90,
            walk_time=75,
            geometry=[[node_a.lng, node_a.lat], [node_b.lng, node_b.lat]],
        )
    )
    session.add(
        Building(
            scene_key=SUMMER_PALACE_SCENE_KEY,
            name="仁寿殿",
            category="palace",
            polygon=[
                [116.2760, 39.9997],
                [116.2762, 39.9997],
                [116.2762, 39.9999],
                [116.2760, 39.9999],
            ],
            description="Stage 35 test-only scenic building fixture.",
        )
    )
    session.add(
        Facility(
            scene_key=SUMMER_PALACE_SCENE_KEY,
            name="东宫门",
            category_id=category.id,
            nearest_node_id=node_a.id,
            lng=node_a.lng,
            lat=node_a.lat,
            description="Stage 35 test-only scenic facility fixture.",
        )
    )
    session.commit()
