# Recommendation Design

## Destination Recommendation

API: `GET /api/v1/recommendations`.

Score factors:

- rating
- popularity
- user interest tags
- distance to current point
- freshness seed factor

The service ranks candidates with a Top-K heap helper and returns `score` plus `reason`.

## Food Recommendation

API: `GET /api/v1/foods/recommend`.

Score factors:

- food rating
- food heat
- restaurant heat
- cuisine/user interest match
- distance
- price

Nearby food uses route preview where possible and Top-K ranking by distance.

## Explainability

Recommendation APIs return `algorithm_trace` and item-level reasons for defense/demo discussion.
