from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.v1.admin import MapImportRequest, admin_stats, cleanup_demo_layers, import_map, map_import_status
from app.db.init_db import create_all
from app.models import Facility, MapNode
from app.seed.osm_sample_data import BUPT_SHAHE_OSM_SAMPLE
from app.seed.seed_all import seed_demo_data
from app.services import osm_import_service
from app.services.amap_import_service import import_amap_poi_items_to_db
from app.services.map_data_service import get_map_payload_from_db
from app.services.osm_import_service import build_osmnx_payload
from app.services.osm_import_service import (
    import_osm_feature_layers_to_db,
    import_osm_payload_to_db,
    import_osm_road_graph_to_db,
)


def test_osm_fixture_payload_imports_map_layers() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        summary = import_osm_payload_to_db(session, BUPT_SHAHE_OSM_SAMPLE, reset_existing=True)
        status = map_import_status(session)

    assert summary["source"] == "fixture-osm-bupt-shahe"
    assert summary["nodes"] == 5
    assert summary["edges"] == 4
    assert summary["buildings"] == 2
    assert summary["facilities"] == 2
    assert status["nodes"] == 5
    assert status["edges"] == 4
    assert status["facility_categories"] == 2


def test_admin_import_fixture_handler_updates_status() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        summary = import_map(MapImportRequest(source="fixture", reset_existing=True), session)
        stats = admin_stats(session)

    assert summary["algorithm_trace"]["stage"] == "stage-7-osm-import"
    assert stats["map"]["nodes"] == 5
    assert stats["map"]["edges"] == 4
    assert stats["map"]["buildings"] == 2
    assert stats["map"]["facilities"] == 2


def test_osm_feature_import_removes_demo_polygons_and_preserves_amap_pois() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        center_node = session.scalar(select(MapNode).order_by(MapNode.id))
        assert center_node is not None
        import_amap_poi_items_to_db(
            session=session,
            pois=[
                {
                    "id": "B0REAL001",
                    "name": "真实高德厕所",
                    "type": "公共设施;公共厕所;公共厕所",
                    "location": "116.289408,40.157331",
                    "_query_keyword": "厕所",
                }
            ],
            center_lng=116.28333,
            center_lat=40.15608,
            radius=3000,
            reset_facilities=True,
        )
        summary = import_osm_feature_layers_to_db(session, BUPT_SHAHE_OSM_SAMPLE)
        payload = get_map_payload_from_db(session)
        facilities = session.scalars(select(Facility).order_by(Facility.id)).all()

    assert summary["buildings_imported"] == 2
    assert summary["facilities_imported"] == 2
    assert len(payload["buildings"]) == 2
    assert len(payload["facilities"]) == 3
    assert any("source=amap" in (facility.description or "") for facility in facilities)
    assert all("Campus-density seed" not in (item["description"] or "") for item in payload["buildings"])


def test_osm_road_graph_import_preserves_seed_fallback_but_exposes_osm_roads() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        summary = import_osm_road_graph_to_db(session, BUPT_SHAHE_OSM_SAMPLE)
        visible = get_map_payload_from_db(session)
        raw = get_map_payload_from_db(session, include_demo=True)

    assert summary["nodes_imported"] == 5
    assert summary["edges_imported"] == 4
    assert len(visible["roads"]) == 4
    assert visible["statistics"]["hidden_demo_roads"] == 641
    assert len(raw["roads"]) == 645


def test_osmnx_place_lookup_falls_back_to_point(monkeypatch) -> None:
    monkeypatch.setattr(osm_import_service, "_load_osmnx", lambda: FakeOsmnx())

    payload = build_osmnx_payload(
        place_name="bad place query",
        center_lng=116.28333,
        center_lat=40.15608,
        dist=500,
    )

    assert payload["lookup_mode"] == "point-fallback"
    assert payload["place_name"].startswith("fallback-point:")
    assert len(payload["nodes"]) == 2
    assert len(payload["edges"]) == 1


def test_admin_cleanup_demo_layers_handler() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        summary = cleanup_demo_layers(session)
        payload = get_map_payload_from_db(session, include_demo=True)

    assert summary["removed_buildings"] == 60
    assert summary["removed_facilities"] == 120
    assert payload["buildings"] == []
    assert payload["facilities"] == []


class FakeOsmnx:
    def graph_from_place(self, *args, **kwargs):
        raise RuntimeError("Nominatim geocoder returned 0 results for query 'bad place query'.")

    def graph_from_point(self, *args, **kwargs):
        return "fake-graph"

    def features_from_point(self, *args, **kwargs):
        return FakeFeaturesFrame()

    def graph_to_gdfs(self, graph):
        return FakeNodesFrame(), FakeEdgesFrame()


class FakeNodesFrame:
    def iterrows(self):
        yield 1001, {"x": 116.28333, "y": 40.15608}
        yield 1002, {"x": 116.28410, "y": 40.15668}


class FakeEdgesFrame:
    def reset_index(self):
        return self

    def iterrows(self):
        yield 0, {"u": 1001, "v": 1002, "length": 98, "geometry": None}


class FakeFeaturesFrame:
    def iterrows(self):
        return iter(())
