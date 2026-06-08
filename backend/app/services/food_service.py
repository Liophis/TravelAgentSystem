from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.algorithms.ranking import top_k_smallest, top_k_smallest_tuple
from app.algorithms.route_planning import RouteNotFoundError, approximate_distance_meters
from app.core.config import settings
from app.models import Destination, Food, Restaurant, UserInterest
from app.seed.sample_data import BUPT_SHAHE_CENTER
from app.services.route_service import plan_route_from_db


DESTINATION_FOOD_SCOPE_METERS = 1500


def list_restaurants_from_db(
    session: Session,
    destination_id: int | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    destination = _load_destination(session, destination_id)
    restaurants = _filter_restaurants_by_destination(_load_restaurants(session), destination)
    items = restaurants[offset : offset + limit]
    return {
        "items": [serialize_restaurant(restaurant) for restaurant in items],
        "total": len(restaurants),
        "destination_id": destination_id,
        "limit": limit,
        "offset": offset,
        "algorithm_trace": {
            "stage": "stage-9-food-aigc-admin",
            "source": "restaurants table with AMap real POI rows and seed fallback rows",
            "returned": str(len(items)),
        },
    }


def list_food_items_from_db(
    session: Session,
    cuisine: str | None,
    restaurant_id: int | None,
    destination_id: int | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    destination = _load_destination(session, destination_id)
    foods = _filter_foods(_load_foods(session), cuisine, restaurant_id, destination)
    items = foods[offset : offset + limit]
    return {
        "items": [serialize_food(food) for food in items],
        "total": len(foods),
        "limit": limit,
        "offset": offset,
        "destination_id": destination_id,
        "cuisines": _load_cuisines(session),
        "algorithm_trace": {
            "stage": "stage-9-food-aigc-admin",
            "filter": "cuisine, restaurant_id, and destination scope",
            "returned": str(len(items)),
        },
    }


def search_foods_from_db(
    session: Session,
    q: str,
    cuisine: str | None,
    destination_id: int | None,
    limit: int,
    sort: str = "match",
    current_lng: float | None = None,
    current_lat: float | None = None,
) -> dict[str, Any]:
    keyword = q.casefold().strip()
    destination = _load_destination(session, destination_id)
    current = _resolve_current(current_lng, current_lat, destination)
    scored = []
    for food in _filter_foods(_load_foods(session), cuisine, None, destination):
        rank = _food_match_rank(food, keyword)
        if rank is None:
            continue
        item = serialize_food(food)
        item["match_rank"] = rank
        item["distance"] = round(approximate_distance_meters(current, (food.restaurant.lng, food.restaurant.lat)))
        scored.append(item)

    resolved_sort = _normalize_food_sort(sort, allow_match=True)
    results = top_k_smallest_tuple(scored, key=lambda item: _food_search_sort_key(item, resolved_sort), k=limit)
    for item in results:
        item.pop("match_rank", None)
    return {
        "items": results,
        "total": len(scored),
        "keyword": q,
        "cuisine": cuisine,
        "destination_id": destination_id,
        "sort": resolved_sort,
        "algorithm_trace": {
            "stage": "stage-9-food-aigc-admin",
            "algorithm": "contains plus lightweight Levenshtein fuzzy search",
            "ranking": "hand-written Top-K heap by match/heat/rating/distance key, no full result sort",
            "scope": "destination-linked or nearby restaurants" if destination is not None else "all restaurants",
            "sort": resolved_sort,
            "candidate_count": str(len(scored)),
            "matched": str(len(scored)),
            "returned": str(len(results)),
            "data_source": _food_data_source_trace(results),
        },
    }


def recommend_foods_from_db(
    session: Session,
    cuisine: str | None,
    destination_id: int | None,
    user_id: int | None,
    current_lng: float | None,
    current_lat: float | None,
    limit: int,
    sort: str = "composite",
) -> dict[str, Any]:
    resolved_sort = _normalize_food_sort(sort, allow_match=False)
    destination = _load_destination(session, destination_id)
    foods = _filter_foods(_load_foods(session), cuisine, None, destination)
    interests = _load_user_interests(session, user_id)
    current = _resolve_current(current_lng, current_lat, destination)
    max_food_heat = max((food.heat for food in foods), default=1)
    max_restaurant_heat = max((food.restaurant.heat for food in foods), default=1)

    scored = [
        _score_food(food, interests, current, max_food_heat, max_restaurant_heat)
        for food in foods
    ]
    if resolved_sort == "distance":
        _attach_routes_to_items(session, scored, current)
    items = top_k_smallest_tuple(scored, key=lambda item: _food_recommend_sort_key(item, resolved_sort), k=limit)
    if resolved_sort != "distance":
        _attach_routes_to_items(session, items, current)
    return {
        "items": items,
        "total": len(foods),
        "cuisine": cuisine,
        "destination_id": destination_id,
        "user_id": user_id,
        "sort": resolved_sort,
        "algorithm_trace": {
            "stage": "stage-24-destination-scoped-food",
            "algorithm": "rating + food heat + restaurant heat + cuisine interest + distance + price scoring",
            "ranking": "hand-written Top-K heap by selected hot/rating/distance/composite key, no full candidate sort",
            "distance_metric": "graph route distance for distance sort; current/destination approximate distance for composite score",
            "scope": "destination-linked or nearby restaurants" if destination is not None else "all restaurants",
            "scope_radius_meters": str(DESTINATION_FOOD_SCOPE_METERS),
            "sort": resolved_sort,
            "candidate_count": str(len(foods)),
            "returned": str(len(items)),
            "interest_tags": ",".join(sorted(interests)) if interests else "",
            "data_source": _food_data_source_trace(items),
        },
    }


def nearby_foods_from_db(
    session: Session,
    current_lng: float | None,
    current_lat: float | None,
    cuisine: str | None,
    destination_id: int | None,
    radius: int,
    limit: int,
) -> dict[str, Any]:
    destination = _load_destination(session, destination_id)
    current = _resolve_current(current_lng, current_lat, destination)
    enriched = []
    for food in _filter_foods(_load_foods(session), cuisine, None, destination):
        route = _route_to_restaurant(session, current, food.restaurant)
        if route["distance"] > radius:
            continue
        item = serialize_food(food)
        item.update(route)
        enriched.append(item)

    items = top_k_smallest(enriched, key=lambda item: float(item["distance"]), k=limit)
    return {
        "items": items,
        "total": len(enriched),
        "radius": radius,
        "cuisine": cuisine,
        "destination_id": destination_id,
        "algorithm_trace": {
            "stage": "stage-24-destination-scoped-food",
            "distance": "route planner graph distance with straight-line fallback",
            "scope": "destination-linked or nearby restaurants" if destination is not None else "all restaurants",
            "ranking": "Top-K heap by route distance",
            "returned": str(len(items)),
            "data_source": _food_data_source_trace(items),
        },
    }


def serialize_restaurant(restaurant: Restaurant) -> dict[str, Any]:
    cuisines = sorted({food.cuisine for food in restaurant.foods})
    return {
        "id": restaurant.id,
        "destination_id": restaurant.destination_id,
        "name": restaurant.name,
        "lng": restaurant.lng,
        "lat": restaurant.lat,
        "heat": restaurant.heat,
        "source": restaurant.source,
        "external_id": restaurant.external_id,
        "address": restaurant.address,
        "category": restaurant.category,
        "food_count": len(restaurant.foods),
        "cuisines": cuisines,
    }


def serialize_food(food: Food) -> dict[str, Any]:
    return {
        "id": food.id,
        "restaurant_id": food.restaurant_id,
        "restaurant_destination_id": food.restaurant.destination_id,
        "restaurant_name": food.restaurant.name,
        "restaurant_lng": food.restaurant.lng,
        "restaurant_lat": food.restaurant.lat,
        "restaurant_heat": food.restaurant.heat,
        "restaurant_source": food.restaurant.source,
        "restaurant_external_id": food.restaurant.external_id,
        "restaurant_address": food.restaurant.address,
        "restaurant_category": food.restaurant.category,
        "name": food.name,
        "cuisine": food.cuisine,
        "price": food.price,
        "rating": food.rating,
        "heat": food.heat,
    }


def _load_restaurants(session: Session) -> list[Restaurant]:
    return list(
        session.scalars(
            select(Restaurant)
            .options(selectinload(Restaurant.foods))
            .order_by(Restaurant.id)
        ).all()
    )


def _load_foods(session: Session) -> list[Food]:
    return list(
        session.scalars(
            select(Food)
            .options(selectinload(Food.restaurant))
            .order_by(Food.id)
        ).all()
    )


def _load_cuisines(session: Session) -> list[str]:
    return sorted({food.cuisine for food in _load_foods(session)})


def _filter_restaurants_by_destination(restaurants: list[Restaurant], destination: Destination | None) -> list[Restaurant]:
    if destination is None:
        return restaurants
    return [
        restaurant
        for restaurant in restaurants
        if _restaurant_matches_destination(restaurant, destination)
    ]


def _filter_foods(
    foods: list[Food],
    cuisine: str | None,
    restaurant_id: int | None,
    destination: Destination | None,
) -> list[Food]:
    return [
        food
        for food in foods
        if (not cuisine or food.cuisine == cuisine)
        and (restaurant_id is None or food.restaurant_id == restaurant_id)
        and (destination is None or _restaurant_matches_destination(food.restaurant, destination))
    ]


def _restaurant_matches_destination(restaurant: Restaurant, destination: Destination) -> bool:
    if restaurant.destination_id == destination.id:
        return True
    distance = approximate_distance_meters((destination.lng, destination.lat), (restaurant.lng, restaurant.lat))
    return distance <= DESTINATION_FOOD_SCOPE_METERS


def _food_match_rank(food: Food, keyword: str) -> int | None:
    if not keyword:
        return 0
    fields = [
        food.name.casefold(),
        food.cuisine.casefold(),
        food.restaurant.name.casefold(),
        (food.restaurant.address or "").casefold(),
        (food.restaurant.category or "").casefold(),
    ]
    if any(field == keyword for field in fields):
        return 0
    if any(field.startswith(keyword) for field in fields):
        return 1
    if any(keyword in field for field in fields):
        return 2
    if any(_levenshtein(keyword, field[: max(len(keyword), 1)]) <= 2 for field in fields):
        return 3
    return None


def _food_search_sort_key(item: dict[str, Any], sort: str) -> tuple[float, ...]:
    if sort == "hot":
        return (-float(item["heat"]), -float(item["rating"]), float(item["distance"]), float(item["match_rank"]))
    if sort == "rating":
        return (-float(item["rating"]), -float(item["heat"]), float(item["distance"]), float(item["match_rank"]))
    if sort == "distance":
        return (float(item["distance"]), float(item["match_rank"]), -float(item["rating"]), -float(item["heat"]))
    return (float(item["match_rank"]), -float(item["heat"]), -float(item["rating"]), float(item["distance"]))


def _food_recommend_sort_key(item: dict[str, Any], sort: str) -> tuple[float, ...]:
    if sort == "hot":
        return (-float(item["heat"]), -float(item["rating"]), float(item["distance"]), -float(item["score"]))
    if sort == "rating":
        return (-float(item["rating"]), -float(item["heat"]), float(item["distance"]), -float(item["score"]))
    if sort == "distance":
        return (float(item["distance"]), -float(item["rating"]), -float(item["heat"]), -float(item["score"]))
    return (-float(item["score"]), -float(item["rating"]), -float(item["heat"]), float(item["distance"]))


def _normalize_food_sort(sort: str | None, allow_match: bool) -> str:
    allowed = {"hot", "rating", "distance", "composite"}
    if allow_match:
        allowed.add("match")
    normalized = str(sort).strip().casefold() if sort is not None else ""
    if normalized in allowed:
        return normalized
    return "match" if allow_match else "composite"


def _score_food(
    food: Food,
    interests: set[str],
    current: tuple[float, float],
    max_food_heat: int,
    max_restaurant_heat: int,
) -> dict[str, Any]:
    rating_score = min(food.rating / 5, 1)
    food_heat_score = food.heat / max(max_food_heat, 1)
    restaurant_heat_score = food.restaurant.heat / max(max_restaurant_heat, 1)
    cuisine_score = 1 if food.cuisine in interests or "food" in interests else 0
    distance = approximate_distance_meters(current, (food.restaurant.lng, food.restaurant.lat))
    distance_score = max(0, 1 - distance / 2500)
    price_score = max(0, 1 - food.price / 60)
    score = (
        0.30 * rating_score
        + 0.25 * food_heat_score
        + 0.15 * restaurant_heat_score
        + 0.15 * cuisine_score
        + 0.10 * distance_score
        + 0.05 * price_score
    )
    item = serialize_food(food)
    item.update(
        {
            "score": round(score, 4),
            "distance": round(distance),
            "reason": _food_reason(food, cuisine_score, distance_score),
        }
    )
    return item


def _food_reason(food: Food, cuisine_score: float, distance_score: float) -> str:
    source_prefix = "真实高德餐饮 POI，" if food.restaurant.source == "amap" else ""
    if cuisine_score > 0:
        return f"{source_prefix}匹配口味偏好，{food.cuisine}，评分 {food.rating:.1f}"
    if distance_score > 0.8:
        return f"{source_prefix}距离当前位置较近，评分 {food.rating:.1f}，热度 {food.heat}"
    return f"{source_prefix}综合热度与评分较高，评分 {food.rating:.1f}，热度 {food.heat}"


def _attach_routes_to_items(session: Session, items: list[dict[str, Any]], current: tuple[float, float]) -> None:
    for item in items:
        route = _route_to_coordinates(
            session,
            current,
            float(item["restaurant_lng"]),
            float(item["restaurant_lat"]),
            prefer_external=bool(item.get("restaurant_source") == "amap"),
        )
        item.update(route)


def _route_to_restaurant(
    session: Session,
    current: tuple[float, float],
    restaurant: Restaurant,
) -> dict[str, Any]:
    return _route_to_coordinates(
        session,
        current,
        restaurant.lng,
        restaurant.lat,
        prefer_external=restaurant.source == "amap",
    )


def _route_to_coordinates(
    session: Session,
    current: tuple[float, float],
    target_lng: float,
    target_lat: float,
    prefer_external: bool = False,
) -> dict[str, Any]:
    if prefer_external and not settings.amap_web_api_key:
        return _fallback_coordinate_route(current, target_lng, target_lat)
    try:
        route = plan_route_from_db(
            session,
            {
                "start_lng": current[0],
                "start_lat": current[1],
                "end_lng": target_lng,
                "end_lat": target_lat,
                "strategy": "shortest_distance",
                "mode": "walk",
                "route_source": "amap_walking" if prefer_external else "local_graph",
            },
        )
        route_path = route["path"]
        if len(route_path) < 2:
            route_path = [[current[0], current[1]], [target_lng, target_lat]]
        return {
            "distance": route["distance"],
            "duration": route["duration"],
            "routePath": route_path,
            "node_ids": route["node_ids"],
        }
    except RouteNotFoundError:
        return _fallback_coordinate_route(current, target_lng, target_lat)


def _fallback_coordinate_route(
    current: tuple[float, float],
    target_lng: float,
    target_lat: float,
) -> dict[str, Any]:
    distance = approximate_distance_meters(current, (target_lng, target_lat))
    return {
        "distance": round(distance),
        "duration": round(distance / 1.2),
        "routePath": [[current[0], current[1]], [target_lng, target_lat]],
        "node_ids": [],
    }


def _food_data_source_trace(items: list[dict[str, Any]]) -> str:
    if any(item.get("restaurant_source") == "amap" for item in items):
        return "includes real AMap Place Around restaurant POIs"
    return "seed fallback restaurant data"


def _load_destination(session: Session, destination_id: int | None) -> Destination | None:
    if destination_id is None:
        return None
    return session.get(Destination, destination_id)


def _resolve_current(
    current_lng: float | None,
    current_lat: float | None,
    destination: Destination | None,
) -> tuple[float, float]:
    if current_lng is None and current_lat is None and destination is not None:
        return (destination.lng, destination.lat)
    return (
        current_lng if current_lng is not None else BUPT_SHAHE_CENTER[0],
        current_lat if current_lat is not None else BUPT_SHAHE_CENTER[1],
    )


def _load_user_interests(session: Session, user_id: int | None) -> set[str]:
    if user_id is None:
        return set()
    return {
        interest.tag
        for interest in session.scalars(select(UserInterest).where(UserInterest.user_id == user_id)).all()
    }


def _levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for index, left_char in enumerate(left, start=1):
        current = [index]
        for right_index, right_char in enumerate(right, start=1):
            insert_cost = current[right_index - 1] + 1
            delete_cost = previous[right_index] + 1
            replace_cost = previous[right_index - 1] + (left_char != right_char)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]
