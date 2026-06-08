from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.init_db import create_all
from app.db.session import PROJECT_ROOT, resolve_sqlite_database_url
from app.models import Building, Destination, Facility, FacilityCategory, MapEdge, User
from app.seed.sample_data import BUPT_SHAHE_CENTER
from app.seed.seed_all import seed_demo_data


def test_core_table_metadata_is_registered() -> None:
    expected_tables = {
        "users",
        "user_profiles",
        "user_interests",
        "destinations",
        "destination_tags",
        "map_nodes",
        "map_edges",
        "buildings",
        "facility_categories",
        "facilities",
        "indoor_nodes",
        "indoor_edges",
        "diaries",
        "restaurants",
        "foods",
    }

    assert expected_tables.issubset(set(Base.metadata.tables.keys()))


def test_seed_demo_data_meets_stage2_scale() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        counts = seed_demo_data(session)

        assert counts["users"] >= 10
        assert counts["destinations"] >= 200
        assert counts["map_nodes"] >= 180
        assert counts["map_edges"] >= 450
        assert counts["buildings"] >= 60
        assert counts["facilities"] >= 120
        assert counts["facility_categories"] >= 10

        first_destination = session.scalars(select(Destination).limit(1)).one()
        assert abs(first_destination.lng - BUPT_SHAHE_CENTER[0]) < 0.003
        assert abs(first_destination.lat - BUPT_SHAHE_CENTER[1]) < 0.003
        assert first_destination.name == "北京邮电大学沙河校区"
        assert first_destination.category == "school"

        assert session.scalars(select(User).limit(1)).first() is not None
        assert session.scalars(select(Building).limit(1)).first() is not None
        assert session.scalars(select(Facility).limit(1)).first() is not None
        assert session.scalars(select(FacilityCategory).limit(1)).first() is not None
        edges = session.scalars(select(MapEdge)).all()
        first_edge = edges[0]
        assert 0 < first_edge.congestion <= 1
        assert "walk" in first_edge.allowed_modes
        assert any("bike" in edge.allowed_modes for edge in edges)
        assert any("electric_cart" in edge.allowed_modes for edge in edges)


def test_relative_sqlite_url_resolves_to_project_root() -> None:
    resolved = resolve_sqlite_database_url("sqlite:///./smart_tour_dev.db")

    assert resolved == f"sqlite:///{(PROJECT_ROOT / 'smart_tour_dev.db').resolve()}"
    assert "/backend/smart_tour_dev.db" not in resolved
