# Testing Plan

## Required Local Commands

```bash
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```

## Backend Coverage

- Stage 1 health/API foundation.
- Stage 2 database and seed counts.
- Stage 3 map data APIs.
- Stage 4 Dijkstra route planning.
- Stage 5 nearby facility graph-distance ranking.
- Stage 6 destination search and recommendation.
- Stage 7 OSM import fixture and fallback.
- Stage 8 diary compression/search/rating/comment.
- Stage 9 food recommendation, AIGC placeholders, admin stats.
- Stage 32 planned: AIGC Agent endpoint/result/trace tests.

## Frontend Coverage

Current required frontend validation is:

- TypeScript typecheck.
- Production build.
- Manual browser pass through all page routes.

## Manual Browser Pass

1. Confirm AMap key is configured.
2. Visit all sidebar routes.
3. Trigger one API request per page.
4. Confirm no empty map caused by missing key.
5. Confirm no obvious text overlap on desktop viewport.
