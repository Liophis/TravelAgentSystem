from app.api.v1.health import health_check
from app.services.mock_map_service import get_map_payload, get_nearby_facilities, get_route_plan


def test_health_check() -> None:
    assert health_check() == {"status": "ok"}


def test_map_geojson_payload_contains_stage1_layers() -> None:
    payload = get_map_payload()

    assert payload["center"] == [116.3260, 40.0030]
    assert payload["statistics"]["buildings"] >= 1
    assert payload["statistics"]["facilities"] >= 1
    assert payload["geojson"]["type"] == "FeatureCollection"


def test_route_plan_returns_polyline_path() -> None:
    payload = get_route_plan(
        {
            "start_lng": 116.3260,
            "start_lat": 40.0030,
            "end_lng": 116.3312,
            "end_lat": 40.0065,
            "strategy": "shortest_distance",
            "mode": "walk",
        }
    )

    assert payload["distance"] > 0
    assert len(payload["path"]) >= 2
    assert payload["algorithm_trace"]["rendering"] == "AMap Polyline on frontend"


def test_nearby_facilities_can_filter_by_category() -> None:
    payload = get_nearby_facilities(
        current_lng=116.3260,
        current_lat=40.0030,
        category="water",
        radius=1000,
        limit=10,
    )

    assert payload["total"] == 1
    assert payload["items"][0]["category"] == "water"
