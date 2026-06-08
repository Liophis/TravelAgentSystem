# Stage 5 Nearby Facilities

## Scope

This stage connected `GET /api/v1/facilities/nearby` to the seeded map graph. Later stages moved the graph to BUPT Shahe reference/OSM data and kept this service as the graph-distance ranking foundation.

## Delivered

- Added reusable Top-K heap helper in `backend/app/algorithms/ranking.py`.
- Added DB-backed nearby facility service in `backend/app/services/facility_service.py`.
- `GET /api/v1/facilities/nearby` now:
  - filters candidates by facility category first
  - snaps the current coordinate to the nearest road node
  - resolves each facility to its bound nearest road node
  - runs Dijkstra graph distance for each candidate
  - filters by radius using graph distance plus snap distance
  - returns Top-K nearest facilities with route paths
- Nearby facilities page now shows all seeded facility categories.
- Added tests for Top-K ordering, graph-distance ranking, and API handler contract.

## API Contract

Request:

```text
GET /api/v1/facilities/nearby?current_lng=116.28333&current_lat=40.15608&category=water&radius=5000&limit=3
```

Stage 34 target request:

```text
GET /api/v1/facilities/nearby?origin_place_id=node-184&category=超市&radius=800&limit=10
```

Response includes:

```text
items[].distance: integer meters
items[].duration: integer seconds
items[].routePath: [lng, lat][]
items[].node_ids: graph node id sequence
algorithm_trace.stage: stage-5-facility-graph-distance
algorithm_trace.ranking: Top-K heap by graph distance
```

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
15 passed
```

## Known Gaps

- The page still defaults to a fixed coordinate when the user has not selected an origin.
- The API accepts coordinate fallback but does not yet accept `origin_place_id`.
- Map click does not yet set the nearby-facility origin.
- Facility route distance runs Dijkstra per candidate; this is acceptable for the current seed scale.
- Direct click-to-route planner navigation is still frontend polish, though routePath drawing is available.
- Dataset separation between `campus_navigation` and `nearby_facilities` is documented, but the current `facilities` table does not yet enforce it with a first-class column.

## Next Stage

Stage 34 should complete the origin-selection workflow:

- origin search with `scope=campus`
- optional map-click origin
- backend `origin_place_id` resolution
- visible origin marker and route drawing
