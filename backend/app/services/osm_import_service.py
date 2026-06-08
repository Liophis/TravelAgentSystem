from importlib import import_module
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.algorithms.route_planning import approximate_distance_meters
from app.models import Building, Facility, FacilityCategory, MapEdge, MapNode
from app.seed.osm_sample_data import BUPT_SHAHE_OSM_SAMPLE
from app.services.map_data_service import cleanup_demo_map_layers


class OsmImportError(RuntimeError):
    pass


def import_fixture_osm_payload(session: Session, reset_existing: bool = True) -> dict[str, Any]:
    return import_osm_payload_to_db(session, BUPT_SHAHE_OSM_SAMPLE, reset_existing=reset_existing)


def import_osm_payload_to_db(
    session: Session,
    payload: dict[str, Any],
    reset_existing: bool = True,
) -> dict[str, Any]:
    if reset_existing:
        _clear_map_tables(session)

    external_to_node: dict[str, MapNode] = {}
    for node_payload in payload.get("nodes", []):
        node = MapNode(
            external_id=str(node_payload["external_id"]),
            name=node_payload.get("name"),
            lng=float(node_payload["lng"]),
            lat=float(node_payload["lat"]),
        )
        session.add(node)
        external_to_node[node.external_id] = node
    session.flush()

    edges_imported = 0
    for edge_payload in payload.get("edges", []):
        from_node = external_to_node.get(str(edge_payload["from_external_id"]))
        to_node = external_to_node.get(str(edge_payload["to_external_id"]))
        if from_node is None or to_node is None:
            continue
        distance = float(
            edge_payload.get("distance")
            or approximate_distance_meters((from_node.lng, from_node.lat), (to_node.lng, to_node.lat))
        )
        session.add(
            MapEdge(
                from_node_id=from_node.id,
                to_node_id=to_node.id,
                distance=distance,
                walk_time=float(edge_payload.get("walk_time") or distance / 1.2),
                congestion=float(edge_payload.get("congestion") or 1.0),
                walk_speed=float(edge_payload.get("walk_speed") or 1.2),
                bike_speed=float(edge_payload.get("bike_speed") or 0.0),
                electric_cart_speed=float(edge_payload.get("electric_cart_speed") or 0.0),
                allowed_modes=edge_payload.get("allowed_modes") or ["walk"],
                geometry=edge_payload.get("geometry") or [[from_node.lng, from_node.lat], [to_node.lng, to_node.lat]],
            )
        )
        edges_imported += 1

    for building_payload in payload.get("buildings", []):
        session.add(
            Building(
                name=building_payload["name"],
                category=building_payload.get("category") or "building",
                polygon=building_payload["polygon"],
                description=building_payload.get("description"),
            )
        )

    categories = _load_or_create_categories(session, payload.get("facilities", []))
    for facility_payload in payload.get("facilities", []):
        nearest_node = external_to_node.get(str(facility_payload.get("nearest_node_external_id")))
        if nearest_node is None and external_to_node:
            nearest_node = _nearest_imported_node(
                float(facility_payload["lng"]),
                float(facility_payload["lat"]),
                external_to_node.values(),
            )
        category = categories[facility_payload["category"]]
        session.add(
            Facility(
                name=facility_payload["name"],
                category_id=category.id,
                nearest_node_id=nearest_node.id if nearest_node else None,
                lng=float(facility_payload["lng"]),
                lat=float(facility_payload["lat"]),
                description=facility_payload.get("description"),
            )
        )

    session.commit()
    return {
        "source": payload.get("source", "osm-payload"),
        "place_name": payload.get("place_name"),
        "nodes": len(payload.get("nodes", [])),
        "edges": edges_imported,
        "buildings": len(payload.get("buildings", [])),
        "facilities": len(payload.get("facilities", [])),
        "reset_existing": reset_existing,
        "algorithm_trace": {
            "stage": "stage-7-osm-import",
            "pipeline": "OSM-shaped payload to map_nodes/map_edges/buildings/facilities",
            "topology_target": "OSM graph for backend routing",
        },
    }


def import_osm_feature_layers_to_db(
    session: Session,
    payload: dict[str, Any],
    remove_demo_layers: bool = True,
    replace_osm_layers: bool = True,
    import_facilities: bool = True,
) -> dict[str, Any]:
    if remove_demo_layers:
        cleanup_demo_map_layers(session, remove_buildings=True, remove_facilities=True)
    if replace_osm_layers:
        _clear_imported_feature_layers(session, include_facilities=import_facilities)

    buildings_imported = 0
    for building_payload in payload.get("buildings", []):
        polygon = building_payload.get("polygon") or []
        if len(polygon) < 3:
            continue
        session.add(
            Building(
                name=building_payload.get("name") or "OSM building",
                category=building_payload.get("category") or "building",
                polygon=polygon,
                description=_source_description(building_payload, fallback="Imported from OpenStreetMap."),
            )
        )
        buildings_imported += 1

    facilities_imported = 0
    facilities_skipped = 0
    if import_facilities:
        categories = _load_or_create_categories(session, payload.get("facilities", []))
        nodes = list(session.scalars(select(MapNode).order_by(MapNode.id)).all())
        existing_signatures = {
            _facility_signature(facility.name, facility.lng, facility.lat)
            for facility in session.scalars(select(Facility)).all()
        }
        for facility_payload in payload.get("facilities", []):
            signature = _facility_signature(
                facility_payload["name"],
                float(facility_payload["lng"]),
                float(facility_payload["lat"]),
            )
            if signature in existing_signatures:
                facilities_skipped += 1
                continue
            category = categories[facility_payload["category"]]
            nearest_node = _nearest_imported_node(
                float(facility_payload["lng"]),
                float(facility_payload["lat"]),
                nodes,
            ) if nodes else None
            session.add(
                Facility(
                    name=facility_payload["name"],
                    category_id=category.id,
                    nearest_node_id=nearest_node.id if nearest_node else None,
                    lng=float(facility_payload["lng"]),
                    lat=float(facility_payload["lat"]),
                    description=_source_description(facility_payload, fallback="Imported from OpenStreetMap."),
                )
            )
            existing_signatures.add(signature)
            facilities_imported += 1

    session.commit()
    return {
        "source": payload.get("source", "osmnx-overpass"),
        "place_name": payload.get("place_name"),
        "buildings_imported": buildings_imported,
        "facilities_imported": facilities_imported,
        "facilities_skipped": facilities_skipped,
        "remove_demo_layers": remove_demo_layers,
        "replace_osm_layers": replace_osm_layers,
        "algorithm_trace": {
            "stage": "stage-27-real-map-layer-cleanup",
            "pipeline": "OSM building/amenity features -> database layers; AMap POIs preserved",
            "merge_policy": "remove seed/demo polygons, replace previous OSM feature layers, keep AMap facilities",
        },
    }


def import_osm_road_graph_to_db(
    session: Session,
    payload: dict[str, Any],
    replace_osm_roads: bool = True,
    rebind_facilities: bool = True,
) -> dict[str, Any]:
    if replace_osm_roads:
        _clear_imported_road_layers(session)

    external_to_node: dict[str, MapNode] = {}
    skipped_nodes = 0
    for node_payload in payload.get("nodes", []):
        external_id = str(node_payload["external_id"])
        existing = session.scalar(select(MapNode).where(MapNode.external_id == external_id))
        if existing is not None:
            external_to_node[external_id] = existing
            skipped_nodes += 1
            continue
        node = MapNode(
            external_id=external_id,
            name=node_payload.get("name"),
            lng=float(node_payload["lng"]),
            lat=float(node_payload["lat"]),
        )
        session.add(node)
        external_to_node[external_id] = node
    session.flush()

    edges_imported = 0
    edges_skipped = 0
    existing_edge_signatures = {
        (edge.from_node_id, edge.to_node_id, round(edge.distance, 1))
        for edge in session.scalars(select(MapEdge)).all()
    }
    for edge_payload in payload.get("edges", []):
        from_node = external_to_node.get(str(edge_payload["from_external_id"]))
        to_node = external_to_node.get(str(edge_payload["to_external_id"]))
        if from_node is None or to_node is None:
            edges_skipped += 1
            continue
        distance = float(
            edge_payload.get("distance")
            or approximate_distance_meters((from_node.lng, from_node.lat), (to_node.lng, to_node.lat))
        )
        signature = (from_node.id, to_node.id, round(distance, 1))
        if signature in existing_edge_signatures:
            edges_skipped += 1
            continue
        session.add(
            MapEdge(
                from_node_id=from_node.id,
                to_node_id=to_node.id,
                distance=distance,
                walk_time=float(edge_payload.get("walk_time") or distance / 1.2),
                congestion=float(edge_payload.get("congestion") or 1.0),
                walk_speed=float(edge_payload.get("walk_speed") or 1.2),
                bike_speed=float(edge_payload.get("bike_speed") or 0.0),
                electric_cart_speed=float(edge_payload.get("electric_cart_speed") or 0.0),
                allowed_modes=edge_payload.get("allowed_modes") or ["walk"],
                geometry=edge_payload.get("geometry") or [[from_node.lng, from_node.lat], [to_node.lng, to_node.lat]],
            )
        )
        existing_edge_signatures.add(signature)
        edges_imported += 1

    rebound_facilities = _rebind_facilities_to_nearest_node(session) if rebind_facilities else 0
    session.commit()
    return {
        "source": payload.get("source", "osmnx-overpass"),
        "place_name": payload.get("place_name"),
        "nodes_imported": len(external_to_node) - skipped_nodes,
        "nodes_skipped": skipped_nodes,
        "edges_imported": edges_imported,
        "edges_skipped": edges_skipped,
        "rebound_facilities": rebound_facilities,
        "algorithm_trace": {
            "stage": "stage-27-real-map-layer-cleanup",
            "pipeline": "OSM walk graph -> map_nodes/map_edges; seed graph hidden but retained for fallback",
            "merge_policy": "replace previous OSM road graph, preserve seed graph and AMap POIs",
        },
    }


def build_osmnx_payload(
    place_name: str | None,
    center_lng: float,
    center_lat: float,
    dist: int,
) -> dict[str, Any]:
    ox = _load_osmnx()
    lookup_mode = "point"
    resolved_place_name = f"point:{center_lng},{center_lat},dist:{dist}"
    if place_name:
        try:
            graph, features = _fetch_osmnx_place(ox, place_name)
            lookup_mode = "place"
            resolved_place_name = place_name
        except Exception as exc:
            if not _is_place_lookup_failure(exc):
                raise
            graph, features = _fetch_osmnx_point(ox, center_lng, center_lat, dist)
            lookup_mode = "point-fallback"
            resolved_place_name = f"fallback-point:{center_lng},{center_lat},dist:{dist}; failed-place:{place_name}"
    else:
        graph, features = _fetch_osmnx_point(ox, center_lng, center_lat, dist)

    nodes_gdf, edges_gdf = ox.graph_to_gdfs(graph)
    nodes = [
        {
            "external_id": f"osm-node-{node_id}",
            "name": None,
            "lng": float(row["x"]),
            "lat": float(row["y"]),
        }
        for node_id, row in nodes_gdf.iterrows()
    ]
    node_lookup = {node["external_id"]: node for node in nodes}

    edges = []
    for index, row in edges_gdf.reset_index().iterrows():
        from_external_id = f"osm-node-{row['u']}"
        to_external_id = f"osm-node-{row['v']}"
        from_node = node_lookup.get(from_external_id)
        to_node = node_lookup.get(to_external_id)
        if from_node is None or to_node is None:
            continue
        geometry = _line_geometry(row.get("geometry")) or [
            [from_node["lng"], from_node["lat"]],
            [to_node["lng"], to_node["lat"]],
        ]
        distance = float(row.get("length") or 0)
        edges.append(
            {
                "from_external_id": from_external_id,
                "to_external_id": to_external_id,
                "distance": distance,
                "walk_time": distance / 1.2 if distance else None,
                "congestion": 1.0,
                "walk_speed": 1.2,
                "bike_speed": 0.0,
                "electric_cart_speed": 0.0,
                "allowed_modes": ["walk"],
                "geometry": geometry,
            }
        )

    buildings: list[dict[str, Any]] = []
    facilities: list[dict[str, Any]] = []
    for _, feature in features.iterrows():
        geometry = feature.get("geometry")
        if geometry is None:
            continue
        building_polygon = _polygon_geometry(geometry)
        if building_polygon:
            buildings.append(
                {
                    "name": _clean_osm_value(feature.get("name"), "OSM building"),
                    "category": _clean_osm_value(feature.get("building"), "building"),
                    "description": "Imported from OpenStreetMap.",
                    "polygon": building_polygon,
                }
            )
            continue

        centroid = geometry.centroid
        category = _clean_osm_value(
            feature.get("amenity") or feature.get("shop") or feature.get("tourism"),
            "poi",
        )
        facilities.append(
            {
                "name": _clean_osm_value(feature.get("name"), category),
                "category": category,
                "category_name": category,
                "description": "Imported from OpenStreetMap.",
                "lng": float(centroid.x),
                "lat": float(centroid.y),
                "nearest_node_external_id": _nearest_node_external_id(float(centroid.x), float(centroid.y), nodes),
            }
        )

    return {
        "source": "osmnx-overpass",
        "place_name": resolved_place_name,
        "lookup_mode": lookup_mode,
        "nodes": nodes,
        "edges": edges,
        "buildings": buildings,
        "facilities": facilities,
    }


def get_map_import_status(session: Session) -> dict[str, Any]:
    return {
        "nodes": _count(session, MapNode),
        "edges": _count(session, MapEdge),
        "buildings": _count(session, Building),
        "facilities": _count(session, Facility),
        "facility_categories": _count(session, FacilityCategory),
        "algorithm_trace": {
            "stage": "stage-7-osm-import",
            "status": "counts from current database",
        },
    }


def _clear_map_tables(session: Session) -> None:
    session.execute(delete(Facility))
    session.execute(delete(FacilityCategory))
    session.execute(delete(MapEdge))
    session.execute(delete(Building))
    session.execute(delete(MapNode))
    session.flush()


def _clear_imported_feature_layers(session: Session, include_facilities: bool) -> None:
    session.execute(
        delete(Building).where(
            (Building.description.like("Imported from OpenStreetMap%"))
            | (Building.description.like("Fixture %OSM%"))
        )
    )
    if include_facilities:
        session.execute(
            delete(Facility).where(
                (Facility.description.like("Imported from OpenStreetMap%"))
                | (Facility.description.like("Fixture %OSM%"))
            )
        )
    session.flush()


def _clear_imported_road_layers(session: Session) -> None:
    osm_node_ids = [
        node.id
        for node in session.scalars(select(MapNode)).all()
        if node.external_id.startswith("osm-")
    ]
    if not osm_node_ids:
        return
    session.execute(
        delete(MapEdge).where(
            (MapEdge.from_node_id.in_(osm_node_ids))
            | (MapEdge.to_node_id.in_(osm_node_ids))
        )
    )
    for facility in session.scalars(select(Facility).where(Facility.nearest_node_id.in_(osm_node_ids))).all():
        facility.nearest_node_id = None
    session.execute(delete(MapNode).where(MapNode.id.in_(osm_node_ids)))
    session.flush()


def _load_or_create_categories(
    session: Session,
    facilities: list[dict[str, Any]],
) -> dict[str, FacilityCategory]:
    categories = {
        category.code: category
        for category in session.scalars(select(FacilityCategory)).all()
    }
    for facility in facilities:
        code = facility["category"]
        if code in categories:
            continue
        category = FacilityCategory(code=code, name=facility.get("category_name") or code)
        session.add(category)
        categories[code] = category
    session.flush()
    return categories


def _nearest_imported_node(lng: float, lat: float, nodes: Any) -> MapNode:
    return min(
        nodes,
        key=lambda node: approximate_distance_meters((lng, lat), (node.lng, node.lat)),
    )


def _nearest_node_external_id(lng: float, lat: float, nodes: list[dict[str, Any]]) -> str | None:
    if not nodes:
        return None
    node = min(
        nodes,
        key=lambda item: approximate_distance_meters((lng, lat), (item["lng"], item["lat"])),
    )
    return str(node["external_id"])


def _facility_signature(name: str, lng: float, lat: float) -> tuple[str, float, float]:
    return (name.strip().casefold(), round(lng, 5), round(lat, 5))


def _source_description(payload: dict[str, Any], fallback: str) -> str:
    description = payload.get("description")
    if not description or str(description).lower() == "nan":
        return fallback
    return str(description)


def _rebind_facilities_to_nearest_node(session: Session) -> int:
    nodes = list(session.scalars(select(MapNode)).all())
    if not nodes:
        return 0
    rebound = 0
    for facility in session.scalars(select(Facility)).all():
        nearest_node = _nearest_imported_node(facility.lng, facility.lat, nodes)
        if facility.nearest_node_id != nearest_node.id:
            facility.nearest_node_id = nearest_node.id
            rebound += 1
    return rebound


def _clean_osm_value(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    if not text or text.casefold() == "nan" or text.casefold() == "none":
        return fallback
    return text


def _load_osmnx() -> Any:
    try:
        return import_module("osmnx")
    except ImportError as exc:
        raise OsmImportError("OSMnx is not installed. Install backend requirements with osmnx support.") from exc


def _fetch_osmnx_place(ox: Any, place_name: str) -> tuple[Any, Any]:
    graph = ox.graph_from_place(place_name, network_type="walk", simplify=True)
    features = ox.features_from_place(
        place_name,
        tags={"building": True, "amenity": True, "shop": True, "tourism": True},
    )
    return graph, features


def _fetch_osmnx_point(ox: Any, center_lng: float, center_lat: float, dist: int) -> tuple[Any, Any]:
    graph = ox.graph_from_point((center_lat, center_lng), dist=dist, network_type="walk", simplify=True)
    features = ox.features_from_point(
        (center_lat, center_lng),
        tags={"building": True, "amenity": True, "shop": True, "tourism": True},
        dist=dist,
    )
    return graph, features


def _is_place_lookup_failure(exc: Exception) -> bool:
    message = str(exc)
    return (
        exc.__class__.__name__ == "InsufficientResponseError"
        or "Nominatim geocoder returned 0 results" in message
        or "returned 0 results" in message
    )


def _line_geometry(geometry: Any) -> list[list[float]] | None:
    if geometry is None or not hasattr(geometry, "coords"):
        return None
    return [[float(lng), float(lat)] for lng, lat in geometry.coords]


def _polygon_geometry(geometry: Any) -> list[list[float]] | None:
    if geometry is None:
        return None
    if geometry.geom_type == "Polygon":
        return [[float(lng), float(lat)] for lng, lat in geometry.exterior.coords[:-1]]
    if geometry.geom_type == "MultiPolygon":
        polygon = max(geometry.geoms, key=lambda item: item.area)
        return [[float(lng), float(lat)] for lng, lat in polygon.exterior.coords[:-1]]
    return None


def _count(session: Session, model: type[Any]) -> int:
    return len(session.scalars(select(model)).all())
