import re
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.algorithms.compression import compress_text, compression_ratio, decompress_text
from app.algorithms.ranking import top_k_smallest
from app.models import (
    DestinationTag,
    Diary,
    DiaryComment,
    DiaryMedia,
    DiaryRating,
    DiarySearchToken,
    DiaryTitleIndex,
    UserInterest,
)


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
    session.flush()
    rebuild_diary_search_index(session, diary)
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
    rebuild_diary_search_index(session, diary)
    session.commit()
    session.refresh(diary)
    return serialize_diary(diary)


def delete_diary_from_db(session: Session, diary_id: int) -> bool:
    diary = _get_diary(session, diary_id)
    if diary is None:
        return False
    session.execute(delete(DiaryComment).where(DiaryComment.diary_id == diary_id))
    session.execute(delete(DiaryRating).where(DiaryRating.diary_id == diary_id))
    session.execute(delete(DiaryMedia).where(DiaryMedia.diary_id == diary_id))
    session.execute(delete(DiaryTitleIndex).where(DiaryTitleIndex.diary_id == diary_id))
    session.execute(delete(DiarySearchToken).where(DiarySearchToken.diary_id == diary_id))
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


def add_diary_media_from_db(session: Session, diary_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    diary = _get_diary(session, diary_id)
    if diary is None:
        return None
    media = DiaryMedia(
        diary_id=diary_id,
        media_type=payload.get("media_type") or "image",
        url=payload["url"],
        caption=payload.get("caption"),
    )
    session.add(media)
    session.commit()
    session.refresh(media)
    return serialize_media(media)


def list_diary_media_from_db(session: Session, diary_id: int) -> dict[str, Any] | None:
    diary = _get_diary(session, diary_id)
    if diary is None:
        return None
    media = session.scalars(select(DiaryMedia).where(DiaryMedia.diary_id == diary_id).order_by(DiaryMedia.id)).all()
    return {
        "items": [serialize_media(item) for item in media],
        "total": len(media),
        "algorithm_trace": {
            "stage": "stage-22-diary-media-search",
            "storage": "local media metadata table; url/path can point to uploaded media",
        },
    }


def search_diaries_from_db(session: Session, keyword: str, limit: int, mode: str = "fulltext") -> dict[str, Any]:
    normalized = _normalize_text(keyword)
    if mode == "exact_title":
        return _search_diaries_exact_title(session, normalized, keyword, limit)
    if mode == "contains":
        return list_diaries_from_db(session, destination_id=None, q=keyword, sort="hot", limit=limit, offset=0)
    return _search_diaries_inverted_index(session, keyword, limit)


def recommend_diaries_from_db(session: Session, limit: int, user_id: int | None = None) -> dict[str, Any]:
    diaries = _load_diaries(session)
    interest_tags = _user_interest_tags(session, user_id)
    scored = [
        {
            **serialize_diary(diary, include_body=False),
            "score": round(_diary_score(session, diary, interest_tags), 2),
            "reason": _diary_reason(session, diary, interest_tags),
        }
        for diary in diaries
    ]
    items = top_k_smallest(scored, key=lambda item: -float(item["score"]), k=limit)
    return {
        "items": items,
        "total": len(diaries),
        "algorithm_trace": {
            "stage": "stage-22-diary-media-search",
            "algorithm": "views + rating + destination interest overlap plus Top-K heap",
            "interest_tags": ",".join(interest_tags),
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


def rebuild_diary_search_index(session: Session, diary: Diary) -> None:
    body = _diary_body(diary)
    session.execute(delete(DiaryTitleIndex).where(DiaryTitleIndex.diary_id == diary.id))
    session.execute(delete(DiarySearchToken).where(DiarySearchToken.diary_id == diary.id))
    session.add(DiaryTitleIndex(diary_id=diary.id, normalized_title=_normalize_text(diary.title)))
    token_counts: dict[tuple[str, str], int] = {}
    for field, text in (("title", diary.title), ("body", body)):
        for token in _tokenize(text):
            key = (field, token)
            token_counts[key] = token_counts.get(key, 0) + 1
    for (field, token), frequency in token_counts.items():
        session.add(DiarySearchToken(diary_id=diary.id, token=token, field=field, frequency=frequency))


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
        item["media"] = [serialize_media(media) for media in diary.media]
    return item


def serialize_comment(comment: DiaryComment) -> dict[str, Any]:
    return {
        "id": comment.id,
        "diary_id": comment.diary_id,
        "user_id": comment.user_id,
        "content": comment.content,
        "created_at": comment.created_at.isoformat(),
    }


def serialize_media(media: DiaryMedia) -> dict[str, Any]:
    return {
        "id": media.id,
        "diary_id": media.diary_id,
        "media_type": media.media_type,
        "url": media.url,
        "caption": media.caption,
        "created_at": media.created_at.isoformat(),
    }


def _search_diaries_exact_title(session: Session, normalized: str, keyword: str, limit: int) -> dict[str, Any]:
    rows = session.scalars(
        select(DiaryTitleIndex)
        .where(DiaryTitleIndex.normalized_title == normalized)
        .limit(limit)
    ).all()
    diary_ids = [row.diary_id for row in rows]
    diaries = _load_diaries_by_ids(session, diary_ids)
    return {
        "items": [serialize_diary(diary, include_body=False) for diary in diaries],
        "total": len(diaries),
        "keyword": keyword,
        "mode": "exact_title",
        "algorithm_trace": {
            "stage": "stage-22-diary-media-search",
            "algorithm": "normalized exact title index lookup",
            "returned": str(len(diaries)),
        },
    }


def _search_diaries_inverted_index(session: Session, keyword: str, limit: int) -> dict[str, Any]:
    tokens = _tokenize(keyword)
    if not tokens:
        return list_diaries_from_db(session, destination_id=None, q=keyword, sort="hot", limit=limit, offset=0)
    rows = session.execute(
        select(
            DiarySearchToken.diary_id,
            func.sum(DiarySearchToken.frequency).label("score"),
        )
        .where(DiarySearchToken.token.in_(tokens))
        .group_by(DiarySearchToken.diary_id)
        .order_by(func.sum(DiarySearchToken.frequency).desc(), DiarySearchToken.diary_id.desc())
        .limit(limit)
    ).all()
    diary_ids = [int(row.diary_id) for row in rows]
    scores = {int(row.diary_id): int(row.score or 0) for row in rows}
    diaries = _load_diaries_by_ids(session, diary_ids)
    items = []
    for diary in diaries:
        item = serialize_diary(diary, include_body=False)
        item["score"] = scores.get(diary.id, 0)
        item["reason"] = f"倒排索引命中 {scores.get(diary.id, 0)} 次"
        items.append(item)
    return {
        "items": items,
        "total": len(items),
        "keyword": keyword,
        "mode": "fulltext",
        "algorithm_trace": {
            "stage": "stage-22-diary-media-search",
            "algorithm": "lightweight inverted index over title/body tokens",
            "query_tokens": ",".join(tokens),
            "returned": str(len(items)),
        },
    }


def _load_diaries(session: Session) -> list[Diary]:
    return list(
        session.scalars(
            select(Diary)
            .options(selectinload(Diary.comments), selectinload(Diary.media))
            .order_by(Diary.id)
        ).all()
    )


def _load_diaries_by_ids(session: Session, diary_ids: list[int]) -> list[Diary]:
    if not diary_ids:
        return []
    diaries = session.scalars(
        select(Diary)
        .options(selectinload(Diary.comments), selectinload(Diary.media))
        .where(Diary.id.in_(diary_ids))
    ).all()
    by_id = {diary.id: diary for diary in diaries}
    return [by_id[diary_id] for diary_id in diary_ids if diary_id in by_id]


def _get_diary(session: Session, diary_id: int) -> Diary | None:
    return session.scalar(
        select(Diary)
        .options(selectinload(Diary.comments), selectinload(Diary.media))
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


def _diary_score(session: Session, diary: Diary, interest_tags: list[str]) -> float:
    interest_overlap = _interest_overlap(session, diary, interest_tags)
    return diary.views * 0.6 + _rating_avg(diary) * 20 + diary.rating_count * 4 + interest_overlap * 25


def _diary_reason(session: Session, diary: Diary, interest_tags: list[str]) -> str:
    overlap = _interest_overlap(session, diary, interest_tags)
    if overlap:
        return f"匹配兴趣 {overlap} 项，评分 {_rating_avg(diary):.1f}，浏览 {diary.views}"
    if diary.rating_count > 0:
        return f"评分 {_rating_avg(diary):.1f}，浏览 {diary.views}"
    return f"浏览 {diary.views}，适合继续补充互动数据"


def _user_interest_tags(session: Session, user_id: int | None) -> list[str]:
    if user_id is None:
        return []
    return [
        interest.tag.casefold()
        for interest in session.scalars(select(UserInterest).where(UserInterest.user_id == user_id)).all()
    ]


def _interest_overlap(session: Session, diary: Diary, interest_tags: list[str]) -> int:
    if not interest_tags:
        return 0
    diary_tags = set()
    if diary.destination_id:
        diary_tags.update(
            tag.tag.casefold()
            for tag in session.scalars(
                select(DestinationTag).where(DestinationTag.destination_id == diary.destination_id)
            ).all()
        )
    text = f"{diary.title} {_diary_body(diary)}".casefold()
    diary_tags.update(token for token in interest_tags if token in text)
    return len(set(interest_tags) & diary_tags)


def _normalize_text(text: str) -> str:
    return " ".join(text.casefold().strip().split())


def _tokenize(text: str) -> list[str]:
    normalized = text.casefold()
    raw_tokens = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]+", normalized)
    results: set[str] = set()
    for token in raw_tokens:
        if len(token) <= 1:
            continue
        results.add(token)
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            for size in range(2, min(5, len(token) + 1)):
                for index in range(0, len(token) - size + 1):
                    results.add(token[index : index + size])
    return sorted(results)
