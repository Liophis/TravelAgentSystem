# Stage 12 Multi-Point Route Planning

## Scope

This stage upgrades route planning from a single start/end pair to the lecture-required start plus 1-N destinations workflow.

## Delivered

- Added `POST /api/v1/routes/multi-point`.
- Added greedy TSP approximation with Dijkstra graph distance for each candidate leg.
- Added merged route path, visit order, route segments, steps, and algorithm trace.
- Added frontend multi-destination input on `RoutePlannerPage`.
- Added backend tests and smoke coverage.

## Validation

Run from repository root:

```bash
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

Expected backend result:

```text
30 passed
```
