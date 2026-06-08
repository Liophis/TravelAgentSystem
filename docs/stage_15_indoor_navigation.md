# Stage 15 Indoor Navigation

## Scope

This stage implements the indoor-navigation requirement from `要求.md`:

- building/floor indoor nodes
- entrance, elevator, stairs, room, toilet nodes
- corridor, elevator, and stair edges
- cross-floor route planning
- frontend page for choosing start/end indoor points

## Delivered

- Added tables:
  - `indoor_nodes`
  - `indoor_edges`
- Seeded `综合教学楼` with 3 floors.
- Added indoor route API:
  - `GET /api/v1/indoor/buildings`
  - `GET /api/v1/indoor/nodes`
  - `POST /api/v1/indoor/routes`
- Added `IndoorNavigationPage`.
- Added admin stats for indoor node/edge counts.
- Added smoke coverage and backend tests.

## Algorithm

Indoor routing uses Dijkstra on `indoor_nodes` / `indoor_edges`.

Edge types:

```text
corridor
elevator
stairs
```

Route output includes:

- building name
- start/end indoor nodes
- total distance
- total duration
- ordered indoor node path
- text steps with floor and access type
- `algorithm_trace`

## Validation

Run:

```bash
PYTHONPATH=backend pytest backend/tests/test_stage15_indoor_navigation.py
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

Expected:

- route from `一层大门` to `305 教室` reaches floor 3
- route steps include elevator access
- frontend typecheck/build passes with `/indoor` route

## Remaining Gaps

- Indoor floor plan is a simple schematic, not CAD/building-image based.
- There is no indoor/outdoor route stitching yet.
