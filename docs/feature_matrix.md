# Feature Matrix

Status values: `planned`, `scaffolded`, `implemented`, `tested`.

| Module | Core Feature | API | Frontend Page | Main Tables | Test Status |
| --- | --- | --- | --- | --- | --- |
| Users | Register, login, profile, interests | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/users/me` | Login, Profile | `users`, `user_profiles`, `user_interests` | planned |
| Users | Favorites, behavior logs, ratings | `POST /api/favorites`, `POST /api/behavior`, `POST /api/ratings` | Profile | `user_favorites`, `user_behavior_logs`, `user_ratings` | planned |
| Destinations | List, detail, category filter | `GET /api/destinations`, `GET /api/destinations/{id}` | Destinations | `destinations`, `destination_tags`, `destination_statistics` | planned |
| Destinations | Search by name/category/keyword | `GET /api/search/places` | Map/Search | `destinations`, `buildings`, `facilities` | planned |
| Recommendation | Hot/high-rating/interest/composite | `GET /api/recommendations` | Home | `destinations`, `user_interests`, `user_behavior_logs` | planned |
| Map Data | OSM import and data stats | `POST /api/admin/map/import`, `GET /api/admin/stats` | Admin Dashboard | `map_nodes`, `map_edges`, `buildings`, `facilities` | planned |
| Map UI | AMap display for roads/buildings/facilities | `GET /api/v1/map/geojson` | MapGuidePage | `map_nodes`, `map_edges`, `buildings`, `facilities` | scaffolded: mock API + page + AMapView |
| Routing | Single-route distance/time/modes on OSM graph | `POST /api/v1/routes/plan` | RoutePlannerPage | `map_nodes`, `map_edges` | scaffolded: mock API + page |
| Routing | Multi-point optimized route on OSM graph | `POST /api/v1/routes/multi-point` | RoutePlannerPage | `map_nodes`, `map_edges` | planned |
| Facilities | Nearby by category and road distance | `GET /api/v1/facilities/nearby` | NearbyFacilitiesPage | `facilities`, `facility_categories`, `map_edges` | scaffolded: mock API + page |
| Indoor | Building, floor, cross-floor route | `POST /api/indoor/routes` | Indoor Navigation | `indoor_nodes`, `indoor_edges` | planned |
| Diaries | Publish, browse, rating, comments | `POST /api/diaries`, `GET /api/diaries` | Diary Community | `diaries`, `diary_media`, `diary_comments`, `diary_ratings` | planned |
| Diaries | Title search, full-text search | `GET /api/diaries/search` | Diary Search | `diaries`, search index | planned |
| Diaries | Compression stats | `GET /api/diaries/{id}/compression` | Diary Detail | `diaries` | planned |
| Food | Search, cuisine filter, fuzzy search | `GET /api/foods` | Food | `foods`, `restaurants` | planned |
| Food | Hot/rating/distance recommendation | `GET /api/foods/recommendations` | Food | `foods`, `user_interests`, `map_edges` | planned |
| AIGC | Diary draft and storyboard prompt | `POST /api/aigc/diary-draft`, `POST /api/aigc/storyboard` | Diary Editor | `diaries`, `diary_media` | planned |
| Admin | Users, destinations, map stats, moderation | `/api/admin/*` | Admin | all core tables | planned |
