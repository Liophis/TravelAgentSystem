from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.indoor_service import (
    IndoorRouteNotFoundError,
    list_indoor_buildings_from_db,
    list_indoor_nodes_from_db,
    plan_indoor_route_from_db,
)

router = APIRouter()


class IndoorRouteRequest(BaseModel):
    building_name: str = Field(default="综合教学楼")
    start_node_id: int | None = Field(default=None)
    end_node_id: int | None = Field(default=None)
    start_name: str | None = Field(default="一层大门")
    end_name: str | None = Field(default="305 教室")


@router.get("/buildings")
def list_indoor_buildings(db: Session = Depends(get_db)) -> dict:
    return list_indoor_buildings_from_db(db)


@router.get("/nodes")
def list_indoor_nodes(
    building_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    return list_indoor_nodes_from_db(db, building_name=building_name)


@router.post("/routes")
def plan_indoor_route(payload: IndoorRouteRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return plan_indoor_route_from_db(db, payload.model_dump())
    except IndoorRouteNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
