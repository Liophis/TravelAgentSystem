# API Design

Base path: `/api/v1`.

## Users And Auth

- `POST /users/register`
- `POST /users/login`
  - response includes `role=user|admin`
  - one login endpoint serves both normal users and admins
- `GET /users/me`
  - requires bearer token
  - response includes current user role

## Map And Routing

- `GET /map/stats`
- `GET /map/geojson`
  - default `scene_key=bupt_shahe`
  - Stage 35 target: `scene_key=summer_palace`
- `POST /routes/plan`
  - default `scene_key=bupt_shahe`
  - accepts `start_place_id` / `end_place_id` from `GET /search/places?scope=campus|scenic&scene_key=...`
  - keeps `start_lng/start_lat/end_lng/end_lat` as coordinate fallback
  - supports `route_source=auto|amap_walking|local_graph`
  - RoutePlannerPage defaults to `local_graph` for BUPT Shahe campus-internal navigation, not cross-city attraction travel
- `POST /routes/multi-point`
  - default `scene_key=bupt_shahe`
  - each point accepts `place_id` or coordinate fallback
  - passes `route_source` to each route leg
- `GET /facilities/nearby`
  - current stable parameters: `scene_key`, `current_lng`, `current_lat`, `category`, `radius`, `limit`
  - accepts `origin_place_id` from `GET /search/places?scope=campus|scenic&scene_key=...`
  - `origin_place_id` is preferred for normal users; coordinate input remains a map-click/debug fallback
  - response should include origin, resolved category, Dijkstra route distance, route path, and Top-K trace

## Search And Recommendation

- `GET /destinations`
- `GET /destinations/{id}`
- `GET /search/places`
  - `scope=destinations`: nationwide attraction/school destinations
  - `scope=campus`: BUPT Shahe campus buildings/facilities/semantic named topology nodes only; generic road/intersection nodes are excluded
  - Stage 35 target `scope=scenic&scene_key=summer_palace`: Summer Palace scenic buildings/facilities/semantic nodes
  - `limit` accepts `1..200`; route endpoint selectors use this expanded limit so dense scenes such as Summer Palace are not truncated to the old 100-candidate ceiling
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
  - supports real destination-nearby AMap restaurant rows when imported through `backend/scripts/import_amap_foods.py`

## AIGC

- `POST /aigc/diary-draft`
- `POST /aigc/storyboard`
  - accepts `media_urls` from scenic/school diary media
  - returns storyboard scenes, reusable prompt, and simulated video link
- `POST /aigc/agent/run`
  - Stage 32 endpoint for a lightweight AIGC workflow Agent
  - accepts task, text, destination context, style, scene count, optional user/diary id, and `media_urls`
  - orchestrates deterministic local tools first: media analyzer, diary writer, storyboard planner, prompt builder, mock video generator, and compression summary
  - returns `result`, `agent_trace.steps[]`, and `algorithm_trace`
  - must run without network access unless a real provider is explicitly configured

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
  - `source=amap_food`: AMap Place Around restaurant enrichment for a `destination_id`, requires `AMAP_WEB_API_KEY`

Auth rule: all `/admin/*` endpoints require bearer token with `role=admin`. Missing/invalid token returns `401`; valid non-admin token returns `403`.

## Response Rule

Feature APIs should include `algorithm_trace` when they demonstrate an algorithm or data-processing strategy.
