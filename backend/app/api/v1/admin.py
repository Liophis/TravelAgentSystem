from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Destination, Diary, Facility, Food, Restaurant, User
from app.services.osm_import_service import (
    OsmImportError,
    build_osmnx_payload,
    get_map_import_status,
    import_fixture_osm_payload,
    import_osm_payload_to_db,
)

router = APIRouter()


class MapImportRequest(BaseModel):
    source: str = Field(default="fixture", description="fixture or osmnx")
    place_name: str | None = Field(default=None)
    center_lng: float | None = Field(default=None)
    center_lat: float | None = Field(default=None)
    dist: int | None = Field(default=None, ge=100, le=10000)
    reset_existing: bool = Field(default=True)


@router.get("/stats")
def admin_stats(db: Session = Depends(get_db)) -> dict:
    return {
        "map": get_map_import_status(db),
        "tables": {
            "users": _count(db, User),
            "destinations": _count(db, Destination),
            "facilities": _count(db, Facility),
            "restaurants": _count(db, Restaurant),
            "foods": _count(db, Food),
            "diaries": _count(db, Diary),
        },
    }


@router.get("/map/import/status")
def map_import_status(db: Session = Depends(get_db)) -> dict:
    return get_map_import_status(db)


@router.post("/map/import")
def import_map(payload: MapImportRequest, db: Session = Depends(get_db)) -> dict:
    try:
        if payload.source == "fixture":
            return import_fixture_osm_payload(db, reset_existing=payload.reset_existing)
        if payload.source == "osmnx":
            osm_payload = build_osmnx_payload(
                place_name=payload.place_name or settings.osm_default_place,
                center_lng=payload.center_lng or settings.osm_fallback_lng,
                center_lat=payload.center_lat or settings.osm_fallback_lat,
                dist=payload.dist or settings.osm_fallback_dist,
            )
            return import_osm_payload_to_db(db, osm_payload, reset_existing=payload.reset_existing)
    except OsmImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OSM import failed: {exc}") from exc

    raise HTTPException(status_code=400, detail="Unsupported import source.")


def _count(db: Session, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)
