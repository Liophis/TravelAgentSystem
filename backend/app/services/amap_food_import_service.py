from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.algorithms.coordinates import gcj02_to_wgs84
from app.algorithms.route_planning import approximate_distance_meters
from app.models import Destination, Food, Restaurant
from app.services.amap_import_service import AMapPoiImportError, fetch_amap_pois


AMAP_FOOD_KEYWORDS = [
    "餐厅",
    "饭店",
    "美食",
    "小吃",
    "咖啡",
    "快餐",
    "中餐",
    "火锅",
    "面馆",
    "茶饮",
]


def fetch_amap_food_pois(
    api_key: str,
    center_lng: float,
    center_lat: float,
    radius: int,
    keywords: list[str] | None = None,
    max_pages: int = 3,
    request_interval: float = 0.3,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pois, trace = fetch_amap_pois(
        api_key=api_key,
        center_lng=center_lng,
        center_lat=center_lat,
        radius=radius,
        keywords=keywords or AMAP_FOOD_KEYWORDS,
        max_pages=max_pages,
        request_interval=request_interval,
    )
    trace["dataset"] = "destination_food"
    return pois, trace


def import_amap_foods_to_db(
    session: Session,
    api_key: str,
    destination_id: int,
    center_lng: float | None = None,
    center_lat: float | None = None,
    radius: int = 3000,
    keywords: list[str] | None = None,
    max_pages: int = 3,
    request_interval: float = 0.3,
    reset_destination: bool = False,
) -> dict[str, Any]:
    destination = _load_destination(session, destination_id)
    resolved_center_lng = center_lng if center_lng is not None else destination.lng
    resolved_center_lat = center_lat if center_lat is not None else destination.lat
    pois, fetch_trace = fetch_amap_food_pois(
        api_key=api_key,
        center_lng=resolved_center_lng,
        center_lat=resolved_center_lat,
        radius=radius,
        keywords=keywords,
        max_pages=max_pages,
        request_interval=request_interval,
    )
    return import_amap_food_items_to_db(
        session=session,
        pois=pois,
        destination_id=destination_id,
        center_lng=resolved_center_lng,
        center_lat=resolved_center_lat,
        radius=radius,
        reset_destination=reset_destination,
        fetch_trace=fetch_trace,
    )


def import_amap_food_items_to_db(
    session: Session,
    pois: list[dict[str, Any]],
    destination_id: int,
    center_lng: float | None = None,
    center_lat: float | None = None,
    radius: int = 3000,
    reset_destination: bool = False,
    fetch_trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    destination = _load_destination(session, destination_id)
    resolved_center_lng = center_lng if center_lng is not None else destination.lng
    resolved_center_lat = center_lat if center_lat is not None else destination.lat

    if reset_destination:
        restaurant_ids = select(Restaurant.id).where(
            Restaurant.destination_id == destination_id,
            Restaurant.source == "amap",
        )
        session.execute(delete(Food).where(Food.restaurant_id.in_(restaurant_ids)))
        session.execute(
            delete(Restaurant).where(
                Restaurant.destination_id == destination_id,
                Restaurant.source == "amap",
            )
        )
        session.flush()

    existing_restaurants = list(
        session.scalars(
            select(Restaurant)
            .options(selectinload(Restaurant.foods))
            .where(Restaurant.destination_id == destination_id)
        ).all()
    )
    existing_by_external_id = {
        restaurant.external_id: restaurant
        for restaurant in existing_restaurants
        if restaurant.source == "amap" and restaurant.external_id
    }
    existing_by_signature = {
        _restaurant_signature(restaurant.name, restaurant.lng, restaurant.lat): restaurant
        for restaurant in existing_restaurants
    }

    seen_external_ids: set[str] = set()
    imported = 0
    updated = 0
    skipped = 0

    for poi in pois:
        normalized = _normalize_amap_food_poi(poi)
        if normalized is None:
            skipped += 1
            continue
        if normalized["amap_id"] and normalized["amap_id"] in seen_external_ids:
            skipped += 1
            continue
        seen_external_ids.add(normalized["amap_id"])

        distance = approximate_distance_meters(
            (resolved_center_lng, resolved_center_lat),
            (normalized["lng"], normalized["lat"]),
        )
        if distance > radius + 150:
            skipped += 1
            continue

        restaurant = None
        if normalized["amap_id"]:
            restaurant = existing_by_external_id.get(normalized["amap_id"])
        signature = _restaurant_signature(normalized["name"], normalized["lng"], normalized["lat"])
        if restaurant is None:
            restaurant = existing_by_signature.get(signature)

        rating = normalized["rating"] if normalized["rating"] is not None else _fallback_rating(distance, radius)
        price = normalized["cost"] if normalized["cost"] is not None else _fallback_price(normalized["cuisine"])
        heat = _derive_heat(rating, distance, radius)

        if restaurant is None:
            restaurant = Restaurant(
                destination_id=destination_id,
                name=normalized["name"],
                lng=normalized["lng"],
                lat=normalized["lat"],
                heat=heat,
                source="amap",
                external_id=normalized["amap_id"] or None,
                address=normalized["address"] or None,
                category=normalized["type"] or normalized["query_keyword"] or None,
            )
            session.add(restaurant)
            session.flush()
            food = Food(
                restaurant_id=restaurant.id,
                name="餐厅推荐",
                cuisine=normalized["cuisine"],
                price=price,
                rating=rating,
                heat=heat,
            )
            session.add(food)
            imported += 1
        else:
            restaurant.destination_id = destination_id
            restaurant.name = normalized["name"]
            restaurant.lng = normalized["lng"]
            restaurant.lat = normalized["lat"]
            restaurant.heat = heat
            restaurant.source = "amap"
            restaurant.external_id = normalized["amap_id"] or restaurant.external_id
            restaurant.address = normalized["address"] or restaurant.address
            restaurant.category = normalized["type"] or restaurant.category
            if restaurant.foods:
                food = restaurant.foods[0]
                food.name = "餐厅推荐"
                food.cuisine = normalized["cuisine"]
                food.price = price
                food.rating = rating
                food.heat = heat
            else:
                session.add(
                    Food(
                        restaurant_id=restaurant.id,
                        name="餐厅推荐",
                        cuisine=normalized["cuisine"],
                        price=price,
                        rating=rating,
                        heat=heat,
                    )
                )
            updated += 1

    session.commit()
    return {
        "source": "amap-place-around-food",
        "destination_id": destination_id,
        "destination_name": destination.name,
        "center": [resolved_center_lng, resolved_center_lat],
        "radius": radius,
        "raw_pois": len(pois),
        "restaurants_imported": imported,
        "restaurants_updated": updated,
        "restaurants_skipped": skipped,
        "reset_destination": reset_destination,
        "algorithm_trace": {
            "stage": "stage-37-real-food-poi",
            "pipeline": "AMap Place Around food POI -> GCJ-02 to WGS84 -> destination binding -> restaurant/food upsert",
            "dedup": "AMap id plus normalized name and rounded coordinate",
            "rating": "AMap biz_ext.rating when provided; deterministic fallback otherwise",
            "heat": "derived local ranking signal because AMap Place Around does not expose public heat",
            "fetch": fetch_trace or {},
        },
    }


def _load_destination(session: Session, destination_id: int) -> Destination:
    destination = session.get(Destination, destination_id)
    if destination is None:
        raise AMapPoiImportError(f"Destination {destination_id} was not found.")
    return destination


def _normalize_amap_food_poi(poi: dict[str, Any]) -> dict[str, Any] | None:
    name = str(poi.get("name") or "").strip()
    location = str(poi.get("location") or "").strip()
    if not name or "," not in location:
        return None
    try:
        gcj_lng, gcj_lat = [float(item) for item in location.split(",", maxsplit=1)]
    except ValueError:
        return None
    lng, lat = gcj02_to_wgs84(gcj_lng, gcj_lat)
    poi_type = str(poi.get("type") or "")
    query_keyword = str(poi.get("_query_keyword") or "")
    biz_ext = poi.get("biz_ext") if isinstance(poi.get("biz_ext"), dict) else {}
    return {
        "amap_id": str(poi.get("id") or ""),
        "name": name,
        "lng": lng,
        "lat": lat,
        "gcj_lng": gcj_lng,
        "gcj_lat": gcj_lat,
        "type": poi_type,
        "typecode": str(poi.get("typecode") or ""),
        "address": _stringify_address(poi.get("address")),
        "query_keyword": query_keyword,
        "cuisine": _classify_cuisine(f"{name} {poi_type} {query_keyword}"),
        "rating": _parse_rating(biz_ext.get("rating")),
        "cost": _parse_cost(biz_ext.get("cost")),
    }


def _classify_cuisine(text: str) -> str:
    lowered = text.casefold()
    rules = [
        ("咖啡茶饮", ["咖啡", "茶饮", "奶茶", "饮品", "甜品"]),
        ("小吃快餐", ["小吃", "快餐", "麦当劳", "肯德基", "汉堡", "炸鸡"]),
        ("面食粉类", ["面馆", "拉面", "面", "粉", "米线"]),
        ("火锅烧烤", ["火锅", "烧烤", "烤肉", "串"]),
        ("清真", ["清真", " halal"]),
        ("西餐", ["西餐", "披萨", "pizza", "牛排"]),
        ("地方菜", ["北京菜", "川菜", "湘菜", "粤菜", "东北菜", "地方菜"]),
    ]
    for cuisine, tokens in rules:
        if any(token in lowered for token in tokens):
            return cuisine
    return "中餐"


def _parse_rating(value: Any) -> float | None:
    parsed = _parse_float(value)
    if parsed is None or parsed <= 0:
        return None
    return round(max(1.0, min(parsed, 5.0)), 1)


def _parse_cost(value: Any) -> float | None:
    parsed = _parse_float(value)
    if parsed is None or parsed <= 0:
        return None
    return round(parsed, 1)


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {"[]", "{}"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _fallback_rating(distance: float, radius: int) -> float:
    distance_factor = max(0, 1 - distance / max(radius, 1))
    return round(4.0 + 0.4 * distance_factor, 1)


def _fallback_price(cuisine: str) -> float:
    return {
        "咖啡茶饮": 28.0,
        "小吃快餐": 32.0,
        "面食粉类": 30.0,
        "火锅烧烤": 85.0,
        "西餐": 95.0,
    }.get(cuisine, 55.0)


def _derive_heat(rating: float, distance: float, radius: int) -> int:
    distance_score = max(0, 1 - distance / max(radius, 1))
    return round(rating * 120 + distance_score * 80)


def _restaurant_signature(name: str, lng: float, lat: float) -> tuple[str, float, float]:
    return (name.strip().casefold(), round(lng, 5), round(lat, 5))


def _stringify_address(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value if item)
    return str(value or "")
