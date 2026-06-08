# Stage 22 Diary Media And Search

## Scope

This stage closes the diary requirement gaps:

- media metadata for diary image/video references
- exact-title lookup with normalized title index
- lightweight inverted index for title/body full-text search
- interest-aware diary recommendation
- AIGC storyboard input with media URLs

## Delivered

- New tables:
  - `diary_media`
  - `diary_title_indexes`
  - `diary_search_tokens`
- `POST /api/v1/diaries/{id}/media`
- `GET /api/v1/diaries/{id}/media`
- `GET /api/v1/diaries/search?mode=exact_title|fulltext|contains`
- `GET /api/v1/diaries/recommend?user_id=1`
- `POST /api/v1/aigc/storyboard` accepts `media_urls`.
- Diary community page can search by mode and attach a media URL.
- AIGC page can pass media URLs into storyboard generation.

## Validation

```bash
PYTHONPATH=backend pytest backend/tests/test_stage8_diaries.py backend/tests/test_stage9_food_aigc_admin.py
npm run typecheck
```

Expected:

- exact title search returns indexed diary
- full-text search uses inverted tokens
- diary detail includes media
- recommendation trace includes user interests
- AIGC storyboard trace includes media input count

## Remaining Limits

- Media is stored as metadata URL/path, not binary multipart upload.
- Compression still uses zlib+base64; replacing it with hand-written Huffman remains optional unless strictly required.
