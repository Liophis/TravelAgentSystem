from heapq import heappop, heappush
from math import inf
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import IndoorEdge, IndoorNode


class IndoorRouteNotFoundError(ValueError):
    pass


def list_indoor_buildings_from_db(session: Session) -> dict[str, Any]:
    nodes = session.scalars(select(IndoorNode).order_by(IndoorNode.building_name, IndoorNode.floor)).all()
    grouped: dict[str, set[int]] = {}
    for node in nodes:
        grouped.setdefault(node.building_name, set()).add(node.floor)
    items = [
        {
            "building_name": building_name,
            "floors": sorted(floors),
        }
        for building_name, floors in sorted(grouped.items())
    ]
    return {
        "items": items,
        "total": len(items),
        "algorithm_trace": {
            "stage": "stage-15-indoor-navigation",
            "source": "indoor_nodes deterministic seed",
        },
    }


def list_indoor_nodes_from_db(session: Session, building_name: str | None = None) -> dict[str, Any]:
    query = select(IndoorNode).order_by(IndoorNode.building_name, IndoorNode.floor, IndoorNode.id)
    if building_name:
        query = query.where(IndoorNode.building_name == building_name)
    nodes = list(session.scalars(query).all())
    return {
        "items": [_serialize_node(node) for node in nodes],
        "total": len(nodes),
        "building_name": building_name,
        "algorithm_trace": {
            "stage": "stage-15-indoor-navigation",
            "source": "indoor_nodes deterministic seed",
        },
    }


def plan_indoor_route_from_db(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    building_name = payload.get("building_name") or "综合教学楼"
    nodes = list(
        session.scalars(
            select(IndoorNode)
            .where(IndoorNode.building_name == building_name)
            .order_by(IndoorNode.id)
        ).all()
    )
    if not nodes:
        raise IndoorRouteNotFoundError(f"No indoor nodes for building {building_name}.")

    start_node = _resolve_node(nodes, payload.get("start_node_id"), payload.get("start_name"))
    end_node = _resolve_node(nodes, payload.get("end_node_id"), payload.get("end_name"))
    edges = list(
        session.scalars(
            select(IndoorEdge)
            .options(selectinload(IndoorEdge.from_node), selectinload(IndoorEdge.to_node))
            .where(IndoorEdge.building_name == building_name)
            .order_by(IndoorEdge.id)
        ).all()
    )
    route_edges = _dijkstra_indoor(edges, start_node.id, end_node.id)
    path_nodes = _nodes_from_edges(start_node, route_edges)
    distance = sum(edge.distance for edge in route_edges)
    duration = sum(edge.duration for edge in route_edges)
    return {
        "building_name": building_name,
        "start": _serialize_node(start_node),
        "end": _serialize_node(end_node),
        "distance": round(distance),
        "duration": round(duration),
        "path": [_serialize_node(node) for node in path_nodes],
        "steps": _build_steps(start_node, route_edges),
        "algorithm_trace": {
            "stage": "stage-15-indoor-navigation",
            "algorithm": "Dijkstra shortest path on indoor_nodes/indoor_edges",
            "nodes": str(len(nodes)),
            "edges": str(len(edges)),
            "start_node_id": str(start_node.id),
            "end_node_id": str(end_node.id),
        },
    }


def _resolve_node(nodes: list[IndoorNode], node_id: int | None, name: str | None) -> IndoorNode:
    if node_id is not None:
        for node in nodes:
            if node.id == int(node_id):
                return node
    if name:
        normalized = name.strip().casefold()
        for node in nodes:
            if node.name.casefold() == normalized:
                return node
        for node in nodes:
            if normalized in node.name.casefold():
                return node
    raise IndoorRouteNotFoundError(f"Indoor node not found: {node_id or name}.")


def _dijkstra_indoor(edges: list[IndoorEdge], start_node_id: int, end_node_id: int) -> list[IndoorEdge]:
    if start_node_id == end_node_id:
        return []
    graph: dict[int, list[IndoorEdge]] = {}
    for edge in edges:
        graph.setdefault(edge.from_node_id, []).append(edge)
        graph.setdefault(edge.to_node_id, []).append(_reverse_edge(edge))

    distances: dict[int, float] = {start_node_id: 0}
    previous: dict[int, tuple[int, IndoorEdge]] = {}
    heap: list[tuple[float, int]] = [(0, start_node_id)]
    while heap:
        current_cost, current_node_id = heappop(heap)
        if current_cost > distances.get(current_node_id, inf):
            continue
        if current_node_id == end_node_id:
            break
        for edge in graph.get(current_node_id, []):
            next_cost = current_cost + edge.duration
            if next_cost < distances.get(edge.to_node_id, inf):
                distances[edge.to_node_id] = next_cost
                previous[edge.to_node_id] = (current_node_id, edge)
                heappush(heap, (next_cost, edge.to_node_id))

    if end_node_id not in previous:
        raise IndoorRouteNotFoundError(f"No indoor route from node {start_node_id} to node {end_node_id}.")

    route_edges: list[IndoorEdge] = []
    cursor = end_node_id
    while cursor != start_node_id:
        previous_node_id, edge = previous[cursor]
        route_edges.append(edge)
        cursor = previous_node_id
    route_edges.reverse()
    return route_edges


def _reverse_edge(edge: IndoorEdge) -> IndoorEdge:
    return IndoorEdge(
        id=edge.id,
        building_name=edge.building_name,
        from_node_id=edge.to_node_id,
        to_node_id=edge.from_node_id,
        distance=edge.distance,
        duration=edge.duration,
        access_type=edge.access_type,
        from_node=edge.to_node,
        to_node=edge.from_node,
    )


def _nodes_from_edges(start_node: IndoorNode, edges: list[IndoorEdge]) -> list[IndoorNode]:
    nodes = [start_node]
    nodes.extend(edge.to_node for edge in edges)
    return nodes


def _build_steps(start_node: IndoorNode, edges: list[IndoorEdge]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    current = start_node
    for edge in edges:
        steps.append(
            {
                "text": f"{current.floor} 层：{current.name} 到 {edge.to_node.name}，{_access_label(edge.access_type)}",
                "from_node_id": current.id,
                "to_node_id": edge.to_node_id,
                "floor": edge.to_node.floor,
                "distance": round(edge.distance),
                "duration": round(edge.duration),
                "access_type": edge.access_type,
            }
        )
        current = edge.to_node
    return steps


def _access_label(access_type: str) -> str:
    return {
        "corridor": "走廊",
        "elevator": "电梯",
        "stairs": "楼梯",
    }.get(access_type, access_type)


def _serialize_node(node: IndoorNode) -> dict[str, Any]:
    return {
        "id": node.id,
        "building_name": node.building_name,
        "floor": node.floor,
        "name": node.name,
        "node_type": node.node_type,
        "x": node.x,
        "y": node.y,
    }
