from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.algorithms.route_planning import (
    GraphEdge,
    GraphNode,
    RouteNotFoundError,
    WeightMode,
    approximate_distance_meters,
    build_bidirectional_graph,
    dijkstra_shortest_path,
    find_nearest_node,
)
from app.models import MapEdge, MapNode


def plan_route_from_db(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        GraphNode(
            id=node.id,
            lng=node.lng,
            lat=node.lat,
            name=node.name,
        )
        for node in session.scalars(select(MapNode).order_by(MapNode.id)).all()
    ]
    edges = [
        GraphEdge(
            id=edge.id,
            from_node_id=edge.from_node_id,
            to_node_id=edge.to_node_id,
            distance=edge.distance,
            duration=edge.walk_time,
            geometry=edge.geometry,
        )
        for edge in session.scalars(select(MapEdge).order_by(MapEdge.id)).all()
    ]
    if not edges:
        raise RouteNotFoundError("No map edges are available.")

    start = (float(payload["start_lng"]), float(payload["start_lat"]))
    end = (float(payload["end_lng"]), float(payload["end_lat"]))
    start_snap = find_nearest_node(start[0], start[1], nodes)
    end_snap = find_nearest_node(end[0], end[1], nodes)
    weight = _resolve_weight(payload.get("strategy"))

    route = dijkstra_shortest_path(
        build_bidirectional_graph(edges),
        start_snap.node.id,
        end_snap.node.id,
        weight=weight,
    )

    snap_distance = start_snap.distance + end_snap.distance
    distance = route.graph_distance + snap_distance
    duration = route.graph_duration + snap_distance / 1.2
    return {
        "strategy": payload.get("strategy", "shortest_distance"),
        "mode": payload.get("mode", "walk"),
        "distance": round(distance),
        "duration": round(duration),
        "path": build_path_coordinates(start, end, start_snap.node, end_snap.node, route.edges),
        "node_ids": route.node_ids,
        "steps": _build_steps(start_snap, end_snap, route.edges),
        "algorithm_trace": {
            "stage": "stage-4-db-graph",
            "algorithm": "Dijkstra shortest path",
            "topology_source": "map_nodes/map_edges seeded database",
            "weight": weight,
            "nodes": str(len(nodes)),
            "edges": str(len(edges)),
            "start_node_id": str(start_snap.node.id),
            "end_node_id": str(end_snap.node.id),
            "rendering": "AMap Polyline on frontend",
        },
    }


def _resolve_weight(strategy: str | None) -> WeightMode:
    if strategy in {"shortest_time", "fastest"}:
        return "duration"
    return "distance"


def build_path_coordinates(
    start: tuple[float, float],
    end: tuple[float, float],
    start_node: GraphNode,
    end_node: GraphNode,
    edges: list[GraphEdge],
) -> list[list[float]]:
    coordinates: list[list[float]] = []
    _append_coordinate(coordinates, [start[0], start[1]])
    _append_coordinate(coordinates, [start_node.lng, start_node.lat])

    if edges:
        for edge in edges:
            for coordinate in edge.geometry:
                _append_coordinate(coordinates, coordinate)
    else:
        _append_coordinate(coordinates, [end_node.lng, end_node.lat])

    _append_coordinate(coordinates, [end_node.lng, end_node.lat])
    _append_coordinate(coordinates, [end[0], end[1]])
    return coordinates


def _append_coordinate(coordinates: list[list[float]], coordinate: list[float]) -> None:
    normalized = [round(float(coordinate[0]), 6), round(float(coordinate[1]), 6)]
    if coordinates and approximate_distance_meters(tuple(coordinates[-1]), tuple(normalized)) < 0.5:
        return
    coordinates.append(normalized)


def _build_steps(start_snap, end_snap, edges: list[GraphEdge]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = [
        {
            "text": f"起点吸附到道路节点 {start_snap.node.id}",
            "distance": round(start_snap.distance),
        }
    ]
    for index, edge in enumerate(edges, start=1):
        steps.append(
            {
                "text": f"第 {index} 段：从节点 {edge.from_node_id} 到节点 {edge.to_node_id}",
                "distance": round(edge.distance),
            }
        )
    steps.append(
        {
            "text": f"从道路节点 {end_snap.node.id} 到达终点",
            "distance": round(end_snap.distance),
        }
    )
    return steps
