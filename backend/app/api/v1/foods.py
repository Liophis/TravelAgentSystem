from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.amap_poi_service import search_foods_at_location, AmapPoiError
from app.services.food_service import (
    list_food_items_from_db,
    list_restaurants_from_db,
    nearby_foods_from_db,
    recommend_foods_from_db,
    search_foods_from_db,
)

router = APIRouter()


@router.get("/restaurants")
def list_restaurants(
    destination_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    return list_restaurants_from_db(db, destination_id=destination_id, limit=limit, offset=offset)


@router.get("/items")
def list_food_items(
    cuisine: str | None = Query(default=None),
    restaurant_id: int | None = Query(default=None),
    destination_id: int | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    return list_food_items_from_db(
        session=db,
        cuisine=cuisine,
        restaurant_id=restaurant_id,
        destination_id=destination_id,
        limit=limit,
        offset=offset,
    )


@router.get("/search")
def search_foods(
    q: str = Query(min_length=1),
    cuisine: str | None = Query(default=None),
    destination_id: int | None = Query(default=None),
    sort: str = Query(default="match"),
    current_lng: float | None = Query(default=None),
    current_lat: float | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict:
    return search_foods_from_db(
        db,
        q=q,
        cuisine=cuisine,
        destination_id=destination_id,
        sort=sort,
        current_lng=current_lng,
        current_lat=current_lat,
        limit=limit,
    )


@router.get("/recommend")
def recommend_foods(
    cuisine: str | None = Query(default=None),
    destination_id: int | None = Query(default=None),
    user_id: int | None = Query(default=1),
    current_lng: float | None = Query(default=None),
    current_lat: float | None = Query(default=None),
    sort: str = Query(default="composite"),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict:
    return recommend_foods_from_db(
        session=db,
        cuisine=cuisine,
        destination_id=destination_id,
        user_id=user_id,
        current_lng=current_lng,
        current_lat=current_lat,
        sort=sort,
        limit=limit,
    )


@router.get("/nearby")
def nearby_foods(
    cuisine: str | None = Query(default=None),
    destination_id: int | None = Query(default=None),
    current_lng: float | None = Query(default=None),
    current_lat: float | None = Query(default=None),
    radius: int = Query(default=1000, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict:
    return nearby_foods_from_db(
        session=db,
        current_lng=current_lng,
        current_lat=current_lat,
        cuisine=cuisine,
        destination_id=destination_id,
        radius=radius,
        limit=limit,
    )


@router.get("/realtime")
async def realtime_foods(
    current_lng: float = Query(..., description="当前经度"),
    current_lat: float = Query(..., description="当前纬度"),
    cuisine: str | None = Query(default=None, description="菜系筛选"),
    radius: int = Query(default=3000, ge=1, le=50000, description="搜索半径(米)"),
    limit: int = Query(default=20, ge=1, le=50, description="返回数量"),
) -> dict:
    """
    实时全国美食搜索 - 使用高德地图API

    支持全国任意位置的美食搜索，不依赖本地数据库
    """
    try:
        result = await search_foods_at_location(
            lng=current_lng,
            lat=current_lat,
            cuisine=cuisine,
            radius=radius,
            limit=limit,
        )
        return result
    except AmapPoiError as e:
        return {
            "items": [],
            "total": 0,
            "error": str(e),
            "center": {"lng": current_lng, "lat": current_lat},
            "source": "error",
        }
    except Exception as e:
        return {
            "items": [],
            "total": 0,
            "error": f"搜索失败: {str(e)}",
            "center": {"lng": current_lng, "lat": current_lat},
            "source": "error",
        }
