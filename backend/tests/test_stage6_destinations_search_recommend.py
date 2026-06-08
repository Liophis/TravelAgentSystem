from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1.destinations import get_destination, list_destinations
from app.api.v1.recommendations import recommend_destinations
from app.api.v1.search import search_places
from app.db.init_db import create_all
from app.seed.seed_all import seed_demo_data
from app.services.destination_service import list_destinations_from_db
from app.services.recommendation_service import recommend_destinations_from_db
from app.services.search_service import search_places_from_db


def test_destination_list_and_detail_use_seeded_database() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        payload = list_destinations_from_db(
            session=session,
            category="school",
            q="大学",
            sort="popularity",
            limit=5,
            offset=0,
        )
        detail = get_destination(1, session)

    assert payload["total"] >= 80
    assert len(payload["items"]) == 5
    assert all(item["category"] == "school" for item in payload["items"])
    assert detail["id"] == 1
    assert detail["name"] == "北京邮电大学沙河校区"


def test_place_search_covers_destinations_buildings_and_facilities() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        destination_results = search_places_from_db(session, keyword="长城", category=None, limit=5)
        building_results = search_places_from_db(session, keyword="建筑", category=None, limit=5)
        facility_results = search_places_from_db(session, keyword="饮水点", category=None, limit=5)

    assert destination_results["items"][0]["source"] == "destination"
    assert any(item["source"] == "building" for item in building_results["items"])
    assert any(item["source"] == "facility" for item in facility_results["items"])


def test_recommendations_return_top_10_with_reasons() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        payload = recommend_destinations_from_db(
            session=session,
            user_id=1,
            strategy="composite",
            limit=10,
            current_lng=None,
            current_lat=None,
        )

    scores = [item["score"] for item in payload["items"]]
    assert len(payload["items"]) == 10
    assert scores == sorted(scores, reverse=True)
    assert all(item["reason"] for item in payload["items"])
    assert payload["algorithm_trace"]["algorithm"] == "rule scoring plus Top-K heap"


def test_stage6_api_handlers_use_seeded_database() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        destinations = list_destinations(category=None, q=None, sort="popularity", limit=3, offset=0, db=session)
        places = search_places(keyword="厕所", category=None, limit=3, db=session)
        recommendations = recommend_destinations(
            user_id=1,
            strategy="composite",
            limit=3,
            current_lng=None,
            current_lat=None,
            db=session,
        )

    assert len(destinations["items"]) == 3
    assert places["items"][0]["source"] == "facility"
    assert len(recommendations["items"]) == 3
