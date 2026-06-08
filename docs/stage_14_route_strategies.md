# Stage 14 Route Strategies

## Scope

This stage closes the course-requirement gap for route strategy depth:

- shortest distance
- shortest time
- per-edge congestion
- walking route
- bicycle route
- fixed electric-cart route
- mixed transport route

## Delivered

- Added route attributes to `map_edges`:
  - `congestion`
  - `walk_speed`
  - `bike_speed`
  - `electric_cart_speed`
  - `allowed_modes`
- Seeded the BUPT Shahe campus graph with:
  - walking paths on all edges
  - bicycle access on main horizontal/vertical roads
  - fixed electric-cart access on central campus trunk lines
  - walking-only diagonal paths
- Route planning now:
  - filters graph edges by `mode`
  - computes real duration as `distance / (ideal_speed * congestion)`
  - uses distance weight for `shortest_distance`
  - uses duration weight for `shortest_time`
  - chooses the fastest allowed transport mode per edge for `mixed`
- Route steps now include transport mode and congestion.
- Route planner page now exposes strategy and transport-mode controls.
- Map edge APIs expose congestion and allowed mode data.

## API Contract

`POST /api/v1/routes/plan`

```json
{
  "start_lng": 116.28333,
  "start_lat": 40.15608,
  "end_lng": 116.2862,
  "end_lat": 40.1582,
  "strategy": "shortest_time",
  "mode": "mixed"
}
```

Supported strategies:

```text
shortest_distance
shortest_time
```

Supported modes:

```text
walk
bike
electric_cart
mixed
```

## Validation

Run:

```bash
PYTHONPATH=backend pytest backend/tests/test_stage4_route_planning.py
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

Expected:

- bike shortest-time route is faster than walk on the same graph
- electric-cart route only uses edges allowing `electric_cart`
- `algorithm_trace` includes congestion and mode filtering details
- frontend typecheck/build passes with route strategy controls

## Remaining Gaps

- Route targets are still coordinate-oriented in the route planner page.
- Electric-cart stops are simulated through fixed road access, not a separate station model.
- Road congestion is deterministic seed data, not live crowding data.
