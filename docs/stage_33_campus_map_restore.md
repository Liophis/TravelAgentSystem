# Stage 33 Campus Map Restore

## Scope

This stage fixes a local demo stability issue: after `bash scripts/reset_dev_db.sh`, the database returned to deterministic seed fallback layers. Public map APIs hide fallback layers by default, so BUPT Shahe campus navigation could render an empty map.

## Root Cause

`reset_dev_db.sh` seeded fallback roads, buildings, and facilities, but did not restore the imported/reference campus layers used by the visible map APIs.

Result after reset:

```text
visible roads = 0
visible buildings = 0
visible facilities = 0
hidden demo roads/buildings/facilities > 0
```

## Fix

Added:

```text
scripts/restore_campus_map.sh
```

The script runs fully offline:

1. Imports the BUPT Shahe reference topology from `data/reference/bupt-shahe/topology/`.
2. Imports offline OSMnx building/POI layers from `data/external/bupt-shahe/osm/osmnx_campus_payload.json`.
3. Verifies visible roads, buildings, and facilities are non-empty.

`scripts/reset_dev_db.sh` now calls `scripts/restore_campus_map.sh` after seeding.

## Expected Local Result

After reset:

```text
visible roads > 0
visible buildings > 0
visible facilities > 0
```

Current verified sample:

```text
roads = 246
buildings = 56
facilities = 58
```

## Validation

```bash
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```
