# Route Planning Design

## API

`POST /api/v1/routes/plan`

Input:

- `start_lng`
- `start_lat`
- `end_lng`
- `end_lat`
- `strategy`
- `mode`

Output:

- `distance`
- `duration`
- `path`
- `node_ids`
- `steps`
- `algorithm_trace`

## Algorithm

The service snaps start/end coordinates to nearest graph nodes, builds a bidirectional graph from `map_edges`, and runs Dijkstra shortest path.

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

`POST /api/v1/routes/multi-point` accepts a start point and 1-12 destination points. The service uses a greedy TSP approximation: for each step, it evaluates remaining destinations by actual Dijkstra leg cost using the selected strategy and visits the nearest next point. It returns:

- optimized `visit_order`
- route `segments`
- merged `path`
- total `distance`
- total `duration`

`return_to_start=true` adds a final segment back to the origin.
