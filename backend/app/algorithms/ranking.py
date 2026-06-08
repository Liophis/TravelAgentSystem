from collections.abc import Callable, Iterable
from heapq import heappop, heappush, heapreplace
from typing import TypeVar


T = TypeVar("T")


def top_k_smallest(items: Iterable[T], key: Callable[[T], float], k: int) -> list[T]:
    if k <= 0:
        return []

    heap: list[tuple[float, int, T]] = []
    for index, item in enumerate(items):
        score = key(item)
        entry = (-score, -index, item)
        if len(heap) < k:
            heappush(heap, entry)
        elif entry > heap[0]:
            heapreplace(heap, entry)

    result: list[T] = []
    while heap:
        result.append(heappop(heap)[2])
    result.reverse()
    return result


def top_k_smallest_tuple(items: Iterable[T], key: Callable[[T], tuple[float, ...]], k: int) -> list[T]:
    if k <= 0:
        return []

    heap: list[tuple[tuple[float, ...], int, T]] = []
    for index, item in enumerate(items):
        score = key(item)
        entry = (tuple(-value for value in score), -index, item)
        if len(heap) < k:
            heappush(heap, entry)
        elif entry > heap[0]:
            heapreplace(heap, entry)

    result: list[T] = []
    while heap:
        result.append(heappop(heap)[2])
    result.reverse()
    return result
