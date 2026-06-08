# Stage 18 Facility And Food Query Polish

## Scope

This stage closes two query requirements from `要求.md`:

- service facilities can be queried by category name, not only internal category code
- food fuzzy-search results can be sorted by heat, rating, and distance

## Delivered

- Nearby facilities now resolve category input by:
  - category code
  - category display name
  - common Chinese aliases
  - contains matching
- Nearby facilities still filter by category before Dijkstra distance ranking.
- Food search now accepts:
  - `sort=match`
  - `sort=hot`
  - `sort=rating`
  - `sort=distance`
  - `current_lng/current_lat` for distance sorting
- Food search returns distance values.
- Frontend updates:
  - nearby facility category select is filterable and accepts typed category names
  - food search page exposes sort controls and distance column
- Smoke and backend tests cover the new query behavior.

## Validation

Run:

```bash
PYTHONPATH=backend pytest backend/tests/test_stage5_nearby_facilities.py backend/tests/test_stage9_food_aigc_admin.py
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

Expected:

- `category=厕所` resolves to `toilet`
- food search with `sort=distance` returns ascending distance
- frontend typecheck/build passes

## Remaining Gaps

- Food recommendation scope was completed later in Stage 24 and strengthened in Stage 36.
- Facility category lookup is deterministic alias/contains matching, not a learned semantic search.
