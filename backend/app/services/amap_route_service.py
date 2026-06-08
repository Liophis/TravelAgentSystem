from typing import Any

import httpx

from app.algorithms.coordinates import gcj02_to_wgs84, wgs84_to_gcj02


class AMapRouteError(RuntimeError):
    pass


AMAP_WALKING_ROUTE_ENDPOINT = "https://restapi.amap.com/v3/direction/walking"


def plan_amap_walking_route(
    api_key: str,
    start_lng: float,
    start_lat: float,
    end_lng: float,
    end_lat: float,
    timeout: float = 10.0,
) -> dict[str, Any]:
    if not api_key:
        raise AMapRouteError("AMAP_WEB_API_KEY is not configured for route planning.")

    start_gcj = wgs84_to_gcj02(start_lng, start_lat)
    end_gcj = wgs84_to_gcj02(end_lng, end_lat)
    payload = _request_walking_route(
        api_key=api_key,
        origin=f"{start_gcj[0]},{start_gcj[1]}",
        destination=f"{end_gcj[0]},{end_gcj[1]}",
        timeout=timeout,
    )
    paths = ((payload.get("route") or {}).get("paths") or [])
    if not paths:
        raise AMapRouteError("AMap walking route returned no paths.")

    path = paths[0]
    steps = path.get("steps") or []
    coordinates = _merge_step_polylines(steps)
    if not coordinates:
        coordinates = [[start_lng, start_lat], [end_lng, end_lat]]

    return {
        "source": "amap-walking",
        "distance": round(float(path.get("distance") or 0)),
        "duration": round(float(path.get("duration") or 0)),
        "path": coordinates,
        "steps": [
            {
                "text": str(step.get("instruction") or step.get("road") or "步行"),
                "distance": round(float(step.get("distance") or 0)),
                "duration": round(float(step.get("duration") or 0)),
                "road": str(step.get("road") or ""),
                "action": str(step.get("action") or ""),
                "assistant_action": str(step.get("assistant_action") or ""),
            }
            for step in steps
        ],
        "algorithm_trace": {
            "stage": "stage-21-real-route-planning",
            "algorithm": "AMap Web Service walking route",
            "topology_source": "AMap walking route service",
            "request_coordinates": "backend WGS84 converted to AMap GCJ-02",
            "response_coordinates": "AMap GCJ-02 polyline converted back to backend WGS84",
        },
    }


def _request_walking_route(
    api_key: str,
    origin: str,
    destination: str,
    timeout: float,
) -> dict[str, Any]:
    try:
        response = httpx.get(
            AMAP_WALKING_ROUTE_ENDPOINT,
            params={
                "key": api_key,
                "origin": origin,
                "destination": destination,
                "output": "json",
            },
            timeout=timeout,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise AMapRouteError(f"AMap walking route request failed: {exc}") from exc
    payload = response.json()
    if str(payload.get("status")) != "1":
        info = payload.get("info") or "unknown error"
        infocode = payload.get("infocode") or "unknown"
        raise AMapRouteError(f"AMap walking route failed: {info} ({infocode}).")
    return payload


def _merge_step_polylines(steps: list[dict[str, Any]]) -> list[list[float]]:
    coordinates: list[list[float]] = []
    for step in steps:
        polyline = str(step.get("polyline") or "")
        for coordinate in _parse_polyline(polyline):
            if coordinates and coordinates[-1] == coordinate:
                continue
            coordinates.append(coordinate)
    return coordinates


def _parse_polyline(polyline: str) -> list[list[float]]:
    coordinates: list[list[float]] = []
    for raw_coordinate in polyline.split(";"):
        if "," not in raw_coordinate:
            continue
        try:
            lng, lat = [float(item) for item in raw_coordinate.split(",", maxsplit=1)]
        except ValueError:
            continue
        wgs_lng, wgs_lat = gcj02_to_wgs84(lng, lat)
        coordinates.append([wgs_lng, wgs_lat])
    return coordinates
