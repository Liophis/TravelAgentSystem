# Stage 41 Navigation Data Cleaning

## Goal

Clean the user-facing navigation data for:

- `bupt_shahe`: 北京邮电大学沙河校区内部导航。
- `summer_palace`: 北京颐和园内部导航。

The goal is not to delete graph topology needed by Dijkstra. Road/intersection nodes may remain in the database, but meaningless points must not appear as user-selectable route endpoints.

## Problems Found

- BUPT reference source contained non-campus POIs:
  - `防御塔景区`
  - `观景区`
- BUPT and Summer Palace route search could expose generic OSM buildings such as `OSM building`.
- Summer Palace imported OSM facilities included generic English names such as `toilets`, `cafe`, `fast_food`, and `poi`.
- Summer Palace payload contained a small number of invalid edges.

## Completed

- Added `backend/app/services/navigation_data_cleaning_service.py`.
- Added CLI:

```bash
PYTHONPATH=backend python backend/scripts/clean_navigation_data.py --scene-key all
PYTHONPATH=backend python backend/scripts/clean_navigation_data.py --scene-key bupt_shahe
PYTHONPATH=backend python backend/scripts/clean_navigation_data.py --scene-key summer_palace
```

- Added shell wrapper:

```bash
bash scripts/clean_navigation_data.sh
bash scripts/clean_navigation_data.sh bupt_shahe
bash scripts/clean_navigation_data.sh summer_palace
```

- Integrated cleaning into:
  - `scripts/restore_campus_map.sh`
  - `scripts/restore_summer_palace_map.sh`
- Updated BUPT reference import to skip blocked non-campus POIs during import.
- Updated place search to hide generic building names and generic POI names.
- Current restore/clean results:
  - BUPT reference import skips blocked facilities before insert.
  - BUPT clean step removed blocked facilities: 0 after import-level blocklist.
  - BUPT visible facilities after restore: 55.
  - Summer Palace normalized facility names: 12.
  - Summer Palace removed invalid edges: 4.
  - Summer Palace visible roads after cleanup: 626.

## Cleaning Rules

- Do not remove road/intersection nodes required by Dijkstra.
- Remove known blocked BUPT non-campus POIs.
- Normalize generic facility names using category:
  - `toilets` -> `洗手间`
  - `cafe` -> `咖啡馆`
  - `fast_food` -> `快餐`
  - `restaurant` -> `餐厅`
  - `drinking_water` -> `饮水点`
- Hide user-facing generic endpoints:
  - `OSM building`
  - `poi`
  - empty/nan/none names
- Remove invalid graph edges:
  - self-loop edges;
  - zero or negative distance edges;
  - edges without usable geometry.

## Verification

```bash
PYTHONPATH=backend python -m pytest \
  backend/tests/test_stage28_reference_campus_import.py \
  backend/tests/test_stage35_multi_scene_navigation.py \
  backend/tests/test_stage6_destinations_search_recommend.py \
  backend/tests/test_stage41_navigation_data_cleaning.py
```

Passed locally during Stage 41.

Smoke expectations after cleaning:

- BUPT route endpoint list does not expose `防御塔景区`, `观景区`, or `OSM building`.
- Summer Palace route endpoint list does not expose `OSM building` or `poi`.
- BUPT and Summer Palace local Dijkstra routes still work.
- Summer Palace visible roads remain above the course minimum of 200 edges.
