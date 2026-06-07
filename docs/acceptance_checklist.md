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
- [x] `map_edges` count >= 200.
- [x] `buildings` count >= 20.
- [x] `facilities` count >= 50.
- [x] Facility categories count >= 10.

## Users

- [ ] User can register.
- [ ] User can log in and receive token.
- [ ] Profile shows nickname, avatar, interests, favorites.
- [ ] Interest changes affect recommendation output.
- [ ] Behavior logs are recorded after browsing/rating/favorite actions.

## Destinations And Recommendations

- [ ] Destination list supports category filter and sorting.
- [ ] Destination detail shows rating, popularity, tags, description, related diaries.
- [ ] Search supports name/category/keyword.
- [ ] Home shows personalized Top 10 recommendations.
- [ ] Recommendation response includes score and reason.

## Map And Routing

- [ ] Map page displays roads, buildings, and facilities.
- [x] Map page scaffold uses AMap JS API for rendering.
- [x] Backend map data and route topology boundary is documented as OSMnx/OpenStreetMap, not AMap routing.
- [x] AMap default center is `[116.28333, 40.15608]` for 北京邮电大学沙河校区.
- [x] Backend GeoJSON coordinate contract is documented as `[lng, lat]` arrays for AMap overlays.
- [ ] Place search highlights a map item.
- [x] Facility markers open an info window on click in `AMapView`.
- [x] Building polygons clear old overlays before filters redraw.
- [ ] Single-route planning returns path steps, distance, time, and mode.
- [x] Route scaffold is drawn as polyline on map.
- [x] Route drawing calls fit-view behavior after rendering.
- [ ] Multi-point planning returns optimized order and closed loop.
- [ ] Nearby facilities are sorted by road distance, not straight-line distance.

## Indoor Navigation

- [ ] User can choose building and floor.
- [ ] Indoor nodes include entrance, elevator/stairs, room, toilet.
- [ ] Indoor route supports cross-floor steps.

## Diary Community

- [ ] User can publish diary with title, body, destination, media.
- [ ] Diary detail increments views.
- [ ] User can rate/comment/like/favorite diary.
- [ ] Title exact search works.
- [ ] Full-text diary search works.
- [ ] Compression ratio can be displayed for a diary.

## Food

- [ ] Food list shows restaurant/window, cuisine, price, rating, heat.
- [ ] Cuisine filter works.
- [ ] Fuzzy search handles close spelling.
- [ ] Food recommendations change with current location.

## Admin

- [ ] Admin dashboard shows user/destination/map/diary/food counts.
- [ ] Admin can inspect OSM import status and data scale.
- [ ] Admin can moderate diaries and edit destinations/facilities/foods.

## Docs And Tests

- [ ] `docs/feature_matrix.md` is updated for implemented features.
- [x] Backend tests pass.
- [x] Frontend typecheck/build passes.
- [x] `bash scripts/check_all.sh` passes.
