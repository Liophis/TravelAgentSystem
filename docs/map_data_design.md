# Map Data Design

## Source

Backend road topology and building polygons can be imported from OpenStreetMap through OSMnx/Overpass when network access is available. Required tests use a deterministic OSM-shaped fixture.

Manually supplied campus reference files belong under `data/reference/bupt-shahe/`. This is the preferred path when we have authoritative WGS84 campus JSON/GeoJSON or topology files from another source.

Facility density can be enriched from AMap Web Service Place Around POIs. This is a POI import path only; it does not replace backend route topology.

POIs are split by role:

- `nearby_facilities`: school-surrounding POIs for nearby facility recommendation.
- `campus_navigation`: BUPT Shahe internal POIs filtered by campus boundary for route endpoint/search support.

Internal navigation now needs multiple scenes:

- `bupt_shahe`: 北京邮电大学沙河校区.
- `summer_palace`: 北京颐和园 scenic area.

Map rows should be filtered by `scene_key` so importing one scene never replaces or pollutes another scene.

## Stored Layers

- Roads: `map_nodes`, `map_edges`.
- Buildings: `buildings` polygons.
- Facilities: `facilities` points and `facility_categories`.

Scene-scoped map tables:

```text
map_nodes.scene_key
map_edges.scene_key
buildings.scene_key
facilities.scene_key
```

Default scene is `bupt_shahe` for backward compatibility.

## Coordinate Contract

All API coordinates are WGS84 `[lng, lat]` arrays. AMap Web Service POIs arrive as GCJ-02 and are converted to WGS84 before storage. Frontend overlays convert WGS84 back to GCJ-02 before rendering on the AMap basemap.

## Frontend Rendering

`AMapView.vue` renders:

- Marker overlays for facilities.
- Polygon overlays for buildings.
- Polyline overlays for roads and routes.

Old overlays are cleared before redraw to avoid duplicate markers and stale routes.

## Import Modes

- Fixture import: offline and test-safe.
- OSMnx import: manual/network-enabled path.
- Reference campus import: offline path from `data/reference/bupt-shahe/raw_wgs84/` and `data/reference/bupt-shahe/topology/`, implemented by `backend/scripts/import_reference_campus.py`.
- AMap POI import: manual/network-enabled facility enrichment path using `AMAP_WEB_API_KEY`, with `--dataset nearby_facilities|campus_navigation`.
- Download-only source capture: `import_osm_campus.py --download-only --save-payload ...` and `import_amap_pois.py --download-only --save-raw ...`.
- If Nominatim place lookup fails, importer falls back to configured center point and radius.
- Summer Palace raw payloads belong under `data/external/summer-palace/`, not the BUPT directories.
- Summer Palace saved OSMnx payload contains 236 nodes, 630 raw road edges, 228 building/scenic polygons, and 79 facilities/POIs. `bash scripts/restore_summer_palace_map.sh` runs Stage 41 cleanup, leaving 626 visible valid road edges.

Raw reference files must be validated and imported into the database before API handlers use them.
