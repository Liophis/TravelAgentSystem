from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.user_service import get_user_profile_from_db, list_users_from_db, update_user_interests_from_db

router = APIRouter()


class UserInterestsRequest(BaseModel):
    interests: list[str] = Field(default_factory=list, max_length=12)


@router.get("")
def list_users(db: Session = Depends(get_db)) -> dict:
    return list_users_from_db(db)


@router.get("/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)) -> dict:
    profile = get_user_profile_from_db(db, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return profile


@router.put("/{user_id}/interests")
def update_user_interests(user_id: int, payload: UserInterestsRequest, db: Session = Depends(get_db)) -> dict:
    profile = update_user_interests_from_db(db, user_id, payload.interests)
    if profile is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return profile
