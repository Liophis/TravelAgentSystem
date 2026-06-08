from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.diary_service import (
    add_diary_comment_from_db,
    add_diary_media_from_db,
    create_diary_from_db,
    delete_diary_from_db,
    get_diary_compression_stats,
    get_diary_from_db,
    increment_diary_view,
    list_diary_media_from_db,
    list_diaries_from_db,
    rate_diary_from_db,
    recommend_diaries_from_db,
    search_diaries_from_db,
    update_diary_from_db,
)

router = APIRouter()


class DiaryCreateRequest(BaseModel):
    user_id: int = Field(default=1)
    destination_id: int | None = Field(default=None)
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1)


class DiaryUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    body: str | None = Field(default=None)


class DiaryRatingRequest(BaseModel):
    user_id: int = Field(default=1)
    value: int = Field(ge=1, le=5)


class DiaryCommentRequest(BaseModel):
    user_id: int = Field(default=1)
    content: str = Field(min_length=1)


class DiaryMediaRequest(BaseModel):
    media_type: str = Field(default="image", pattern="^(image|video)$")
    url: str = Field(min_length=1, max_length=512)
    caption: str | None = Field(default=None, max_length=160)


@router.get("/search")
def search_diaries(
    keyword: str = Query(min_length=1),
    mode: str = Query(default="fulltext", pattern="^(fulltext|exact_title|contains)$"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    return search_diaries_from_db(db, keyword=keyword, mode=mode, limit=limit)


@router.get("/recommend")
def recommend_diaries(
    user_id: int | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict:
    return recommend_diaries_from_db(db, limit=limit, user_id=user_id)


@router.get("")
def list_diaries(
    destination_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    sort: str = Query(default="hot"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    return list_diaries_from_db(
        session=db,
        destination_id=destination_id,
        q=q,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.post("")
def create_diary(payload: DiaryCreateRequest, db: Session = Depends(get_db)) -> dict:
    return create_diary_from_db(db, payload.model_dump())


@router.get("/{diary_id}")
def get_diary(diary_id: int, db: Session = Depends(get_db)) -> dict:
    diary = get_diary_from_db(db, diary_id)
    if diary is None:
        raise HTTPException(status_code=404, detail="Diary not found.")
    return diary


@router.put("/{diary_id}")
def update_diary(diary_id: int, payload: DiaryUpdateRequest, db: Session = Depends(get_db)) -> dict:
    diary = update_diary_from_db(db, diary_id, payload.model_dump(exclude_none=True))
    if diary is None:
        raise HTTPException(status_code=404, detail="Diary not found.")
    return diary


@router.delete("/{diary_id}")
def delete_diary(diary_id: int, db: Session = Depends(get_db)) -> dict:
    if not delete_diary_from_db(db, diary_id):
        raise HTTPException(status_code=404, detail="Diary not found.")
    return {"deleted": True}


@router.post("/{diary_id}/view")
def view_diary(diary_id: int, db: Session = Depends(get_db)) -> dict:
    diary = increment_diary_view(db, diary_id)
    if diary is None:
        raise HTTPException(status_code=404, detail="Diary not found.")
    return diary


@router.post("/{diary_id}/rating")
def rate_diary(diary_id: int, payload: DiaryRatingRequest, db: Session = Depends(get_db)) -> dict:
    diary = rate_diary_from_db(db, diary_id=diary_id, user_id=payload.user_id, value=payload.value)
    if diary is None:
        raise HTTPException(status_code=404, detail="Diary not found.")
    return diary


@router.post("/{diary_id}/comments")
def add_diary_comment(diary_id: int, payload: DiaryCommentRequest, db: Session = Depends(get_db)) -> dict:
    comment = add_diary_comment_from_db(db, diary_id=diary_id, user_id=payload.user_id, content=payload.content)
    if comment is None:
        raise HTTPException(status_code=404, detail="Diary not found.")
    return comment


@router.post("/{diary_id}/media")
def add_diary_media(diary_id: int, payload: DiaryMediaRequest, db: Session = Depends(get_db)) -> dict:
    media = add_diary_media_from_db(db, diary_id=diary_id, payload=payload.model_dump())
    if media is None:
        raise HTTPException(status_code=404, detail="Diary not found.")
    return media


@router.get("/{diary_id}/media")
def list_diary_media(diary_id: int, db: Session = Depends(get_db)) -> dict:
    media = list_diary_media_from_db(db, diary_id=diary_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Diary not found.")
    return media


@router.get("/{diary_id}/compression")
def diary_compression(diary_id: int, db: Session = Depends(get_db)) -> dict:
    stats = get_diary_compression_stats(db, diary_id)
    if stats is None:
        raise HTTPException(status_code=404, detail="Diary not found.")
    return stats
