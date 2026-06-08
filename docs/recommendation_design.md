# Recommendation Design

## Scope Clarification

The course requirement separates two scopes:

- Destination recommendation is city/regional level: recommend tourist attractions and schools.
- Campus navigation is internal level: after a school/campus is selected, routing, facilities, buildings, and indoor navigation operate inside that campus map.

Do not treat campus buildings or facilities as tourism recommendation candidates unless they are explicitly modeled as destination records.

## Destination Recommendation

API: `GET /api/v1/recommendations`.

Score factors:

- rating
- popularity
- user interest tags
- distance to current point
- freshness seed factor

Candidate data:

- `destinations` contains 207 curated real China scenic attractions and schools/campuses.
- destination tags describe tourism interest, school type, scenery, culture, transport convenience, and visit style.
- user interests select preferred attraction/school categories before recommendation.

The service ranks candidates with a Top-K heap helper and returns `score` plus `reason`. This matches the requirement that users usually inspect only the Top 10 results and the system should avoid full sorting when possible. Names, categories, provinces, cities, and coordinates are real-world seed data; rating/popularity are deterministic demo signals for repeatable sorting.

## Destination Search

Search targets:

- attraction/school name
- destination category
- interest tags and keywords

Search results can be sorted by popularity or rating. Place search may still include buildings/facilities/named topology nodes for map and route input, but that is a separate campus navigation workflow, not the tourism recommendation candidate pool.

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
