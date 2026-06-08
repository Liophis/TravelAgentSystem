from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models import User, UserInterest
from app.seed.sample_data import INTEREST_TAGS


def list_users_from_db(session: Session) -> dict[str, Any]:
    users = _load_users(session)
    return {
        "items": [_serialize_user(user) for user in users],
        "total": len(users),
        "available_interests": INTEREST_TAGS,
        "algorithm_trace": {
            "stage": "stage-16-user-preference-loop",
            "source": "users/user_profiles/user_interests",
        },
    }


def get_user_profile_from_db(session: Session, user_id: int) -> dict[str, Any] | None:
    user = _get_user(session, user_id)
    if user is None:
        return None
    return {
        **_serialize_user(user),
        "available_interests": INTEREST_TAGS,
        "algorithm_trace": {
            "stage": "stage-16-user-preference-loop",
            "source": "users/user_profiles/user_interests",
        },
    }


def update_user_interests_from_db(session: Session, user_id: int, interests: list[str]) -> dict[str, Any] | None:
    user = _get_user(session, user_id)
    if user is None:
        return None
    normalized = _normalize_interests(interests)
    session.execute(delete(UserInterest).where(UserInterest.user_id == user_id))
    for tag in normalized:
        session.add(UserInterest(user_id=user_id, tag=tag))
    session.commit()
    user = _get_user(session, user_id)
    if user is None:
        return None
    return get_user_profile_from_db(session, user_id)


def _load_users(session: Session) -> list[User]:
    return list(
        session.scalars(
            select(User)
            .options(selectinload(User.profile), selectinload(User.interests))
            .order_by(User.id)
        ).all()
    )


def _get_user(session: Session, user_id: int) -> User | None:
    return session.scalar(
        select(User)
        .options(selectinload(User.profile), selectinload(User.interests))
        .where(User.id == user_id)
    )


def _serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nickname": user.profile.nickname if user.profile else user.username,
        "avatar_url": user.profile.avatar_url if user.profile else None,
        "interests": sorted({interest.tag for interest in user.interests}),
    }


def _normalize_interests(interests: list[str]) -> list[str]:
    allowed = set(INTEREST_TAGS)
    normalized = []
    for tag in interests:
        value = tag.strip()
        if value in allowed and value not in normalized:
            normalized.append(value)
    return normalized
