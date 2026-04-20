from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.graph import Graph
from app.db import crud
from app.db.database import get_db

router = APIRouter(tags=["travel-agent-system"])

# Global graph instance used by placeholder route-planning logic.
graph = Graph()
graph.add_node("A", {"name": "入口"})
graph.add_node("B", {"name": "主广场"})
graph.add_node("C", {"name": "观景台"})
graph.add_edge("A", "B", 1.2)
graph.add_edge("B", "C", 2.1)


@router.get("/route")
def find_route(
    start_poi_name: str,
    end_poi_name: str,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    start_poi = crud.get_poi_by_name(db, start_poi_name)
    end_poi = crud.get_poi_by_name(db, end_poi_name)

    if not start_poi or not end_poi:
        raise HTTPException(status_code=404, detail="起点或终点 POI 不存在")

    # Placeholder call: real path algorithm will be implemented later by team.
    simulated_path = graph.dijkstra(start_poi.name, end_poi.name)

    return {
        "start": start_poi_name,
        "end": end_poi_name,
        "path": simulated_path,
    }
