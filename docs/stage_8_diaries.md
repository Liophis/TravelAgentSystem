# Stage 8 Diary Community

## Scope

This stage implements the first diary-community slice of the project plan's fifth phase. It keeps the required harness offline-friendly and focuses on DB-backed publish, browse, search, recommendation, rating, comments, and compression/decompression verification.

For the current course-requirement alignment, also see `docs/stage_22_diary_media_search.md` and `docs/stage_30_diary_requirement_alignment.md`.

## Delivered

- Added diary compression helper: `backend/app/algorithms/compression.py`.
- Extended diary models:
  - `diaries.compressed_body`
  - `diaries.original_size`
  - `diaries.compressed_size`
  - `diaries.rating_sum`
  - `diaries.rating_count`
  - `diary_comments`
  - `diary_ratings`
- Added diary service: `backend/app/services/diary_service.py`.
- Added diary APIs:
  - `POST /api/v1/diaries`
  - `GET /api/v1/diaries`
  - `GET /api/v1/diaries/{id}`
  - `PUT /api/v1/diaries/{id}`
  - `DELETE /api/v1/diaries/{id}`
  - `POST /api/v1/diaries/{id}/view`
  - `POST /api/v1/diaries/{id}/rating`
  - `POST /api/v1/diaries/{id}/comments`
  - `GET /api/v1/diaries/search`
  - `GET /api/v1/diaries/recommend`
  - `GET /api/v1/diaries/{id}/compression`
- Added `frontend/src/pages/DiaryCommunityPage.vue` for browse/search/detail/rating/comment.
- Added `frontend/src/pages/DiaryCreateAigcPage.vue` for publishing diaries and running the AIGC Agent.
- Added route and navigation entries for `/diaries` and `/diaries/create`.
- Seed diaries now describe scenic attraction destinations and are stored through compressed text fields.
- Diary browse/query and publish/AIGC are split into two pages to avoid a crowded combined workflow.
- Updated harness docs and tests.

## API Contracts

Create diary:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/diaries \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"destination_id":1,"title":"颐和园旅行日记","body":"沿着湖边步道游览，记录景点、餐饮和休息点。"}'
```

Search:

```bash
curl 'http://127.0.0.1:8000/api/v1/diaries/search?keyword=目的地&limit=10'
```

Recommend:

```bash
curl 'http://127.0.0.1:8000/api/v1/diaries/recommend?limit=10'
```

Compression stats:

```bash
curl 'http://127.0.0.1:8000/api/v1/diaries/1/compression'
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
25 passed
```

## Historical Gaps At Stage 8

- Image upload and `diary_media` persistence are not implemented yet.
- AIGC diary draft/storyboard endpoints remain in a later fifth-phase slice.
- Full-text search currently uses deterministic title/body contains matching after decompression; a true inverted index can be added in the AIGC/admin slice.
- Rating accepts repeated ratings from the same user; this is acceptable for demo scoring but should be constrained in production.

Stage 22 later added media metadata, exact title index, inverted index search, and AIGC media input. Remaining limits are tracked in `docs/stage_30_diary_requirement_alignment.md`.

## Next Stage

Continue the project plan's fifth phase:

- food restaurant/item APIs
- food search and recommendation
- nearby food route integration
- AIGC placeholder endpoints
- admin dashboard frontend
