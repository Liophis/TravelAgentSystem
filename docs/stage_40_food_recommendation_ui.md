# Stage 40 Food Recommendation UI

## Goal

Make the food recommendation page easier to demo and closer to a real discovery page:

- keep algorithm controls visible;
- show restaurants with their specialty cuisines;
- show recommended dishes as visual cards instead of a dense table;
- keep route drawing and algorithm trace available.

## Completed

- Replaced the result table in `FoodRecommendPage` with food recommendation cards.
- Each food card shows:
  - cuisine cover image cropped from a project-local food collage asset;
  - restaurant name;
  - recommended food item;
  - cuisine tag;
  - price, rating, heat, score, and distance;
  - source tag for AMap real POI vs seed fallback;
  - route drawing button when route geometry is available.
- Added a `特色店铺` section:
  - restaurant name;
  - address/category;
  - top specialty cuisine tags from `RestaurantItem.cuisines`;
  - source tag for AMap rows.
- Kept filters, destination scope, cuisine filtering, fuzzy search, nearby Top-10, map markers, and algorithm trace.

## Asset Note

The current API does not expose restaurant or food `image_url`. Stage 40 therefore uses a project-local generated food collage:

```text
frontend/public/images/food-cuisine-collage.png
```

Cards crop this image by cuisine/category. Do not treat these as real restaurant photos. When backend data includes verified `image_url`, the card cover area should render the real image first and fall back to the cuisine collage.

## Verification

```bash
cd frontend
npm run typecheck
npm run build
```

## Acceptance

- [x] Food recommendations are readable as cards, not only a table.
- [x] Restaurant specialty cuisines are visible.
- [x] Food cards provide project-local cuisine cover images.
- [x] Route drawing and map markers remain available.
- [x] Algorithm trace remains available.
