# Stage 9 Food, AIGC, And Admin Dashboard

## Scope

This stage completes the remaining demo-friendly slice of the project plan's fifth phase after Stage 8 diaries: food recommendation, AIGC placeholder endpoints, and a basic admin data dashboard.

## Delivered

- Added food APIs:
  - `GET /api/v1/foods/restaurants`
  - `GET /api/v1/foods/items`
  - `GET /api/v1/foods/search`
  - `GET /api/v1/foods/recommend`
  - `GET /api/v1/foods/nearby`
- Added food service with cuisine filtering, fuzzy search, rule scoring, Top-K heap ranking, and route preview for nearby foods.
- Added AIGC placeholder APIs:
  - `POST /api/v1/aigc/diary-draft`
  - `POST /api/v1/aigc/storyboard`
- Extended `GET /api/v1/admin/stats` with core table counts.
- Added frontend pages:
  - `FoodRecommendPage`
  - `AigcAssistantPage`
  - `AdminDashboardPage`
- Updated route/sidebar/home entries.
- Added Stage 9 backend tests and smoke coverage.

## API Contracts

Food recommendation:

```bash
curl 'http://127.0.0.1:8000/api/v1/foods/recommend?user_id=1&limit=10&current_lng=116.28333&current_lat=40.15608'
```

Nearby food:

```bash
curl 'http://127.0.0.1:8000/api/v1/foods/nearby?radius=5000&limit=5'
```

AIGC diary draft:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/aigc/diary-draft \
  -H 'Content-Type: application/json' \
  -d '{"topic":"沙河校区路线","keywords":["食堂","图书馆"],"tone":"自然"}'
```

Admin stats:

```bash
ADMIN_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/users/login \
  -H 'Content-Type: application/json' \
  -d '{"username_or_email":"admin01","password":"admin123456"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
curl -H "Authorization: Bearer $ADMIN_TOKEN" 'http://127.0.0.1:8000/api/v1/admin/stats'
```

## Validation

Run from repository root:

```bash
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```

Expected backend result after this stage:

```text
28 passed
```

## Known Gaps

- AIGC is deterministic mock logic; no external model API is called.
- Stage 31 adds role-based admin access control; this stage originally delivered the dashboard shell.
- This stage used deterministic seed food rows; Stage 37 later adds real AMap restaurant POIs around Summer Palace.
- Food search uses lightweight fuzzy matching, not PostgreSQL trigram/full-text search yet.

## Next Stage

Continue the project plan's sixth phase:

- harden tests and smoke scripts
- docker compose validation
- deployment docs
- final demo checklist and defense materials
