from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.algorithms.ranking import top_k_smallest
from app.algorithms.route_planning import RouteNotFoundError, approximate_distance_meters
from app.models import Food, Restaurant, UserInterest
from app.seed.sample_data import BUPT_SHAHE_CENTER
from app.services.route_service import plan_route_from_db


def list_restaurants_from_db(session: Session, limit: int, offset: int) -> dict[str, Any]:
    restaurants = _load_restaurants(session)
    items = restaurants[offset : offset + limit]
    return {
        "items": [serialize_restaurant(restaurant) for restaurant in items],
        "total": len(restaurants),
        "limit": limit,
        "offset": offset,
        "algorithm_trace": {
            "stage": "stage-9-food-aigc-admin",
            "source": "restaurants seeded database",
            "returned": str(len(items)),
        },
    }


def list_food_items_from_db(
    session: Session,
    cuisine: str | None,
    restaurant_id: int | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    foods = _filter_foods(_load_foods(session), cuisine, restaurant_id)
    items = foods[offset : offset + limit]
    return {
        "items": [serialize_food(food) for food in items],
        "total": len(foods),
        "limit": limit,
        "offset": offset,
        "cuisines": _load_cuisines(session),
        "algorithm_trace": {
            "stage": "stage-9-food-aigc-admin",
            "filter": "cuisine and restaurant_id",
            "returned": str(len(items)),
        },
    }


def search_foods_from_db(
    session: Session,
    q: str,
    cuisine: str | None,
    limit: int,
    sort: str = "match",
    current_lng: float | None = None,
    current_lat: float | None = None,
) -> dict[str, Any]:
    keyword = q.casefold().strip()
    current = _resolve_current(current_lng, current_lat)
    scored = []
    for food in _filter_foods(_load_foods(session), cuisine, None):
        rank = _food_match_rank(food, keyword)
        if rank is None:
            continue
        item = serialize_food(food)
        item["match_rank"] = rank
        item["distance"] = round(approximate_distance_meters(current, (food.restaurant.lng, food.restaurant.lat)))
        scored.append(item)

    results = sorted(scored, key=lambda item: _food_search_sort_key(item, sort))[:limit]
    for item in results:
        item.pop("match_rank", None)
    return {
        "items": results,
        "total": len(scored),
        "keyword": q,
        "cuisine": cuisine,
        "sort": sort,
        "algorithm_trace": {
            "stage": "stage-9-food-aigc-admin",
            "algorithm": "contains plus lightweight Levenshtein fuzzy search",
            "sort": sort,
            "matched": str(len(scored)),
            "returned": str(len(results)),
        },
    }


def recommend_foods_from_db(
    session: Session,
    cuisine: str | None,
    user_id: int | None,
    current_lng: float | None,
    current_lat: float | None,
    limit: int,
) -> dict[str, Any]:
    foods = _filter_foods(_load_foods(session), cuisine, None)
    interests = _load_user_interests(session, user_id)
    current = _resolve_current(current_lng, current_lat)
    max_food_heat = max((food.heat for food in foods), default=1)
    max_restaurant_heat = max((food.restaurant.heat for food in foods), default=1)

    scored = [
        _score_food(food, interests, current, max_food_heat, max_restaurant_heat)
        for food in foods
    ]
    items = top_k_smallest(scored, key=lambda item: -float(item["score"]), k=limit)
    return {
        "items": items,
        "total": len(foods),
        "cuisine": cuisine,
        "user_id": user_id,
        "algorithm_trace": {
            "stage": "stage-9-food-aigc-admin",
            "algorithm": "rating + food heat + restaurant heat + cuisine interest + distance + price scoring, Top-K heap",
            "returned": str(len(items)),
            "interest_tags": ",".join(sorted(interests)) if interests else "",
        },
    }


def nearby_foods_from_db(
    session: Session,
    current_lng: float | None,
    current_lat: float | None,
    cuisine: str | None,
    radius: int,
    limit: int,
) -> dict[str, Any]:
    current = _resolve_current(current_lng, current_lat)
    enriched = []
    for food in _filter_foods(_load_foods(session), cuisine, None):
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
        "algorithm_trace": {
            "stage": "stage-9-food-aigc-admin",
            "distance": "route planner graph distance with straight-line fallback",
            "ranking": "Top-K heap by route distance",
            "returned": str(len(items)),
        },
    }


def serialize_restaurant(restaurant: Restaurant) -> dict[str, Any]:
    cuisines = sorted({food.cuisine for food in restaurant.foods})
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "lng": restaurant.lng,
        "lat": restaurant.lat,
        "heat": restaurant.heat,
        "food_count": len(restaurant.foods),
        "cuisines": cuisines,
    }


def serialize_food(food: Food) -> dict[str, Any]:
    return {
        "id": food.id,
        "restaurant_id": food.restaurant_id,
        "restaurant_name": food.restaurant.name,
        "restaurant_lng": food.restaurant.lng,
        "restaurant_lat": food.restaurant.lat,
        "restaurant_heat": food.restaurant.heat,
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


def _filter_foods(foods: list[Food], cuisine: str | None, restaurant_id: int | None) -> list[Food]:
    return [
        food
        for food in foods
        if (not cuisine or food.cuisine == cuisine)
        and (restaurant_id is None or food.restaurant_id == restaurant_id)
    ]


def _food_match_rank(food: Food, keyword: str) -> int | None:
    if not keyword:
        return 0
    fields = [
        food.name.casefold(),
        food.cuisine.casefold(),
        food.restaurant.name.casefold(),
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
    if cuisine_score > 0:
        return f"匹配口味偏好，{food.cuisine}，评分 {food.rating:.1f}"
    if distance_score > 0.8:
        return f"距离当前位置较近，评分 {food.rating:.1f}，热度 {food.heat}"
    return f"综合热度与评分较高，评分 {food.rating:.1f}，热度 {food.heat}"


def _route_to_restaurant(
    session: Session,
    current: tuple[float, float],
    restaurant: Restaurant,
) -> dict[str, Any]:
    try:
        route = plan_route_from_db(
            session,
            {
                "start_lng": current[0],
                "start_lat": current[1],
                "end_lng": restaurant.lng,
                "end_lat": restaurant.lat,
                "strategy": "shortest_distance",
                "mode": "walk",
                "route_source": "local_graph",
            },
        )
        route_path = route["path"]
        if len(route_path) < 2:
            route_path = [[current[0], current[1]], [restaurant.lng, restaurant.lat]]
        return {
            "distance": route["distance"],
            "duration": route["duration"],
            "routePath": route_path,
            "node_ids": route["node_ids"],
        }
    except RouteNotFoundError:
        distance = approximate_distance_meters(current, (restaurant.lng, restaurant.lat))
        return {
            "distance": round(distance),
            "duration": round(distance / 1.2),
            "routePath": [[current[0], current[1]], [restaurant.lng, restaurant.lat]],
            "node_ids": [],
        }


def _resolve_current(current_lng: float | None, current_lat: float | None) -> tuple[float, float]:
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
