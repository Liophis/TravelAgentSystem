# Route Planning Design

## API

`POST /api/v1/routes/plan`

Input:

- `start_place_id` optional
- `end_place_id` optional
- `start_lng`
- `start_lat`
- `end_lng`
- `end_lat`
- `strategy`
- `mode`
- `route_source`

The user-facing frontend should prefer `start_place_id` and `end_place_id` selected from `GET /api/v1/search/places`. Raw coordinates remain as a fallback for debugging, imported data issues, and algorithm tests.

Output:

- `distance`
- `duration`
- `path`
- `node_ids`
- `steps`
- `algorithm_trace`

## Route Source

Supported `route_source` values:

- `auto`: use AMap walking directions for walking routes when `AMAP_WEB_API_KEY` exists, otherwise fall back to local Dijkstra.
- `amap_walking`: require AMap walking directions.
- `local_graph`: force local Dijkstra over `map_nodes/map_edges`.

This split is intentional: AMap route data gives a more credible user-facing campus route, while local Dijkstra remains available for algorithm demonstration and network-free tests.

## Algorithm

The service snaps start/end coordinates to nearest graph nodes, builds a bidirectional graph from `map_edges`, and runs Dijkstra shortest path.

If a place ID is provided, the service resolves it first:

- `destination-{id}` uses destination coordinates
- `building-{id}` uses the building polygon center
- `facility-{id}` uses facility coordinates

Then the resolved coordinate is snapped to the nearest graph node.

For `amap_walking`, the service resolves the same place IDs, converts WGS84 to GCJ-02 for AMap, calls the walking route Web Service, and converts the returned polyline back to WGS84.

Supported weights:

- distance
- duration, computed as `distance / (ideal_speed * congestion)`

Supported transport modes:

- `walk`: uses edges allowing walking
- `bike`: uses edges allowing bicycles
- `electric_cart`: uses fixed electric-cart route edges
- `mixed`: uses any allowed edge and picks the fastest allowed mode per edge

## Nearby Facilities

Nearby facility search filters facility category first, then computes graph distance from the current point to each candidate facility and returns Top-K by distance.

## Multi-Point Route

`POST /api/v1/routes/multi-point` accepts a start point and 1-12 destination points. Each destination can use `place_id` or coordinate fallback. The service uses a greedy TSP approximation: for each step, it evaluates remaining destinations by actual Dijkstra leg cost using the selected strategy and visits the nearest next point. It returns:

- optimized `visit_order`
- route `segments`
- merged `path`
- total `distance`
- total `duration`

`return_to_start=true` adds a final segment back to the origin.
