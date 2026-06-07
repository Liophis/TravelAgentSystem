from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.algorithms.route_planning import RouteNotFoundError
from app.db.session import get_db
from app.services.facility_service import get_nearby_facilities_from_db

router = APIRouter()


@router.get("/nearby")
def nearby_facilities(
    current_lng: float = Query(default=116.28333),
    current_lat: float = Query(default=40.15608),
    category: str | None = Query(default=None),
    radius: int = Query(default=800, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return get_nearby_facilities_from_db(
            session=db,
            current_lng=current_lng,
            current_lat=current_lat,
            category=category,
            radius=radius,
            limit=limit,
        )
    except RouteNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
