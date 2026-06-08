# Course Requirement Gap Analysis

Source: `要求.md`. The current source file contains a complete functional-requirements section and then starts an incomplete document-submission section, so this analysis only covers the functional requirements.

## Overall Judgment

The project has a runnable MVP for the main demo chain: attraction/school destination recommendation, destination search, campus map display, campus-internal single-route planning, multi-point route planning, nearby facilities, diary community, diary compression, food recommendation, AIGC placeholder, and admin stats.

The main weakness is no longer API absence; it is browser-level verification depth. Several features are still simplified demos where the course requirement asks for verified real map interaction:

- browser-level map verification requires optional AMap key and Playwright environment

## Highest-Risk Gaps

| Priority | Area | Current State | Gap Against `要求.md` | Next Action |
| --- | --- | --- | --- | --- |
| P1 | Map demo verification | AMap component exists, converts WGS84 to GCJ-02, and optional Playwright harness exists | Screenshot proof still depends on a valid `VITE_AMAP_KEY`, backend server, and local Playwright install | Run `bash scripts/check_map_frontend_optional.sh` in a prepared demo environment |
| P2 | Real map data repeatability | Local dev DB now can use offline BUPT reference topology plus AMap/OSM POIs; seed layers are hidden by default | OSM/AMap live imports still depend on network/quota, but reference campus import is offline | Use `backend/scripts/import_reference_campus.py --replace-campus-layers` for repeatable campus routing |
| P2 | Admin/user auth boundary | User login token exists and admin APIs exist | Admin APIs are not yet role-protected, so normal users and admins do not have separate login states | Implement Stage 31 role-aware auth with `role=user|admin` and `require_admin` |

## Requirement Coverage By Module

| Requirement Module | Coverage | Notes |
| --- | --- | --- |
| 旅游推荐 | Mostly covered | Recommendation candidates are 207 real China attraction/university destination records. Top-K heap, hot/rating/interest/behavior strategies, editable interests, favorites, ratings, browse logs, and recommendation refresh exist. |
| 景点/学校查询 | Mostly covered | Destination list supports attraction/school keyword/category and hot/rating sort. `scope=destinations` keeps tourism search separate from campus route endpoints. |
| 单点路线规划 | Mostly covered | RoutePlannerPage is scoped to BUPT Shahe campus-internal buildings/facilities/semantic named topology nodes via `scope=campus`, while generic road/intersection nodes are filtered out; it defaults to local Dijkstra over the imported campus topology. AMap walking remains API-level optional behavior. |
| 多点路线规划 | Partial | Greedy multi-point route exists for BUPT Shahe campus-internal route planning and supports return-to-start, campus place IDs, and local-graph legs. Candidate ordering is still greedy approximation. |
| 最短时间/拥挤度 | Covered for demo | `shortest_time` uses duration computed from per-edge congestion and ideal speed. |
| 交通工具策略 | Covered for demo | Route planning filters walking, bicycle, electric-cart, and mixed-mode edges. |
| 室内导航 | Covered for demo | Indoor nodes/edges, cross-floor Dijkstra, elevator/stair steps, and frontend page are implemented. |
| 场所查询 | Covered for demo | Category-name lookup, category filtering, graph distance, and Top-K heap are implemented. |
| 旅游日记管理/交流 | Mostly covered | Text diary publish/list/detail/view/rating/comment/delete work, all-user list exists, admin delete exists, and image/video media URL metadata is supported. Browser multipart upload and richer moderation statuses remain optional enhancements. |
| 日记热度/评分/兴趣推荐 | Covered for demo | Views are heat; list sort supports hot/rating; `GET /api/v1/diaries/recommend` uses views + rating + personal interest with Top-K heap. |
| 目的地相关日记查询排序 | Covered for demo | `GET /api/v1/diaries?destination_id=...&sort=hot|rating` filters destination-related diaries and sorts by heat/rating. Frontend destination selector can be made more explicit in a polish stage. |
| 日记精确查询/全文检索 | Covered for demo | Exact title uses `diary_title_indexes`; full-text uses lightweight `diary_search_tokens` inverted index. Chinese segmentation quality can be improved later. |
| 日记压缩 | Covered for demo | Uses zlib+base64 lossless compression on publish and decompression on read, with compression ratio and `decompress_ok`. If hand-written compression is required, add a Huffman implementation. |
| AIGC 动画 | Covered for demo | Deterministic mock draft/storyboard accepts scenic/school media URLs and returns storyboard scenes plus a simulated video link. Real external AIGC generation remains future work. |
| 美食推荐 | Mostly covered | Cuisine filter, destination scope, hot/rating/distance scoring, Top-K heap, route preview, fuzzy query, and explicit search sort controls exist. |
| 管理员/普通用户登录状态 | Planned | One login endpoint should return `role=user|admin`; admin APIs should require admin token. This is not a core algorithm requirement but improves demo completeness and data-management credibility. |

## Recommended Next Stages

1. Stage 23: user auth and behavior feedback.
   Implemented registration/login/token auth, favorites, ratings, behavior logs, and behavior-aware destination recommendation.

2. Stage 24: destination-scoped food.
   Implemented restaurant destination linkage and destination-aware food list/search/recommend/nearby endpoints.

3. Stage 25: admin moderation and editing.
   Implemented destination/facility/food edit endpoints and diary moderation delete flow.

4. Stage 28: reference campus navigation.
   Implemented BUPT Shahe WGS84 reference topology import, campus-scoped endpoint search, and RoutePlannerPage defaulting to the imported campus graph.

5. Optional browser map smoke.
   `bash scripts/check_map_frontend_optional.sh` skips cleanly without key/browser and runs screenshot verification when the environment is prepared.

## Harness Commands

Run after every stage:

```bash
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

For map visual checks, add a guarded browser smoke once a valid AMap key is available:

```bash
VITE_AMAP_KEY=... npm run test:e2e
```
