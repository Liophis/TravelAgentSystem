from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Building, Facility, FacilityCategory, MapEdge, MapNode
from app.seed.sample_data import BUPT_SHAHE_CENTER


DEMO_BUILDING_PREFIX = "Campus-density seed building polygon"
DEMO_FACILITY_PREFIX = "Campus-density seed facility"
DEMO_NODE_PREFIX = "bupt-node-"


def get_map_stats_from_db(session: Session, include_demo: bool = False) -> dict[str, int]:
    roads = _load_roads(session, include_demo=include_demo)
    buildings = _load_buildings(session, include_demo=include_demo)
    facilities = _load_facilities(session, include_demo=include_demo)
    hidden_demo = _demo_layer_counts(session)
    return {
        "nodes": _count(session, MapNode),
        "roads": len(roads),
        "buildings": len(buildings),
        "facilities": len(facilities),
        "categories": _count(session, FacilityCategory),
        "hidden_demo_roads": hidden_demo["roads"] if not include_demo else 0,
        "hidden_demo_buildings": hidden_demo["buildings"] if not include_demo else 0,
        "hidden_demo_facilities": hidden_demo["facilities"] if not include_demo else 0,
    }


def get_map_payload_from_db(session: Session, include_demo: bool = False) -> dict[str, Any]:
    roads = _load_roads(session, include_demo=include_demo)
    buildings = _load_buildings(session, include_demo=include_demo)
    facilities = _load_facilities(session, include_demo=include_demo)
    categories = [
        category.code for category in session.scalars(select(FacilityCategory).order_by(FacilityCategory.code)).all()
    ]
    return {
        "center": BUPT_SHAHE_CENTER,
        "statistics": get_map_stats_from_db(session, include_demo=include_demo),
        "roads": roads,
        "buildings": buildings,
        "facilities": facilities,
        "facility_categories": categories,
        "geojson": _to_feature_collection(roads, buildings, facilities),
        "source": "database-real-priority-map-layers" if not include_demo else "database-all-map-layers",
        "layer_policy": {
            "include_demo": include_demo,
            "buildings": "OSM/imported building polygons only by default",
            "facilities": "AMap/OSM imported POIs only by default",
            "roads": "OSM/imported roads only by default; local seed graph remains for algorithm demo",
        },
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
            "congestion": edge.congestion,
            "walk_speed": edge.walk_speed,
            "bike_speed": edge.bike_speed,
            "electric_cart_speed": edge.electric_cart_speed,
            "allowed_modes": edge.allowed_modes,
            "geometry": edge.geometry,
        }
        for edge in session.scalars(select(MapEdge).order_by(MapEdge.id)).all()
    ]


def get_buildings_from_db(session: Session, include_demo: bool = False) -> list[dict[str, Any]]:
    return get_map_payload_from_db(session, include_demo=include_demo)["buildings"]


def get_facilities_from_db(session: Session, include_demo: bool = False) -> list[dict[str, Any]]:
    return get_map_payload_from_db(session, include_demo=include_demo)["facilities"]


def cleanup_demo_map_layers(session: Session, remove_buildings: bool = True, remove_facilities: bool = True) -> dict[str, Any]:
    counts = _demo_layer_counts(session)
    if remove_buildings:
        session.execute(delete(Building).where(Building.description.like(f"{DEMO_BUILDING_PREFIX}%")))
    if remove_facilities:
        session.execute(delete(Facility).where(Facility.description.like(f"{DEMO_FACILITY_PREFIX}%")))
    session.commit()
    after = _demo_layer_counts(session)
    return {
        "removed_buildings": counts["buildings"] - after["buildings"] if remove_buildings else 0,
        "removed_facilities": counts["facilities"] - after["facilities"] if remove_facilities else 0,
        "remaining_demo_roads": after["roads"],
        "remaining_demo_buildings": after["buildings"],
        "remaining_demo_facilities": after["facilities"],
        "algorithm_trace": {
            "stage": "stage-27-real-map-layer-cleanup",
            "policy": "remove offline fake building/facility layers; keep seed road graph for local Dijkstra fallback",
        },
    }


def _count(session: Session, model: type[Any]) -> int:
    return len(session.scalars(select(model)).all())


def _load_roads(session: Session, include_demo: bool) -> list[dict[str, Any]]:
    nodes = {node.id: node.external_id for node in session.scalars(select(MapNode)).all()}
    roads = []
    for edge in session.scalars(select(MapEdge).order_by(MapEdge.id)).all():
        if not include_demo and _is_demo_edge(edge, nodes):
            continue
        roads.append(
            {
                "id": f"edge-{edge.id}",
                "from_node_id": edge.from_node_id,
                "to_node_id": edge.to_node_id,
                "distance": edge.distance,
                "congestion": edge.congestion,
                "allowed_modes": edge.allowed_modes,
                "path": edge.geometry,
            }
        )
    return roads


def _load_buildings(session: Session, include_demo: bool) -> list[dict[str, Any]]:
    buildings = []
    for building in session.scalars(select(Building).order_by(Building.id)).all():
        if not include_demo and _is_demo_building(building):
            continue
        buildings.append(
            {
                "id": f"building-{building.id}",
                "name": building.name,
                "category": building.category,
                "polygon": building.polygon,
                "description": building.description,
            }
        )
    return buildings


def _load_facilities(session: Session, include_demo: bool) -> list[dict[str, Any]]:
    facilities = []
    for facility in session.scalars(select(Facility).order_by(Facility.id)).all():
        if not include_demo and _is_demo_facility(facility):
            continue
        facilities.append(
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
        )
    return facilities


def _demo_layer_counts(session: Session) -> dict[str, int]:
    nodes = {node.id: node.external_id for node in session.scalars(select(MapNode)).all()}
    return {
        "roads": sum(
            1 for edge in session.scalars(select(MapEdge)).all()
            if _is_demo_edge(edge, nodes)
        ),
        "buildings": sum(
            1 for building in session.scalars(select(Building)).all()
            if _is_demo_building(building)
        ),
        "facilities": sum(
            1 for facility in session.scalars(select(Facility)).all()
            if _is_demo_facility(facility)
        ),
    }


def _is_demo_edge(edge: MapEdge, node_external_ids: dict[int, str]) -> bool:
    from_external_id = node_external_ids.get(edge.from_node_id, "")
    to_external_id = node_external_ids.get(edge.to_node_id, "")
    return from_external_id.startswith(DEMO_NODE_PREFIX) and to_external_id.startswith(DEMO_NODE_PREFIX)


def _is_demo_building(building: Building) -> bool:
    return bool(building.description and building.description.startswith(DEMO_BUILDING_PREFIX))


def _is_demo_facility(facility: Facility) -> bool:
    return bool(facility.description and facility.description.startswith(DEMO_FACILITY_PREFIX))


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
                    "congestion": road["congestion"],
                    "allowed_modes": road["allowed_modes"],
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
