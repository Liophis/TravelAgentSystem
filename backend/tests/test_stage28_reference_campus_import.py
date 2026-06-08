from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1.admin import MapImportRequest, import_map
from app.db.init_db import create_all
from app.services.map_data_service import get_map_stats_from_db
from app.services.reference_campus_import_service import import_reference_campus_to_db
from app.services.route_service import plan_route_from_db
from app.services.search_service import search_places_from_db
from app.seed.seed_all import seed_demo_data


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_SOURCE = PROJECT_ROOT / "data" / "reference" / "bupt-shahe"


def test_reference_campus_import_uses_supplied_wgs84_files() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        summary = import_reference_campus_to_db(
            session=session,
            source_dir=REFERENCE_SOURCE,
            replace_campus_layers=True,
        )
        stats = get_map_stats_from_db(session)
        start = search_places_from_db(session, "西门", None, 5)["items"][0]
        end = search_places_from_db(session, "图书馆", None, 5)["items"][0]
        route = plan_route_from_db(
            session,
            {
                "start_place_id": start["id"],
                "end_place_id": end["id"],
                "strategy": "shortest_distance",
                "mode": "walk",
                "route_source": "local_graph",
            },
        )

    assert summary["nodes_imported"] == 106
    assert summary["edges_imported"] == 246
    assert summary["facilities_imported"] >= 20
    assert summary["invalid_nodes"] == 0
    assert summary["invalid_edges"] == 0
    assert stats["roads"] >= 246
    assert stats["hidden_demo_roads"] >= 600
    assert route["route_source"] == "local_graph"
    assert route["distance"] > 0
    assert len(route["path"]) >= 2
    assert route["algorithm_trace"]["topology_source"] == "local map_nodes/map_edges graph"


def test_admin_reference_campus_import_handler() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        summary = import_map(MapImportRequest(source="reference_campus", reset_existing=True), session)

    assert summary["source"] == "reference-bupt-shahe"
    assert summary["nodes_imported"] == 106
    assert summary["edges_imported"] == 246
    assert summary["algorithm_trace"]["stage"] == "stage-28-reference-campus-navigation"
