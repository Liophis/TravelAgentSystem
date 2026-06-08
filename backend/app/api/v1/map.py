from fastapi import APIRouter, Query
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.map_data_service import (
    get_buildings_from_db,
    get_facilities_from_db,
    get_map_edges_from_db,
    get_map_nodes_from_db,
    get_map_payload_from_db,
    get_map_stats_from_db,
)

router = APIRouter()


@router.get("/stats")
def get_map_stats(
    include_demo: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    return get_map_stats_from_db(db, include_demo=include_demo)


@router.get("/geojson")
def get_map_geojson(
    include_demo: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> dict:
    return get_map_payload_from_db(db, include_demo=include_demo)


@router.get("/nodes")
def get_map_nodes(db: Session = Depends(get_db)) -> list[dict]:
    return get_map_nodes_from_db(db)


@router.get("/edges")
def get_map_edges(db: Session = Depends(get_db)) -> list[dict]:
    return get_map_edges_from_db(db)


@router.get("/buildings")
def get_map_buildings(
    include_demo: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[dict]:
    return get_buildings_from_db(db, include_demo=include_demo)


@router.get("/facilities")
def get_map_facilities(
    include_demo: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[dict]:
    return get_facilities_from_db(db, include_demo=include_demo)
