# Map Data Design

## Source

Backend map data is imported from OpenStreetMap through OSMnx/Overpass. Required tests use a deterministic OSM-shaped fixture.

## Stored Layers

- Roads: `map_nodes`, `map_edges`.
- Buildings: `buildings` polygons.
- Facilities: `facilities` points and `facility_categories`.

## Coordinate Contract

All API coordinates are WGS84 `[lng, lat]` arrays. AMap overlays receive the same order.

## Frontend Rendering

`AMapView.vue` renders:

- Marker overlays for facilities.
- Polygon overlays for buildings.
- Polyline overlays for roads and routes.

Old overlays are cleared before redraw to avoid duplicate markers and stale routes.

## Import Modes

- Fixture import: offline and test-safe.
- OSMnx import: manual/network-enabled path.
- If Nominatim place lookup fails, importer falls back to configured center point and radius.
