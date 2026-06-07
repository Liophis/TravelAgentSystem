from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1.diaries import (
    DiaryCommentRequest,
    DiaryCreateRequest,
    DiaryRatingRequest,
    add_diary_comment,
    create_diary,
    diary_compression,
    get_diary,
    rate_diary,
    search_diaries,
    view_diary,
)
from app.db.init_db import create_all
from app.seed.seed_all import seed_demo_data
from app.services.diary_service import create_diary_from_db, recommend_diaries_from_db, search_diaries_from_db


def test_diary_publish_compresses_and_detail_decompresses() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    body = "沙河校区的图书馆和教学区很适合学习。" * 12
    with Session(engine) as session:
        seed_demo_data(session)
        diary = create_diary_from_db(
            session,
            {
                "user_id": 1,
                "destination_id": 1,
                "title": "压缩游记",
                "body": body,
            },
        )
        detail = get_diary(diary["id"], session)
        stats = diary_compression(diary["id"], session)

    assert detail["body"] == body
    assert stats["algorithm"] == "zlib+base64"
    assert stats["compressed_size"] < stats["original_size"]
    assert stats["decompress_ok"] is True


def test_diary_search_recommend_view_rating_and_comment() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        search_payload = search_diaries_from_db(session, keyword="Stage 2", limit=5)
        viewed = view_diary(1, session)
        rated = rate_diary(1, DiaryRatingRequest(user_id=1, value=5), session)
        comment = add_diary_comment(1, DiaryCommentRequest(user_id=1, content="很有帮助"), session)
        recommend_payload = recommend_diaries_from_db(session, limit=3)

    assert search_payload["total"] >= 5
    assert viewed["views"] == 1
    assert rated["rating_avg"] == 5
    assert comment["content"] == "很有帮助"
    assert len(recommend_payload["items"]) == 3


def test_diary_api_handlers_create_and_search() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        created = create_diary(
            DiaryCreateRequest(
                user_id=1,
                destination_id=1,
                title="API 游记",
                body="这是通过 API handler 创建的沙河校区游记。",
            ),
            session,
        )
        results = search_diaries(keyword="API", limit=10, db=session)

    assert created["title"] == "API 游记"
    assert results["items"][0]["title"] == "API 游记"
