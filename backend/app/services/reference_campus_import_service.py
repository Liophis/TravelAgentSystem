import json
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.algorithms.route_planning import approximate_distance_meters
from app.core.scenes import DEFAULT_SCENE_KEY, normalize_scene_key
from app.models import Facility, FacilityCategory, MapEdge, MapNode


REFERENCE_NODE_PREFIX = "ref-bupt-shahe:"
REFERENCE_FACILITY_PREFIX = "Imported from BUPT Shahe reference campus data."
DEFAULT_SOURCE_DIR = Path("data/reference/bupt-shahe")


class ReferenceCampusImportError(RuntimeError):
    pass


def import_reference_campus_to_db(
    session: Session,
    source_dir: str | Path = DEFAULT_SOURCE_DIR,
    replace_campus_layers: bool = True,
    scene_key: str | None = DEFAULT_SCENE_KEY,
) -> dict[str, Any]:
    resolved_scene_key = normalize_scene_key(scene_key)
    source_path = Path(source_dir)
    scene_payload = _load_json(source_path / "raw_wgs84" / "scenes.json")
    geojson_payload = _load_json(source_path / "topology" / "scene_bupt_campus.geojson")
    scene = _resolve_single_scene(scene_payload)

    if replace_campus_layers:
        removed = _clear_previous_reference_layers(session, remove_osm_roads=True, scene_key=resolved_scene_key)
    else:
        removed = {"nodes": 0, "edges": 0, "facilities": 0, "osm_nodes": 0, "osm_edges": 0}

    external_to_node: dict[str, MapNode] = {}
    nodes_imported = 0
    nodes_skipped = 0
    invalid_nodes = 0
    for node_payload in scene.get("nodes", []):
        try:
            external_id = _node_external_id(str(node_payload["id"]))
            node = MapNode(
                scene_key=resolved_scene_key,
                external_id=external_id,
                name=_node_name(node_payload),
                lng=float(node_payload["x"]),
                lat=float(node_payload["y"]),
            )
        except (KeyError, TypeError, ValueError):
            invalid_nodes += 1
            continue
        existing = session.scalar(
            select(MapNode).where(MapNode.external_id == external_id, MapNode.scene_key == resolved_scene_key)
        )
        if existing is not None:
            external_to_node[external_id] = existing
            nodes_skipped += 1
            continue
        session.add(node)
        external_to_node[external_id] = node
        nodes_imported += 1
    session.flush()

    edges_imported = 0
    edges_skipped = 0
    invalid_edges = 0
    for edge_payload in scene.get("edges", []):
        try:
            from_node = external_to_node[_node_external_id(str(edge_payload["fromNodeId"]))]
            to_node = external_to_node[_node_external_id(str(edge_payload["toNodeId"]))]
        except KeyError:
            invalid_edges += 1
            continue
        distance = _edge_distance(edge_payload, from_node, to_node)
        if distance <= 0:
            invalid_edges += 1
            continue
        allowed_modes = _allowed_modes(edge_payload)
        walk_speed = _mode_speed(edge_payload, "walking", 1.2)
        bike_speed = _mode_speed(edge_payload, "bicycle", 0.0) if "bike" in allowed_modes else 0.0
        congestion = _congestion(edge_payload)
        signature = (from_node.id, to_node.id, round(distance, 1), tuple(allowed_modes))
        if _edge_exists(session, signature):
            edges_skipped += 1
            continue
        session.add(
            MapEdge(
                scene_key=resolved_scene_key,
                from_node_id=from_node.id,
                to_node_id=to_node.id,
                distance=distance,
                walk_time=distance / max(walk_speed * congestion, 0.1),
                congestion=congestion,
                walk_speed=walk_speed,
                bike_speed=bike_speed,
                electric_cart_speed=0.0,
                allowed_modes=allowed_modes,
                geometry=[[from_node.lng, from_node.lat], [to_node.lng, to_node.lat]],
            )
        )
        edges_imported += 1
    session.flush()

    categories = _load_or_create_categories(session)
    facility_items = _facility_items_from_scene(scene, external_to_node)
    facility_items.extend(_facility_items_from_geojson(geojson_payload, external_to_node))
    facilities_imported, facilities_skipped = _import_facilities(
        session,
        categories,
        facility_items,
        scene_key=resolved_scene_key,
    )
    rebound_facilities = _rebind_facilities_to_reference_nodes(
        session,
        list(external_to_node.values()),
        scene_key=resolved_scene_key,
    )

    session.commit()
    return {
        "source": "reference-bupt-shahe",
        "scene_key": resolved_scene_key,
        "source_dir": str(source_path),
        "scene_id": scene.get("id"),
        "scene_name": scene.get("name"),
        "nodes_imported": nodes_imported,
        "nodes_skipped": nodes_skipped,
        "edges_imported": edges_imported,
        "edges_skipped": edges_skipped,
        "facilities_imported": facilities_imported,
        "facilities_skipped": facilities_skipped,
        "invalid_nodes": invalid_nodes,
        "invalid_edges": invalid_edges,
        "rebound_facilities": rebound_facilities,
        "removed": removed,
        "algorithm_trace": {
            "stage": "stage-28-reference-campus-navigation",
            "pipeline": "WGS84 scene JSON + GeoJSON topology -> map_nodes/map_edges/facilities",
            "coordinate_contract": "source WGS84 [lng, lat], frontend converts to GCJ-02 for AMap",
            "route_graph": "local Dijkstra graph from manually supplied campus topology",
        },
    }


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ReferenceCampusImportError(f"Reference campus file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReferenceCampusImportError(f"Invalid JSON file: {path}") from exc


def _resolve_single_scene(payload: dict[str, Any]) -> dict[str, Any]:
    scenes = payload.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ReferenceCampusImportError("scenes.json must contain a non-empty scenes list.")
    scene = scenes[0]
    if not isinstance(scene.get("nodes"), list) or not isinstance(scene.get("edges"), list):
        raise ReferenceCampusImportError("Scene must contain nodes and edges lists.")
    return scene


def _clear_previous_reference_layers(session: Session, remove_osm_roads: bool, scene_key: str) -> dict[str, int]:
    reference_node_ids = [
        node.id
        for node in session.scalars(select(MapNode).where(MapNode.scene_key == scene_key)).all()
        if node.external_id.startswith(REFERENCE_NODE_PREFIX)
    ]
    osm_node_ids = [
        node.id
        for node in session.scalars(select(MapNode).where(MapNode.scene_key == scene_key)).all()
        if remove_osm_roads and node.external_id.startswith("osm-")
    ]
    node_ids = [*reference_node_ids, *osm_node_ids]
    edge_ids = [
        edge.id
        for edge in session.scalars(select(MapEdge)).all()
        if edge.from_node_id in node_ids or edge.to_node_id in node_ids
    ]
    if edge_ids:
        session.execute(delete(MapEdge).where(MapEdge.id.in_(edge_ids)))
    if node_ids:
        for facility in session.scalars(
            select(Facility).where(Facility.scene_key == scene_key, Facility.nearest_node_id.in_(node_ids))
        ).all():
            facility.nearest_node_id = None
        session.execute(delete(MapNode).where(MapNode.id.in_(node_ids)))
    reference_facility_ids = [
        facility.id
        for facility in session.scalars(select(Facility).where(Facility.scene_key == scene_key)).all()
        if facility.description and facility.description.startswith(REFERENCE_FACILITY_PREFIX)
    ]
    if reference_facility_ids:
        session.execute(delete(Facility).where(Facility.id.in_(reference_facility_ids)))
    session.flush()
    return {
        "nodes": len(reference_node_ids),
        "edges": len(edge_ids),
        "facilities": len(reference_facility_ids),
        "osm_nodes": len(osm_node_ids),
        "osm_edges": len(edge_ids),
    }


def _node_external_id(node_id: str) -> str:
    return f"{REFERENCE_NODE_PREFIX}{node_id}"


def _node_name(node_payload: dict[str, Any]) -> str | None:
    node_type = str(node_payload.get("nodeType") or "")
    name = str(node_payload.get("name") or "").strip()
    if node_type == "path_node" and name.startswith("node_auto_"):
        return None
    return name or None


def _edge_distance(edge_payload: dict[str, Any], from_node: MapNode, to_node: MapNode) -> float:
    raw = edge_payload.get("distanceMeters")
    if raw is not None:
        return float(raw)
    return approximate_distance_meters((from_node.lng, from_node.lat), (to_node.lng, to_node.lat))


def _allowed_modes(edge_payload: dict[str, Any]) -> list[str]:
    raw_modes = edge_payload.get("allowedModes") or ["walking"]
    mapped = []
    for mode in raw_modes:
        if mode == "walking":
            mapped.append("walk")
        elif mode == "bicycle":
            mapped.append("bike")
        elif mode == "electric_cart":
            mapped.append("electric_cart")
    return mapped or ["walk"]


def _mode_speed(edge_payload: dict[str, Any], source_mode: str, default: float) -> float:
    speed = (edge_payload.get("idealSpeed") or {}).get(source_mode)
    if speed is None:
        return default
    value = float(speed)
    return value / 60 if value > 20 else value


def _congestion(edge_payload: dict[str, Any]) -> float:
    raw = edge_payload.get("congestionFactor")
    if raw is None:
        return 1.0
    value = float(raw)
    if value <= 0:
        return 1.0
    return max(0.2, min(value, 1.0))


def _edge_exists(session: Session, signature: tuple[int, int, float, tuple[str, ...]]) -> bool:
    from_node_id, to_node_id, distance, allowed_modes = signature
    for edge in session.scalars(
        select(MapEdge).where(
            MapEdge.from_node_id == from_node_id,
            MapEdge.to_node_id == to_node_id,
        )
    ).all():
        if round(edge.distance, 1) == distance and tuple(edge.allowed_modes or []) == allowed_modes:
            return True
    return False


def _load_or_create_categories(session: Session) -> dict[str, FacilityCategory]:
    names = {
        "gate": "校门/入口",
        "library": "图书馆服务",
        "canteen": "食堂/餐饮",
        "shop": "商店/超市",
        "sport": "运动设施",
        "clinic": "医务室",
        "landscape": "景观地标",
        "service": "校园服务",
    }
    categories = {
        category.code: category
        for category in session.scalars(select(FacilityCategory)).all()
    }
    for code, name in names.items():
        if code in categories:
            continue
        category = FacilityCategory(code=code, name=name)
        session.add(category)
        categories[code] = category
    session.flush()
    return categories


def _facility_items_from_scene(scene: dict[str, Any], external_to_node: dict[str, MapNode]) -> list[dict[str, Any]]:
    items = []
    for node in scene.get("nodes", []):
        node_type = str(node.get("nodeType") or "")
        tags = [str(tag) for tag in node.get("tags") or []]
        if node_type == "path_node" or "nav_only" in tags:
            continue
        external_id = _node_external_id(str(node.get("id")))
        nearest_node = external_to_node.get(external_id)
        if nearest_node is None:
            continue
        items.append(
            {
                "name": str(node.get("name") or node.get("id")),
                "lng": float(node["x"]),
                "lat": float(node["y"]),
                "category": _facility_category(str(node.get("name") or ""), node_type, tags),
                "node_type": node_type,
                "tags": tags,
                "nearest_node": nearest_node,
                "source_key": str(node.get("id")),
            }
        )
    return items


def _facility_items_from_geojson(
    payload: dict[str, Any],
    external_to_node: dict[str, MapNode],
) -> list[dict[str, Any]]:
    items = []
    for feature in payload.get("features", []):
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}
        if geometry.get("type") != "Point":
            continue
        kind = properties.get("kind")
        node_type = str(properties.get("nodeType") or "")
        name = str(properties.get("name") or properties.get("key") or "").strip()
        if kind != "poi" and name != "西门":
            continue
        coordinates = geometry.get("coordinates") or []
        if len(coordinates) < 2:
            continue
        tags = [str(tag) for tag in properties.get("tags") or []]
        anchor_key = properties.get("anchorKey")
        nearest_node = None
        if anchor_key:
            nearest_node = external_to_node.get(_node_external_id(f"node_{anchor_key}"))
        if nearest_node is None:
            nearest_node = _nearest_node(float(coordinates[0]), float(coordinates[1]), list(external_to_node.values()))
        items.append(
            {
                "name": name,
                "lng": float(coordinates[0]),
                "lat": float(coordinates[1]),
                "category": _facility_category(name, node_type, tags),
                "node_type": node_type or str(kind or "poi"),
                "tags": tags,
                "nearest_node": nearest_node,
                "source_key": str(properties.get("key") or name),
            }
        )
    return items


def _import_facilities(
    session: Session,
    categories: dict[str, FacilityCategory],
    items: list[dict[str, Any]],
    scene_key: str,
) -> tuple[int, int]:
    existing_signatures = {
        _facility_signature(facility.name, facility.lng, facility.lat)
        for facility in session.scalars(select(Facility).where(Facility.scene_key == scene_key)).all()
    }
    imported = 0
    skipped = 0
    for item in items:
        signature = _facility_signature(item["name"], item["lng"], item["lat"])
        if signature in existing_signatures:
            skipped += 1
            continue
        category = categories[item["category"]]
        session.add(
            Facility(
                scene_key=scene_key,
                name=item["name"],
                category_id=category.id,
                nearest_node_id=item["nearest_node"].id if item.get("nearest_node") else None,
                lng=item["lng"],
                lat=item["lat"],
                description=_facility_description(item),
            )
        )
        existing_signatures.add(signature)
        imported += 1
    session.flush()
    return imported, skipped


def _facility_category(name: str, node_type: str, tags: list[str]) -> str:
    text = f"{name} {node_type} {' '.join(tags)}".casefold()
    if "library" in text or "图书馆" in text:
        return "library"
    if "canteen" in text or "cafe" in text or "食堂" in text or "咖啡" in text or "醉面" in text or "煎饼" in text:
        return "canteen"
    if "convenience" in text or "shop" in text or "超市" in text or "商店" in text:
        return "shop"
    if "sports" in text or "操场" in text or "运动" in text:
        return "sport"
    if "clinic" in text or "校医院" in text or "医院" in text:
        return "clinic"
    if "entrance" in text or "gate" in text or "门" in text or "入口" in text:
        return "gate"
    if "湖" in text or "观景" in text or "景区" in text:
        return "landscape"
    return "service"


def _facility_description(item: dict[str, Any]) -> str:
    tags = ",".join(item.get("tags") or [])
    return (
        f"{REFERENCE_FACILITY_PREFIX}; "
        f"source_key={item.get('source_key')}; "
        f"node_type={item.get('node_type')}; "
        f"tags={tags}"
    )


def _facility_signature(name: str, lng: float, lat: float) -> tuple[str, float, float]:
    return " ".join(name.casefold().split()), round(lng, 5), round(lat, 5)


def _nearest_node(lng: float, lat: float, nodes: list[MapNode]) -> MapNode | None:
    if not nodes:
        return None
    return min(nodes, key=lambda node: approximate_distance_meters((lng, lat), (node.lng, node.lat)))


def _rebind_facilities_to_reference_nodes(session: Session, reference_nodes: list[MapNode], scene_key: str) -> int:
    if not reference_nodes:
        return 0
    rebound = 0
    for facility in session.scalars(select(Facility).where(Facility.scene_key == scene_key)).all():
        nearest = _nearest_node(facility.lng, facility.lat, reference_nodes)
        if nearest is not None and facility.nearest_node_id != nearest.id:
            facility.nearest_node_id = nearest.id
            rebound += 1
    session.flush()
    return rebound
