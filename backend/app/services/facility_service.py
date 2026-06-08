from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.algorithms.ranking import top_k_smallest
from app.algorithms.route_planning import (
    GraphEdge,
    GraphNode,
    NearestNode,
    RouteNotFoundError,
    approximate_distance_meters,
    build_bidirectional_graph,
    dijkstra_shortest_path,
)
from app.core.scenes import DEFAULT_SCENE_KEY, normalize_scene_key
from app.models import Building, Facility, FacilityCategory, MapEdge, MapNode
from app.services.route_service import build_path_coordinates


def get_nearby_facilities_from_db(
    session: Session,
    current_lng: float,
    current_lat: float,
    category: str | None,
    radius: int,
    limit: int,
    origin_place_id: str | None = None,
    scene_key: str | None = DEFAULT_SCENE_KEY,
) -> dict[str, Any]:
    resolved_scene_key = normalize_scene_key(scene_key)
    nodes, edges = _load_graph_data(session, resolved_scene_key)
    if not edges:
        raise RouteNotFoundError(f"No map edges are available for scene {resolved_scene_key}.")

    origin = _resolve_origin(session, origin_place_id, current_lng, current_lat, resolved_scene_key)
    start = (origin["lng"], origin["lat"])
    graph = build_bidirectional_graph(edges)
    components = _connected_components(nodes, edges)

    resolved_category = _resolve_category_code(session, category)
    candidates = _load_facilities(session, resolved_category, resolved_scene_key)
    enriched = []
    for facility in candidates:
        facility_point = (facility.lng, facility.lat)
        try:
            start_snap, facility_snap = _snap_to_best_component(start, facility_point, components)
            route = dijkstra_shortest_path(graph, start_snap.node.id, facility_snap.node.id)
        except RouteNotFoundError:
            continue

        facility_snap_distance = approximate_distance_meters(
            facility_point,
            (facility_snap.node.lng, facility_snap.node.lat),
        )
        distance = start_snap.distance + route.graph_distance + facility_snap_distance
        if distance > radius:
            continue

        enriched.append(
            {
                "id": f"facility-{facility.id}",
                "name": facility.name,
                "category": facility.category.code,
                "category_name": facility.category.name,
                "lng": facility.lng,
                "lat": facility.lat,
                "description": facility.description,
                "nearest_node_id": facility_snap.node.id,
                "distance": round(distance),
                "duration": round(route.graph_duration + (start_snap.distance + facility_snap_distance) / 1.2),
                "routePath": build_path_coordinates(start, facility_point, start_snap.node, facility_snap.node, route.edges),
                "node_ids": route.node_ids,
            }
        )

    ranked = top_k_smallest(enriched, key=lambda item: float(item["distance"]), k=limit)
    return {
        "items": ranked,
        "total": len(enriched),
        "scene_key": resolved_scene_key,
        "origin": origin,
        "category": resolved_category,
        "category_query": category,
        "radius": radius,
        "algorithm_trace": {
            "stage": "stage-5-facility-graph-distance",
            "scene_key": resolved_scene_key,
            "origin_resolution": "origin_place_id" if origin_place_id else "coordinate fallback",
            "origin_id": origin.get("id") or "",
            "origin_source": origin.get("source") or "",
            "filter": "facility category before routing",
            "category_lookup": "code/name/contains matching",
            "resolved_category": resolved_category or "",
            "distance": "Dijkstra graph distance plus snap distance",
            "ranking": "Top-K heap by graph distance",
            "candidates": str(len(candidates)),
            "returned": str(len(ranked)),
            "nodes": str(len(nodes)),
            "edges": str(len(edges)),
            "connected_components": str(len(components)),
        },
    }


def _load_graph_data(session: Session, scene_key: str) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes = [
        GraphNode(
            id=node.id,
            lng=node.lng,
            lat=node.lat,
            name=node.name,
        )
        for node in session.scalars(select(MapNode).where(MapNode.scene_key == scene_key).order_by(MapNode.id)).all()
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
        for edge in session.scalars(select(MapEdge).where(MapEdge.scene_key == scene_key).order_by(MapEdge.id)).all()
    ]
    return nodes, edges


def _load_facilities(session: Session, category: str | None, scene_key: str) -> list[Facility]:
    query = (
        select(Facility)
        .where(Facility.scene_key == scene_key)
        .options(selectinload(Facility.category))
        .order_by(Facility.id)
    )
    if category:
        query = query.join(FacilityCategory).where(FacilityCategory.code == category)
    return list(session.scalars(query).all())


def _resolve_origin(
    session: Session,
    origin_place_id: str | None,
    current_lng: float,
    current_lat: float,
    scene_key: str,
) -> dict[str, Any]:
    if origin_place_id:
        return _lookup_place_coordinate(session, origin_place_id, scene_key)
    return {
        "id": "",
        "source": "coordinate",
        "name": "当前位置",
        "lng": float(current_lng),
        "lat": float(current_lat),
    }


def _lookup_place_coordinate(session: Session, place_id: str, scene_key: str) -> dict[str, Any]:
    source, raw_id = _split_place_id(place_id)
    model_id = int(raw_id)
    if source == "facility":
        facility = session.get(Facility, model_id)
        if facility is None:
            raise RouteNotFoundError(f"Facility {place_id} was not found.")
        _ensure_place_in_scene(place_id, facility.scene_key, scene_key)
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
        _ensure_place_in_scene(place_id, building.scene_key, scene_key)
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
        _ensure_place_in_scene(place_id, node.scene_key, scene_key)
        return {
            "id": place_id,
            "source": "node",
            "name": node.name or f"校内点 {node.id}",
            "lng": node.lng,
            "lat": node.lat,
        }
    raise RouteNotFoundError(f"Unsupported nearby origin place id: {place_id}.")


def _ensure_place_in_scene(place_id: str, item_scene_key: str, requested_scene_key: str) -> None:
    if item_scene_key != requested_scene_key:
        raise RouteNotFoundError(
            f"Nearby origin {place_id} belongs to scene {item_scene_key}, not {requested_scene_key}."
        )


def _split_place_id(place_id: str) -> tuple[str, str]:
    if "-" not in place_id:
        raise RouteNotFoundError(f"Invalid nearby origin place id: {place_id}.")
    source, raw_id = place_id.split("-", maxsplit=1)
    if not raw_id.isdigit():
        raise RouteNotFoundError(f"Invalid nearby origin place id: {place_id}.")
    return source, raw_id


def _building_center(polygon: list[list[float]]) -> tuple[float, float]:
    if not polygon:
        raise RouteNotFoundError("Building polygon is empty.")
    lng = sum(point[0] for point in polygon) / len(polygon)
    lat = sum(point[1] for point in polygon) / len(polygon)
    return lng, lat


def _resolve_category_code(session: Session, category: str | None) -> str | None:
    if not category:
        return None
    keyword = category.strip().casefold()
    if not keyword:
        return None
    aliases = {
        "卫生间": "toilet",
        "厕所": "toilet",
        "洗手间": "toilet",
        "水": "water",
        "饮水": "water",
        "食堂": "canteen",
        "餐厅": "canteen",
        "超市": "shop",
        "商店": "shop",
        "便利店": "shop",
        "校门": "gate",
        "门": "gate",
        "图书馆": "library",
        "运动": "sport",
        "体育": "sport",
        "医院": "clinic",
        "医务": "clinic",
        "交通": "transport",
        "车站": "transport",
        "atm": "atm",
    }
    if keyword in aliases:
        return aliases[keyword]
    categories = session.scalars(select(FacilityCategory).order_by(FacilityCategory.id)).all()
    for item in categories:
        if keyword in {item.code.casefold(), item.name.casefold()}:
            return item.code
    for item in categories:
        haystack = f"{item.code} {item.name}".casefold()
        if keyword in haystack or haystack in keyword:
            return item.code
    return category


def _connected_components(nodes: list[GraphNode], edges: list[GraphEdge]) -> list[list[GraphNode]]:
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
    return components


def _snap_to_best_component(
    start: tuple[float, float],
    facility_point: tuple[float, float],
    components: list[list[GraphNode]],
) -> tuple[NearestNode, NearestNode]:
    best: tuple[float, NearestNode, NearestNode] | None = None
    for component_nodes in components:
        start_snap = _nearest_node_in_component(start, component_nodes)
        facility_snap = _nearest_node_in_component(facility_point, component_nodes)
        score = start_snap.distance + facility_snap.distance
        if best is None or score < best[0]:
            best = (score, start_snap, facility_snap)
    if best is None:
        raise RouteNotFoundError("No connected route graph component is available.")
    _, start_snap, facility_snap = best
    return start_snap, facility_snap


def _nearest_node_in_component(target: tuple[float, float], nodes: list[GraphNode]) -> NearestNode:
    node = min(nodes, key=lambda item: approximate_distance_meters(target, (item.lng, item.lat)))
    return NearestNode(node=node, distance=approximate_distance_meters(target, (node.lng, node.lat)))
