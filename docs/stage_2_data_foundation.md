# Stage 2 Data Foundation

## Delivered

- Default campus changed to 北京邮电大学沙河校区.
- SQLAlchemy model registry added for core tables:
  - users, profiles, interests
  - destinations, tags
  - map nodes, map edges, buildings, facility categories, facilities
  - diaries
  - restaurants, foods
- Deterministic seed data added for tourism recommendation and campus navigation:
  - users: 10
  - destinations: 207 real China attraction/university rows
  - map nodes: 180
  - map edges: 641
  - buildings: 60
  - facility categories: 10
  - facilities: 120
  - indoor nodes: 19
  - indoor edges: 20
  - restaurants: 12
  - foods: 72
  - diaries: 20
- `scripts/reset_dev_db.sh` drops/recreates the dev schema and reseeds.
- `scripts/seed_all.sh` is idempotent when data already exists.
- Backend tests verify model metadata and seed scale against SQLite.

## Commands

```bash
bash scripts/reset_dev_db.sh
bash scripts/seed_all.sh
bash scripts/check_all.sh
```

## Notes

- Dev seed defaults to `DEV_DATABASE_URL=sqlite:///./smart_tour_dev.db`.
- PostgreSQL/PostGIS remains the target deployment database.
- Destination seed data uses real attraction/university names, categories, provinces, cities, and approximate coordinates. Rating/popularity are deterministic demo signals for recommendation sorting.
- Real OSMnx import is not implemented in this stage; seeded map data is deterministic mock data shaped like campus map data.
- `scripts/smoke_features.sh` should not leave persistent user-interest mutations in the dev DB.
