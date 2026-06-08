from dataclasses import dataclass
from heapq import heappop, heappush
from math import inf
from typing import Literal


Coordinate = tuple[float, float]
WeightMode = Literal["distance", "duration"]


@dataclass(frozen=True)
class GraphNode:
    id: int
    lng: float
    lat: float
    name: str | None = None


@dataclass(frozen=True)
class GraphEdge:
    id: int
    from_node_id: int
    to_node_id: int
    distance: float
    duration: float
    geometry: list[list[float]]
    congestion: float = 1.0
    allowed_modes: tuple[str, ...] = ("walk",)
    transport_mode: str = "walk"


@dataclass(frozen=True)
class NearestNode:
    node: GraphNode
    distance: float


@dataclass(frozen=True)
class RouteResult:
    node_ids: list[int]
    edges: list[GraphEdge]
    graph_distance: float
    graph_duration: float


class RouteNotFoundError(ValueError):
    pass


def approximate_distance_meters(first: Coordinate, second: Coordinate) -> float:
    lng_delta = (first[0] - second[0]) * 85000
    lat_delta = (first[1] - second[1]) * 111000
    return (lng_delta * lng_delta + lat_delta * lat_delta) ** 0.5


def find_nearest_node(lng: float, lat: float, nodes: list[GraphNode]) -> NearestNode:
    if not nodes:
        raise RouteNotFoundError("No map nodes are available.")

    target = (lng, lat)
    node = min(nodes, key=lambda item: approximate_distance_meters(target, (item.lng, item.lat)))
    return NearestNode(node=node, distance=approximate_distance_meters(target, (node.lng, node.lat)))


def build_bidirectional_graph(edges: list[GraphEdge]) -> dict[int, list[GraphEdge]]:
    graph: dict[int, list[GraphEdge]] = {}
    for edge in edges:
        graph.setdefault(edge.from_node_id, []).append(edge)
        graph.setdefault(edge.to_node_id, []).append(
            GraphEdge(
                id=edge.id,
                from_node_id=edge.to_node_id,
                to_node_id=edge.from_node_id,
                distance=edge.distance,
                duration=edge.duration,
                geometry=list(reversed(edge.geometry)),
                congestion=edge.congestion,
                allowed_modes=edge.allowed_modes,
                transport_mode=edge.transport_mode,
            )
        )
    return graph


def dijkstra_shortest_path(
    graph: dict[int, list[GraphEdge]],
    start_node_id: int,
    end_node_id: int,
    weight: WeightMode = "distance",
) -> RouteResult:
    if start_node_id == end_node_id:
        return RouteResult(
            node_ids=[start_node_id],
            edges=[],
            graph_distance=0,
            graph_duration=0,
        )

    distances: dict[int, float] = {start_node_id: 0}
    previous: dict[int, tuple[int, GraphEdge]] = {}
    heap: list[tuple[float, int]] = [(0, start_node_id)]

    while heap:
        current_cost, current_node_id = heappop(heap)
        if current_cost > distances.get(current_node_id, inf):
            continue
        if current_node_id == end_node_id:
            break

        for edge in graph.get(current_node_id, []):
            edge_weight = edge.duration if weight == "duration" else edge.distance
            next_cost = current_cost + edge_weight
            if next_cost < distances.get(edge.to_node_id, inf):
                distances[edge.to_node_id] = next_cost
                previous[edge.to_node_id] = (current_node_id, edge)
                heappush(heap, (next_cost, edge.to_node_id))

    if end_node_id not in previous and end_node_id != start_node_id:
        raise RouteNotFoundError(f"No route from node {start_node_id} to node {end_node_id}.")

    node_ids = [end_node_id]
    route_edges: list[GraphEdge] = []
    cursor = end_node_id
    while cursor != start_node_id:
        previous_node_id, edge = previous[cursor]
        route_edges.append(edge)
        node_ids.append(previous_node_id)
        cursor = previous_node_id

    node_ids.reverse()
    route_edges.reverse()
    return RouteResult(
        node_ids=node_ids,
        edges=route_edges,
        graph_distance=sum(edge.distance for edge in route_edges),
        graph_duration=sum(edge.duration for edge in route_edges),
    )
