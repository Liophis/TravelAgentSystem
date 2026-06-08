from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.algorithms.route_planning import RouteNotFoundError
from app.db.session import get_db
from app.services.facility_service import get_nearby_facilities_from_db

router = APIRouter()


@router.get("/nearby")
def nearby_facilities(
    origin_place_id: str | None = Query(default=None),
    current_lng: float = Query(default=116.28333),
    current_lat: float = Query(default=40.15608),
    category: str | None = Query(default=None),
    radius: int = Query(default=800, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    scene_key: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return get_nearby_facilities_from_db(
            session=db,
            origin_place_id=origin_place_id,
            current_lng=current_lng,
            current_lat=current_lat,
            category=category,
            radius=radius,
            limit=limit,
            scene_key=scene_key,
        )
    except RouteNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
