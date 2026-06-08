# Stage 21 Real Route Planning

## Problem

The local seeded road graph is useful for Dijkstra demonstrations, but it is not accurate enough for real campus route planning. Users expect route geometry and steps that match the visible AMap basemap.

## Decision

Use a hybrid route strategy:

- Default frontend route source: `auto`
- If `AMAP_WEB_API_KEY` is available and mode is `walk`, `auto` uses AMap Web Service walking directions.
- If AMap is unavailable, or `route_source=local_graph`, backend falls back to local Dijkstra over `map_nodes/map_edges`.
- Local Dijkstra remains necessary for algorithm demonstration, transport-mode experiments, and network-free tests.
- Manually supplied WGS84 campus topology can be imported with `backend/scripts/import_reference_campus.py` and should be the preferred local graph source for algorithmic campus Dijkstra.

## Coordinate Contract

- Backend API receives and returns WGS84.
- AMap walking directions require GCJ-02 request coordinates.
- AMap walking directions return GCJ-02 polyline.
- Backend converts returned route polyline back to WGS84 before sending it to the frontend.
- `AMapView` still converts WGS84 to GCJ-02 when rendering.

## API

`POST /api/v1/routes/plan`:

```json
{
  "start_place_id": "facility-1",
  "end_place_id": "facility-2",
  "mode": "walk",
  "route_source": "auto"
}
```

Route source values:

- `auto`: AMap walking when possible, local Dijkstra fallback
- `amap_walking`: require AMap walking route
- `local_graph`: force local Dijkstra

`POST /api/v1/routes/multi-point` passes `route_source` to each leg. Required smoke tests use `local_graph` to stay network-free.

## Validation

```bash
PYTHONPATH=backend pytest backend/tests/test_stage21_real_route_planning.py
python backend/scripts/smoke_amap_route.py
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

Expected:

- mocked AMap route responses convert GCJ-02 polylines back to WGS84
- live AMap route smoke returns distance, duration, path point count, and step count when network/key are available
- `route_source=auto` uses AMap when key exists
- smoke tests remain network-free with `route_source=local_graph`

## Live Route Smoke Result

Executed locally with a real `AMAP_WEB_API_KEY`:

```bash
python backend/scripts/smoke_amap_route.py
```

Result:

- source: `amap-walking`
- distance: 411m
- duration: 329s
- path points: 12
- steps: 4

## Remaining Limits

- AMap walking route is external API data, not a hand-built road graph.
- Bike/electric-cart route modes still use local graph data.
- For a fully algorithmic real route graph, import the verified campus walk-path dataset from `data/reference/bupt-shahe/`.
- Current local snapping is nearest-node based; edge projection with temporary virtual nodes remains the next precision upgrade.
