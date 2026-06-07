from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.destination_service import (
    SortMode,
    get_destination_detail_from_db,
    list_destinations_from_db,
)

router = APIRouter()


@router.get("")
def list_destinations(
    category: str | None = Query(default=None),
    q: str | None = Query(default=None),
    sort: SortMode = Query(default="popularity"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    return list_destinations_from_db(
        session=db,
        category=category,
        q=q,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/{destination_id}")
def get_destination(destination_id: int, db: Session = Depends(get_db)) -> dict:
    destination = get_destination_detail_from_db(db, destination_id)
    if destination is None:
        raise HTTPException(status_code=404, detail="Destination not found.")
    return destination
