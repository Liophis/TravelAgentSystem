from fastapi import APIRouter

from app.services.mock_map_service import get_map_payload

router = APIRouter()


@router.get("/stats")
def get_map_stats() -> dict[str, int]:
    return get_map_payload()["statistics"]


@router.get("/geojson")
def get_map_geojson() -> dict:
    return get_map_payload()
