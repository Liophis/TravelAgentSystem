from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.session import get_db
from app.models import (
    Destination,
    DestinationTag,
    Diary,
    DiaryComment,
    DiaryMedia,
    DiaryRating,
    DiarySearchToken,
    DiaryTitleIndex,
    Facility,
    FacilityCategory,
    Food,
    IndoorEdge,
    IndoorNode,
    Restaurant,
    User,
    UserBehaviorLog,
    UserFavorite,
    UserRating,
)
from app.services.amap_import_service import AMapPoiImportError, import_amap_pois_to_db
from app.services.destination_service import serialize_destination
from app.services.food_service import serialize_food
from app.services.osm_import_service import (
    OsmImportError,
    build_osmnx_payload,
    get_map_import_status,
    import_fixture_osm_payload,
    import_osm_payload_to_db,
)

router = APIRouter()


class MapImportRequest(BaseModel):
    source: str = Field(default="fixture", description="fixture, osmnx, or amap_poi")
    place_name: str | None = Field(default=None)
    center_lng: float | None = Field(default=None)
    center_lat: float | None = Field(default=None)
    dist: int | None = Field(default=None, ge=100, le=10000)
    keywords: list[str] | None = Field(default=None)
    max_pages: int = Field(default=3, ge=1, le=20)
    request_interval: float = Field(default=0.3, ge=0, le=5)
    reset_existing: bool = Field(default=True)


class DestinationAdminUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=2000)
    rating: float | None = Field(default=None, ge=1, le=5)
    popularity: int | None = Field(default=None, ge=0)
    tags: list[str] | None = Field(default=None, max_length=12)


class FacilityAdminUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    category_code: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=1000)
    lng: float | None = None
    lat: float | None = None


class FoodAdminUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    cuisine: str | None = Field(default=None, max_length=64)
    price: float | None = Field(default=None, ge=0)
    rating: float | None = Field(default=None, ge=1, le=5)
    heat: int | None = Field(default=None, ge=0)


@router.get("/stats")
def admin_stats(db: Session = Depends(get_db)) -> dict:
    return {
        "map": get_map_import_status(db),
        "tables": {
            "users": _count(db, User),
            "user_favorites": _count(db, UserFavorite),
            "user_ratings": _count(db, UserRating),
            "user_behavior_logs": _count(db, UserBehaviorLog),
            "destinations": _count(db, Destination),
            "facilities": _count(db, Facility),
            "restaurants": _count(db, Restaurant),
            "foods": _count(db, Food),
            "diaries": _count(db, Diary),
            "indoor_nodes": _count(db, IndoorNode),
            "indoor_edges": _count(db, IndoorEdge),
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
        if payload.source == "amap_poi":
            return import_amap_pois_to_db(
                session=db,
                api_key=settings.amap_web_api_key or "",
                center_lng=payload.center_lng or settings.osm_fallback_lng,
                center_lat=payload.center_lat or settings.osm_fallback_lat,
                radius=payload.dist or settings.osm_fallback_dist,
                keywords=payload.keywords,
                max_pages=payload.max_pages,
                reset_facilities=payload.reset_existing,
                request_interval=payload.request_interval,
            )
    except AMapPoiImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OsmImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Map import failed: {exc}") from exc

    raise HTTPException(status_code=400, detail="Unsupported import source.")


@router.get("/diaries")
def admin_list_diaries(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    diaries = list(
        db.scalars(
            select(Diary)
            .order_by(Diary.created_at.desc(), Diary.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return {
        "items": [
            {
                "id": diary.id,
                "user_id": diary.user_id,
                "destination_id": diary.destination_id,
                "title": diary.title,
                "views": diary.views,
                "rating_count": diary.rating_count,
                "created_at": diary.created_at.isoformat(),
            }
            for diary in diaries
        ],
        "total": _count(db, Diary),
        "limit": limit,
        "offset": offset,
        "algorithm_trace": {
            "stage": "stage-25-admin-moderation",
            "source": "diaries moderation list",
        },
    }


@router.delete("/diaries/{diary_id}")
def admin_delete_diary(diary_id: int, db: Session = Depends(get_db)) -> dict:
    diary = db.get(Diary, diary_id)
    if diary is None:
        raise HTTPException(status_code=404, detail="Diary not found.")
    db.execute(delete(DiaryComment).where(DiaryComment.diary_id == diary_id))
    db.execute(delete(DiaryRating).where(DiaryRating.diary_id == diary_id))
    db.execute(delete(DiaryMedia).where(DiaryMedia.diary_id == diary_id))
    db.execute(delete(DiaryTitleIndex).where(DiaryTitleIndex.diary_id == diary_id))
    db.execute(delete(DiarySearchToken).where(DiarySearchToken.diary_id == diary_id))
    db.delete(diary)
    db.commit()
    return {
        "deleted": True,
        "diary_id": diary_id,
        "algorithm_trace": {
            "stage": "stage-25-admin-moderation",
            "effect": "diary and related comments/ratings/media/search indexes deleted",
        },
    }


@router.patch("/destinations/{destination_id}")
def admin_update_destination(destination_id: int, payload: DestinationAdminUpdate, db: Session = Depends(get_db)) -> dict:
    destination = db.scalar(
        select(Destination)
        .options(selectinload(Destination.tags))
        .where(Destination.id == destination_id)
    )
    if destination is None:
        raise HTTPException(status_code=404, detail="Destination not found.")
    if payload.name is not None:
        destination.name = payload.name
    if payload.category is not None:
        destination.category = payload.category
    if payload.description is not None:
        destination.description = payload.description
    if payload.rating is not None:
        destination.rating = payload.rating
    if payload.popularity is not None:
        destination.popularity = payload.popularity
    if payload.tags is not None:
        db.execute(delete(DestinationTag).where(DestinationTag.destination_id == destination_id))
        for tag in _normalize_tags(payload.tags):
            db.add(DestinationTag(destination_id=destination_id, tag=tag))
    db.commit()
    destination = db.scalar(
        select(Destination)
        .options(selectinload(Destination.tags))
        .where(Destination.id == destination_id)
    )
    if destination is None:
        raise HTTPException(status_code=404, detail="Destination not found.")
    return {
        **serialize_destination(destination),
        "algorithm_trace": {
            "stage": "stage-25-admin-moderation",
            "effect": "destination updated",
        },
    }


@router.patch("/facilities/{facility_id}")
def admin_update_facility(facility_id: int, payload: FacilityAdminUpdate, db: Session = Depends(get_db)) -> dict:
    facility = db.scalar(
        select(Facility)
        .options(selectinload(Facility.category))
        .where(Facility.id == facility_id)
    )
    if facility is None:
        raise HTTPException(status_code=404, detail="Facility not found.")
    if payload.category_code is not None:
        category = db.scalar(select(FacilityCategory).where(FacilityCategory.code == payload.category_code))
        if category is None:
            raise HTTPException(status_code=404, detail="Facility category not found.")
        facility.category_id = category.id
    if payload.name is not None:
        facility.name = payload.name
    if payload.description is not None:
        facility.description = payload.description
    if payload.lng is not None:
        facility.lng = payload.lng
    if payload.lat is not None:
        facility.lat = payload.lat
    db.commit()
    facility = db.scalar(
        select(Facility)
        .options(selectinload(Facility.category))
        .where(Facility.id == facility_id)
    )
    if facility is None:
        raise HTTPException(status_code=404, detail="Facility not found.")
    return {
        **_serialize_facility(facility),
        "algorithm_trace": {
            "stage": "stage-25-admin-moderation",
            "effect": "facility updated",
        },
    }


@router.patch("/foods/{food_id}")
def admin_update_food(food_id: int, payload: FoodAdminUpdate, db: Session = Depends(get_db)) -> dict:
    food = db.scalar(
        select(Food)
        .options(selectinload(Food.restaurant))
        .where(Food.id == food_id)
    )
    if food is None:
        raise HTTPException(status_code=404, detail="Food not found.")
    if payload.name is not None:
        food.name = payload.name
    if payload.cuisine is not None:
        food.cuisine = payload.cuisine
    if payload.price is not None:
        food.price = payload.price
    if payload.rating is not None:
        food.rating = payload.rating
    if payload.heat is not None:
        food.heat = payload.heat
    db.commit()
    db.refresh(food)
    return {
        **serialize_food(food),
        "algorithm_trace": {
            "stage": "stage-25-admin-moderation",
            "effect": "food updated",
        },
    }


def _count(db: Session, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _normalize_tags(tags: list[str]) -> list[str]:
    normalized = []
    for tag in tags:
        value = tag.strip()
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def _serialize_facility(facility: Facility) -> dict:
    return {
        "id": facility.id,
        "name": facility.name,
        "category": facility.category.code,
        "category_name": facility.category.name,
        "lng": facility.lng,
        "lat": facility.lat,
        "description": facility.description,
        "nearest_node_id": facility.nearest_node_id,
    }
