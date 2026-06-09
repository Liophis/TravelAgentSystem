from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.scenes import DEFAULT_SCENE_KEY, SUMMER_PALACE_SCENE_KEY, normalize_scene_key
from app.models import Building, Facility, MapEdge, MapNode
from app.services.reference_campus_import_service import BUPT_NAVIGATION_BLOCKLIST


GENERIC_BUILDING_NAMES = {"", "OSM building", "building", "yes", "nan", "none"}
GENERIC_POI_NAMES = {"", "poi", "nan", "none"}
FACILITY_NAME_NORMALIZATION = {
    "toilets": "洗手间",
    "toilet": "洗手间",
    "restroom": "洗手间",
    "wc": "洗手间",
    "cafe": "咖啡馆",
    "fast_food": "快餐",
    "restaurant": "餐厅",
    "drinking_water": "饮水点",
    "parking": "停车场",
    "bicycle_parking": "自行车停放点",
    "ticket": "售票处",
    "tickets": "售票处",
    "entrance": "入口",
    "gate": "入口",
}


def clean_navigation_scene_data(
    session: Session,
    scene_key: str | None = None,
) -> dict[str, Any]:
    resolved_scene_key = normalize_scene_key(scene_key)
    removed_facilities = _remove_blocked_facilities(session, resolved_scene_key)
    normalized_facilities = _normalize_facility_names(session, resolved_scene_key)
    invalid_edges = _remove_invalid_edges(session, resolved_scene_key)
    orphan_nodes = _remove_orphan_import_nodes(session, resolved_scene_key)
    session.commit()
    return {
        "scene_key": resolved_scene_key,
        "removed_blocked_facilities": removed_facilities,
        "normalized_facilities": normalized_facilities,
        "removed_invalid_edges": invalid_edges,
        "removed_orphan_import_nodes": orphan_nodes,
        "algorithm_trace": {
            "stage": "stage-41-navigation-data-cleaning",
            "policy": "clean user-facing navigation data without removing topology nodes needed by Dijkstra",
        },
    }


def clean_all_navigation_scenes(session: Session) -> dict[str, Any]:
    summaries = [
        clean_navigation_scene_data(session, DEFAULT_SCENE_KEY),
        clean_navigation_scene_data(session, SUMMER_PALACE_SCENE_KEY),
    ]
    return {
        "scenes": summaries,
        "total_removed_blocked_facilities": sum(item["removed_blocked_facilities"] for item in summaries),
        "total_normalized_facilities": sum(item["normalized_facilities"] for item in summaries),
        "total_removed_invalid_edges": sum(item["removed_invalid_edges"] for item in summaries),
        "total_removed_orphan_import_nodes": sum(item["removed_orphan_import_nodes"] for item in summaries),
    }


def is_generic_building_name(name: str | None) -> bool:
    return (name or "").strip() in GENERIC_BUILDING_NAMES


def is_generic_poi_name(name: str | None) -> bool:
    return (name or "").strip().casefold() in GENERIC_POI_NAMES


def _remove_blocked_facilities(session: Session, scene_key: str) -> int:
    if scene_key != DEFAULT_SCENE_KEY:
        return 0
    ids = [
        facility.id
        for facility in session.scalars(select(Facility).where(Facility.scene_key == scene_key)).all()
        if facility.name in BUPT_NAVIGATION_BLOCKLIST
    ]
    if not ids:
        return 0
    session.execute(delete(Facility).where(Facility.id.in_(ids)))
    session.flush()
    return len(ids)


def _normalize_facility_names(session: Session, scene_key: str) -> int:
    changed = 0
    facilities = session.scalars(select(Facility).where(Facility.scene_key == scene_key)).all()
    for facility in facilities:
        normalized = _normalized_facility_name(facility)
        if normalized and normalized != facility.name:
            facility.name = normalized
            changed += 1
    session.flush()
    return changed


def _normalized_facility_name(facility: Facility) -> str | None:
    raw_name = (facility.name or "").strip()
    raw_key = raw_name.casefold()
    category_code = facility.category.code.casefold() if facility.category else ""
    if raw_key in FACILITY_NAME_NORMALIZATION:
        return FACILITY_NAME_NORMALIZATION[raw_key]
    if raw_key in GENERIC_POI_NAMES and category_code in FACILITY_NAME_NORMALIZATION:
        return FACILITY_NAME_NORMALIZATION[category_code]
    if raw_key == category_code and category_code in FACILITY_NAME_NORMALIZATION:
        return FACILITY_NAME_NORMALIZATION[category_code]
    return None


def _remove_invalid_edges(session: Session, scene_key: str) -> int:
    edge_ids = [
        edge.id
        for edge in session.scalars(select(MapEdge).where(MapEdge.scene_key == scene_key)).all()
        if edge.from_node_id == edge.to_node_id or edge.distance <= 0 or len(edge.geometry or []) < 2
    ]
    if not edge_ids:
        return 0
    session.execute(delete(MapEdge).where(MapEdge.id.in_(edge_ids)))
    session.flush()
    return len(edge_ids)


def _remove_orphan_import_nodes(session: Session, scene_key: str) -> int:
    edge_node_ids = {
        node_id
        for edge in session.scalars(select(MapEdge).where(MapEdge.scene_key == scene_key)).all()
        for node_id in (edge.from_node_id, edge.to_node_id)
    }
    facility_node_ids = {
        facility.nearest_node_id
        for facility in session.scalars(select(Facility).where(Facility.scene_key == scene_key)).all()
        if facility.nearest_node_id is not None
    }
    protected_node_ids = edge_node_ids | facility_node_ids
    orphan_ids = [
        node.id
        for node in session.scalars(select(MapNode).where(MapNode.scene_key == scene_key)).all()
        if node.id not in protected_node_ids and _is_import_node(node)
    ]
    if not orphan_ids:
        return 0
    session.execute(delete(MapNode).where(MapNode.id.in_(orphan_ids)))
    session.flush()
    return len(orphan_ids)


def _is_import_node(node: MapNode) -> bool:
    return node.external_id.startswith(("osm-", "ref-bupt-shahe:"))
