from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Building, Facility, FacilityCategory, MapEdge, MapNode
from app.seed.sample_data import BUPT_SHAHE_CENTER


def get_map_stats_from_db(session: Session) -> dict[str, int]:
    return {
        "nodes": _count(session, MapNode),
        "roads": _count(session, MapEdge),
        "buildings": _count(session, Building),
        "facilities": _count(session, Facility),
        "categories": _count(session, FacilityCategory),
    }


def get_map_payload_from_db(session: Session) -> dict[str, Any]:
    roads = [
        {
            "id": f"edge-{edge.id}",
            "from_node_id": edge.from_node_id,
            "to_node_id": edge.to_node_id,
            "distance": edge.distance,
            "path": edge.geometry,
        }
        for edge in session.scalars(select(MapEdge).order_by(MapEdge.id)).all()
    ]
    buildings = [
        {
            "id": f"building-{building.id}",
            "name": building.name,
            "category": building.category,
            "polygon": building.polygon,
            "description": building.description,
        }
        for building in session.scalars(select(Building).order_by(Building.id)).all()
    ]
    facilities = [
        {
            "id": f"facility-{facility.id}",
            "name": facility.name,
            "category": facility.category.code,
            "category_name": facility.category.name,
            "lng": facility.lng,
            "lat": facility.lat,
            "description": facility.description,
            "nearest_node_id": facility.nearest_node_id,
        }
        for facility in session.scalars(select(Facility).order_by(Facility.id)).all()
    ]
    categories = [
        category.code for category in session.scalars(select(FacilityCategory).order_by(FacilityCategory.code)).all()
    ]
    return {
        "center": BUPT_SHAHE_CENTER,
        "statistics": get_map_stats_from_db(session),
        "roads": roads,
        "buildings": buildings,
        "facilities": facilities,
        "facility_categories": categories,
        "geojson": _to_feature_collection(roads, buildings, facilities),
        "source": "database-seed-stage-3",
    }


def get_map_nodes_from_db(session: Session) -> list[dict[str, Any]]:
    return [
        {
            "id": node.id,
            "external_id": node.external_id,
            "name": node.name,
            "lng": node.lng,
            "lat": node.lat,
        }
        for node in session.scalars(select(MapNode).order_by(MapNode.id)).all()
    ]


def get_map_edges_from_db(session: Session) -> list[dict[str, Any]]:
    return [
        {
            "id": edge.id,
            "from_node_id": edge.from_node_id,
            "to_node_id": edge.to_node_id,
            "distance": edge.distance,
            "walk_time": edge.walk_time,
            "geometry": edge.geometry,
        }
        for edge in session.scalars(select(MapEdge).order_by(MapEdge.id)).all()
    ]


def get_buildings_from_db(session: Session) -> list[dict[str, Any]]:
    return get_map_payload_from_db(session)["buildings"]


def get_facilities_from_db(session: Session) -> list[dict[str, Any]]:
    return get_map_payload_from_db(session)["facilities"]


def _count(session: Session, model: type[Any]) -> int:
    return len(session.scalars(select(model)).all())


def _to_feature_collection(
    roads: list[dict[str, Any]],
    buildings: list[dict[str, Any]],
    facilities: list[dict[str, Any]],
) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for road in roads:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": road["path"]},
                "properties": {
                    "id": road["id"],
                    "kind": "road",
                    "distance": road["distance"],
                },
            }
        )
    for building in buildings:
        if not building["polygon"]:
            continue
        ring = [*building["polygon"], building["polygon"][0]]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [ring]},
                "properties": {
                    "id": building["id"],
                    "name": building["name"],
                    "kind": "building",
                    "category": building["category"],
                },
            }
        )
    for facility in facilities:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [facility["lng"], facility["lat"]]},
                "properties": {
                    "id": facility["id"],
                    "name": facility["name"],
                    "category": facility["category"],
                    "category_name": facility["category_name"],
                    "description": facility["description"],
                    "kind": "facility",
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}
