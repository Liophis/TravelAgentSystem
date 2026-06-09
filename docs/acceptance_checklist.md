# Acceptance Checklist

## Environment

- [ ] `docker compose up --build` starts frontend, backend, PostgreSQL/PostGIS, Redis, and Nginx.
- [ ] Frontend is reachable from browser.
- [ ] Backend `/docs` is reachable.
- [ ] `.env.local` is not required for basic local demo.
- [x] `VITE_AMAP_KEY` is documented and never hard-coded in source files.

## Data

- [x] Seed users count >= 10.
- [x] Destinations count >= 200.
- [x] At least one real OSM campus/scenic map can be imported.
- [x] Deterministic campus seed is documented as offline fallback, not real collected data.
- [x] AMap Web Service POI import path exists for real facility enrichment.
- [x] AMap POI import converts GCJ-02 coordinates to backend WGS84 before storage.
- [x] AMap POI import de-duplicates repeated keyword hits.
- [x] AMap POI import can tag `nearby_facilities` and `campus_navigation` datasets separately.
- [x] AMap campus-navigation POI import supports `--campus-only` boundary filtering.
- [x] OSMnx and AMap download-only source payload commands save files under `data/external/bupt-shahe/`.
- [x] AMap campus-navigation source download produced 319 raw POIs, with 13 inside the BUPT Shahe campus boundary after conversion/filtering.
- [x] AMap campus-navigation import from saved raw file tagged 11 existing facility rows without duplicating shared nearby POIs.
- [x] OSMnx campus source download produced 162 nodes, 456 edges, 56 buildings, and 24 facilities with point-fallback lookup.
- [x] AMap POI live import has been run with a real key and produced 516 clean BUPT Shahe surrounding facility rows after replacing offline facility seed rows.
- [x] OSMnx live import has been run for BUPT Shahe fallback point and produced 681 OSM nodes, 2045 OSM road edges, 188 building polygons, and 49 OSM POIs.
- [x] Old offline square building polygons are removed from the local dev DB and hidden by default from public map APIs.
- [x] `map_edges` count >= 450.
- [x] `buildings` count >= 60.
- [x] `facilities` count >= 120.
- [x] Facility categories count >= 10.
- [x] `GET /api/v1/map/stats` reads the local database and returns map scale counts.
- [x] OSM import pipeline can import an OSM-shaped payload into map tables.
- [x] Reference campus source directory is documented for WGS84 JSON/GeoJSON and topology files.
- [x] Reference campus import script validates and imports `data/reference/bupt-shahe/` files into map tables.
- [x] Reference campus import has been run locally and produced 106 nodes, 246 road edges, and 35 BUPT Shahe reference facilities.
- [x] `bash scripts/reset_dev_db.sh` restores visible BUPT Shahe campus navigation roads, buildings, and facilities after reset.
- [x] Admin map import/status API reports current map table counts.

## Users

- [x] User can register.
- [x] User can log in and receive token.
- [x] Login is an application-level gate before choosing service modules.
- [x] Home/overview is a service-entry page and does not render the recommendation preview.
- [x] Login response includes `role=user|admin`.
- [x] Seed data includes one normal user account and one admin account.
- [x] Profile shows nickname, avatar, interests, favorites.
- [x] Profile shows nickname and interests.
- [x] User can edit interests from the frontend.
- [x] User can select preferred destinations/schools before recommendation.
- [x] Interest changes affect recommendation output.
- [x] Behavior logs are recorded after browsing/rating/favorite actions.

## Destinations And Recommendations

- [x] Destination list supports attraction/school category filter and sorting.
- [x] Destination seed uses real China attraction/university names and approximate coordinates.
- [ ] Destination detail shows rating, popularity, tags, description, related diaries.
- [x] Search supports attraction/school name/category/keyword.
- [x] Personal center shows personalized Top 10 attraction/school recommendations.
- [x] Recommendation response includes score and reason.
- [x] Recommendation candidate pool is destination records, not raw campus buildings or facilities.
- [x] User interests can represent preferred attraction and school categories before recommendation.

## Map And Routing

- [x] Navigation scope is school/campus internal after a campus destination is selected.
- [x] RoutePlannerPage is labeled as 北京邮电大学沙河校区内部场所导航, not cross-city tourism routing.
- [x] `GET /api/v1/search/places?scope=campus` returns only BUPT Shahe campus buildings/facilities/semantic named topology nodes and excludes nationwide attraction/school destinations.
- [x] Campus route endpoint search excludes generic road/intersection nodes such as `校园路口` and `道路节点`.
- [x] Map page displays roads, buildings, and facilities.
- [x] Map page can switch to nationwide attraction/school POI markers.
- [x] Attraction/school POI map supports category filter, keyword search, and hot/rating/name sort.
- [x] Map page scaffold uses AMap JS API for rendering.
- [x] Backend map data and route topology boundary is documented as OSMnx/OpenStreetMap, not AMap routing.
- [x] AMap default center is `[116.28333, 40.15608]` for 北京邮电大学沙河校区.
- [x] Backend GeoJSON coordinate contract is documented as `[lng, lat]` arrays for AMap overlays.
- [x] AMap overlays convert backend WGS84 coordinates to GCJ-02 before rendering.
- [x] `GET /api/v1/map/geojson` returns roads, buildings, facilities, categories, statistics, and GeoJSON from local DB rows.
- [ ] Place search highlights a map item.
- [x] Facility markers open an info window on click in `AMapView`.
- [x] Building polygons clear old overlays before filters redraw.
- [x] Single-route planning returns path steps, distance, time, and mode.
- [x] Single-route planning uses local `map_nodes` / `map_edges` and Dijkstra instead of mock route data.
- [x] Route target can be selected by BUPT Shahe campus building/facility/semantic named topology node, not only typed coordinates.
- [x] RoutePlannerPage defaults to `route_source=local_graph` over the imported BUPT Shahe campus topology.
- [x] Route API can still use AMap walking directions when explicitly requested, while the campus navigation page defaults to local topology.
- [x] Route API keeps `local_graph` mode for Dijkstra demonstration and network-free tests.
- [x] Shortest-time routing uses per-edge congestion where real speed = congestion * ideal speed.
- [x] Route planning filters by transport mode: walking, bicycle, electric cart, and mixed mode.
- [x] Route scaffold is drawn as polyline on map.
- [x] Route drawing calls fit-view behavior after rendering.
- [x] Optional AMap browser smoke harness exists and skips cleanly when `VITE_AMAP_KEY` or Playwright is unavailable.
- [x] Multi-point planning returns optimized order and closed loop.
- [x] Nearby facilities are sorted by graph distance, not straight-line distance.
- [x] Nearby facility query filters by category before route-distance ranking.
- [x] Nearby facility query returns Top-K results with route paths for AMap drawing.
- [x] Nearby facility query supports category-name text input and fuzzy category lookup.
- [x] NearbyFacilitiesPage lets the user choose the current campus place/origin.
- [x] NearbyFacilitiesPage can set the origin from a map click.
- [x] Nearby facility API accepts `origin_place_id` and resolves it before Dijkstra ranking.
- [x] Coordinate inputs remain available only as fallback/debug controls.
- [x] Nearby facility result displays origin, resolved category, route distance, duration, and route path.
- [x] System supports a second internal-navigation scene for 北京颐和园.
- [x] Scene-specific map APIs filter by `scene_key` and do not mix BUPT/Summer Palace data.
- [x] Summer Palace has at least 200 route edges, 20 buildings/scenic structures, and 50 facilities/POIs if source data allows.
- [x] Summer Palace scene restores from saved real OSMnx payload after `bash scripts/reset_dev_db.sh`.
- [x] Summer Palace supports route planning, multi-point planning, and nearby facility lookup by graph distance.

## Indoor Navigation

- [x] User can choose building and floor.
- [x] Indoor nodes include entrance, elevator/stairs, room, toilet.
- [x] Indoor route supports cross-floor steps.
- [x] Stage 38 building is upgraded to `中国科学技术馆主展厅`.
- [x] Stage 38 graph includes B1, 1F, 2F, 3F, 4F, and 5F.
- [x] Route from main entrance to elevator hall works.
- [x] Route from entrance to a fourth-floor exhibition hall uses elevator and reaches floor 4.
- [x] Accessible route mode avoids stairs/escalators and uses elevator.
- [x] Indoor route trace reports Dijkstra, route mode, node count, edge count, and vertical traffic choice.

## Diary Community

- [x] User can publish diary with title, body, and destination.
- [x] Seed diaries are scenic attraction travel diaries, not campus-only placeholder text.
- [x] User can record travel content with text plus image/video URL metadata.
- [ ] User can upload local image/video binary files through the browser when this is required for the demo.
- [x] All users' diaries are browsable in one community list.
- [x] Admin can list and delete diaries for unified management.
- [x] Diary detail increments views.
- [x] Diary views are treated as diary heat.
- [x] User can rate/comment on diary.
- [x] Diary list can be sorted by heat.
- [x] Diary list can be sorted by rating.
- [x] Diary recommendation uses Top-K ranking over views, rating, and personal interest.
- [x] Destination-related diaries can be queried with `destination_id`.
- [x] Destination-related diary results can be sorted by heat/rating.
- [x] Title exact search uses an indexed exact lookup instead of generic contains matching.
- [x] Body keyword diary search uses an inverted index or database full-text search.
- [x] Compression ratio can be displayed for a diary.
- [x] Compression endpoint reports lossless decompression check.
- [ ] Hand-written Huffman compression exists if the teacher explicitly requires a custom compression algorithm.
- [x] AIGC flow accepts scenic/school image or video URLs from diary media.
- [x] AIGC flow returns storyboard scenes and a simulated tourism animation/video link.
- [x] `/diaries` is a dedicated browse/search/detail page.
- [x] `/diaries` uses a card-style community result list and reader panel instead of a dense table-first layout.
- [x] `/diaries/create` is a dedicated publish/AIGC creation page.

## Food

- [x] Food list shows restaurant/window, cuisine, price, rating, heat.
- [x] Food page shows recommendations as visual cards with cuisine cover visuals.
- [x] Food page shows restaurant specialty cuisine tags.
- [x] Cuisine filter works.
- [x] Fuzzy search handles close spelling.
- [x] Fuzzy search covers food name, cuisine, restaurant name, and window/canteen name.
- [x] Fuzzy search covers real restaurant address after AMap food POI import.
- [x] Search uses Top-K heap ranking and can sort by match, heat, rating, and distance.
- [x] Food recommendations change with current location.
- [x] Food recommendation can be scoped to the selected destination/school.
- [x] Food recommendation supports scenic-spot nearby restaurants, with Summer Palace AMap POI restore data.
- [x] Food recommendation supports Top-10 by composite score, heat, rating, and distance without fully sorting all candidates.
- [x] Distance recommendation uses graph route distance when the local route graph can connect the restaurant, with coordinate fallback.
- [x] Food fuzzy search results can be explicitly sorted by heat, rating, and distance.
- [x] Food page defaults to Summer Palace for the real scenic food dataset and exposes current-location coordinates.
- [x] Real AMap food rows are marked with `restaurant_source=amap`; seed rows remain explicit fallback.

## AIGC

- [x] Diary draft endpoint returns title, draft, and reusable prompt.
- [x] Storyboard endpoint returns scene list, prompt, and simulated video link.
- [x] Frontend page can call both placeholder endpoints.
- [x] AIGC flow accepts scenic/campus media URLs as input.
- [x] AIGC flow returns a simulated tourism animation/video artifact from photo or diary content.
- [x] `POST /api/v1/aigc/agent/run` exposes an Agent-style workflow.
- [x] Agent response includes `result`, `agent_trace.steps[]`, and `algorithm_trace`.
- [x] Agent trace shows at least 4 deterministic tool steps with timing and status.
- [x] Media URLs affect the Agent media-analysis and storyboard output.
- [x] DiaryCreateAigcPage displays both generated artifact and Agent execution trace.
- [x] Legacy `diary-draft` and `storyboard` endpoints remain backward-compatible.

## Admin

- [x] Admin dashboard shows user/destination/map/diary/food counts.
- [x] Admin can inspect OSM import status and data scale.
- [x] Admin can moderate diaries and edit destinations/facilities/foods.
- [x] Admin dashboard requires `role=admin`.
- [x] Normal user token receives `403` from `/api/v1/admin/*`.
- [x] Missing admin token receives `401` from `/api/v1/admin/*`.
- [x] Frontend hides admin navigation for normal users.

## Docs And Tests

- [x] `docs/feature_matrix.md` is updated for implemented features.
- [x] `docs/course_requirement_gap_analysis.md` tracks gaps against `要求.md`.
- [x] Backend tests pass.
- [x] Frontend typecheck/build passes.
- [x] `bash scripts/check_all.sh` passes.
