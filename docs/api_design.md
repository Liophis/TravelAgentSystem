# API Design

Base path: `/api/v1`.

## Users And Auth

- `POST /users/register`
- `POST /users/login`
  - planned response includes `role=user|admin`
  - one login endpoint serves both normal users and admins
- `GET /users/me`
  - requires bearer token
  - planned response includes current user role

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
  - `scope=campus`: BUPT Shahe campus buildings/facilities/semantic named topology nodes only; generic road/intersection nodes are excluded
- `GET /recommendations`

Destination recommendation/search is for tourist attractions and schools/campuses. Campus navigation must use `scope=campus` so route endpoints do not come from the nationwide destination pool.

## Diaries

- `POST /diaries`
- `GET /diaries`
  - supports `destination_id`, `q`, `sort=hot|rating|latest`, `limit`, and `offset`
- `GET /diaries/{id}`
- `PUT /diaries/{id}`
- `DELETE /diaries/{id}`
- `POST /diaries/{id}/view`
  - increments `views`; views are diary heat
- `POST /diaries/{id}/rating`
- `POST /diaries/{id}/comments`
  - supports all-user diary communication
- `POST /diaries/{id}/media`
  - accepts image/video URL metadata for scenic/school media
- `GET /diaries/{id}/media`
- `GET /diaries/search`
  - supports `mode=exact_title|fulltext|contains`
  - `exact_title` uses normalized title index
  - `fulltext` uses lightweight inverted tokens
- `GET /diaries/recommend`
  - ranks by views, rating, and personal interest through Top-K
- `GET /diaries/{id}/compression`
  - reports lossless compression stats and decompression check

## Food

- `GET /foods/restaurants`
- `GET /foods/items`
- `GET /foods/search`
- `GET /foods/recommend`
- `GET /foods/nearby`

## AIGC

- `POST /aigc/diary-draft`
- `POST /aigc/storyboard`
  - accepts `media_urls` from scenic/school diary media
  - returns storyboard scenes, reusable prompt, and simulated video link

## Admin

- `GET /admin/stats`
- `GET /admin/diaries`
- `DELETE /admin/diaries/{id}`
- `GET /admin/map/import/status`
- `POST /admin/map/import`
  - `source=fixture`: offline fallback payload
  - `source=osmnx`: OSMnx road/building/POI import
  - `source=osmnx_graph`: OSMnx road graph import
  - `source=osmnx_features`: OSMnx building/POI feature import
  - `source=reference_campus`: offline WGS84 campus scene/topology import from `data/reference/bupt-shahe/`
  - `source=amap_poi`: AMap Place Around facility enrichment, requires `AMAP_WEB_API_KEY`

Planned auth rule: all `/admin/*` endpoints require bearer token with `role=admin`. Missing/invalid token returns `401`; valid non-admin token returns `403`.

## Response Rule

Feature APIs should include `algorithm_trace` when they demonstrate an algorithm or data-processing strategy.
