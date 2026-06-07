from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1.admin import admin_stats
from app.api.v1.aigc import DiaryDraftRequest, StoryboardRequest, diary_draft, storyboard
from app.db.init_db import create_all
from app.seed.seed_all import seed_demo_data
from app.services.food_service import (
    list_food_items_from_db,
    list_restaurants_from_db,
    nearby_foods_from_db,
    recommend_foods_from_db,
    search_foods_from_db,
)


def test_food_list_search_recommend_and_nearby() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        restaurants = list_restaurants_from_db(session, limit=10, offset=0)
        items = list_food_items_from_db(session, cuisine="noodle", restaurant_id=None, limit=10, offset=0)
        search = search_foods_from_db(session, q="推荐菜品 1", cuisine=None, limit=5)
        recommend = recommend_foods_from_db(
            session=session,
            cuisine=None,
            user_id=1,
            current_lng=116.28333,
            current_lat=40.15608,
            limit=5,
        )
        nearby = nearby_foods_from_db(
            session=session,
            current_lng=116.28333,
            current_lat=40.15608,
            cuisine=None,
            radius=5000,
            limit=3,
        )

    assert restaurants["total"] == 5
    assert items["total"] > 0
    assert search["total"] >= 1
    assert len(recommend["items"]) == 5
    assert recommend["items"][0]["score"] >= recommend["items"][-1]["score"]
    assert len(nearby["items"]) == 3
    assert len(nearby["items"][0]["routePath"]) >= 2


def test_aigc_placeholder_handlers_return_prompts() -> None:
    draft = diary_draft(
        DiaryDraftRequest(
            topic="沙河校区午后路线",
            keywords=["图书馆", "食堂"],
            tone="轻松",
        )
    )
    board = storyboard(StoryboardRequest(text="从校门走到食堂，再去图书馆。", scene_count=3))

    assert "沙河校区午后路线" in draft["prompt"]
    assert draft["title"]
    assert len(board["scenes"]) == 3
    assert board["simulated_video_url"].startswith("https://example.local")


def test_admin_stats_reports_core_table_counts() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        stats = admin_stats(session)

    assert stats["map"]["nodes"] == 80
    assert stats["tables"]["users"] == 10
    assert stats["tables"]["foods"] == 30
    assert stats["tables"]["diaries"] == 20
