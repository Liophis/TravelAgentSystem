from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.algorithms.compression import compress_text, compression_ratio, decompress_text
from app.algorithms.ranking import top_k_smallest
from app.models import Diary, DiaryComment, DiaryRating


def create_diary_from_db(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    compressed_body, original_size, compressed_size = compress_text(payload["body"])
    diary = Diary(
        user_id=payload.get("user_id") or 1,
        destination_id=payload.get("destination_id"),
        title=payload["title"],
        body="",
        compressed_body=compressed_body,
        original_size=original_size,
        compressed_size=compressed_size,
    )
    session.add(diary)
    session.commit()
    session.refresh(diary)
    return serialize_diary(diary)


def list_diaries_from_db(
    session: Session,
    destination_id: int | None,
    q: str | None,
    sort: str,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    diaries = _filter_diaries(_load_diaries(session), destination_id, q)
    sorted_diaries = _sort_diaries(diaries, sort)
    items = sorted_diaries[offset : offset + limit]
    return {
        "items": [serialize_diary(diary, include_body=False) for diary in items],
        "total": len(diaries),
        "limit": limit,
        "offset": offset,
        "algorithm_trace": {
            "stage": "stage-8-diaries",
            "filter": "destination and keyword contains matching",
            "sort": sort,
            "compression": "zlib+base64 on publish, decompress on read",
            "matched": str(len(diaries)),
            "returned": str(len(items)),
        },
    }


def get_diary_from_db(session: Session, diary_id: int) -> dict[str, Any] | None:
    diary = _get_diary(session, diary_id)
    if diary is None:
        return None
    return serialize_diary(diary, include_comments=True)


def update_diary_from_db(session: Session, diary_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    diary = _get_diary(session, diary_id)
    if diary is None:
        return None
    if "title" in payload and payload["title"]:
        diary.title = payload["title"]
    if "body" in payload and payload["body"]:
        compressed_body, original_size, compressed_size = compress_text(payload["body"])
        diary.body = ""
        diary.compressed_body = compressed_body
        diary.original_size = original_size
        diary.compressed_size = compressed_size
    session.commit()
    session.refresh(diary)
    return serialize_diary(diary)


def delete_diary_from_db(session: Session, diary_id: int) -> bool:
    diary = _get_diary(session, diary_id)
    if diary is None:
        return False
    session.execute(delete(DiaryComment).where(DiaryComment.diary_id == diary_id))
    session.execute(delete(DiaryRating).where(DiaryRating.diary_id == diary_id))
    session.delete(diary)
    session.commit()
    return True


def increment_diary_view(session: Session, diary_id: int) -> dict[str, Any] | None:
    diary = _get_diary(session, diary_id)
    if diary is None:
        return None
    diary.views += 1
    session.commit()
    session.refresh(diary)
    return serialize_diary(diary, include_body=False)


def rate_diary_from_db(session: Session, diary_id: int, user_id: int, value: int) -> dict[str, Any] | None:
    diary = _get_diary(session, diary_id)
    if diary is None:
        return None
    rating = DiaryRating(diary_id=diary_id, user_id=user_id, value=value)
    diary.rating_sum += value
    diary.rating_count += 1
    session.add(rating)
    session.commit()
    session.refresh(diary)
    return serialize_diary(diary, include_body=False)


def add_diary_comment_from_db(session: Session, diary_id: int, user_id: int, content: str) -> dict[str, Any] | None:
    diary = _get_diary(session, diary_id)
    if diary is None:
        return None
    comment = DiaryComment(diary_id=diary_id, user_id=user_id, content=content)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return serialize_comment(comment)


def search_diaries_from_db(session: Session, keyword: str, limit: int) -> dict[str, Any]:
    return list_diaries_from_db(session, destination_id=None, q=keyword, sort="hot", limit=limit, offset=0)


def recommend_diaries_from_db(session: Session, limit: int) -> dict[str, Any]:
    diaries = _load_diaries(session)
    scored = [
        {
            **serialize_diary(diary, include_body=False),
            "score": round(diary.views * 0.6 + _rating_avg(diary) * 20 + diary.rating_count * 4, 2),
            "reason": _diary_reason(diary),
        }
        for diary in diaries
    ]
    items = top_k_smallest(scored, key=lambda item: -float(item["score"]), k=limit)
    return {
        "items": items,
        "total": len(diaries),
        "algorithm_trace": {
            "stage": "stage-8-diaries",
            "algorithm": "views + rating rule scoring plus Top-K heap",
            "returned": str(len(items)),
        },
    }


def get_diary_compression_stats(session: Session, diary_id: int) -> dict[str, Any] | None:
    diary = _get_diary(session, diary_id)
    if diary is None:
        return None
    body = _diary_body(diary)
    original_size = diary.original_size or len(body.encode("utf-8"))
    compressed_size = diary.compressed_size or len(body.encode("utf-8"))
    return {
        "diary_id": diary.id,
        "algorithm": "zlib+base64",
        "original_size": original_size,
        "compressed_size": compressed_size,
        "compression_ratio": compression_ratio(original_size, compressed_size),
        "decompress_ok": body == _diary_body(diary),
    }


def serialize_diary(diary: Diary, include_body: bool = True, include_comments: bool = False) -> dict[str, Any]:
    item = {
        "id": diary.id,
        "user_id": diary.user_id,
        "destination_id": diary.destination_id,
        "title": diary.title,
        "summary": _diary_body(diary)[:90],
        "views": diary.views,
        "rating_avg": _rating_avg(diary),
        "rating_count": diary.rating_count,
        "created_at": diary.created_at.isoformat(),
    }
    if include_body:
        item["body"] = _diary_body(diary)
    if include_comments:
        item["comments"] = [serialize_comment(comment) for comment in diary.comments]
    return item


def serialize_comment(comment: DiaryComment) -> dict[str, Any]:
    return {
        "id": comment.id,
        "diary_id": comment.diary_id,
        "user_id": comment.user_id,
        "content": comment.content,
        "created_at": comment.created_at.isoformat(),
    }


def _load_diaries(session: Session) -> list[Diary]:
    return list(
        session.scalars(
            select(Diary)
            .options(selectinload(Diary.comments))
            .order_by(Diary.id)
        ).all()
    )


def _get_diary(session: Session, diary_id: int) -> Diary | None:
    return session.scalar(
        select(Diary)
        .options(selectinload(Diary.comments))
        .where(Diary.id == diary_id)
    )


def _filter_diaries(diaries: list[Diary], destination_id: int | None, q: str | None) -> list[Diary]:
    keyword = q.casefold().strip() if q else ""
    results = []
    for diary in diaries:
        if destination_id is not None and diary.destination_id != destination_id:
            continue
        if keyword and keyword not in f"{diary.title} {_diary_body(diary)}".casefold():
            continue
        results.append(diary)
    return results


def _sort_diaries(diaries: list[Diary], sort: str) -> list[Diary]:
    if sort == "rating":
        return sorted(diaries, key=lambda diary: (-_rating_avg(diary), -diary.views, diary.id))
    if sort == "new":
        return sorted(diaries, key=lambda diary: (-diary.id, -diary.views))
    return sorted(diaries, key=lambda diary: (-diary.views, -_rating_avg(diary), diary.id))


def _diary_body(diary: Diary) -> str:
    if diary.compressed_body:
        return decompress_text(diary.compressed_body)
    return diary.body


def _rating_avg(diary: Diary) -> float:
    if diary.rating_count <= 0:
        return 0
    return round(diary.rating_sum / diary.rating_count, 2)


def _diary_reason(diary: Diary) -> str:
    if diary.rating_count > 0:
        return f"评分 {_rating_avg(diary):.1f}，浏览 {diary.views}"
    return f"浏览 {diary.views}，适合继续补充互动数据"
