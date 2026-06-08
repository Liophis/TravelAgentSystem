from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.v1.indoor import IndoorRouteRequest, list_indoor_buildings, list_indoor_nodes, plan_indoor_route
from app.db.init_db import create_all
from app.models import IndoorEdge, IndoorNode
from app.seed.seed_all import seed_demo_data
from app.services.indoor_service import plan_indoor_route_from_db


def test_seed_contains_indoor_building_graph() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        counts = seed_demo_data(session)
        nodes = session.scalars(select(IndoorNode).order_by(IndoorNode.id)).all()
        edges = session.scalars(select(IndoorEdge).order_by(IndoorEdge.id)).all()

    assert counts["indoor_nodes"] >= 19
    assert counts["indoor_edges"] >= 20
    assert any(node.node_type == "entrance" for node in nodes)
    assert any(node.node_type == "elevator" and node.floor == 3 for node in nodes)
    assert any(edge.access_type == "elevator" for edge in edges)


def test_indoor_route_crosses_floors_with_elevator() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        route = plan_indoor_route_from_db(
            session,
            {
                "building_name": "综合教学楼",
                "start_name": "一层大门",
                "end_name": "305 教室",
            },
        )

    assert route["algorithm_trace"]["stage"] == "stage-15-indoor-navigation"
    assert route["distance"] > 0
    assert route["duration"] > 0
    assert route["path"][0]["name"] == "一层大门"
    assert route["path"][-1]["name"] == "305 教室"
    assert any(step["access_type"] == "elevator" for step in route["steps"])
    assert route["path"][-1]["floor"] == 3


def test_indoor_api_handlers_use_seeded_database() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        buildings = list_indoor_buildings(session)
        nodes = list_indoor_nodes("综合教学楼", session)
        route = plan_indoor_route(IndoorRouteRequest(), session)

    assert buildings["total"] == 1
    assert buildings["items"][0]["floors"] == [1, 2, 3]
    assert nodes["total"] >= 19
    assert route["end"]["name"] == "305 教室"
