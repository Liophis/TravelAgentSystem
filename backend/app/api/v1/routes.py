from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.mock_map_service import get_route_plan

router = APIRouter()


class RoutePlanRequest(BaseModel):
    start_lng: float = Field(default=116.3260)
    start_lat: float = Field(default=40.0030)
    end_lng: float = Field(default=116.3312)
    end_lat: float = Field(default=40.0065)
    strategy: str = Field(default="shortest_distance")
    mode: str = Field(default="walk")


@router.post("/plan")
def plan_route(payload: RoutePlanRequest) -> dict:
    return get_route_plan(payload.model_dump())
