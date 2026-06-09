# Stage 42 Data Requirement Coverage

## Goal

Make the course data-volume requirements verifiable from the local dev database.

Required by the assignment:

- scenic/campus destination count >= 200;
- scenic/campus internal buildings or scenic structures >= 20;
- service facility categories >= 10;
- service facilities >= 50;
- internal route graph edges >= 200;
- map should include buildings, services, and road topology.

## Completed

- Increased RoutePlannerPage candidate retention from 80 to 200 route endpoints.
  - BUPT currently exposes 74 selectable internal places.
  - Summer Palace currently exposes 130 selectable internal places.
  - `GET /api/v1/search/places` now accepts `limit=200` so the frontend selector contract matches the retained candidate count.
- Added data requirement check CLI:

```bash
PYTHONPATH=backend python backend/scripts/check_data_requirements.py
```

- Added shell wrapper:

```bash
bash scripts/check_data_requirements.sh
```

## Current Counts

```text
destinations: 207

bupt_shahe:
  roads: 246
  buildings: 56
  facilities: 55
  facility_categories: 16
  selectable_places: 74

summer_palace:
  roads: 626
  buildings: 228
  facilities: 79
  facility_categories: 10
  selectable_places: 130
```

## Verification

```bash
bash scripts/check_data_requirements.sh
```

Expected:

```text
[data-check] OK
```

## Notes

- Counts are from cleaned, visible scene data after Stage 41 navigation data cleanup.
- Road/intersection nodes are retained for Dijkstra but are not shown as user-selectable endpoints.
- Selectable places include named buildings, services, and semantic topology nodes.
