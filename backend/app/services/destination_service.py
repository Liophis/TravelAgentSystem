from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Destination


SortMode = Literal["popularity", "rating", "name"]


def list_destinations_from_db(
    session: Session,
    category: str | None,
    q: str | None,
    sort: SortMode,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    destinations = _filter_destinations(_load_destinations(session), category, q)
    sorted_destinations = _sort_destinations(destinations, sort)
    items = sorted_destinations[offset : offset + limit]
    categories = sorted({destination.category for destination in destinations})
    return {
        "items": [serialize_destination(destination) for destination in items],
        "total": len(destinations),
        "limit": limit,
        "offset": offset,
        "categories": categories,
        "algorithm_trace": {
            "stage": "stage-6-destination-search-recommend",
            "filter": "category and keyword contains matching",
            "sort": sort,
            "source": "real China attraction/university destination seed",
            "matched": str(len(destinations)),
            "returned": str(len(items)),
        },
    }


def get_destination_detail_from_db(session: Session, destination_id: int) -> dict[str, Any] | None:
    destination = session.scalar(
        select(Destination)
        .options(selectinload(Destination.tags))
        .where(Destination.id == destination_id)
    )
    if destination is None:
        return None
    return {
        **serialize_destination(destination),
        "algorithm_trace": {
            "stage": "stage-6-destination-search-recommend",
            "source": "real China attraction/university destination seed",
        },
    }


def serialize_destination(destination: Destination) -> dict[str, Any]:
    return {
        "id": destination.id,
        "name": destination.name,
        "category": destination.category,
        "description": destination.description,
        "lng": destination.lng,
        "lat": destination.lat,
        "rating": round(destination.rating, 2),
        "popularity": destination.popularity,
        "tags": [tag.tag for tag in destination.tags],
    }


def _load_destinations(session: Session) -> list[Destination]:
    return list(
        session.scalars(
            select(Destination)
            .options(selectinload(Destination.tags))
            .order_by(Destination.id)
        ).all()
    )


def _filter_destinations(
    destinations: list[Destination],
    category: str | None,
    q: str | None,
) -> list[Destination]:
    keyword = q.casefold().strip() if q else ""
    results = []
    for destination in destinations:
        if category and destination.category != category:
            continue
        if keyword and not _matches_keyword(destination, keyword):
            continue
        results.append(destination)
    return results


def _matches_keyword(destination: Destination, keyword: str) -> bool:
    haystack = " ".join(
        [
            destination.name,
            destination.category,
            destination.description,
            *[tag.tag for tag in destination.tags],
        ]
    ).casefold()
    return keyword in haystack


def _sort_destinations(destinations: list[Destination], sort: SortMode) -> list[Destination]:
    if sort == "rating":
        return sorted(destinations, key=lambda item: (-item.rating, -item.popularity, item.id))
    if sort == "name":
        return sorted(destinations, key=lambda item: item.name)
    return sorted(destinations, key=lambda item: (-item.popularity, -item.rating, item.id))
