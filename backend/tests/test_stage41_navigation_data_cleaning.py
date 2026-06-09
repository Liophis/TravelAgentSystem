from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.scenes import SUMMER_PALACE_SCENE_KEY
from app.db.init_db import create_all
from app.models import Building, Facility, FacilityCategory, MapEdge, MapNode
from app.seed.seed_all import seed_demo_data
from app.services.navigation_data_cleaning_service import clean_navigation_scene_data
from app.services.reference_campus_import_service import import_reference_campus_to_db
from app.services.route_service import plan_route_from_db
from app.services.search_service import search_places_from_db


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_SOURCE = PROJECT_ROOT / "data" / "reference" / "bupt-shahe"


def test_bupt_reference_cleaning_removes_blocked_fake_pois() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        import_reference_campus_to_db(session, source_dir=REFERENCE_SOURCE, replace_campus_layers=True)
        clean_navigation_scene_data(session, "bupt_shahe")
        places = search_places_from_db(session, "", None, 100, scope="campus", scene_key="bupt_shahe")["items"]
        route = plan_route_from_db(
            session,
            {
                "scene_key": "bupt_shahe",
                "start_place_id": next(item["id"] for item in places if item["name"] == "西门"),
                "end_place_id": next(item["id"] for item in places if item["name"] == "图书馆"),
                "route_source": "local_graph",
            },
        )

    names = {item["name"] for item in places}
    assert "防御塔景区" not in names
    assert "观景区" not in names
    assert "OSM building" not in names
    assert route["distance"] > 0


def test_scenic_cleaning_hides_generic_endpoint_names_and_keeps_routes() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        _add_dirty_scenic_scene(session)
        summary = clean_navigation_scene_data(session, SUMMER_PALACE_SCENE_KEY)
        places = search_places_from_db(
            session,
            "",
            None,
            20,
            scope="scenic",
            scene_key=SUMMER_PALACE_SCENE_KEY,
        )["items"]
        route = plan_route_from_db(
            session,
            {
                "scene_key": SUMMER_PALACE_SCENE_KEY,
                "start_place_id": next(item["id"] for item in places if item["name"] == "东宫门"),
                "end_place_id": next(item["id"] for item in places if item["name"] == "仁寿殿"),
                "route_source": "local_graph",
            },
        )
        normalized_facility = session.scalar(
            select(Facility).where(Facility.scene_key == SUMMER_PALACE_SCENE_KEY, Facility.name == "洗手间")
        )
        bench_facility = session.scalar(
            select(Facility).where(Facility.scene_key == SUMMER_PALACE_SCENE_KEY, Facility.name == "bench")
        )

    names = {item["name"] for item in places}
    assert "OSM building" not in names
    assert "poi" not in names
    assert "bench" not in names
    assert summary["normalized_facilities"] == 2
    assert summary["removed_meaningless_facilities"] == 1
    assert summary["removed_invalid_edges"] == 1
    assert normalized_facility is not None
    assert bench_facility is None
    assert route["distance"] > 0


def _add_dirty_scenic_scene(session: Session) -> None:
    category = session.scalar(select(FacilityCategory).where(FacilityCategory.code == "toilets"))
    if category is None:
        category = FacilityCategory(code="toilets", name="洗手间")
        session.add(category)
        session.flush()
    bench_category = session.scalar(select(FacilityCategory).where(FacilityCategory.code == "bench"))
    if bench_category is None:
        bench_category = FacilityCategory(code="bench", name="座椅")
        session.add(bench_category)
        session.flush()
    node_a = MapNode(
        scene_key=SUMMER_PALACE_SCENE_KEY,
        external_id="test-clean-summer-a",
        name="东宫门",
        lng=116.2752,
        lat=39.9995,
    )
    node_b = MapNode(
        scene_key=SUMMER_PALACE_SCENE_KEY,
        external_id="test-clean-summer-b",
        name="仁寿殿",
        lng=116.2761,
        lat=39.9998,
    )
    session.add_all([node_a, node_b])
    session.flush()
    session.add_all(
        [
            MapEdge(
                scene_key=SUMMER_PALACE_SCENE_KEY,
                from_node_id=node_a.id,
                to_node_id=node_b.id,
                distance=90,
                walk_time=75,
                geometry=[[node_a.lng, node_a.lat], [node_b.lng, node_b.lat]],
            ),
            MapEdge(
                scene_key=SUMMER_PALACE_SCENE_KEY,
                from_node_id=node_a.id,
                to_node_id=node_a.id,
                distance=0,
                walk_time=0,
                geometry=[],
            ),
        ]
    )
    session.add_all(
        [
            Building(
                scene_key=SUMMER_PALACE_SCENE_KEY,
                name="OSM building",
                category="yes",
                polygon=[
                    [116.2750, 39.9994],
                    [116.2751, 39.9994],
                    [116.2751, 39.9995],
                    [116.2750, 39.9995],
                ],
                description="Imported from OpenStreetMap.",
            ),
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
                description="Imported from OpenStreetMap.",
            ),
            Facility(
                scene_key=SUMMER_PALACE_SCENE_KEY,
                name="toilets",
                category_id=category.id,
                nearest_node_id=node_a.id,
                lng=node_a.lng,
                lat=node_a.lat,
                description="Imported from OpenStreetMap.",
            ),
            Facility(
                scene_key=SUMMER_PALACE_SCENE_KEY,
                name="poi",
                category_id=category.id,
                nearest_node_id=node_a.id,
                lng=node_a.lng,
                lat=node_a.lat,
                description="Imported from OpenStreetMap.",
            ),
            Facility(
                scene_key=SUMMER_PALACE_SCENE_KEY,
                name="bench",
                category_id=bench_category.id,
                nearest_node_id=node_a.id,
                lng=node_a.lng,
                lat=node_a.lat,
                description="Imported from OpenStreetMap.",
            ),
        ]
    )
    session.commit()
