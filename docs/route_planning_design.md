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
- duration

## Nearby Facilities

Nearby facility search filters facility category first, then computes graph distance from the current point to each candidate facility and returns Top-K by distance.
