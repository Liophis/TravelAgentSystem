from pydantic import BaseModel, Field


class POISchema(BaseModel):
    id: int | None = None
    name: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=100)
    latitude: float
    longitude: float
    floor: int = 1

    model_config = {"from_attributes": True}
