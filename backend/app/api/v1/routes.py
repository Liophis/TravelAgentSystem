from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.algorithms.route_planning import RouteNotFoundError
from app.db.session import get_db
from app.services.route_service import plan_multi_point_route_from_db, plan_route_from_db

router = APIRouter()


class RoutePlanRequest(BaseModel):
    start_lng: float = Field(default=116.28333)
    start_lat: float = Field(default=40.15608)
    end_lng: float = Field(default=116.28620)
    end_lat: float = Field(default=40.15820)
    strategy: str = Field(default="shortest_distance")
    mode: str = Field(default="walk")


class RoutePointRequest(BaseModel):
    lng: float
    lat: float
    name: str | None = Field(default=None)


class MultiPointRouteRequest(BaseModel):
    start_lng: float = Field(default=116.28333)
    start_lat: float = Field(default=40.15608)
    points: list[RoutePointRequest] = Field(min_length=1, max_length=12)
    return_to_start: bool = Field(default=False)
    strategy: str = Field(default="shortest_distance")
    mode: str = Field(default="walk")


@router.post("/plan")
def plan_route(payload: RoutePlanRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return plan_route_from_db(db, payload.model_dump())
    except RouteNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/multi-point")
def plan_multi_point_route(payload: MultiPointRouteRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return plan_multi_point_route_from_db(db, payload.model_dump())
    except RouteNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
