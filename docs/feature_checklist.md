# Feature Checklist

Run this after `bash scripts/reset_dev_db.sh`.

## Backend

- [x] `GET /api/v1/health`
- [x] `GET /api/v1/map/stats`
- [x] `GET /api/v1/map/geojson`
- [x] `POST /api/v1/routes/plan`
- [x] `GET /api/v1/facilities/nearby`
- [x] `GET /api/v1/destinations`
- [x] `GET /api/v1/search/places`
- [x] `GET /api/v1/recommendations`
- [x] `POST /api/v1/admin/map/import`
- [x] `GET /api/v1/diaries`
- [x] `POST /api/v1/diaries`
- [x] `GET /api/v1/foods/recommend`
- [x] `GET /api/v1/foods/nearby`
- [x] `POST /api/v1/aigc/diary-draft`
- [x] `POST /api/v1/aigc/storyboard`
- [x] `GET /api/v1/admin/stats`

## Frontend Pages

- [x] Home
- [x] Destinations
- [x] Map Guide
- [x] Route Planner
- [x] Nearby Facilities
- [x] Diary Community
- [x] Food Recommendation
- [x] AIGC Assistant
- [x] Admin Dashboard

## Required Checks

- [ ] `bash scripts/smoke_features.sh`
- [ ] `bash scripts/check_backend.sh`
- [ ] `bash scripts/check_frontend.sh`
- [ ] `bash scripts/check_all.sh`
