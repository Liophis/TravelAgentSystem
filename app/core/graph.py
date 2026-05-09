from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Node:
    """Basic node object used by the graph."""

    node_id: str
    data: Any = None


class Graph:
    """Graph implemented with an adjacency list dictionary."""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.adjacency_list: dict[str, list[tuple[str, float]]] = {}

    def add_node(self, node_id: str, data: Any = None) -> None:
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id=node_id, data=data)
            self.adjacency_list[node_id] = []

    def add_edge(self, from_node: str, to_node: str, weight: float) -> None:
        if from_node not in self.nodes:
            self.add_node(from_node)
        if to_node not in self.nodes:
            self.add_node(to_node)
        self.adjacency_list[from_node].append((to_node, weight))

    def dijkstra(self, start_node_id: str, end_node_id: str) -> list[str]:
        """Return shortest path from start_node_id to end_node_id using Dijkstra's algorithm.

        Returns a list of node ids representing the path. If no path exists, returns an empty list.
        """
        import heapq

        if start_node_id not in self.nodes or end_node_id not in self.nodes:
            return []

        # distances and previous node mapping
        distances: dict[str, float] = {nid: float("inf") for nid in self.nodes}
        previous: dict[str, str | None] = {nid: None for nid in self.nodes}

        distances[start_node_id] = 0.0

        # priority queue of (distance, node_id)
        heap: list[tuple[float, str]] = [(0.0, start_node_id)]

        while heap:
            current_dist, current = heapq.heappop(heap)
            if current_dist > distances[current]:
                continue
            if current == end_node_id:
                break

            for neighbor, weight in self.adjacency_list.get(current, []):
                new_dist = current_dist + weight
                if new_dist < distances.get(neighbor, float("inf")):
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(heap, (new_dist, neighbor))

        # reconstruct path
        if distances[end_node_id] == float("inf"):
            return []

        path: list[str] = []
        cur: str | None = end_node_id
        while cur is not None:
            path.append(cur)
            cur = previous[cur]

        path.reverse()
        return path
