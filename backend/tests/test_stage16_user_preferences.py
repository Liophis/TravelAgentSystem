from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1.users import (
    UserInterestsRequest,
    UserLoginRequest,
    UserRegisterRequest,
    get_current_user,
    get_user_profile,
    list_users,
    login_user,
    register_user,
    update_user_interests,
)
from app.db.init_db import create_all
from app.models import Destination
from app.seed.seed_all import seed_demo_data
from app.services.recommendation_service import recommend_destinations_from_db
from app.services.user_service import (
    add_user_favorite_from_db,
    rate_target_from_db,
    record_user_behavior_from_db,
    update_user_interests_from_db,
)


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
        profile = update_user_interests_from_db(session, 1, ["technology"])
        after = recommend_destinations_from_db(session, 1, "interest", 5, 116.28333, 40.15608)

    assert profile is not None
    assert profile["interests"] == ["technology"]
    assert before["algorithm_trace"]["interest_tags"] != after["algorithm_trace"]["interest_tags"]
    assert after["algorithm_trace"]["interest_tags"] == "technology"
    assert any("technology" in item["tags"] for item in after["items"])


def test_update_user_interests_api_handler() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        profile = update_user_interests(1, UserInterestsRequest(interests=["food", "quiet", "unknown"]), session)

    assert profile["interests"] == ["food", "quiet"]


def test_register_login_and_token_profile_flow() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        registered = register_user(
            UserRegisterRequest(
                username="new_user",
                email="new_user@example.com",
                password="secret123",
                nickname="新用户",
                interests=["food", "sports"],
            ),
            session,
        )
        logged_in = login_user(UserLoginRequest(username_or_email="new_user", password="secret123"), session)
        profile = get_current_user(f"Bearer {logged_in['access_token']}", session)

    assert registered["user"]["username"] == "new_user"
    assert logged_in["token_type"] == "bearer"
    assert profile["username"] == "new_user"
    assert profile["interests"] == ["food", "sports"]


def test_favorite_rating_and_behavior_feedback_affect_recommendations() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        target_id = 120
        before = recommend_destinations_from_db(session, 1, "behavior", 5, 116.28333, 40.15608)
        favorite = add_user_favorite_from_db(session, 1, "destination", target_id, "想去这里")
        rating = rate_target_from_db(session, 1, "destination", target_id, 5.0)
        behavior = record_user_behavior_from_db(session, 1, "destination", target_id, "view", "test browse")
        after = recommend_destinations_from_db(session, 1, "behavior", 10, 116.28333, 40.15608)
        destination = session.get(Destination, target_id)
        profile = get_user_profile(1, session)

    assert favorite is not None
    assert favorite["target_id"] == target_id
    assert rating is not None
    assert rating["aggregate_rating"] == 5.0
    assert behavior is not None
    assert destination is not None
    assert destination.rating == 5.0
    assert destination.popularity > 10000
    assert any(item["id"] == target_id and item["behavior_score"] > 0 for item in after["items"])
    assert int(after["algorithm_trace"]["behavior_targets"]) > int(before["algorithm_trace"]["behavior_targets"])
    assert len(profile["favorites"]) >= 1
    assert len(profile["recent_behaviors"]) >= 1
