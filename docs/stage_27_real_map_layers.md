# Stage 27 Real Map Layers

## Scope

This stage removes old offline square/demo layers from the public map and switches the map API to real-priority data:

- OSMnx/OpenStreetMap walking graph for visible road overlays
- OSMnx/OpenStreetMap building polygons
- AMap Web Service POIs for dense facilities
- OSM amenities as extra facilities
- deterministic seed graph kept as hidden fallback for tests and local Dijkstra demos

## Delivered

- Public map APIs hide seed/fallback roads, buildings, and facilities by default.
- `include_demo=true` keeps old fallback layers available for debugging and tests.
- `POST /api/v1/admin/map/cleanup-demo-layers`
- `POST /api/v1/admin/map/import` supports:
  - `source=osmnx_graph`
  - `source=osmnx_features`
  - `source=amap_poi`
- `backend/scripts/import_osm_campus.py --graph-only`
- `backend/scripts/import_osm_campus.py --features-only`
- `backend/scripts/clean_demo_map_layers.py`
- `scripts/clean_demo_map_layers.sh`
- `AMapView` uses compact facility dots instead of large default pins.
- `MapGuidePage` text now describes OSM buildings plus AMap/OSM facilities accurately.

## Local Live Data

Current local dev DB after cleanup and live imports:

- visible OSM road edges: 2045
- OSM building polygons: 188
- AMap POIs: 516
- OSM POIs: 49
- visible facilities: 565
- old demo building polygons: 0
- hidden fallback seed roads: 641

## Rebuild Commands

```bash
bash scripts/reset_dev_db.sh
python backend/scripts/import_amap_pois.py --radius 3000 --max-pages 3 --request-interval 0.8 --reset-facilities
bash scripts/clean_demo_map_layers.sh
python backend/scripts/import_osm_campus.py --source osmnx --graph-only --dist 1800
python backend/scripts/import_osm_campus.py --source osmnx --features-only --dist 1800
bash scripts/smoke_features.sh
```

## Validation

```bash
PYTHONPATH=backend pytest backend/tests/test_stage3_map_data_service.py backend/tests/test_stage7_osm_import.py
npm run typecheck
```

Expected:

- default map API does not return demo seed polygons
- `include_demo=true` still exposes fallback layers for tests
- OSM feature import removes seed polygons and preserves AMap POIs
- OSM road graph import exposes OSM roads while hiding fallback roads

## Remaining Limits

- Live import depends on OSM/Nominatim/Overpass availability and external quotas.
- Seed road graph remains in the DB for algorithm tests, but public map APIs hide it by default.
