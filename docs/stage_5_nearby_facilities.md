# Stage 5 Nearby Facilities

## Scope

This stage connects `GET /api/v1/facilities/nearby` to the seeded map graph. It does not implement real OSMnx import yet.

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

- The graph is deterministic seed data for 北京邮电大学沙河校区.
- Real OSMnx / Overpass import is still planned.
- Facility route distance runs Dijkstra per candidate; this is acceptable for the current seed scale.
- Direct click-to-route planner navigation is still frontend polish, though routePath drawing is available.

## Next Stage

Implement destination search and recommendation foundation:

- destination list/detail API from seeded data
- search by name/category/keyword
- Top-10 recommendation by rating/popularity/interests
- frontend destination and home recommendation views
