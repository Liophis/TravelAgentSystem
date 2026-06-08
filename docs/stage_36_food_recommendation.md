# Stage 36 Food Recommendation

## Scope

Strengthen the food recommendation module against the course requirements.

Required behavior:

- Select a destination/school scope before recommending foods.
- Filter by cuisine.
- Recommend Top-10 by selected hot/rating/distance/composite strategy without fully sorting all candidates.
- Fuzzy search by food name, cuisine, restaurant, or window name.
- Sort fuzzy search results by match, hot, rating, or distance.

## Implemented API

```text
GET /api/v1/foods/recommend?destination_id=1&cuisine=noodle&sort=hot&limit=10
GET /api/v1/foods/search?q=南区食堂&destination_id=1&sort=distance&limit=10
GET /api/v1/foods/nearby?destination_id=1&radius=1200&limit=10
```

Supported recommendation sorts:

```text
composite
hot
rating
distance
```

Supported search sorts:

```text
match
hot
rating
distance
composite
```

## Algorithm

- Candidate filtering: destination/school scope, cuisine, optional query.
- Fuzzy search: exact, prefix, contains, lightweight Levenshtein.
- Ranking: hand-written Top-K heap, no full candidate sort for Top-10.
- Distance: `sort=distance` enriches candidates with graph route distance before Top-K ranking; other recommendation modes attach route preview after Top-K and use current/destination distance in the composite score.
- Trace: API responses include `algorithm_trace.ranking`, `sort`, `candidate_count`, and `returned`.

## Data Boundary

- Stage 36 completed the algorithm and UI contract while still relying on deterministic BUPT Shahe seed food data.
- Stage 37 adds real AMap restaurant POIs around Summer Palace and keeps the same API contract.
- Destination scoping uses direct `restaurants.destination_id` plus a 1500m destination-nearby rule for fallback rows.

## Frontend

`FoodRecommendPage` now exposes:

- destination selector
- cuisine filter
- shared sort selector
- current-location longitude/latitude controls
- fuzzy search input for food/cuisine/restaurant/window
- Top-10 recommendation button
- nearby Top-10 button
- score, heat, rating, distance, route drawing, and algorithm trace display

## Acceptance

- [x] Cuisine filter works before ranking.
- [x] Recommendation supports hot/rating/distance/composite sorting.
- [x] Search supports food name, cuisine, restaurant/window fuzzy query.
- [x] Search supports match/hot/rating/distance sorting.
- [x] Recommendation and search use a hand-written Top-K heap instead of full candidate sorting.
- [x] Returned recommendation items include route preview when available.
- [x] Distance recommendation ranks by graph route distance when available.
- [x] Tests cover hot/rating/distance recommendation order and restaurant/window search.
- [x] Smoke script covers recommendation sort, restaurant/window search, and route preview.
