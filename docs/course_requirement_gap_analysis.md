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
| P2 | Real map data repeatability | Local dev DB now has OSM graph/buildings plus AMap/OSM POIs; seed layers are hidden by default | Re-running live imports still depends on network availability and external map service quotas | Use documented import scripts and keep fallback seed for tests |

## Requirement Coverage By Module

| Requirement Module | Coverage | Notes |
| --- | --- | --- |
| 旅游推荐 | Mostly covered | Recommendation candidates are 207 real China attraction/university destination records. Top-K heap, hot/rating/interest/behavior strategies, editable interests, favorites, ratings, browse logs, and recommendation refresh exist. |
| 景点/学校查询 | Mostly covered | Destination list supports attraction/school keyword/category and hot/rating sort. Cross-source place search also returns campus buildings/facilities for route input, but these are not tourism recommendation candidates. |
| 单点路线规划 | Mostly covered | Navigation is campus-internal after selecting a school/campus map. Place-name start/end selection works. Walking routes can use AMap real route geometry; local Dijkstra remains available for algorithm demo. |
| 多点路线规划 | Partial | Greedy multi-point route exists for campus-internal route planning and supports return-to-start, place IDs, and per-leg route source selection. Candidate ordering is still greedy approximation. |
| 最短时间/拥挤度 | Covered for demo | `shortest_time` uses duration computed from per-edge congestion and ideal speed. |
| 交通工具策略 | Covered for demo | Route planning filters walking, bicycle, electric-cart, and mixed-mode edges. |
| 室内导航 | Covered for demo | Indoor nodes/edges, cross-floor Dijkstra, elevator/stair steps, and frontend page are implemented. |
| 场所查询 | Covered for demo | Category-name lookup, category filtering, graph distance, and Top-K heap are implemented. |
| 旅游日记管理/交流 | Mostly covered | Publish/list/detail/view/rating/comment/delete and media metadata work. Admin moderation remains. |
| 日记推荐 | Covered for demo | Views + rating + personal interest Top-K exists. |
| 日记精确查询/全文检索 | Covered for demo | Exact title index and lightweight inverted index full-text search are implemented. |
| 日记压缩 | Covered for demo | Uses zlib+base64 lossless compression on publish and decompression on read. If hand-written compression is required, this needs a Huffman replacement. |
| AIGC 动画 | Covered for demo | Deterministic mock draft/storyboard accepts media URLs and returns a simulated video link. |
| 美食推荐 | Mostly covered | Cuisine filter, destination scope, hot/rating/distance scoring, Top-K heap, route preview, fuzzy query, and explicit search sort controls exist. |

## Recommended Next Stages

1. Stage 23: user auth and behavior feedback.
   Implemented registration/login/token auth, favorites, ratings, behavior logs, and behavior-aware destination recommendation.

2. Stage 24: destination-scoped food.
   Implemented restaurant destination linkage and destination-aware food list/search/recommend/nearby endpoints.

3. Stage 25: admin moderation and editing.
   Implemented destination/facility/food edit endpoints and diary moderation delete flow.

4. Stage 27: real map layer cleanup and OSM+POI merge.
   Implemented real-priority map APIs, seed-layer cleanup, OSM road graph import, OSM building/amenity import, AMap POI preservation, and facility rebind.

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
