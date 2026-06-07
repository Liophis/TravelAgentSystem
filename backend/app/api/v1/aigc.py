from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.aigc_service import generate_diary_draft, generate_storyboard

router = APIRouter()


class DiaryDraftRequest(BaseModel):
    topic: str = Field(default="沙河校区游览", max_length=120)
    keywords: list[str] = Field(default_factory=list)
    tone: str = Field(default="自然", max_length=40)


class StoryboardRequest(BaseModel):
    text: str = Field(min_length=1)
    scene_count: int = Field(default=4, ge=1, le=8)


@router.post("/diary-draft")
def diary_draft(payload: DiaryDraftRequest) -> dict:
    return generate_diary_draft(payload.model_dump())


@router.post("/storyboard")
def storyboard(payload: StoryboardRequest) -> dict:
    return generate_storyboard(payload.model_dump())
