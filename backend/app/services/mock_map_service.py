from math import hypot
from typing import Any

DEFAULT_CENTER = [116.3260, 40.0030]

ROADS = [
    {"id": "r1", "path": [[116.3260, 40.0030], [116.3276, 40.0038], [116.3290, 40.0046]]},
    {"id": "r2", "path": [[116.3290, 40.0046], [116.3302, 40.0055], [116.3312, 40.0065]]},
    {"id": "r3", "path": [[116.3276, 40.0038], [116.3271, 40.0052], [116.3268, 40.0062]]},
]

BUILDINGS = [
    {
        "id": "b1",
        "name": "Library",
        "polygon": [
            [116.3270, 40.0040],
            [116.3281, 40.0042],
            [116.3279, 40.0049],
            [116.3269, 40.0048],
        ],
    },
    {
        "id": "b2",
        "name": "Teaching Building",
        "polygon": [
            [116.3302, 40.0059],
            [116.3313, 40.0060],
            [116.3310, 40.0067],
            [116.3300, 40.0066],
        ],
    },
]

FACILITIES = [
    {
        "id": "f1",
        "name": "North Gate Restroom",
        "category": "toilet",
        "lng": 116.3268,
        "lat": 40.0037,
        "description": "Public restroom near the north gate.",
        "node_id": "n2",
    },
    {
        "id": "f2",
        "name": "Library Water Station",
        "category": "water",
        "lng": 116.3277,
        "lat": 40.0045,
        "description": "Drinking water station beside the library.",
        "node_id": "n3",
    },
    {
        "id": "f3",
        "name": "Campus Store",
        "category": "shop",
        "lng": 116.3304,
        "lat": 40.0058,
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
        [116.3276, 40.0038],
        [116.3290, 40.0046],
        [116.3302, 40.0055],
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
