from datetime import datetime

from pydantic import BaseModel, Field


class TravelDiarySchema(BaseModel):
    """Travel Diary Schema for API requests/responses"""
    id: int | None = None
    user_id: int
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    poi_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class TravelDiaryListResponse(BaseModel):
    """Response for diary list"""
    total: int
    items: list[TravelDiarySchema]
