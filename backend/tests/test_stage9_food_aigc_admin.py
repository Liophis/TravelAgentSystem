from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1.admin import (
    DestinationAdminUpdate,
    FacilityAdminUpdate,
    FoodAdminUpdate,
    admin_delete_diary,
    admin_list_diaries,
    admin_stats,
    admin_update_destination,
    admin_update_facility,
    admin_update_food,
)
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
        restaurants = list_restaurants_from_db(session, destination_id=None, limit=10, offset=0)
        scoped_restaurants = list_restaurants_from_db(session, destination_id=1, limit=10, offset=0)
        items = list_food_items_from_db(
            session,
            cuisine="noodle",
            restaurant_id=None,
            destination_id=None,
            limit=10,
            offset=0,
        )
        search = search_foods_from_db(session, q="番茄牛腩面", cuisine=None, destination_id=None, limit=5)
        search_hot = search_foods_from_db(session, q="饭", cuisine=None, destination_id=None, sort="hot", limit=5)
        search_distance = search_foods_from_db(
            session,
            q="饭",
            cuisine=None,
            destination_id=None,
            sort="distance",
            current_lng=116.28333,
            current_lat=40.15608,
            limit=5,
        )
        recommend = recommend_foods_from_db(
            session=session,
            cuisine=None,
            destination_id=1,
            user_id=1,
            current_lng=None,
            current_lat=None,
            limit=5,
        )
        nearby = nearby_foods_from_db(
            session=session,
            current_lng=116.28333,
            current_lat=40.15608,
            cuisine=None,
            destination_id=1,
            radius=5000,
            limit=3,
        )

    assert restaurants["total"] >= 12
    assert scoped_restaurants["total"] > 0
    assert items["total"] > 0
    assert search["total"] >= 1
    assert search_hot["items"][0]["heat"] >= search_hot["items"][-1]["heat"]
    assert search_distance["items"][0]["distance"] <= search_distance["items"][-1]["distance"]
    assert len(recommend["items"]) == 5
    assert recommend["destination_id"] == 1
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

    assert stats["map"]["nodes"] >= 180
    assert stats["tables"]["users"] == 10
    assert stats["tables"]["foods"] >= 72
    assert stats["tables"]["diaries"] == 20
    assert stats["tables"]["indoor_nodes"] >= 19
    assert stats["tables"]["indoor_edges"] >= 20


def test_admin_can_edit_core_content_and_moderate_diaries() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        destination = admin_update_destination(
            1,
            DestinationAdminUpdate(
                name="后台更新目的地",
                category="school",
                popularity=999,
                tags=["food", "study"],
            ),
            session,
        )
        facility = admin_update_facility(
            1,
            FacilityAdminUpdate(name="后台更新设施", category_code="toilet"),
            session,
        )
        food = admin_update_food(
            1,
            FoodAdminUpdate(name="后台更新美食", price=18.5, rating=4.9, heat=888),
            session,
        )
        diaries = admin_list_diaries(limit=5, offset=0, db=session)
        deleted = admin_delete_diary(diaries["items"][0]["id"], session)
        stats = admin_stats(session)

    assert destination["name"] == "后台更新目的地"
    assert destination["popularity"] == 999
    assert destination["tags"] == ["food", "study"]
    assert facility["name"] == "后台更新设施"
    assert facility["category"] == "toilet"
    assert food["name"] == "后台更新美食"
    assert food["heat"] == 888
    assert deleted["deleted"] is True
    assert stats["tables"]["diaries"] == 19
