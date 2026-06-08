from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Building, Destination, Facility, MapNode

BUPT_SHAHE_CAMPUS_BOUNDS = {
    "min_lng": 116.2770,
    "max_lng": 116.2896,
    "min_lat": 40.1534,
    "max_lat": 40.1602,
}


def search_places_from_db(
    session: Session,
    keyword: str,
    category: str | None,
    limit: int,
    scope: str = "all",
) -> dict[str, Any]:
    normalized_keyword = keyword.casefold().strip()
    normalized_scope = _normalize_scope(scope)
    results: list[dict[str, Any]] = []
    if normalized_keyword or normalized_scope == "campus":
        if normalized_scope in {"all", "destinations"}:
            results.extend(_search_destinations(session, normalized_keyword, category))
        if normalized_scope in {"all", "campus"}:
            results.extend(_search_buildings(session, normalized_keyword, category, campus_only=normalized_scope == "campus"))
            results.extend(_search_facilities(session, normalized_keyword, category, campus_only=normalized_scope == "campus"))
            results.extend(_search_map_nodes(session, normalized_keyword, category, campus_only=normalized_scope == "campus"))

    ranked = sorted(results, key=lambda item: (item["rank"], _source_priority(item["source"], normalized_scope), item["name"]))[:limit]
    for item in ranked:
        item.pop("rank", None)
    return {
        "items": ranked,
        "total": len(results),
        "keyword": keyword,
        "category": category,
        "scope": normalized_scope,
        "algorithm_trace": {
            "stage": "stage-6-destination-search-recommend",
            "algorithm": "case-insensitive contains search",
            "sources": _scope_sources(normalized_scope),
            "scope": normalized_scope,
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


def _search_buildings(
    session: Session,
    keyword: str,
    category: str | None,
    campus_only: bool = False,
) -> list[dict[str, Any]]:
    buildings = session.scalars(select(Building).order_by(Building.id)).all()
    results = []
    for building in buildings:
        if category and building.category != category:
            continue
        center = _building_center(building.polygon)
        if campus_only and not _is_in_bupt_shahe_bounds(center[0], center[1]):
            continue
        text = " ".join([building.name, building.category, building.description or ""]).casefold()
        if keyword not in text:
            continue
        results.append(
            {
                "id": f"building-{building.id}",
                "source": "building",
                "source_id": building.id,
                "name": building.name,
                "category": building.category,
                "lng": center[0],
                "lat": center[1],
                "description": building.description,
                "rank": _rank(building.name, building.category, keyword),
            }
        )
    return results


def _search_facilities(
    session: Session,
    keyword: str,
    category: str | None,
    campus_only: bool = False,
) -> list[dict[str, Any]]:
    facilities = session.scalars(select(Facility).options(selectinload(Facility.category))).all()
    results = []
    for facility in facilities:
        if category and facility.category.code != category:
            continue
        if campus_only and not _is_in_bupt_shahe_bounds(facility.lng, facility.lat):
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


def _search_map_nodes(
    session: Session,
    keyword: str,
    category: str | None,
    campus_only: bool = False,
) -> list[dict[str, Any]]:
    if category and category not in {"node", "campus_node", "route_node"}:
        return []
    nodes = session.scalars(select(MapNode).order_by(MapNode.id)).all()
    results = []
    for node in nodes:
        if not node.name:
            continue
        if campus_only and not _is_in_bupt_shahe_bounds(node.lng, node.lat):
            continue
        text = " ".join([node.name, node.external_id, "campus_node", "route_node"]).casefold()
        if keyword and keyword not in text:
            continue
        results.append(
            {
                "id": f"node-{node.id}",
                "source": "node",
                "source_id": node.id,
                "name": node.name,
                "category": "campus_node",
                "lng": node.lng,
                "lat": node.lat,
                "description": "BUPT Shahe named topology node.",
                "rank": _rank(node.name, "campus_node", keyword),
            }
        )
    return results


def _normalize_scope(scope: str | None) -> str:
    if scope in {"all", "destinations", "campus"}:
        return scope
    return "all"


def _scope_sources(scope: str) -> str:
    return {
        "destinations": "destinations",
        "campus": "BUPT Shahe campus buildings, facilities, named topology nodes",
    }.get(scope, "destinations, buildings, facilities")


def _source_priority(source: str, scope: str) -> int:
    if scope == "campus":
        return {
            "node": 0,
            "building": 1,
            "facility": 2,
        }.get(source, 9)
    return {
        "destination": 0,
        "building": 1,
        "facility": 2,
        "node": 3,
    }.get(source, 9)


def _building_center(polygon: list[list[float]]) -> tuple[float, float]:
    if not polygon:
        return (0.0, 0.0)
    return (
        sum(point[0] for point in polygon) / len(polygon),
        sum(point[1] for point in polygon) / len(polygon),
    )


def _is_in_bupt_shahe_bounds(lng: float, lat: float) -> bool:
    return (
        BUPT_SHAHE_CAMPUS_BOUNDS["min_lng"] <= lng <= BUPT_SHAHE_CAMPUS_BOUNDS["max_lng"]
        and BUPT_SHAHE_CAMPUS_BOUNDS["min_lat"] <= lat <= BUPT_SHAHE_CAMPUS_BOUNDS["max_lat"]
    )


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
