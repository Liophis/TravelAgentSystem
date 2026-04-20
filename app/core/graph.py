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
        """Placeholder implementation for future handwritten algorithm."""
        return [start_node_id, "模拟中间点", end_node_id]
