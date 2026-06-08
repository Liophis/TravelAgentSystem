from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.search_service import search_places_from_db

router = APIRouter()


@router.get("/places")
def search_places(
    keyword: str = Query(min_length=1),
    category: str | None = Query(default=None),
    scope: str = Query(default="all", pattern="^(all|destinations|campus)$"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    return search_places_from_db(
        session=db,
        keyword=keyword,
        category=category,
        limit=limit,
        scope=scope,
    )
