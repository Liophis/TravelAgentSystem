# API Design

Base path: `/api/v1`.

## Map And Routing

- `GET /map/stats`
- `GET /map/geojson`
- `POST /routes/plan`
  - accepts `start_place_id` / `end_place_id` from `GET /search/places?scope=campus`
  - keeps `start_lng/start_lat/end_lng/end_lat` as coordinate fallback
  - supports `route_source=auto|amap_walking|local_graph`
  - RoutePlannerPage defaults to `local_graph` for BUPT Shahe campus-internal navigation, not cross-city attraction travel
- `POST /routes/multi-point`
  - each point accepts `place_id` or coordinate fallback
  - passes `route_source` to each route leg
- `GET /facilities/nearby`

## Search And Recommendation

- `GET /destinations`
- `GET /destinations/{id}`
- `GET /search/places`
  - `scope=destinations`: nationwide attraction/school destinations
  - `scope=campus`: BUPT Shahe campus buildings/facilities/named topology nodes only
- `GET /recommendations`

Destination recommendation/search is for tourist attractions and schools/campuses. Campus navigation must use `scope=campus` so route endpoints do not come from the nationwide destination pool.

## Diaries

- `POST /diaries`
- `GET /diaries`
- `GET /diaries/{id}`
- `PUT /diaries/{id}`
- `DELETE /diaries/{id}`
- `POST /diaries/{id}/view`
- `POST /diaries/{id}/rating`
- `POST /diaries/{id}/comments`
- `GET /diaries/search`
- `GET /diaries/recommend`
- `GET /diaries/{id}/compression`

## Food

- `GET /foods/restaurants`
- `GET /foods/items`
- `GET /foods/search`
- `GET /foods/recommend`
- `GET /foods/nearby`

## AIGC

- `POST /aigc/diary-draft`
- `POST /aigc/storyboard`

## Admin

- `GET /admin/stats`
- `GET /admin/map/import/status`
- `POST /admin/map/import`
  - `source=fixture`: offline fallback payload
  - `source=osmnx`: OSMnx road/building/POI import
  - `source=reference_campus`: offline WGS84 campus scene/topology import from `data/reference/bupt-shahe/`
  - `source=amap_poi`: AMap Place Around facility enrichment, requires `AMAP_WEB_API_KEY`

## Response Rule

Feature APIs should include `algorithm_trace` when they demonstrate an algorithm or data-processing strategy.
