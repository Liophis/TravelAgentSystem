# Feature Matrix

Status values: `planned`, `scaffolded`, `implemented`, `tested`.

| Module | Core Feature | API | Frontend Page | Main Tables | Test Status |
| --- | --- | --- | --- | --- | --- |
| Users | Register, login, profile, interests | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/users/me` | Login, Profile | `users`, `user_profiles`, `user_interests` | scaffolded: models + seed |
| Users | Favorites, behavior logs, ratings | `POST /api/favorites`, `POST /api/behavior`, `POST /api/ratings` | Profile | `user_favorites`, `user_behavior_logs`, `user_ratings` | planned |
| Destinations | List, detail, category filter | `GET /api/v1/destinations`, `GET /api/v1/destinations/{id}` | Destinations | `destinations`, `destination_tags` | tested: DB-backed API + page |
| Destinations | Search by name/category/keyword | `GET /api/v1/search/places` | Destinations/Search | `destinations`, `buildings`, `facilities` | tested: contains search across places |
| Recommendation | Hot/high-rating/interest/composite | `GET /api/v1/recommendations` | Home | `destinations`, `user_interests` | tested: rule scoring + Top-K heap |
| Map Data | Seeded map data stats and layer API | `GET /api/v1/map/stats`, `GET /api/v1/map/nodes`, `GET /api/v1/map/edges`, `GET /api/v1/map/buildings`, `GET /api/v1/map/facilities` | MapGuidePage, Admin Dashboard | `map_nodes`, `map_edges`, `buildings`, `facilities`, `facility_categories` | tested: DB-backed seed API |
| Map Data | OSM import and admin import status | `POST /api/v1/admin/map/import`, `GET /api/v1/admin/map/import/status`, `GET /api/v1/admin/stats` | Admin Dashboard | `map_nodes`, `map_edges`, `buildings`, `facilities` | tested: fixture import + OSMnx source path |
| Map UI | AMap display for roads/buildings/facilities | `GET /api/v1/map/geojson` | MapGuidePage | `map_nodes`, `map_edges`, `buildings`, `facilities` | tested: DB-backed API + AMap overlay transform + typecheck/build |
| Routing | Single-route distance/time response on OSM-shaped graph | `POST /api/v1/routes/plan` | RoutePlannerPage | `map_nodes`, `map_edges` | tested: DB-backed Dijkstra API + page |
| Routing | Multi-point optimized route on OSM graph | `POST /api/v1/routes/multi-point` | RoutePlannerPage | `map_nodes`, `map_edges` | tested: greedy TSP approximation + Dijkstra leg costs |
| Routing | Congestion, transport modes, and mixed shortest-time strategy | `POST /api/v1/routes/plan` | RoutePlannerPage | `map_edges` congestion/mode/speed fields | tested: required by `要求.md` |
| Facilities | Nearby by category and graph distance | `GET /api/v1/facilities/nearby` | NearbyFacilitiesPage | `facilities`, `facility_categories`, `map_nodes`, `map_edges` | tested: DB-backed Dijkstra distance + Top-K heap |
| Facilities | Category-name text lookup and fuzzy category input | `GET /api/v1/facilities/nearby` or future search API | NearbyFacilitiesPage | `facility_categories`, `facilities` | planned: required by `要求.md` |
| Indoor | Building, floor, cross-floor route | `POST /api/indoor/routes` | Indoor Navigation | `indoor_nodes`, `indoor_edges` | planned |
| Diaries | Publish, browse, rating, comments | `POST /api/v1/diaries`, `GET /api/v1/diaries`, `POST /api/v1/diaries/{id}/rating`, `POST /api/v1/diaries/{id}/comments` | Diary Community | `diaries`, `diary_comments`, `diary_ratings` | tested: DB-backed API + page |
| Diaries | Title/body search and recommendation | `GET /api/v1/diaries/search`, `GET /api/v1/diaries/recommend` | Diary Community | `diaries` | tested: contains search + Top-K recommendation |
| Diaries | Compression stats | `GET /api/v1/diaries/{id}/compression` | Diary Community | `diaries` | tested: zlib compression/decompression |
| Diaries | Media upload, exact-title index, inverted/full-text search, interest-aware recommendation | future media/search APIs | Diary Community, AIGC Assistant | `diary_media`, search index | planned: required by `要求.md` |
| Food | Restaurant/item list, cuisine filter, fuzzy search | `GET /api/v1/foods/restaurants`, `GET /api/v1/foods/items`, `GET /api/v1/foods/search` | FoodRecommendPage | `foods`, `restaurants` | tested: DB-backed API + page |
| Food | Hot/rating/distance recommendation and nearby route preview | `GET /api/v1/foods/recommend`, `GET /api/v1/foods/nearby` | FoodRecommendPage | `foods`, `restaurants`, `user_interests`, `map_edges` | tested: scoring + Top-K + route path |
| Food | Destination-scoped filtering and explicit heat/rating/distance sort for fuzzy results | `GET /api/v1/foods/search`, `GET /api/v1/foods/recommend` | FoodRecommendPage | `foods`, `restaurants`, future destination linkage | planned: required by `要求.md` |
| AIGC | Diary draft and storyboard prompt | `POST /api/v1/aigc/diary-draft`, `POST /api/v1/aigc/storyboard` | AigcAssistantPage | mock service | tested: deterministic placeholder |
| AIGC | Photo-driven tourism animation generation | future media AIGC API | AigcAssistantPage | `diary_media` | planned: mock accepted, photo input missing |
| Admin | Data dashboard and OSM import status | `GET /api/v1/admin/stats`, `GET /api/v1/admin/map/import/status` | AdminDashboardPage | all core tables | tested: stats API + page |
