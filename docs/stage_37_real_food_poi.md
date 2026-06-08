# Stage 37 Real Destination Food POI

## Scope

Correct the food recommendation semantics from campus seed dishes to destination-nearby real restaurants.

Primary demo target:

- Destination: `颐和园`
- Data source: AMap Place Around Web Service
- Raw payload: `data/external/summer-palace/amap_gcj02/food_pois_raw.json`

## Implemented

- Added `backend/scripts/import_amap_foods.py`.
- Added `app.services.amap_food_import_service`.
- Added admin import source `amap_food`.
- Added restaurant metadata fields:
  - `source`
  - `external_id`
  - `address`
  - `category`
- Saved and imported real Summer Palace surrounding restaurant POIs.
- Added `scripts/restore_summer_palace_foods.sh`.
- `scripts/reset_dev_db.sh` now restores Summer Palace food POIs when the raw payload exists.

## Data Result

Current saved Summer Palace food payload:

```text
raw AMap POIs: 343
clean imported restaurants: 202
generated recommendation rows: 202
```

AMap does not expose public heat directly through Place Around. The importer uses:

- real POI name/address/category/coordinate from AMap
- real `biz_ext.rating` and `biz_ext.cost` when present
- deterministic heat signal derived from rating and destination distance

## Commands

Download and import live AMap food POIs:

```bash
PYTHONPATH=backend python backend/scripts/import_amap_foods.py \
  --destination-id 103 \
  --radius 3000 \
  --max-pages 2 \
  --request-interval 0.5 \
  --reset-destination \
  --save-raw data/external/summer-palace/amap_gcj02/food_pois_raw.json
```

Restore from saved raw payload:

```bash
bash scripts/restore_summer_palace_foods.sh
```

## Acceptance

- [x] Food recommendation is destination-nearby restaurant recommendation.
- [x] Summer Palace has real AMap restaurant POIs.
- [x] Raw source payload is saved under `data/external`.
- [x] Imported rows are marked `restaurant_source=amap`.
- [x] Food search can match real restaurant names and addresses.
- [x] Reset flow can restore the real food dataset without network.
- [x] Tests cover importing AMap-shaped restaurant POIs into recommendation/search.
