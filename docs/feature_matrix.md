# Feature Matrix

Status values: `planned`, `scaffolded`, `implemented`, `tested`.

| Module | Core Feature | API | Frontend Page | Main Tables | Test Status |
| --- | --- | --- | --- | --- | --- |
| Users | Register, login, profile, interests | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/users/me` | Login, Profile | `users`, `user_profiles`, `user_interests` | scaffolded: models + seed |
| Users | Favorites, behavior logs, ratings | `POST /api/favorites`, `POST /api/behavior`, `POST /api/ratings` | Profile | `user_favorites`, `user_behavior_logs`, `user_ratings` | planned |
| Destinations | List, detail, category filter | `GET /api/destinations`, `GET /api/destinations/{id}` | Destinations | `destinations`, `destination_tags`, `destination_statistics` | scaffolded: models + 200 seed rows |
| Destinations | Search by name/category/keyword | `GET /api/search/places` | Map/Search | `destinations`, `buildings`, `facilities` | planned |
| Recommendation | Hot/high-rating/interest/composite | `GET /api/recommendations` | Home | `destinations`, `user_interests`, `user_behavior_logs` | planned |
| Map Data | Seeded map data stats and layer API | `GET /api/v1/map/stats`, `GET /api/v1/map/nodes`, `GET /api/v1/map/edges`, `GET /api/v1/map/buildings`, `GET /api/v1/map/facilities` | MapGuidePage, Admin Dashboard | `map_nodes`, `map_edges`, `buildings`, `facilities`, `facility_categories` | tested: DB-backed seed API |
| Map Data | OSM import and admin import status | `POST /api/admin/map/import`, `GET /api/admin/stats` | Admin Dashboard | `map_nodes`, `map_edges`, `buildings`, `facilities` | planned: real OSMnx import |
| Map UI | AMap display for roads/buildings/facilities | `GET /api/v1/map/geojson` | MapGuidePage | `map_nodes`, `map_edges`, `buildings`, `facilities` | scaffolded: page + AMapView, API is DB-backed seed |
| Routing | Single-route distance/time/modes on OSM graph | `POST /api/v1/routes/plan` | RoutePlannerPage | `map_nodes`, `map_edges` | scaffolded: mock API + page |
| Routing | Multi-point optimized route on OSM graph | `POST /api/v1/routes/multi-point` | RoutePlannerPage | `map_nodes`, `map_edges` | planned |
| Facilities | Nearby by category and road distance | `GET /api/v1/facilities/nearby` | NearbyFacilitiesPage | `facilities`, `facility_categories`, `map_edges` | scaffolded: mock API + page |
| Indoor | Building, floor, cross-floor route | `POST /api/indoor/routes` | Indoor Navigation | `indoor_nodes`, `indoor_edges` | planned |
| Diaries | Publish, browse, rating, comments | `POST /api/diaries`, `GET /api/diaries` | Diary Community | `diaries`, `diary_media`, `diary_comments`, `diary_ratings` | scaffolded: model + seed |
| Diaries | Title search, full-text search | `GET /api/diaries/search` | Diary Search | `diaries`, search index | planned |
| Diaries | Compression stats | `GET /api/diaries/{id}/compression` | Diary Detail | `diaries` | planned |
| Food | Search, cuisine filter, fuzzy search | `GET /api/foods` | Food | `foods`, `restaurants` | scaffolded: models + seed |
| Food | Hot/rating/distance recommendation | `GET /api/foods/recommendations` | Food | `foods`, `user_interests`, `map_edges` | planned |
| AIGC | Diary draft and storyboard prompt | `POST /api/aigc/diary-draft`, `POST /api/aigc/storyboard` | Diary Editor | `diaries`, `diary_media` | planned |
| Admin | Users, destinations, map stats, moderation | `/api/admin/*` | Admin | all core tables | planned |
