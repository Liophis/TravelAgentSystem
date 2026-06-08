# Stage 4 Route Planning

## Scope

This stage connects `POST /api/v1/routes/plan` to the local map graph. Later stages add OSM import, transport strategies, and place-name route inputs.

## Delivered

- Added reusable route algorithms in `backend/app/algorithms/route_planning.py`.
- Added DB-backed route orchestration in `backend/app/services/route_service.py`.
- `POST /api/v1/routes/plan` now:
  - accepts `start_place_id/end_place_id` from place search
  - keeps raw coordinates as fallback
  - snaps start/end coordinates to nearest `map_nodes`
  - builds a bidirectional graph from `map_edges`
  - runs Dijkstra shortest path
  - returns path coordinates, node ids, distance, duration, steps, mode, and `algorithm_trace`
- Added tests for:
  - Dijkstra path selection on a small graph
  - seeded DB route planning
  - route API handler contract

## API Contract

Request:

```json
{
  "start_place_id": "facility-1",
  "end_place_id": "building-8",
  "start_lng": 116.28333,
  "start_lat": 40.15608,
  "end_lng": 116.2862,
  "end_lat": 40.1582,
  "strategy": "shortest_distance",
  "mode": "walk"
}
```

Response includes:

```text
distance: integer meters
duration: integer seconds
path: [lng, lat][]
node_ids: graph node id sequence
steps: text + distance entries
algorithm_trace.stage: stage-4-db-graph
algorithm_trace.algorithm: Dijkstra shortest path
```

Strategies:

```text
shortest_distance -> edge distance weight
shortest_time / fastest -> edge duration weight
```

Stage 14 extends this with per-edge congestion, ideal speeds, and walk/bike/electric-cart/mixed mode filtering.

Stage 20 changes the user-facing route planner to place-name selection first. Raw coordinate inputs remain in an advanced panel for debugging and algorithm tests.

Stage 21 adds `route_source=auto|amap_walking|local_graph`. User-facing walking routes can use AMap real route geometry, while `local_graph` keeps Dijkstra available for algorithm demonstration.

## Validation

Run from repository root:

```bash
bash scripts/reset_dev_db.sh
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```

Expected backend result:

```text
12 passed
```

## Current Follow-up Status

- Stage 5 added graph-distance nearby facilities.
- Stage 7 added OSM import.
- Stage 12 added multi-point route planning.
- Stage 14 added congestion, speed, and transport-mode routing.
- Stage 20 added place-name target selection and `place_id` route inputs.
- Stage 21 added AMap walking route source with local Dijkstra fallback.

## Next Stage

Improve real campus road topology and map visual verification.
