from importlib import import_module
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.algorithms.route_planning import approximate_distance_meters
from app.models import Building, Facility, FacilityCategory, MapEdge, MapNode
from app.seed.osm_sample_data import BUPT_SHAHE_OSM_SAMPLE


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


def build_osmnx_payload(
    place_name: str | None,
    center_lng: float,
    center_lat: float,
    dist: int,
) -> dict[str, Any]:
    ox = _load_osmnx()
    if place_name:
        graph = ox.graph_from_place(place_name, network_type="walk", simplify=True)
        features = ox.features_from_place(
            place_name,
            tags={"building": True, "amenity": True, "shop": True, "tourism": True},
        )
    else:
        graph = ox.graph_from_point((center_lat, center_lng), dist=dist, network_type="walk", simplify=True)
        features = ox.features_from_point(
            (center_lat, center_lng),
            tags={"building": True, "amenity": True, "shop": True, "tourism": True},
            dist=dist,
        )

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
                    "name": str(feature.get("name") or "OSM building"),
                    "category": str(feature.get("building") or "building"),
                    "description": "Imported from OpenStreetMap.",
                    "polygon": building_polygon,
                }
            )
            continue

        centroid = geometry.centroid
        category = str(feature.get("amenity") or feature.get("shop") or feature.get("tourism") or "poi")
        if category == "nan":
            category = "poi"
        facilities.append(
            {
                "name": str(feature.get("name") or category),
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
        "place_name": place_name or f"point:{center_lng},{center_lat},dist:{dist}",
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


def _load_osmnx() -> Any:
    try:
        return import_module("osmnx")
    except ImportError as exc:
        raise OsmImportError("OSMnx is not installed. Install backend requirements with osmnx support.") from exc


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
