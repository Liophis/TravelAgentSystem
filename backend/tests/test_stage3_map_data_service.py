from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1 import map as map_api
from app.db.init_db import create_all
from app.seed.seed_all import seed_demo_data
from app.services.map_data_service import cleanup_demo_map_layers, get_map_payload_from_db, get_map_stats_from_db


def test_map_stats_are_read_from_seeded_database() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        stats = get_map_stats_from_db(session, include_demo=True)

    assert stats["nodes"] == 180
    assert stats["roads"] == 641
    assert stats["buildings"] == 60
    assert stats["facilities"] == 120
    assert stats["categories"] == 10


def test_map_stats_hide_demo_layers_by_default() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        stats = get_map_stats_from_db(session)
        payload = get_map_payload_from_db(session)

    assert stats["roads"] == 0
    assert stats["buildings"] == 0
    assert stats["facilities"] == 0
    assert stats["hidden_demo_roads"] == 641
    assert stats["hidden_demo_buildings"] == 60
    assert stats["hidden_demo_facilities"] == 120
    assert payload["source"] == "database-real-priority-map-layers"
    assert payload["buildings"] == []
    assert payload["facilities"] == []


def test_map_payload_matches_amap_frontend_contract() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        payload = get_map_payload_from_db(session, include_demo=True)

    assert payload["center"] == [116.28333, 40.15608]
    assert payload["source"] == "database-all-map-layers"
    assert len(payload["roads"]) == 641
    assert len(payload["buildings"]) == 60
    assert len(payload["facilities"]) == 120
    assert len(payload["facility_categories"]) == 10
    assert payload["geojson"]["type"] == "FeatureCollection"
    assert len(payload["geojson"]["features"]) >= 641 + 60 + 120

    first_road = payload["roads"][0]
    assert isinstance(first_road["path"][0], list)
    assert len(first_road["path"][0]) == 2
    assert 0 < first_road["congestion"] <= 1
    assert "walk" in first_road["allowed_modes"]


def test_map_api_handlers_read_seeded_database() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        stats = map_api.get_map_stats(include_demo=True, db=session)
        payload = map_api.get_map_geojson(include_demo=True, db=session)
        nodes = map_api.get_map_nodes(session)
        facilities = map_api.get_map_facilities(include_demo=True, db=session)

    assert stats["nodes"] == 180
    assert stats["roads"] == 641
    assert stats["buildings"] == 60
    assert stats["facilities"] == 120
    assert stats["categories"] == 10

    assert payload["source"] == "database-all-map-layers"
    assert payload["statistics"]["roads"] == 641
    assert payload["geojson"]["type"] == "FeatureCollection"
    assert len(payload["roads"]) == 641
    assert len(nodes) == 180
    assert len(facilities) == 120


def test_cleanup_demo_map_layers_removes_old_squares() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        summary = cleanup_demo_map_layers(session)
        payload = get_map_payload_from_db(session, include_demo=True)

    assert summary["removed_buildings"] == 60
    assert summary["removed_facilities"] == 120
    assert summary["remaining_demo_roads"] == 641
    assert len(payload["buildings"]) == 0
    assert len(payload["facilities"]) == 0
    assert len(payload["roads"]) == 641
