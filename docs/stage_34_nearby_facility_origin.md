# Stage 34 Nearby Facility Origin Selection

## Scope

This is the preparation document for fixing the nearby-facility workflow against requirement `(3) 场所查询`.

The current backend can rank facilities by graph distance, but the frontend still defaults to a fixed coordinate. That is not a complete "nearby" interaction. The user must first select a current place or map point.

## Requirement Mapping

| Requirement | Target Behavior | Current State | Gap |
| --- | --- | --- | --- |
| Select a scenic/campus place and find nearby facilities in a range | User chooses an origin place such as library, gate, canteen, building, facility, or map click | API has coordinate fallback; frontend uses default BUPT center | Missing explicit origin selector and map-click origin |
| Filter by category | User chooses facility category before search | Category query exists | Page needs clearer category text input plus stable options from API/data |
| Input category name and sort by distance | User can type `厕所/卫生间/超市/食堂`, backend resolves category and ranks by real walking distance | Backend supports alias/category contains matching | UI should expose text input and show resolved category |
| Distance is not straight-line | Backend runs Dijkstra and Top-K over route distance | Implemented in service | Needs visible `algorithm_trace`/distance explanation in page |

## Product Flow

```text
MapGuidePage
  -> user selects a campus place/facility/building or clicks map
  -> NearbyFacilitiesPage receives origin
  -> user selects or types a facility category
  -> backend filters candidates by category
  -> backend runs Dijkstra route distance from origin to each candidate
  -> backend returns Top-K facilities with routePath
  -> frontend marks origin, facilities, and selected route on AMap
```

NearbyFacilitiesPage should also work independently:

```text
origin selector: GET /api/v1/search/places?scope=campus
category input: dropdown + free text
radius input: meters
result table: facility name, resolved category, route distance, duration
map: origin marker, facility markers, route polyline
```

## API Target

Extend:

```text
GET /api/v1/facilities/nearby
```

New preferred parameters:

```text
origin_place_id=building-33 | facility-123 | node-184
category=超市
radius=800
limit=10
```

Coordinate fallback remains for map clicks and debugging:

```text
current_lng=116.28333
current_lat=40.15608
```

Response should include:

```text
origin.id
origin.name
origin.lng
origin.lat
category_query
category
items[].distance
items[].duration
items[].routePath
algorithm_trace.origin_resolution
algorithm_trace.category_lookup
algorithm_trace.distance
algorithm_trace.ranking
```

## Dataset Boundary

- `campus_navigation`: school-internal buildings, semantic nodes, and campus POIs; used for origin selection and strict campus demo.
- `nearby_facilities`: school-surrounding facilities; used for surrounding-service recommendation.
- Stage 34 first fixes the interaction with the current `facilities` table. A later data-model hardening stage should add an explicit `dataset`/`scope` column if we need strict separation in queries.

## Acceptance Criteria

- [ ] User can choose origin from campus place search.
- [ ] User can set origin by clicking the map.
- [ ] User can still use coordinate fallback from an advanced/debug panel.
- [ ] Query sends selected origin to backend instead of silently using fixed BUPT center.
- [ ] Backend accepts `origin_place_id` and resolves it through the same campus place model used by route planning.
- [ ] Category can be selected or typed in Chinese.
- [ ] Result shows resolved category, real route distance, duration, and routePath.
- [ ] Map shows origin marker, facility markers, and selected route.
- [ ] `algorithm_trace` explains category lookup, Dijkstra graph distance, and Top-K heap ranking.

## Planned Validation

```bash
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```
