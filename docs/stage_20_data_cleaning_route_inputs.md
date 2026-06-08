# Stage 20 Data Cleaning And Route Inputs

## Problems

- The previous live AMap POI import used append mode, so offline fallback facility rows remained mixed with real POIs.
- Route planning exposed raw longitude/latitude as the primary UI input. This is useful for algorithm debugging, but it is not a reasonable default user workflow.

## Data Cleaning

Facilities were re-imported from AMap with replacement mode:

```bash
python backend/scripts/import_amap_pois.py --radius 3000 --max-pages 3 --request-interval 0.8 --reset-facilities
```

Current local facility data:

- total facilities: 516
- source: AMap Web Service Place Around
- offline fallback facility rows: removed from the local dev DB
- road nodes/edges: still local graph data, kept for Dijkstra route planning

Category distribution:

| Category | Count |
| --- | ---: |
| shop | 182 |
| transport | 128 |
| clinic | 53 |
| sport | 45 |
| canteen | 41 |
| gate | 22 |
| library | 14 |
| water | 13 |
| toilet | 9 |
| atm | 9 |

## Route Input Decision

Raw coordinates are reasonable at the service/algorithm boundary because Dijkstra needs snap points on the graph. They are not reasonable as the primary frontend interaction.

The route planner now uses:

- place search for start/end selection
- `start_place_id` and `end_place_id` in `POST /api/v1/routes/plan`
- `place_id` for multi-point destinations
- coordinate fallback inside an advanced panel for debugging and edge cases
- `route_source` selection added in Stage 21: real AMap walking route by default, local graph for Dijkstra demonstration

Supported route place IDs are the same IDs returned by `GET /api/v1/search/places`, for example:

- `destination-12`
- `building-8`
- `facility-203`

## Validation

```bash
PYTHONPATH=backend pytest backend/tests/test_stage4_route_planning.py
npm run typecheck
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

Expected:

- single-route planning accepts facility/building/destination IDs
- multi-point planning accepts `place_id`
- frontend route page typechecks
- smoke uses the cleaned 516-facility local DB

## Remaining Limits

- Road topology still needs stronger real campus walk-path data.
- Destination and food seed data remain demo data and should be cleaned or linked to real campus sources in a later stage.
