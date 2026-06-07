# Stage 2 Data Foundation

## Delivered

- Default campus changed to 北京邮电大学沙河校区.
- SQLAlchemy model registry added for core tables:
  - users, profiles, interests
  - destinations, tags
  - map nodes, map edges, buildings, facility categories, facilities
  - diaries
  - restaurants, foods
- Deterministic seed data added for the current campus:
  - users: 10
  - destinations: 200
  - map nodes: 80
  - map edges: 220
  - buildings: 20
  - facility categories: 10
  - facilities: 50
  - restaurants: 5
  - foods: 30
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
- Real OSMnx import is not implemented in this stage; seeded map data is deterministic mock data shaped like campus map data.

