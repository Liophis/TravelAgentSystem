from __future__ import annotations


class MinHeap:
    """A handwritten binary min-heap for Top-K scenarios."""

    def __init__(self) -> None:
        self._data: list[tuple[float, object]] = []

    def __len__(self) -> int:
        return len(self._data)

    def peek(self) -> tuple[float, object] | None:
        return self._data[0] if self._data else None

    def push(self, item: tuple[float, object]) -> None:
        self._data.append(item)
        self._sift_up(len(self._data) - 1)

    def pop(self) -> tuple[float, object] | None:
        if not self._data:
            return None
        self._swap(0, len(self._data) - 1)
        item = self._data.pop()
        if self._data:
            self._sift_down(0)
        return item

    def pushpop(self, item: tuple[float, object]) -> tuple[float, object]:
        if not self._data:
            return item
        if item[0] <= self._data[0][0]:
            return item
        root = self._data[0]
        self._data[0] = item
        self._sift_down(0)
        return root

    def to_sorted_desc(self) -> list[tuple[float, object]]:
        return sorted(self._data, key=lambda x: x[0], reverse=True)

    def _parent(self, index: int) -> int:
        return (index - 1) // 2

    def _left(self, index: int) -> int:
        return index * 2 + 1

    def _right(self, index: int) -> int:
        return index * 2 + 2

    def _swap(self, i: int, j: int) -> None:
        self._data[i], self._data[j] = self._data[j], self._data[i]

    def _sift_up(self, index: int) -> None:
        while index > 0:
            parent = self._parent(index)
            if self._data[parent][0] <= self._data[index][0]:
                break
            self._swap(parent, index)
            index = parent

    def _sift_down(self, index: int) -> None:
        size = len(self._data)
        while True:
            smallest = index
            left = self._left(index)
            right = self._right(index)

            if left < size and self._data[left][0] < self._data[smallest][0]:
                smallest = left
            if right < size and self._data[right][0] < self._data[smallest][0]:
                smallest = right
            if smallest == index:
                return

            self._swap(index, smallest)
            index = smallest


def top_k(items: list[tuple[float, object]], k: int) -> list[tuple[float, object]]:
    """Return Top-K items by score in descending order with handwritten heap."""
    if k <= 0:
        return []

    heap = MinHeap()
    for item in items:
        if len(heap) < k:
            heap.push(item)
        else:
            heap.pushpop(item)

    return heap.to_sorted_desc()
