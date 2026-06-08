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
- [ ] At least one real OSM campus/scenic map can be imported.
- [x] `map_edges` count >= 450.
- [x] `buildings` count >= 60.
- [x] `facilities` count >= 120.
- [x] Facility categories count >= 10.
- [x] `GET /api/v1/map/stats` reads the seeded database and returns map scale counts.
- [x] OSM import pipeline can import an OSM-shaped payload into map tables.
- [x] Admin map import/status API reports current map table counts.

## Users

- [ ] User can register.
- [ ] User can log in and receive token.
- [ ] Profile shows nickname, avatar, interests, favorites.
- [ ] User can edit interests from the frontend.
- [ ] User can select preferred destinations/schools before recommendation.
- [ ] Interest changes affect recommendation output.
- [ ] Behavior logs are recorded after browsing/rating/favorite actions.

## Destinations And Recommendations

- [x] Destination list supports category filter and sorting.
- [ ] Destination detail shows rating, popularity, tags, description, related diaries.
- [x] Search supports name/category/keyword.
- [x] Home shows personalized Top 10 recommendations.
- [x] Recommendation response includes score and reason.

## Map And Routing

- [ ] Map page displays roads, buildings, and facilities.
- [x] Map page scaffold uses AMap JS API for rendering.
- [x] Backend map data and route topology boundary is documented as OSMnx/OpenStreetMap, not AMap routing.
- [x] AMap default center is `[116.28333, 40.15608]` for 北京邮电大学沙河校区.
- [x] Backend GeoJSON coordinate contract is documented as `[lng, lat]` arrays for AMap overlays.
- [x] AMap overlays convert backend WGS84 coordinates to GCJ-02 before rendering.
- [x] `GET /api/v1/map/geojson` returns roads, buildings, facilities, categories, statistics, and GeoJSON from seeded DB rows.
- [ ] Place search highlights a map item.
- [x] Facility markers open an info window on click in `AMapView`.
- [x] Building polygons clear old overlays before filters redraw.
- [x] Single-route planning returns path steps, distance, time, and mode.
- [x] Single-route planning uses seeded `map_nodes` / `map_edges` and Dijkstra instead of mock route data.
- [ ] Route target can be selected by destination/place/facility name, not only typed coordinates.
- [x] Shortest-time routing uses per-edge congestion where real speed = congestion * ideal speed.
- [x] Route planning filters by transport mode: walking, bicycle, electric cart, and mixed mode.
- [x] Route scaffold is drawn as polyline on map.
- [x] Route drawing calls fit-view behavior after rendering.
- [x] Multi-point planning returns optimized order and closed loop.
- [x] Nearby facilities are sorted by graph distance, not straight-line distance.
- [x] Nearby facility query filters by category before route-distance ranking.
- [x] Nearby facility query returns Top-K results with route paths for AMap drawing.
- [ ] Nearby facility query supports category-name text input and fuzzy category lookup.

## Indoor Navigation

- [x] User can choose building and floor.
- [x] Indoor nodes include entrance, elevator/stairs, room, toilet.
- [x] Indoor route supports cross-floor steps.

## Diary Community

- [x] User can publish diary with title, body, and destination.
- [ ] User can attach image/video media to diary.
- [x] Diary detail increments views.
- [x] User can rate/comment on diary.
- [ ] Title exact search uses an indexed exact lookup instead of generic contains matching.
- [ ] Body keyword diary search uses an inverted index or database full-text search.
- [ ] Diary recommendation uses views, rating, and personal interest.
- [x] Compression ratio can be displayed for a diary.

## Food

- [x] Food list shows restaurant/window, cuisine, price, rating, heat.
- [x] Cuisine filter works.
- [x] Fuzzy search handles close spelling.
- [x] Food recommendations change with current location.
- [ ] Food recommendation can be scoped to the selected destination/school.
- [ ] Food fuzzy search results can be explicitly sorted by heat, rating, and distance.

## AIGC

- [x] Diary draft endpoint returns title, draft, and reusable prompt.
- [x] Storyboard endpoint returns scene list, prompt, and simulated video link.
- [x] Frontend page can call both placeholder endpoints.
- [ ] AIGC flow accepts uploaded scenic/campus photos as input.
- [ ] AIGC flow returns a simulated tourism animation/video artifact from photo or diary content.

## Admin

- [x] Admin dashboard shows user/destination/map/diary/food counts.
- [x] Admin can inspect OSM import status and data scale.
- [ ] Admin can moderate diaries and edit destinations/facilities/foods.

## Docs And Tests

- [x] `docs/feature_matrix.md` is updated for implemented features.
- [x] `docs/course_requirement_gap_analysis.md` tracks gaps against `要求.md`.
- [x] Backend tests pass.
- [x] Frontend typecheck/build passes.
- [x] `bash scripts/check_all.sh` passes.
