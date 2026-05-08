from pydantic import BaseModel, Field


class FacilitySchema(BaseModel):
    """Facility Schema for API requests/responses"""
    id: int | None = None
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=100)
    poi_id: int
    location_desc: str | None = None

    model_config = {"from_attributes": True}


class FacilityListResponse(BaseModel):
    """Response for facility list"""
    total: int
    items: list[FacilitySchema]
