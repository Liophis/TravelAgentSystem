import base64
import hashlib
import hmac
import json
import secrets
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models import Destination, Food, User, UserBehaviorLog, UserFavorite, UserInterest, UserProfile, UserRating
from app.seed.sample_data import INTEREST_TAGS


ALLOWED_TARGET_TYPES = {"destination", "food", "restaurant", "diary"}
ALLOWED_ACTIONS = {"view", "search", "favorite", "rate", "route", "share", "recommend_click"}
LEGACY_DEMO_PASSWORDS = {"demo123456", "password", "demo-password"}
NORMAL_USER_ROLE = "user"
ADMIN_ROLE = "admin"
ALLOWED_ROLES = {NORMAL_USER_ROLE, ADMIN_ROLE}


def list_users_from_db(session: Session) -> dict[str, Any]:
    users = _load_users(session)
    return {
        "items": [_serialize_user(user, include_activity=False) for user in users],
        "total": len(users),
        "available_interests": INTEREST_TAGS,
        "algorithm_trace": {
            "stage": "stage-23-user-feedback-loop",
            "source": "users/user_profiles/user_interests",
        },
    }


def get_user_profile_from_db(session: Session, user_id: int) -> dict[str, Any] | None:
    user = _get_user(session, user_id)
    if user is None:
        return None
    return {
        **_serialize_user(user, session=session, include_activity=True),
        "available_interests": INTEREST_TAGS,
        "algorithm_trace": {
            "stage": "stage-23-user-feedback-loop",
            "source": "users/user_profiles/user_interests/user_favorites/user_ratings/user_behavior_logs",
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


def register_user_from_db(
    session: Session,
    username: str,
    email: str,
    password: str,
    nickname: str | None,
    interests: list[str],
) -> dict[str, Any]:
    normalized_username = username.strip()
    normalized_email = email.strip().casefold()
    if session.scalar(select(User).where(User.username == normalized_username)) is not None:
        raise ValueError("Username already exists.")
    if session.scalar(select(User).where(User.email == normalized_email)) is not None:
        raise ValueError("Email already exists.")

    user = User(
        username=normalized_username,
        email=normalized_email,
        password_hash=hash_password(password),
        role=NORMAL_USER_ROLE,
    )
    session.add(user)
    session.flush()
    session.add(UserProfile(user_id=user.id, nickname=nickname.strip() if nickname else normalized_username))
    for tag in _normalize_interests(interests):
        session.add(UserInterest(user_id=user.id, tag=tag))
    session.commit()
    created = _get_user(session, user.id)
    if created is None:
        raise RuntimeError("User registration failed.")
    return _build_auth_payload(created)


def login_user_from_db(session: Session, username_or_email: str, password: str) -> dict[str, Any] | None:
    login = username_or_email.strip()
    user = session.scalar(
        select(User)
        .options(selectinload(User.profile), selectinload(User.interests))
        .where((User.username == login) | (User.email == login.casefold()))
    )
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return _build_auth_payload(user)


def get_user_from_token(session: Session, token: str) -> dict[str, Any] | None:
    user = get_user_model_from_token(session, token)
    if user is None:
        return None
    return get_user_profile_from_db(session, user.id)


def get_user_model_from_token(session: Session, token: str) -> User | None:
    payload = verify_access_token_payload(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if not isinstance(user_id, int):
        return None
    user = _get_user(session, user_id)
    if user is None or not user.is_active:
        return None
    return user


def add_user_favorite_from_db(
    session: Session,
    user_id: int,
    target_type: str,
    target_id: int,
    note: str | None,
) -> dict[str, Any] | None:
    user = _get_user(session, user_id)
    if user is None:
        return None
    _validate_target_type(target_type)
    _ensure_target_exists(session, target_type, target_id)
    favorite = session.scalar(
        select(UserFavorite).where(
            UserFavorite.user_id == user_id,
            UserFavorite.target_type == target_type,
            UserFavorite.target_id == target_id,
        )
    )
    if favorite is None:
        favorite = UserFavorite(user_id=user_id, target_type=target_type, target_id=target_id, note=note)
        session.add(favorite)
    else:
        favorite.note = note
    _append_behavior_log(session, user_id, target_type, target_id, "favorite", "created from favorite API")
    if target_type == "destination":
        _increment_destination_popularity(session, target_id, amount=3)
    session.commit()
    session.refresh(favorite)
    return {
        **_serialize_favorite(session, favorite),
        "algorithm_trace": {
            "stage": "stage-23-user-feedback-loop",
            "effect": "favorite stored and behavior log appended",
        },
    }


def list_user_favorites_from_db(session: Session, user_id: int) -> dict[str, Any] | None:
    if _get_user(session, user_id) is None:
        return None
    favorites = list(
        session.scalars(
            select(UserFavorite)
            .where(UserFavorite.user_id == user_id)
            .order_by(UserFavorite.created_at.desc(), UserFavorite.id.desc())
        ).all()
    )
    return {
        "items": [_serialize_favorite(session, favorite) for favorite in favorites],
        "total": len(favorites),
        "algorithm_trace": {
            "stage": "stage-23-user-feedback-loop",
            "source": "user_favorites",
        },
    }


def rate_target_from_db(
    session: Session,
    user_id: int,
    target_type: str,
    target_id: int,
    rating: float,
) -> dict[str, Any] | None:
    user = _get_user(session, user_id)
    if user is None:
        return None
    _validate_target_type(target_type)
    _ensure_target_exists(session, target_type, target_id)
    rating_value = round(float(rating), 2)
    user_rating = session.scalar(
        select(UserRating).where(
            UserRating.user_id == user_id,
            UserRating.target_type == target_type,
            UserRating.target_id == target_id,
        )
    )
    if user_rating is None:
        user_rating = UserRating(user_id=user_id, target_type=target_type, target_id=target_id, rating=rating_value)
        session.add(user_rating)
    else:
        user_rating.rating = rating_value
    aggregate_rating = _refresh_target_rating(session, target_type, target_id)
    _append_behavior_log(session, user_id, target_type, target_id, "rate", f"rating={rating_value}")
    session.commit()
    session.refresh(user_rating)
    return {
        **_serialize_rating(session, user_rating),
        "aggregate_rating": aggregate_rating,
        "algorithm_trace": {
            "stage": "stage-23-user-feedback-loop",
            "effect": "rating upserted, aggregate rating refreshed, behavior log appended",
        },
    }


def record_user_behavior_from_db(
    session: Session,
    user_id: int,
    target_type: str,
    target_id: int,
    action: str,
    metadata_text: str | None,
) -> dict[str, Any] | None:
    user = _get_user(session, user_id)
    if user is None:
        return None
    _validate_target_type(target_type)
    _ensure_target_exists(session, target_type, target_id)
    normalized_action = action.strip().casefold()
    if normalized_action not in ALLOWED_ACTIONS:
        raise ValueError(f"Unsupported behavior action: {action}")
    log = _append_behavior_log(session, user_id, target_type, target_id, normalized_action, metadata_text)
    if target_type == "destination" and normalized_action == "view":
        _increment_destination_popularity(session, target_id, amount=1)
    session.commit()
    session.refresh(log)
    return {
        **_serialize_behavior_log(session, log),
        "algorithm_trace": {
            "stage": "stage-23-user-feedback-loop",
            "effect": "behavior log stored and recommendation feedback became available",
        },
    }


def list_user_behavior_logs_from_db(session: Session, user_id: int, limit: int) -> dict[str, Any] | None:
    if _get_user(session, user_id) is None:
        return None
    logs = list(
        session.scalars(
            select(UserBehaviorLog)
            .where(UserBehaviorLog.user_id == user_id)
            .order_by(UserBehaviorLog.created_at.desc(), UserBehaviorLog.id.desc())
            .limit(limit)
        ).all()
    )
    return {
        "items": [_serialize_behavior_log(session, log) for log in logs],
        "total": len(logs),
        "algorithm_trace": {
            "stage": "stage-23-user-feedback-loop",
            "source": "user_behavior_logs",
        },
    }


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 100_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash == "demo-hash":
        return password in LEGACY_DEMO_PASSWORDS
    try:
        algorithm, iterations, salt, digest = password_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(candidate, digest)


def create_access_token(user_id: int, role: str = NORMAL_USER_ROLE) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "role": _normalize_role(role),
        "exp": int(expires_at.timestamp()),
    }
    payload_text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_token = _base64url_encode(payload_text.encode("utf-8"))
    signature = hmac.new(settings.secret_key.encode("utf-8"), payload_token.encode("ascii"), hashlib.sha256).digest()
    return f"{payload_token}.{_base64url_encode(signature)}"


def verify_access_token_payload(token: str) -> dict[str, Any] | None:
    try:
        payload_token, signature_token = token.split(".", 1)
    except ValueError:
        return None
    expected = hmac.new(settings.secret_key.encode("utf-8"), payload_token.encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(_base64url_encode(expected), signature_token):
        return None
    try:
        payload = json.loads(_base64url_decode(payload_token).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return None
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        return None
    if "role" not in payload:
        payload["role"] = NORMAL_USER_ROLE
    if payload["role"] not in ALLOWED_ROLES:
        return None
    return payload


def verify_access_token(token: str) -> int | None:
    payload = verify_access_token_payload(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    return int(user_id) if isinstance(user_id, int) else None


def _load_users(session: Session) -> list[User]:
    return list(
        session.scalars(
            select(User)
            .options(
                selectinload(User.profile),
                selectinload(User.interests),
                selectinload(User.favorites),
                selectinload(User.ratings),
                selectinload(User.behavior_logs),
            )
            .order_by(User.id)
        ).all()
    )


def _get_user(session: Session, user_id: int) -> User | None:
    return session.scalar(
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.interests),
            selectinload(User.favorites),
            selectinload(User.ratings),
            selectinload(User.behavior_logs),
        )
        .where(User.id == user_id)
    )


def _serialize_user(user: User, session: Session | None = None, include_activity: bool = True) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": _normalize_role(user.role),
        "nickname": user.profile.nickname if user.profile else user.username,
        "avatar_url": user.profile.avatar_url if user.profile else None,
        "interests": sorted({interest.tag for interest in user.interests}),
    }
    if include_activity:
        item["favorites"] = [
            _serialize_favorite(session, favorite) if session is not None else _serialize_target_ref(favorite)
            for favorite in sorted(user.favorites, key=lambda value: value.created_at, reverse=True)[:20]
        ]
        item["ratings"] = [
            _serialize_rating(session, rating) if session is not None else _serialize_target_ref(rating)
            for rating in sorted(user.ratings, key=lambda value: value.updated_at, reverse=True)[:20]
        ]
        item["recent_behaviors"] = [
            _serialize_behavior_log(session, log) if session is not None else _serialize_target_ref(log)
            for log in sorted(user.behavior_logs, key=lambda value: value.created_at, reverse=True)[:20]
        ]
    return item


def _normalize_interests(interests: list[str]) -> list[str]:
    allowed = set(INTEREST_TAGS)
    normalized = []
    for tag in interests:
        value = tag.strip()
        if value in allowed and value not in normalized:
            normalized.append(value)
    return normalized


def _normalize_role(role: str | None) -> str:
    value = (role or NORMAL_USER_ROLE).strip().casefold()
    return value if value in ALLOWED_ROLES else NORMAL_USER_ROLE


def _build_auth_payload(user: User) -> dict[str, Any]:
    return {
        "access_token": create_access_token(user.id, user.role),
        "token_type": "bearer",
        "expires_in_minutes": settings.access_token_expire_minutes,
        "role": _normalize_role(user.role),
        "user": _serialize_user(user, include_activity=False),
        "algorithm_trace": {
            "stage": "stage-31-admin-user-auth",
            "auth": "PBKDF2 password hash plus HMAC signed role-aware demo token",
        },
    }


def _validate_target_type(target_type: str) -> None:
    if target_type not in ALLOWED_TARGET_TYPES:
        raise ValueError(f"Unsupported target type: {target_type}")


def _ensure_target_exists(session: Session, target_type: str, target_id: int) -> None:
    model_by_type = {
        "destination": Destination,
        "food": Food,
    }
    model = model_by_type.get(target_type)
    if model is None:
        return
    if session.get(model, target_id) is None:
        raise LookupError(f"{target_type} not found.")


def _append_behavior_log(
    session: Session,
    user_id: int,
    target_type: str,
    target_id: int,
    action: str,
    metadata_text: str | None,
) -> UserBehaviorLog:
    log = UserBehaviorLog(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        action=action,
        metadata_text=metadata_text,
    )
    session.add(log)
    return log


def _increment_destination_popularity(session: Session, destination_id: int, amount: int) -> None:
    destination = session.get(Destination, destination_id)
    if destination is not None:
        destination.popularity += amount


def _refresh_target_rating(session: Session, target_type: str, target_id: int) -> float | None:
    if target_type not in {"destination", "food"}:
        return None
    aggregate = session.scalar(
        select(func.avg(UserRating.rating)).where(
            UserRating.target_type == target_type,
            UserRating.target_id == target_id,
        )
    )
    if aggregate is None:
        return None
    rounded = round(float(aggregate), 2)
    if target_type == "destination":
        destination = session.get(Destination, target_id)
        if destination is not None:
            destination.rating = rounded
    elif target_type == "food":
        food = session.get(Food, target_id)
        if food is not None:
            food.rating = rounded
    return rounded


def _serialize_favorite(session: Session | None, favorite: UserFavorite) -> dict[str, Any]:
    return {
        **_serialize_target_ref(favorite),
        "note": favorite.note,
        "target_name": _target_name(session, favorite.target_type, favorite.target_id),
        "created_at": favorite.created_at.isoformat(),
    }


def _serialize_rating(session: Session | None, rating: UserRating) -> dict[str, Any]:
    return {
        **_serialize_target_ref(rating),
        "rating": rating.rating,
        "target_name": _target_name(session, rating.target_type, rating.target_id),
        "created_at": rating.created_at.isoformat(),
        "updated_at": rating.updated_at.isoformat(),
    }


def _serialize_behavior_log(session: Session | None, log: UserBehaviorLog) -> dict[str, Any]:
    return {
        **_serialize_target_ref(log),
        "action": log.action,
        "metadata_text": log.metadata_text,
        "target_name": _target_name(session, log.target_type, log.target_id),
        "created_at": log.created_at.isoformat(),
    }


def _serialize_target_ref(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "target_type": item.target_type,
        "target_id": item.target_id,
    }


def _target_name(session: Session | None, target_type: str, target_id: int) -> str | None:
    if session is None:
        return None
    if target_type == "destination":
        destination = session.get(Destination, target_id)
        return destination.name if destination is not None else None
    if target_type == "food":
        food = session.get(Food, target_id)
        return food.name if food is not None else None
    return None


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}")
