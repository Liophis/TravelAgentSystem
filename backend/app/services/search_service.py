from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Building, Destination, Facility


def search_places_from_db(
    session: Session,
    keyword: str,
    category: str | None,
    limit: int,
) -> dict[str, Any]:
    normalized_keyword = keyword.casefold().strip()
    results: list[dict[str, Any]] = []
    if normalized_keyword:
        results.extend(_search_destinations(session, normalized_keyword, category))
        results.extend(_search_buildings(session, normalized_keyword, category))
        results.extend(_search_facilities(session, normalized_keyword, category))

    ranked = sorted(results, key=lambda item: (item["rank"], item["source"], item["name"]))[:limit]
    for item in ranked:
        item.pop("rank", None)
    return {
        "items": ranked,
        "total": len(results),
        "keyword": keyword,
        "category": category,
        "algorithm_trace": {
            "stage": "stage-6-destination-search-recommend",
            "algorithm": "case-insensitive contains search",
            "sources": "destinations, buildings, facilities",
            "matched": str(len(results)),
            "returned": str(len(ranked)),
        },
    }


def _search_destinations(session: Session, keyword: str, category: str | None) -> list[dict[str, Any]]:
    destinations = session.scalars(select(Destination).options(selectinload(Destination.tags))).all()
    results = []
    for destination in destinations:
        if category and destination.category != category:
            continue
        text = " ".join(
            [
                destination.name,
                destination.category,
                destination.description,
                *[tag.tag for tag in destination.tags],
            ]
        ).casefold()
        if keyword not in text:
            continue
        results.append(
            {
                "id": f"destination-{destination.id}",
                "source": "destination",
                "source_id": destination.id,
                "name": destination.name,
                "category": destination.category,
                "lng": destination.lng,
                "lat": destination.lat,
                "description": destination.description,
                "rank": _rank(destination.name, destination.category, keyword),
            }
        )
    return results


def _search_buildings(session: Session, keyword: str, category: str | None) -> list[dict[str, Any]]:
    buildings = session.scalars(select(Building).order_by(Building.id)).all()
    results = []
    for building in buildings:
        if category and building.category != category:
            continue
        text = " ".join([building.name, building.category, building.description or ""]).casefold()
        if keyword not in text:
            continue
        first_point = building.polygon[0] if building.polygon else [0, 0]
        results.append(
            {
                "id": f"building-{building.id}",
                "source": "building",
                "source_id": building.id,
                "name": building.name,
                "category": building.category,
                "lng": first_point[0],
                "lat": first_point[1],
                "description": building.description,
                "rank": _rank(building.name, building.category, keyword),
            }
        )
    return results


def _search_facilities(session: Session, keyword: str, category: str | None) -> list[dict[str, Any]]:
    facilities = session.scalars(select(Facility).options(selectinload(Facility.category))).all()
    results = []
    for facility in facilities:
        if category and facility.category.code != category:
            continue
        text = " ".join(
            [
                facility.name,
                facility.category.code,
                facility.category.name,
                facility.description or "",
            ]
        ).casefold()
        if keyword not in text:
            continue
        results.append(
            {
                "id": f"facility-{facility.id}",
                "source": "facility",
                "source_id": facility.id,
                "name": facility.name,
                "category": facility.category.code,
                "category_name": facility.category.name,
                "lng": facility.lng,
                "lat": facility.lat,
                "description": facility.description,
                "rank": _rank(facility.name, facility.category.code, keyword),
            }
        )
    return results


def _rank(name: str, category: str, keyword: str) -> int:
    normalized_name = name.casefold()
    normalized_category = category.casefold()
    if normalized_name == keyword:
        return 0
    if normalized_name.startswith(keyword):
        return 1
    if normalized_category == keyword:
        return 2
    return 3
