# Course Requirement Gap Analysis

Source: `要求.md`. The current source file contains a complete functional-requirements section and then starts an incomplete document-submission section, so this analysis only covers the functional requirements.

## Overall Judgment

The project has a runnable MVP for the main demo chain: destination recommendation, destination search, map display, single-route planning, multi-point route planning, nearby facilities, diary community, diary compression, food recommendation, AIGC placeholder, and admin stats.

The main weakness is not API absence; it is requirement depth. Several features are still simplified demos where the course requirement asks for richer algorithms or interaction:

- dynamic user interests and behavior
- diary media and photo-driven AIGC
- exact/full-text/fuzzy search algorithm evidence
- browser-level map verification

## Highest-Risk Gaps

| Priority | Area | Current State | Gap Against `要求.md` | Next Action |
| --- | --- | --- | --- | --- |
| P1 | Route target selection | Route strategy depth is covered for demo: distance/time, congestion, walk/bike/electric-cart/mixed modes | Route planner still expects coordinates instead of selecting destination/facility names | Add target search/select controls connected to destination/facility APIs |
| P1 | User preference dynamics | Seeded users/interests exist; frontend hard-codes `user_id=1` | Users cannot edit interests, favorite/rate destinations, or change recommendation state through UI | Add minimal auth/profile/interest editor and behavior/rating events |
| P1 | Diary media | Text diary works; compression works | No image/video upload, no media preview, AIGC does not accept photos | Add media table/local upload and pass uploaded media metadata to mock AIGC |
| P1 | Diary search | Title/body contains search works | No exact-title index/hash/trie; full-text is not an inverted index or DB full-text search | Add exact title lookup and lightweight inverted index or SQLite/Postgres FTS path |
| P1 | Diary recommendation | Uses views + rating Top-K | Does not use personal interest | Add user-interest overlap to diary score and expose reason |
| P1 | Facility query | Category code filter and graph-distance Top-K work | No category-name text lookup/fuzzy input flow | Add category-name search and UI text input |
| P1 | Food search/recommend | Cuisine filter, fuzzy search, Top-K scoring work | Food is not explicitly scoped to selected destination; fuzzy search does not expose sorting by distance | Add destination/current-place context and sort controls |
| P1 | Map demo verification | AMap component exists and converts WGS84 to GCJ-02 | No browser/e2e screenshot proof because AMap key is environment-dependent | Add optional Playwright smoke guarded by `VITE_AMAP_KEY` |
| P2 | Real map data richness | Dense deterministic BUPT seed; OSM import path exists | OSM POI/building data may still be sparse for campus | Optional AMap POI enrichment import into local DB |

## Requirement Coverage By Module

| Requirement Module | Coverage | Notes |
| --- | --- | --- |
| 旅游推荐 | Partial | Top-K heap and hot/rating/interest strategies exist. Missing editable user preference and dynamic behavior feedback. |
| 景点/学校查询 | Mostly covered | Destination list supports keyword/category and hot/rating sort. Cross-source search does not yet sort all result types by heat/rating. |
| 单点路线规划 | Partial | Dijkstra route and map polyline exist. Distance/time/mode strategies work. Target input is still coordinate-oriented. |
| 多点路线规划 | Partial | Greedy multi-point route exists and supports return-to-start. Candidate legs use the selected distance/time strategy, but it is still an approximation. |
| 最短时间/拥挤度 | Covered for demo | `shortest_time` uses duration computed from per-edge congestion and ideal speed. |
| 交通工具策略 | Covered for demo | Route planning filters walking, bicycle, electric-cart, and mixed-mode edges. |
| 室内导航 | Covered for demo | Indoor nodes/edges, cross-floor Dijkstra, elevator/stair steps, and frontend page are implemented. |
| 场所查询 | Mostly covered | Category filtering, graph distance, and Top-K heap are implemented. Category-name text lookup remains. |
| 旅游日记管理/交流 | Partial | Publish/list/detail/view/rating/comment/delete work. Media upload and admin moderation are missing. |
| 日记推荐 | Partial | Views + rating Top-K exists. Personal interest is not included. |
| 日记精确查询/全文检索 | Partial | Contains search works, but exact-title index and inverted/full-text search are not yet implemented. |
| 日记压缩 | Covered for demo | Uses zlib+base64 lossless compression on publish and decompression on read. If hand-written compression is required, this needs a Huffman replacement. |
| AIGC 动画 | Partial | Deterministic mock draft/storyboard exists. Photo upload and photo-to-animation input flow are missing. |
| 美食推荐 | Partial | Cuisine filter, hot/rating/distance scoring, Top-K heap, route preview, and fuzzy query exist. Destination-scoped filtering and explicit sort controls remain. |

## Recommended Next Stages

1. Stage 16: user preference loop.
   Add minimal profile interest editing, destination rating/favorite/behavior logging, and recommendation refresh.

2. Stage 17: diary search and media.
   Add media upload, exact title lookup, inverted/full-text search, and interest-aware diary recommendations.

3. Stage 18: query polish for facilities and food.
   Add category-name lookup, destination-scoped food filtering, and visible sort controls for heat/rating/distance.

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
