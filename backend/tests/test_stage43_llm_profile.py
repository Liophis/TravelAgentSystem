from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1.users import extract_user_profile_with_llm, get_user_profile_analysis
from app.db.init_db import create_all
from app.seed.seed_all import seed_demo_data
from app.services.recommendation_service import recommend_destinations_from_db
from app.services.user_profile_llm_service import extract_user_profile_with_llm_from_db


def test_llm_profile_fallback_updates_interests_and_trace(monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.settings.llm_api_key", None)
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        payload = extract_user_profile_with_llm_from_db(session, 1)
        recommendation = recommend_destinations_from_db(session, 1, "interest", 5, 116.28333, 40.15608)

    assert payload is not None
    assert payload["tags"]
    assert sorted(payload["updated_profile"]["interests"]) == sorted(payload["tags"])
    assert payload["algorithm_trace"]["fallback_used"] == "true"
    assert recommendation["algorithm_trace"]["interest_tags"] == ",".join(sorted(payload["tags"]))


def test_llm_profile_mock_provider_json_updates_recommendation_trace() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    def fake_llm_call(**_: object) -> str:
        return (
            '{"tags":["technology","campus"],'
            '"weights":{"technology":0.94,"campus":0.81},'
            '"summary":"用户偏好科技校园参观。",'
            '"evidence":["收藏和浏览记录集中在校园与科技类目的地。"]}'
        )

    with Session(engine) as session:
        seed_demo_data(session)
        before = recommend_destinations_from_db(session, 1, "interest", 5, 116.28333, 40.15608)
        payload = extract_user_profile_with_llm_from_db(session, 1, llm_call=fake_llm_call)
        after = recommend_destinations_from_db(session, 1, "interest", 5, 116.28333, 40.15608)
        analysis = get_user_profile_analysis(1, session)

    assert payload is not None
    assert payload["tags"] == ["technology", "campus"]
    assert payload["weights"]["technology"] == 0.94
    assert payload["algorithm_trace"]["fallback_used"] == "false"
    assert before["algorithm_trace"]["interest_tags"] != after["algorithm_trace"]["interest_tags"]
    assert after["algorithm_trace"]["interest_tags"] == "campus,technology"
    assert analysis["summary"] == "用户偏好科技校园参观。"


def test_llm_profile_api_handler_returns_404_for_missing_user() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        try:
            extract_user_profile_with_llm(9999, session)
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 404
        else:
            raise AssertionError("Expected 404 for missing user.")
