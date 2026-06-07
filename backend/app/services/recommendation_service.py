from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.algorithms.ranking import top_k_smallest
from app.algorithms.route_planning import approximate_distance_meters
from app.models import Destination, UserInterest
from app.seed.sample_data import BUPT_SHAHE_CENTER
from app.services.destination_service import serialize_destination


def recommend_destinations_from_db(
    session: Session,
    user_id: int | None,
    strategy: str,
    limit: int,
    current_lng: float | None,
    current_lat: float | None,
) -> dict[str, Any]:
    destinations = list(
        session.scalars(
            select(Destination)
            .options(selectinload(Destination.tags))
            .order_by(Destination.id)
        ).all()
    )
    interests = _load_user_interests(session, user_id)
    max_popularity = max((destination.popularity for destination in destinations), default=1)
    current = (
        current_lng if current_lng is not None else BUPT_SHAHE_CENTER[0],
        current_lat if current_lat is not None else BUPT_SHAHE_CENTER[1],
    )

    scored = [
        _score_destination(destination, interests, max_popularity, current, strategy)
        for destination in destinations
    ]
    top_items = top_k_smallest(scored, key=lambda item: -float(item["score"]), k=limit)
    return {
        "items": top_items,
        "total": len(destinations),
        "strategy": strategy,
        "user_id": user_id,
        "algorithm_trace": {
            "stage": "stage-6-destination-search-recommend",
            "algorithm": "rule scoring plus Top-K heap",
            "formula": "rating 0.30 + popularity 0.25 + interest 0.25 + distance 0.10 + freshness 0.10",
            "candidates": str(len(destinations)),
            "returned": str(len(top_items)),
            "interest_tags": ",".join(sorted(interests)) if interests else "",
        },
    }


def _load_user_interests(session: Session, user_id: int | None) -> set[str]:
    if user_id is None:
        return set()
    return {
        interest.tag
        for interest in session.scalars(select(UserInterest).where(UserInterest.user_id == user_id)).all()
    }


def _score_destination(
    destination: Destination,
    interests: set[str],
    max_popularity: int,
    current: tuple[float, float],
    strategy: str,
) -> dict[str, Any]:
    tags = {tag.tag for tag in destination.tags}
    rating_score = min(destination.rating / 5, 1)
    popularity_score = destination.popularity / max(max_popularity, 1)
    interest_score = len(tags & interests) / max(len(interests), 1) if interests else 0
    distance = approximate_distance_meters(current, (destination.lng, destination.lat))
    distance_score = max(0, 1 - distance / 2500)
    freshness_score = min(destination.id / 200, 1)

    if strategy == "rating":
        score = rating_score
    elif strategy == "hot":
        score = popularity_score
    elif strategy == "interest":
        score = 0.7 * interest_score + 0.2 * rating_score + 0.1 * popularity_score
    else:
        score = (
            0.30 * rating_score
            + 0.25 * popularity_score
            + 0.25 * interest_score
            + 0.10 * distance_score
            + 0.10 * freshness_score
        )

    item = serialize_destination(destination)
    item.update(
        {
            "score": round(score, 4),
            "reason": _build_reason(
                rating_score=rating_score,
                popularity_score=popularity_score,
                interest_score=interest_score,
                distance_score=distance_score,
                strategy=strategy,
            ),
        }
    )
    return item


def _build_reason(
    rating_score: float,
    popularity_score: float,
    interest_score: float,
    distance_score: float,
    strategy: str,
) -> str:
    if strategy == "rating":
        return f"评分表现突出，评分因子 {rating_score:.2f}"
    if strategy == "hot":
        return f"热度表现突出，热度因子 {popularity_score:.2f}"
    if interest_score > 0:
        return f"匹配用户兴趣，兴趣因子 {interest_score:.2f}"
    if distance_score > 0.8:
        return f"距离当前位置较近，距离因子 {distance_score:.2f}"
    return f"综合评分较高，评分 {rating_score:.2f}，热度 {popularity_score:.2f}"
