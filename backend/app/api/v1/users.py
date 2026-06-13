from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.services.user_service import (
    ADMIN_ROLE,
    add_user_favorite_from_db,
    get_user_model_from_token,
    get_user_from_token,
    get_user_profile_from_db,
    list_user_behavior_logs_from_db,
    list_user_favorites_from_db,
    list_users_from_db,
    login_user_from_db,
    rate_target_from_db,
    record_user_behavior_from_db,
    register_user_from_db,
    update_user_interests_from_db,
)
from app.services.user_profile_llm_service import (
    extract_user_profile_with_llm_from_db,
    get_user_profile_analysis_from_db,
)

router = APIRouter()


class UserRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str = Field(min_length=5, max_length=128)
    password: str = Field(min_length=6, max_length=128)
    nickname: str | None = Field(default=None, max_length=64)
    interests: list[str] = Field(default_factory=list, max_length=12)


class UserLoginRequest(BaseModel):
    username_or_email: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)


class UserInterestsRequest(BaseModel):
    interests: list[str] = Field(default_factory=list, max_length=12)


class UserFavoriteRequest(BaseModel):
    target_type: str = Field(min_length=1, max_length=32)
    target_id: int = Field(ge=1)
    note: str | None = Field(default=None, max_length=500)


class UserRatingRequest(BaseModel):
    target_type: str = Field(min_length=1, max_length=32)
    target_id: int = Field(ge=1)
    rating: float = Field(ge=1, le=5)


class UserBehaviorRequest(BaseModel):
    target_type: str = Field(min_length=1, max_length=32)
    target_id: int = Field(ge=1)
    action: str = Field(min_length=1, max_length=32)
    metadata_text: str | None = Field(default=None, max_length=500)


@router.post("/register", status_code=201)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return register_user_from_db(
            session=db,
            username=payload.username,
            email=payload.email,
            password=payload.password,
            nickname=payload.nickname,
            interests=payload.interests,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/login")
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)) -> dict:
    auth = login_user_from_db(db, payload.username_or_email, payload.password)
    if auth is None:
        raise HTTPException(status_code=401, detail="Invalid username/email or password.")
    return auth


@router.get("/me")
def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> dict:
    token = _extract_bearer_token(authorization)
    profile = get_user_from_token(db, token)
    if profile is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return profile


def get_current_user_model(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    token = _extract_bearer_token(authorization)
    user = get_user_model_from_token(db, token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return user


def require_admin(current_user: User = Depends(get_current_user_model)) -> User:
    if current_user.role != ADMIN_ROLE:
        raise HTTPException(status_code=403, detail="Admin role required.")
    return current_user


@router.get("")
def list_users(db: Session = Depends(get_db)) -> dict:
    return list_users_from_db(db)


@router.get("/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)) -> dict:
    profile = get_user_profile_from_db(db, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return profile


@router.post("/{user_id}/profile/llm-extract")
def extract_user_profile_with_llm(user_id: int, db: Session = Depends(get_db)) -> dict:
    profile = extract_user_profile_with_llm_from_db(db, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return profile


@router.get("/{user_id}/profile/analysis")
def get_user_profile_analysis(user_id: int, db: Session = Depends(get_db)) -> dict:
    analysis = get_user_profile_analysis_from_db(db, user_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return analysis


@router.put("/{user_id}/interests")
def update_user_interests(user_id: int, payload: UserInterestsRequest, db: Session = Depends(get_db)) -> dict:
    profile = update_user_interests_from_db(db, user_id, payload.interests)
    if profile is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return profile


@router.post("/{user_id}/favorites")
def add_user_favorite(user_id: int, payload: UserFavoriteRequest, db: Session = Depends(get_db)) -> dict:
    try:
        favorite = add_user_favorite_from_db(
            session=db,
            user_id=user_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
            note=payload.note,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if favorite is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return favorite


@router.get("/{user_id}/favorites")
def list_user_favorites(user_id: int, db: Session = Depends(get_db)) -> dict:
    favorites = list_user_favorites_from_db(db, user_id)
    if favorites is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return favorites


@router.post("/{user_id}/ratings")
def rate_target(user_id: int, payload: UserRatingRequest, db: Session = Depends(get_db)) -> dict:
    try:
        rating = rate_target_from_db(
            session=db,
            user_id=user_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
            rating=payload.rating,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if rating is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return rating


@router.post("/{user_id}/behavior")
def record_user_behavior(user_id: int, payload: UserBehaviorRequest, db: Session = Depends(get_db)) -> dict:
    try:
        behavior = record_user_behavior_from_db(
            session=db,
            user_id=user_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
            action=payload.action,
            metadata_text=payload.metadata_text,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if behavior is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return behavior


@router.get("/{user_id}/behavior")
def list_user_behavior(user_id: int, limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)) -> dict:
    behavior = list_user_behavior_logs_from_db(db, user_id, limit)
    if behavior is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return behavior


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="Authorization header must use Bearer token.")
    return authorization[len(prefix) :].strip()
