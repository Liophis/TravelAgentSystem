# Stage 6 Destinations, Search, Recommendation

## Scope

This stage implements the remaining recommendation and search work from the project plan's fourth phase. It uses deterministic real-destination seed data and does not implement PostgreSQL full-text search or pg_trgm yet.

Destination scope:

- Tourism recommendation candidates are real China attractions and schools/universities from `destinations`.
- Campus buildings/facilities/named topology nodes remain map and route entities; they are not mixed into the tourism recommendation candidate pool.
- Rating/popularity are deterministic demo signals so Top-K, hot sort, and rating sort remain repeatable in tests.

## Delivered

- Added destination list/detail service and API:
  - `GET /api/v1/destinations`
  - `GET /api/v1/destinations/{id}`
- Added place search across destinations, buildings, and facilities:
  - `GET /api/v1/search/places`
  - `scope=destinations` returns attraction/school destination records for tourism search.
  - `scope=campus` returns only BUPT Shahe campus buildings/facilities/named topology nodes for campus navigation endpoints.
- Added destination recommendation service and API:
  - `GET /api/v1/recommendations`
- Recommendation uses:
  - rating score
  - popularity score
  - user interest match
  - distance score
  - freshness score
  - Top-K heap selection
- Added destination list/search page.
- Home page now shows Top 10 recommendations and strategy switching.
- Added backend tests for destination list/detail, place search, recommendation, and API handlers.

## API Contracts

Destination list:

```text
GET /api/v1/destinations?category=school&q=大学&sort=popularity&limit=20&offset=0
```

Place search:

```text
GET /api/v1/search/places?keyword=厕所&limit=5
GET /api/v1/search/places?keyword=厕所&scope=campus&limit=5
GET /api/v1/search/places?keyword=大学&scope=destinations&limit=5
```

Recommendations:

```text
GET /api/v1/recommendations?user_id=1&strategy=composite&limit=10
```

Recommendation response includes:

```text
items[].score
items[].reason
items[].tags
algorithm_trace.formula
```

## Validation

Run from repository root:

```bash
bash scripts/reset_dev_db.sh
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```

Expected backend result:

```text
19 passed
```

## Known Gaps

- Search is case-insensitive contains matching, not PostgreSQL full-text / pg_trgm.
- Recommendation is rule scoring, not collaborative filtering.
- Destination detail page does not yet show related diaries.
- User login/profile and dynamic behavior logging are still planned.

## Next Stage

Continue project plan P0/P1 work with user-facing content modules:

- user auth and profile basics
- diary publish/list/detail/search
- food search and recommendation
