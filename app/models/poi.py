from pydantic import BaseModel, Field


class POISchema(BaseModel):
    """POI Schema for API requests/responses"""
    id: int | None = None
    name: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=100)
    latitude: float
    longitude: float
    floor: int = 1
    description: str | None = None

    model_config = {"from_attributes": True}


class POIListResponse(BaseModel):
    """Response for POI list"""
    total: int
    items: list[POISchema]
