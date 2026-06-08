from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1.users import UserInterestsRequest, get_user_profile, list_users, update_user_interests
from app.db.init_db import create_all
from app.seed.seed_all import seed_demo_data
from app.services.recommendation_service import recommend_destinations_from_db
from app.services.user_service import update_user_interests_from_db


def test_user_profile_api_lists_available_interests() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        users = list_users(session)
        profile = get_user_profile(1, session)

    assert users["total"] == 10
    assert "food" in users["available_interests"]
    assert profile["id"] == 1
    assert profile["interests"]


def test_updating_user_interests_changes_interest_recommendation_trace() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        before = recommend_destinations_from_db(session, 1, "interest", 5, 116.28333, 40.15608)
        profile = update_user_interests_from_db(session, 1, ["sports"])
        after = recommend_destinations_from_db(session, 1, "interest", 5, 116.28333, 40.15608)

    assert profile is not None
    assert profile["interests"] == ["sports"]
    assert before["algorithm_trace"]["interest_tags"] != after["algorithm_trace"]["interest_tags"]
    assert after["algorithm_trace"]["interest_tags"] == "sports"
    assert any("sports" in item["tags"] for item in after["items"])


def test_update_user_interests_api_handler() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        profile = update_user_interests(1, UserInterestsRequest(interests=["food", "quiet", "unknown"]), session)

    assert profile["interests"] == ["food", "quiet"]
