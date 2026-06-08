from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.algorithms.route_planning import (
    GraphEdge,
    GraphNode,
    NearestNode,
    RouteNotFoundError,
    WeightMode,
    approximate_distance_meters,
    build_bidirectional_graph,
    dijkstra_shortest_path,
)
from app.models import Building, Destination, Facility, MapEdge, MapNode
from app.services.amap_route_service import AMapRouteError, plan_amap_walking_route

TRANSPORT_MODES = {"walk", "bike", "electric_cart"}
MODE_LABELS = {
    "walk": "步行",
    "bike": "自行车",
    "electric_cart": "电瓶车",
    "mixed": "混合交通",
}


def plan_route_from_db(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    mode = _normalize_mode(payload.get("mode"))
    route_source = _normalize_route_source(payload.get("route_source"))
    start_endpoint = _resolve_route_endpoint(session, payload, "start")
    end_endpoint = _resolve_route_endpoint(session, payload, "end")
    start = (start_endpoint["lng"], start_endpoint["lat"])
    end = (end_endpoint["lng"], end_endpoint["lat"])

    if _should_use_amap_walking(route_source, mode):
        try:
            route = plan_amap_walking_route(
                api_key=settings.amap_web_api_key or "",
                start_lng=start[0],
                start_lat=start[1],
                end_lng=end[0],
                end_lat=end[1],
            )
            return {
                "strategy": payload.get("strategy", "shortest_distance"),
                "mode": mode,
                "route_source": "amap_walking",
                "distance": route["distance"],
                "duration": route["duration"],
                "start": start_endpoint,
                "end": end_endpoint,
                "path": route["path"],
                "node_ids": [],
                "steps": route["steps"],
                "algorithm_trace": {
                    **route["algorithm_trace"],
                    "input_model": "place_id first, coordinate fallback",
                    "fallback": "local Dijkstra graph when AMap is unavailable or route_source=local_graph",
                },
            }
        except AMapRouteError:
            if route_source == "amap_walking":
                raise RouteNotFoundError("AMap walking route is unavailable.")

    nodes, edges = _load_route_graph_data(session, mode)
    if not edges:
        raise RouteNotFoundError(f"No map edges are available for mode {mode}.")

    start_snap, end_snap, component_count = _find_connected_snaps(start, end, nodes, edges)
    weight = _resolve_weight(payload.get("strategy"))

    route = dijkstra_shortest_path(
        build_bidirectional_graph(edges),
        start_snap.node.id,
        end_snap.node.id,
        weight=weight,
    )

    snap_distance = start_snap.distance + end_snap.distance
    distance = route.graph_distance + snap_distance
    duration = route.graph_duration + _snap_duration(start_snap.distance, mode) + _snap_duration(end_snap.distance, mode)
    return {
        "strategy": payload.get("strategy", "shortest_distance"),
        "mode": mode,
        "route_source": "local_graph",
        "distance": round(distance),
        "duration": round(duration),
        "start": start_endpoint,
        "end": end_endpoint,
        "path": build_path_coordinates(start, end, start_snap.node, end_snap.node, route.edges),
        "node_ids": route.node_ids,
        "steps": _build_steps(start_snap, end_snap, route.edges),
        "algorithm_trace": {
            "stage": "stage-4-db-graph",
            "algorithm": "Dijkstra shortest path",
            "topology_source": "local map_nodes/map_edges graph",
            "input_model": "place_id first, coordinate fallback",
            "weight": weight,
            "mode": mode,
            "mode_filter": _mode_trace(mode),
            "congestion_model": "duration = distance / (ideal_speed * congestion)",
            "nodes": str(len(nodes)),
            "edges": str(len(edges)),
            "connected_components": str(component_count),
            "start_node_id": str(start_snap.node.id),
            "end_node_id": str(end_snap.node.id),
            "rendering": "AMap Polyline on frontend",
        },
    }


def plan_multi_point_route_from_db(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    points = list(payload.get("points") or [])
    if not points:
        raise RouteNotFoundError("At least one destination point is required.")

    start_endpoint = _resolve_route_endpoint(session, payload, "start")
    current = {
        **start_endpoint,
        "name": start_endpoint.get("name") or "起点",
    }
    start = dict(current)
    remaining = [
        _resolve_multi_point_endpoint(session, point, index)
        for index, point in enumerate(points)
    ]
    segments = []
    visit_order = []
    full_path: list[list[float]] = []
    node_ids: list[int] = []
    total_distance = 0
    total_duration = 0

    while remaining:
        best_index, best_route = _nearest_route(session, current, remaining, payload)
        target = remaining.pop(best_index)
        segment = _serialize_segment(current, target, best_route)
        segments.append(segment)
        visit_order.append(target)
        total_distance += int(best_route["distance"])
        total_duration += int(best_route["duration"])
        _extend_path(full_path, best_route["path"])
        node_ids.extend(best_route.get("node_ids", []))
        current = target

    if payload.get("return_to_start"):
        return_route = _plan_between(session, current, start, payload)
        segments.append(_serialize_segment(current, start, return_route))
        total_distance += int(return_route["distance"])
        total_duration += int(return_route["duration"])
        _extend_path(full_path, return_route["path"])
        node_ids.extend(return_route.get("node_ids", []))

    return {
        "strategy": payload.get("strategy", "shortest_distance"),
        "mode": payload.get("mode", "walk"),
        "route_source": payload.get("route_source", "local_graph"),
        "distance": total_distance,
        "duration": total_duration,
        "path": full_path,
        "node_ids": _dedupe_ints(node_ids),
        "visit_order": visit_order,
        "segments": segments,
        "steps": _build_multi_point_steps(segments),
        "algorithm_trace": {
            "stage": "stage-12-multi-point-route",
            "algorithm": "Greedy TSP approximation, each candidate leg scored by Dijkstra graph distance",
            "input_model": "place_id first, coordinate fallback",
            "points": str(len(points)),
            "segments": str(len(segments)),
            "return_to_start": str(bool(payload.get("return_to_start"))),
            "route_source": payload.get("route_source", "local_graph"),
        },
    }


def _resolve_weight(strategy: str | None) -> WeightMode:
    if strategy in {"shortest_time", "fastest", "transport_time", "mixed_time"}:
        return "duration"
    return "distance"


def _find_connected_snaps(
    start: tuple[float, float],
    end: tuple[float, float],
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> tuple[NearestNode, NearestNode, int]:
    node_by_id = {node.id: node for node in nodes}
    adjacency: dict[int, set[int]] = {}
    for edge in edges:
        adjacency.setdefault(edge.from_node_id, set()).add(edge.to_node_id)
        adjacency.setdefault(edge.to_node_id, set()).add(edge.from_node_id)

    components: list[list[GraphNode]] = []
    visited: set[int] = set()
    for node_id in adjacency:
        if node_id in visited:
            continue
        stack = [node_id]
        visited.add(node_id)
        component_nodes: list[GraphNode] = []
        while stack:
            current = stack.pop()
            node = node_by_id.get(current)
            if node is not None:
                component_nodes.append(node)
            for next_id in adjacency.get(current, set()):
                if next_id not in visited:
                    visited.add(next_id)
                    stack.append(next_id)
        if component_nodes:
            components.append(component_nodes)

    if not components:
        raise RouteNotFoundError("No connected route graph component is available.")

    best: tuple[float, NearestNode, NearestNode] | None = None
    for component_nodes in components:
        start_snap = _nearest_node_in_component(start, component_nodes)
        end_snap = _nearest_node_in_component(end, component_nodes)
        score = start_snap.distance + end_snap.distance
        if best is None or score < best[0]:
            best = (score, start_snap, end_snap)

    if best is None:
        raise RouteNotFoundError("No reachable node pair is available.")
    _, start_snap, end_snap = best
    return start_snap, end_snap, len(components)


def _nearest_node_in_component(target: tuple[float, float], nodes: list[GraphNode]) -> NearestNode:
    node = min(nodes, key=lambda item: approximate_distance_meters(target, (item.lng, item.lat)))
    return NearestNode(node=node, distance=approximate_distance_meters(target, (node.lng, node.lat)))


def _normalize_route_source(route_source: str | None) -> str:
    if route_source in {"auto", "amap_walking", "local_graph"}:
        return route_source
    return "auto"


def _should_use_amap_walking(route_source: str, mode: str) -> bool:
    if mode != "walk":
        return False
    return route_source in {"auto", "amap_walking"} and bool(settings.amap_web_api_key)


def _nearest_route(
    session: Session,
    current: dict[str, Any],
    remaining: list[dict[str, Any]],
    payload: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    scored = []
    score_key = "duration" if _resolve_weight(payload.get("strategy")) == "duration" else "distance"
    for index, point in enumerate(remaining):
        route = _plan_between(session, current, point, payload)
        scored.append((int(route[score_key]), index, route))
    scored.sort(key=lambda item: (item[0], item[1]))
    _, index, route = scored[0]
    return index, route


def _plan_between(
    session: Session,
    start: dict[str, Any],
    end: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    return plan_route_from_db(
        session,
        {
            "start_lng": start["lng"],
            "start_lat": start["lat"],
            "end_lng": end["lng"],
            "end_lat": end["lat"],
            "strategy": payload.get("strategy", "shortest_distance"),
            "mode": payload.get("mode", "walk"),
            "route_source": payload.get("route_source", "local_graph"),
        },
    )


def _resolve_route_endpoint(session: Session, payload: dict[str, Any], prefix: str) -> dict[str, Any]:
    place_id = payload.get(f"{prefix}_place_id")
    if place_id:
        return _lookup_place_coordinate(session, str(place_id))

    lng = payload.get(f"{prefix}_lng")
    lat = payload.get(f"{prefix}_lat")
    if lng is None or lat is None:
        raise RouteNotFoundError(f"{prefix} point requires either place_id or lng/lat.")
    return {
        "id": "",
        "source": "coordinate",
        "name": "起点" if prefix == "start" else "终点",
        "lng": float(lng),
        "lat": float(lat),
    }


def _resolve_multi_point_endpoint(session: Session, point: dict[str, Any], index: int) -> dict[str, Any]:
    place_id = point.get("place_id")
    if place_id:
        endpoint = _lookup_place_coordinate(session, str(place_id))
        endpoint["index"] = index
        endpoint["name"] = point.get("name") or endpoint.get("name") or f"终点 {index + 1}"
        return endpoint

    if point.get("lng") is None or point.get("lat") is None:
        raise RouteNotFoundError(f"Destination point {index + 1} requires either place_id or lng/lat.")
    return {
        "index": index,
        "id": "",
        "source": "coordinate",
        "name": point.get("name") or f"终点 {index + 1}",
        "lng": float(point["lng"]),
        "lat": float(point["lat"]),
    }


def _lookup_place_coordinate(session: Session, place_id: str) -> dict[str, Any]:
    source, raw_id = _split_place_id(place_id)
    model_id = int(raw_id)
    if source == "destination":
        destination = session.get(Destination, model_id)
        if destination is None:
            raise RouteNotFoundError(f"Destination {place_id} was not found.")
        return {
            "id": place_id,
            "source": "destination",
            "name": destination.name,
            "lng": destination.lng,
            "lat": destination.lat,
        }
    if source == "facility":
        facility = session.get(Facility, model_id)
        if facility is None:
            raise RouteNotFoundError(f"Facility {place_id} was not found.")
        return {
            "id": place_id,
            "source": "facility",
            "name": facility.name,
            "lng": facility.lng,
            "lat": facility.lat,
        }
    if source == "building":
        building = session.get(Building, model_id)
        if building is None:
            raise RouteNotFoundError(f"Building {place_id} was not found.")
        lng, lat = _building_center(building.polygon)
        return {
            "id": place_id,
            "source": "building",
            "name": building.name,
            "lng": lng,
            "lat": lat,
        }
    if source == "node":
        node = session.get(MapNode, model_id)
        if node is None:
            raise RouteNotFoundError(f"Map node {place_id} was not found.")
        return {
            "id": place_id,
            "source": "node",
            "name": node.name or f"道路节点 {node.id}",
            "lng": node.lng,
            "lat": node.lat,
        }
    raise RouteNotFoundError(f"Unsupported route place id: {place_id}.")


def _split_place_id(place_id: str) -> tuple[str, str]:
    if "-" not in place_id:
        raise RouteNotFoundError(f"Invalid route place id: {place_id}.")
    source, raw_id = place_id.split("-", maxsplit=1)
    if not raw_id.isdigit():
        raise RouteNotFoundError(f"Invalid route place id: {place_id}.")
    return source, raw_id


def _building_center(polygon: list[list[float]]) -> tuple[float, float]:
    if not polygon:
        raise RouteNotFoundError("Building polygon is empty.")
    lng = sum(point[0] for point in polygon) / len(polygon)
    lat = sum(point[1] for point in polygon) / len(polygon)
    return lng, lat


def _serialize_segment(start: dict[str, Any], end: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    return {
        "from": start["name"],
        "to": end["name"],
        "distance": route["distance"],
        "duration": route["duration"],
        "path": route["path"],
        "node_ids": route.get("node_ids", []),
    }


def _extend_path(full_path: list[list[float]], segment_path: list[list[float]]) -> None:
    for coordinate in segment_path:
        if full_path and approximate_distance_meters(tuple(full_path[-1]), tuple(coordinate)) < 0.5:
            continue
        full_path.append(coordinate)


def _dedupe_ints(values: list[int]) -> list[int]:
    results = []
    for value in values:
        if not results or results[-1] != value:
            results.append(value)
    return results


def _build_multi_point_steps(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "text": f"第 {index} 段：{segment['from']} 到 {segment['to']}",
            "distance": segment["distance"],
        }
        for index, segment in enumerate(segments, start=1)
    ]


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
                "text": (
                    f"第 {index} 段：从节点 {edge.from_node_id} 到节点 {edge.to_node_id}"
                    f"，{MODE_LABELS.get(edge.transport_mode, edge.transport_mode)}"
                    f"，拥挤度 {edge.congestion:.2f}"
                ),
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


def _load_route_graph_data(session: Session, mode: str) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes = [
        GraphNode(
            id=node.id,
            lng=node.lng,
            lat=node.lat,
            name=node.name,
        )
        for node in session.scalars(select(MapNode).order_by(MapNode.id)).all()
    ]
    edges = []
    for edge in session.scalars(select(MapEdge).order_by(MapEdge.id)).all():
        resolved = _resolve_edge_for_mode(edge, mode)
        if resolved is not None:
            edges.append(resolved)
    return nodes, edges


def _resolve_edge_for_mode(edge: MapEdge, requested_mode: str) -> GraphEdge | None:
    allowed_modes = tuple(mode for mode in (edge.allowed_modes or ["walk"]) if mode in TRANSPORT_MODES)
    if not allowed_modes:
        allowed_modes = ("walk",)

    if requested_mode == "mixed":
        transport_mode = min(allowed_modes, key=lambda mode: _edge_duration(edge, mode))
    elif requested_mode in allowed_modes:
        transport_mode = requested_mode
    else:
        return None

    return GraphEdge(
        id=edge.id,
        from_node_id=edge.from_node_id,
        to_node_id=edge.to_node_id,
        distance=edge.distance,
        duration=_edge_duration(edge, transport_mode),
        geometry=edge.geometry,
        congestion=_bounded_congestion(edge.congestion),
        allowed_modes=allowed_modes,
        transport_mode=transport_mode,
    )


def _edge_duration(edge: MapEdge, mode: str) -> float:
    speed = {
        "walk": edge.walk_speed or 1.2,
        "bike": edge.bike_speed or 3.5,
        "electric_cart": edge.electric_cart_speed or 4.5,
    }.get(mode, edge.walk_speed or 1.2)
    return edge.distance / max(speed * _bounded_congestion(edge.congestion), 0.1)


def _bounded_congestion(congestion: float | None) -> float:
    if congestion is None:
        return 1.0
    return max(0.2, min(float(congestion), 1.0))


def _normalize_mode(mode: str | None) -> str:
    if mode in {"walk", "bike", "electric_cart", "mixed"}:
        return mode
    return "walk"


def _snap_duration(distance: float, mode: str) -> float:
    if mode == "bike":
        return distance / 3.5
    return distance / 1.2


def _mode_trace(mode: str) -> str:
    if mode == "mixed":
        return "any edge with at least one allowed transport mode; fastest allowed mode per edge"
    return f"only edges allowing {mode}"
