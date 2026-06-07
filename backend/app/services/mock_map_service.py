from math import hypot
from typing import Any

DEFAULT_CENTER = [116.28333, 40.15608]

ROADS = [
    {"id": "r1", "path": [[116.28333, 40.15608], [116.28430, 40.15680], [116.28515, 40.15745]]},
    {"id": "r2", "path": [[116.28515, 40.15745], [116.28580, 40.15790], [116.28620, 40.15820]]},
    {"id": "r3", "path": [[116.28430, 40.15680], [116.28370, 40.15770], [116.28320, 40.15835]]},
]

BUILDINGS = [
    {
        "id": "b1",
        "name": "Library",
        "polygon": [
            [116.28410, 40.15695],
            [116.28495, 40.15710],
            [116.28478, 40.15758],
            [116.28398, 40.15744],
        ],
    },
    {
        "id": "b2",
        "name": "Teaching Building",
        "polygon": [
            [116.28570, 40.15778],
            [116.28645, 40.15790],
            [116.28628, 40.15842],
            [116.28555, 40.15830],
        ],
    },
]

FACILITIES = [
    {
        "id": "f1",
        "name": "Shahe Campus Restroom",
        "category": "toilet",
        "lng": 116.28395,
        "lat": 40.15682,
        "description": "Public restroom in BUPT Shahe Campus.",
        "node_id": "n2",
    },
    {
        "id": "f2",
        "name": "Library Water Station",
        "category": "water",
        "lng": 116.28472,
        "lat": 40.15732,
        "description": "Drinking water station beside the library area.",
        "node_id": "n3",
    },
    {
        "id": "f3",
        "name": "Campus Store",
        "category": "shop",
        "lng": 116.28600,
        "lat": 40.15804,
        "description": "Convenience store for snacks and daily supplies.",
        "node_id": "n5",
    },
]


def get_map_payload() -> dict[str, Any]:
    categories = sorted({item["category"] for item in FACILITIES})
    return {
        "center": DEFAULT_CENTER,
        "statistics": {
            "roads": len(ROADS),
            "buildings": len(BUILDINGS),
            "facilities": len(FACILITIES),
            "categories": len(categories),
        },
        "roads": ROADS,
        "buildings": BUILDINGS,
        "facilities": FACILITIES,
        "facility_categories": categories,
        "geojson": _to_feature_collection(),
        "source": "mock-osm-stage-1",
    }


def get_route_plan(payload: dict[str, Any]) -> dict[str, Any]:
    path = [
        [payload["start_lng"], payload["start_lat"]],
        [116.28430, 40.15680],
        [116.28515, 40.15745],
        [116.28580, 40.15790],
        [payload["end_lng"], payload["end_lat"]],
    ]
    return {
        "strategy": payload["strategy"],
        "mode": payload["mode"],
        "distance": 690,
        "duration": 575,
        "path": path,
        "steps": [
            {"text": "Start from the selected point", "distance": 120},
            {"text": "Walk east along the main road", "distance": 280},
            {"text": "Turn north toward the teaching building", "distance": 290},
        ],
        "algorithm_trace": {
            "stage": "stage-1-mock",
            "topology_source": "OSM graph placeholder",
            "rendering": "AMap Polyline on frontend",
        },
    }


def get_nearby_facilities(
    current_lng: float,
    current_lat: float,
    category: str | None,
    radius: int,
    limit: int,
) -> dict[str, Any]:
    candidates = [item for item in FACILITIES if category is None or item["category"] == category]
    enriched = []
    for item in candidates:
        approx_distance = int(hypot((item["lng"] - current_lng) * 85000, (item["lat"] - current_lat) * 111000))
        if approx_distance <= radius:
            enriched.append(
                {
                    **item,
                    "distance": approx_distance,
                    "duration": max(1, int(approx_distance / 1.2)),
                    "routePath": [[current_lng, current_lat], [item["lng"], item["lat"]]],
                }
            )
    enriched.sort(key=lambda item: item["distance"])
    return {
        "items": enriched[:limit],
        "total": len(enriched),
        "category": category,
        "radius": radius,
        "algorithm_trace": {
            "stage": "stage-1-mock",
            "ranking": "distance placeholder; replace with OSM shortest path distance",
        },
    }


def _to_feature_collection() -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for road in ROADS:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": road["path"]},
                "properties": {"id": road["id"], "kind": "road"},
            }
        )
    for building in BUILDINGS:
        ring = [*building["polygon"], building["polygon"][0]]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [ring]},
                "properties": {"id": building["id"], "name": building["name"], "kind": "building"},
            }
        )
    for facility in FACILITIES:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [facility["lng"], facility["lat"]]},
                "properties": {
                    "id": facility["id"],
                    "name": facility["name"],
                    "category": facility["category"],
                    "description": facility["description"],
                    "kind": "facility",
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}
