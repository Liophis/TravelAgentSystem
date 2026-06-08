from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1 import map as map_api
from app.db.init_db import create_all
from app.seed.seed_all import seed_demo_data
from app.services.map_data_service import get_map_payload_from_db, get_map_stats_from_db


def test_map_stats_are_read_from_seeded_database() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        stats = get_map_stats_from_db(session)

    assert stats["nodes"] == 180
    assert stats["roads"] == 641
    assert stats["buildings"] == 60
    assert stats["facilities"] == 120
    assert stats["categories"] == 10


def test_map_payload_matches_amap_frontend_contract() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        payload = get_map_payload_from_db(session)

    assert payload["center"] == [116.28333, 40.15608]
    assert payload["source"] == "database-seed-stage-3"
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
        stats = map_api.get_map_stats(session)
        payload = map_api.get_map_geojson(session)
        nodes = map_api.get_map_nodes(session)
        facilities = map_api.get_map_facilities(session)

    assert stats == {
        "nodes": 180,
        "roads": 641,
        "buildings": 60,
        "facilities": 120,
        "categories": 10,
    }

    assert payload["source"] == "database-seed-stage-3"
    assert payload["statistics"]["roads"] == 641
    assert payload["geojson"]["type"] == "FeatureCollection"
    assert len(payload["roads"]) == 641
    assert len(nodes) == 180
    assert len(facilities) == 120
