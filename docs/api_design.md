# API Design

Base path: `/api/v1`.

## Map And Routing

- `GET /map/stats`
- `GET /map/geojson`
- `POST /routes/plan`
- `GET /facilities/nearby`

## Search And Recommendation

- `GET /destinations`
- `GET /destinations/{id}`
- `GET /search/places`
- `GET /recommendations`

## Diaries

- `POST /diaries`
- `GET /diaries`
- `GET /diaries/{id}`
- `PUT /diaries/{id}`
- `DELETE /diaries/{id}`
- `POST /diaries/{id}/view`
- `POST /diaries/{id}/rating`
- `POST /diaries/{id}/comments`
- `GET /diaries/search`
- `GET /diaries/recommend`
- `GET /diaries/{id}/compression`

## Food

- `GET /foods/restaurants`
- `GET /foods/items`
- `GET /foods/search`
- `GET /foods/recommend`
- `GET /foods/nearby`

## AIGC

- `POST /aigc/diary-draft`
- `POST /aigc/storyboard`

## Admin

- `GET /admin/stats`
- `GET /admin/map/import/status`
- `POST /admin/map/import`

## Response Rule

Feature APIs should include `algorithm_trace` when they demonstrate an algorithm or data-processing strategy.
