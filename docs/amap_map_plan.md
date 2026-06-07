# AMap Map Rendering Plan

## Goal

Frontend map rendering uses AMap JS API. Backend map data, route planning, and road-distance calculations still use OSMnx/OpenStreetMap topology.

## Dependencies

- Frontend package: `@amap/amap-jsapi-loader`
- Environment variable: `VITE_AMAP_KEY`
- Key source: `.env.local`; never hard-code the key in source files.

## Frontend Files To Add Later

```text
frontend/src/utils/amap.ts
frontend/src/components/AMapView.vue
frontend/src/pages/MapGuidePage.vue
frontend/src/pages/RoutePlannerPage.vue
frontend/src/pages/NearbyFacilitiesPage.vue
```

## AMapView Contract

Props:

```text
facilities: facility points
buildings: building polygons
roadPaths: road polyline paths for guide display
routePath: route coordinate path
```

Rendering rules:

- Default center is `[116.3260, 40.0030]`.
- Facilities render as AMap `Marker`.
- Building areas render as AMap `Polygon`.
- Roads render as neutral AMap `Polyline`.
- Routes render as AMap `Polyline`.
- Clicking a facility marker opens an info window.
- After rendering a route, call map fit-view behavior.
- Clear old overlays before redrawing to avoid duplicate markers, polygons, or polylines.

## Page Contracts

`MapGuidePage.vue`:

- Calls `GET /api/v1/map/geojson`.
- Reads roads, buildings, and facilities.
- Converts backend GeoJSON to AMap coordinate arrays.
- Supports facility category filtering.
- Current stage uses mock OSM-shaped payloads until OSM import is implemented.

`RoutePlannerPage.vue`:

- Calls `POST /api/v1/routes/plan`.
- Reads route `path` or `path_geojson`.
- Uses `AMapView` to draw the route polyline.
- Shows total distance, estimated duration, and route steps.
- Current stage uses mock route output until OSM graph routing is implemented.

`NearbyFacilitiesPage.vue`:

- Calls `GET /api/v1/facilities/nearby`.
- Draws nearby facilities as markers.
- Clicking a facility can route to the planner or draw the route directly.
- Current stage uses placeholder distance ranking until road-distance routing is implemented.

## Coordinate Rules

- Backend GeoJSON follows longitude/latitude order.
- AMap overlays require `[longitude, latitude]`.
- Route path arrays should be normalized to `[lng, lat][]` before passing to `AMapView`.

## Backend Boundary

- Do not use AMap routing as the backend route source.
- Use OSMnx/OSM graph data for shortest path, route distance, route time, and nearby-facility road-distance sorting.
- AMap is only the frontend rendering layer.
