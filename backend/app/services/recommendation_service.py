from typing import Any
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.algorithms.ranking import top_k_smallest
from app.algorithms.route_planning import approximate_distance_meters
from app.models import Destination, UserBehaviorLog, UserFavorite, UserInterest, UserRating
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
    feedback = _load_user_feedback(session, user_id)
    max_popularity = max((destination.popularity for destination in destinations), default=1)
    current = (
        (current_lng, current_lat)
        if current_lng is not None and current_lat is not None
        else None
    )

    scored = [
        _score_destination(destination, interests, feedback, max_popularity, current, strategy)
        for destination in destinations
    ]
    top_items = top_k_smallest(scored, key=lambda item: -float(item["score"]), k=limit)
    return {
        "items": top_items,
        "total": len(destinations),
        "strategy": strategy,
        "user_id": user_id,
        "algorithm_trace": {
            "stage": "stage-23-user-feedback-loop",
            "algorithm": "rule scoring plus Top-K heap",
            "formula": "rating 0.28 + popularity 0.22 + interest 0.20 + behavior 0.12 + distance 0.10 + freshness 0.08",
            "candidate_scope": "real China attractions and schools from destinations table",
            "candidates": str(len(destinations)),
            "returned": str(len(top_items)),
            "interest_tags": ",".join(sorted(interests)) if interests else "",
            "behavior_tags": ",".join(sorted(feedback["tags"])) if feedback["tags"] else "",
            "behavior_targets": str(len(feedback["target_ids"])),
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
    feedback: dict[str, Any],
    max_popularity: int,
    current: tuple[float, float] | None,
    strategy: str,
) -> dict[str, Any]:
    tags = {tag.tag for tag in destination.tags}
    rating_score = min(destination.rating / 5, 1)
    popularity_score = destination.popularity / max(max_popularity, 1)
    interest_score = len(tags & interests) / max(len(interests), 1) if interests else 0
    behavior_score = _behavior_score(destination, tags, feedback)
    distance = approximate_distance_meters(current, (destination.lng, destination.lat)) if current else None
    distance_score = max(0, 1 - distance / 200000) if distance is not None else 0.5
    freshness_score = min(destination.id / 200, 1)

    if strategy == "rating":
        score = rating_score
    elif strategy == "hot":
        score = popularity_score
    elif strategy == "interest":
        score = 0.7 * interest_score + 0.2 * rating_score + 0.1 * popularity_score
    elif strategy == "behavior":
        score = 0.7 * behavior_score + 0.2 * rating_score + 0.1 * popularity_score
    else:
        score = (
            0.28 * rating_score
            + 0.22 * popularity_score
            + 0.20 * interest_score
            + 0.12 * behavior_score
            + 0.10 * distance_score
            + 0.08 * freshness_score
        )

    item = serialize_destination(destination)
    item.update(
        {
            "score": round(score, 4),
            "behavior_score": round(behavior_score, 4),
            "reason": _build_reason(
                rating_score=rating_score,
                popularity_score=popularity_score,
                interest_score=interest_score,
                behavior_score=behavior_score,
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
    behavior_score: float,
    distance_score: float,
    strategy: str,
) -> str:
    if strategy == "rating":
        return f"评分表现突出，评分因子 {rating_score:.2f}"
    if strategy == "hot":
        return f"热度表现突出，热度因子 {popularity_score:.2f}"
    if strategy == "behavior":
        return f"由浏览、收藏、评分行为增强，行为因子 {behavior_score:.2f}"
    if behavior_score > 0.7:
        return f"匹配近期收藏、评分或浏览行为，行为因子 {behavior_score:.2f}"
    if interest_score > 0:
        return f"匹配用户兴趣，兴趣因子 {interest_score:.2f}"
    if distance_score > 0.8:
        return f"距离当前位置较近，距离因子 {distance_score:.2f}"
    return f"综合评分较高，评分 {rating_score:.2f}，热度 {popularity_score:.2f}"


def _load_user_feedback(session: Session, user_id: int | None) -> dict[str, Any]:
    if user_id is None:
        return {
            "favorite_ids": set(),
            "ratings": {},
            "behavior_counts": Counter(),
            "tags": set(),
            "target_ids": set(),
        }

    favorite_ids = {
        favorite.target_id
        for favorite in session.scalars(
            select(UserFavorite).where(
                UserFavorite.user_id == user_id,
                UserFavorite.target_type == "destination",
            )
        ).all()
    }
    ratings = {
        rating.target_id: rating.rating
        for rating in session.scalars(
            select(UserRating).where(
                UserRating.user_id == user_id,
                UserRating.target_type == "destination",
            )
        ).all()
    }
    behavior_counts: Counter[int] = Counter()
    for log in session.scalars(
        select(UserBehaviorLog).where(
            UserBehaviorLog.user_id == user_id,
            UserBehaviorLog.target_type == "destination",
        )
    ).all():
        behavior_counts[log.target_id] += 1

    target_ids = set(favorite_ids) | set(ratings) | set(behavior_counts)
    tags = set()
    if target_ids:
        for destination in session.scalars(
            select(Destination)
            .options(selectinload(Destination.tags))
            .where(Destination.id.in_(target_ids))
        ).all():
            if destination.id in favorite_ids or ratings.get(destination.id, 0) >= 4 or behavior_counts[destination.id] > 0:
                tags.update(tag.tag for tag in destination.tags)

    return {
        "favorite_ids": favorite_ids,
        "ratings": ratings,
        "behavior_counts": behavior_counts,
        "tags": tags,
        "target_ids": target_ids,
    }


def _behavior_score(destination: Destination, tags: set[str], feedback: dict[str, Any]) -> float:
    direct_scores = []
    if destination.id in feedback["favorite_ids"]:
        direct_scores.append(1.0)
    if destination.id in feedback["ratings"]:
        direct_scores.append(max(0, min(float(feedback["ratings"][destination.id]) / 5, 1)))
    behavior_count = feedback["behavior_counts"][destination.id]
    if behavior_count:
        direct_scores.append(min(behavior_count / 4, 1))

    direct_score = max(direct_scores, default=0)
    tag_score = len(tags & feedback["tags"]) / max(len(feedback["tags"]), 1) if feedback["tags"] else 0
    return min(1, max(direct_score, 0.65 * tag_score))
