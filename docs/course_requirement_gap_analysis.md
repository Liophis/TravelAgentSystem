# Course Requirement Gap Analysis

Source: `要求.md`. The current source file contains a complete functional-requirements section and then starts an incomplete document-submission section, so this analysis only covers the functional requirements.

## Overall Judgment

The project has a runnable MVP for the main demo chain: destination recommendation, destination search, map display, single-route planning, multi-point route planning, nearby facilities, diary community, diary compression, food recommendation, AIGC placeholder, and admin stats.

The main weakness is not API absence; it is requirement depth. Several features are still simplified demos where the course requirement asks for richer algorithms or interaction:

- user auth, favorites, ratings, and behavior logs
- browser-level map verification

## Highest-Risk Gaps

| Priority | Area | Current State | Gap Against `要求.md` | Next Action |
| --- | --- | --- | --- | --- |
| P1 | User auth and behavior loop | Editable user interests now update recommendation output | Registration/login, favorites, destination ratings, and browsing behavior logs are still missing | Add minimal auth plus favorite/rating/behavior APIs |
| P1 | Food destination scope | Cuisine filter, fuzzy search, heat/rating/distance sort, and Top-K scoring work | Food is not explicitly scoped to selected destination/school | Add destination/current-place context and destination linkage |
| P1 | Map demo verification | AMap component exists and converts WGS84 to GCJ-02 | No browser/e2e screenshot proof because AMap key is environment-dependent | Add optional Playwright smoke guarded by `VITE_AMAP_KEY` |
| P2 | Real map data richness | Dense deterministic BUPT seed is documented as offline fallback; OSM import path exists; AMap POI importer exists; clean live AMap import replaced facility seed with 516 real facility rows locally | Building polygons and walkable campus topology may still be sparse if OSM data is incomplete | Keep OSM/manual graph data for routes and use AMap import for POI density |

## Requirement Coverage By Module

| Requirement Module | Coverage | Notes |
| --- | --- | --- |
| 旅游推荐 | Partial | Top-K heap, hot/rating/interest strategies, editable interests, and recommendation refresh exist. Missing favorites/ratings/behavior feedback. |
| 景点/学校查询 | Mostly covered | Destination list supports keyword/category and hot/rating sort. Cross-source search does not yet sort all result types by heat/rating. |
| 单点路线规划 | Mostly covered | Place-name start/end selection works. Walking routes can use AMap real route geometry; local Dijkstra remains available for algorithm demo. |
| 多点路线规划 | Partial | Greedy multi-point route exists and supports return-to-start, place IDs, and per-leg route source selection. Candidate ordering is still greedy approximation. |
| 最短时间/拥挤度 | Covered for demo | `shortest_time` uses duration computed from per-edge congestion and ideal speed. |
| 交通工具策略 | Covered for demo | Route planning filters walking, bicycle, electric-cart, and mixed-mode edges. |
| 室内导航 | Covered for demo | Indoor nodes/edges, cross-floor Dijkstra, elevator/stair steps, and frontend page are implemented. |
| 场所查询 | Covered for demo | Category-name lookup, category filtering, graph distance, and Top-K heap are implemented. |
| 旅游日记管理/交流 | Mostly covered | Publish/list/detail/view/rating/comment/delete and media metadata work. Admin moderation remains. |
| 日记推荐 | Covered for demo | Views + rating + personal interest Top-K exists. |
| 日记精确查询/全文检索 | Covered for demo | Exact title index and lightweight inverted index full-text search are implemented. |
| 日记压缩 | Covered for demo | Uses zlib+base64 lossless compression on publish and decompression on read. If hand-written compression is required, this needs a Huffman replacement. |
| AIGC 动画 | Covered for demo | Deterministic mock draft/storyboard accepts media URLs and returns a simulated video link. |
| 美食推荐 | Partial | Cuisine filter, hot/rating/distance scoring, Top-K heap, route preview, fuzzy query, and explicit search sort controls exist. Destination-scoped filtering remains. |

## Recommended Next Stages

1. Stage 17: diary search and media.
   Add media upload, exact title lookup, inverted/full-text search, and interest-aware diary recommendations.

2. Stage 20: auth and behavior feedback.
   Add registration/login, favorites, destination ratings, and browsing behavior logs.

3. Stage 21: destination-scoped food.
   Link restaurants/foods to destinations or map regions and filter food recommendations by selected destination/school.

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
