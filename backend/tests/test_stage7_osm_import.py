from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1.admin import MapImportRequest, admin_stats, import_map, map_import_status
from app.db.init_db import create_all
from app.seed.osm_sample_data import BUPT_SHAHE_OSM_SAMPLE
from app.services.osm_import_service import import_osm_payload_to_db


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
