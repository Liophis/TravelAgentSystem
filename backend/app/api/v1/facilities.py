from fastapi import APIRouter, Query

from app.services.mock_map_service import get_nearby_facilities

router = APIRouter()


@router.get("/nearby")
def nearby_facilities(
    current_lng: float = Query(default=116.3260),
    current_lat: float = Query(default=40.0030),
    category: str | None = Query(default=None),
    radius: int = Query(default=800, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
) -> dict:
    return get_nearby_facilities(
        current_lng=current_lng,
        current_lat=current_lat,
        category=category,
        radius=radius,
        limit=limit,
    )
