from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.recommendation_service import recommend_destinations_from_db

router = APIRouter()


@router.get("")
def recommend_destinations(
    user_id: int | None = Query(default=1),
    strategy: str = Query(default="composite"),
    limit: int = Query(default=10, ge=1, le=50),
    current_lng: float | None = Query(default=None),
    current_lat: float | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    return recommend_destinations_from_db(
        session=db,
        user_id=user_id,
        strategy=strategy,
        limit=limit,
        current_lng=current_lng,
        current_lat=current_lat,
    )
