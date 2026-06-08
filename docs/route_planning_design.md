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

The user-facing campus navigation page is scoped to 北京邮电大学沙河校区内部场所. It should prefer `start_place_id` and `end_place_id` selected from `GET /api/v1/search/places?scope=campus`, which returns only campus buildings, facilities, and named topology nodes inside the BUPT Shahe coordinate boundary. Raw coordinates remain as a fallback for debugging, imported data issues, and algorithm tests.

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

The BUPT campus navigation page defaults to `local_graph` because the imported campus topology is the source of truth for internal walk paths. AMap walking remains available at the API level for explicit experiments and fallback comparisons, but it is not the default UI route source for campus-internal navigation.

## Algorithm

The service snaps start/end coordinates to nearest graph nodes, builds a bidirectional graph from `map_edges`, and runs Dijkstra shortest path.

For campus-grade navigation, imported topology should come from real campus reference files when available. Place WGS84 source layers in `data/reference/bupt-shahe/raw_wgs84/` and graph topology in `data/reference/bupt-shahe/topology/`, then import them into `map_nodes` and `map_edges` through a validation script.

If a place ID is provided, the service resolves it first:

- `building-{id}` uses the building polygon center
- `facility-{id}` uses facility coordinates
- `node-{id}` uses a named `map_nodes` coordinate from the imported campus topology

Then the resolved coordinate is snapped to the nearest graph node.

`destination-{id}` is still accepted by the backend for backward compatibility and smoke tests, but the BUPT campus navigation UI and `scope=campus` search do not expose destination IDs as route endpoints.

Current snapping is node-based. The next improvement is edge projection with temporary virtual nodes, so facilities/buildings that lie along long path segments can route from the nearest point on an edge instead of the nearest graph node.

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
