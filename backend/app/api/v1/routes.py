from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.algorithms.route_planning import RouteNotFoundError
from app.db.session import get_db
from app.services.route_service import plan_multi_point_route_from_db, plan_route_from_db

router = APIRouter()


class RoutePlanRequest(BaseModel):
    scene_key: str = Field(default="bupt_shahe")
    start_place_id: str | None = Field(default=None)
    end_place_id: str | None = Field(default=None)
    start_lng: float = Field(default=116.28333)
    start_lat: float = Field(default=40.15608)
    end_lng: float = Field(default=116.28620)
    end_lat: float = Field(default=40.15820)
    strategy: str = Field(default="shortest_distance")
    mode: str = Field(default="walk")
    route_source: str = Field(default="auto")


class RoutePointRequest(BaseModel):
    place_id: str | None = Field(default=None)
    lng: float | None = Field(default=None)
    lat: float | None = Field(default=None)
    name: str | None = Field(default=None)


class MultiPointRouteRequest(BaseModel):
    scene_key: str = Field(default="bupt_shahe")
    start_place_id: str | None = Field(default=None)
    start_lng: float = Field(default=116.28333)
    start_lat: float = Field(default=40.15608)
    points: list[RoutePointRequest] = Field(min_length=1, max_length=12)
    return_to_start: bool = Field(default=False)
    strategy: str = Field(default="shortest_distance")
    mode: str = Field(default="walk")
    route_source: str = Field(default="local_graph")


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
