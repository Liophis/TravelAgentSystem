# Acceptance Demo Script

Target length: 15 minutes.

## 1. System Positioning

Show home page and describe the system as a campus/scenic-area smart guide.

## 2. Environment And Data

Run or show:

```bash
bash scripts/smoke_features.sh
```

Mention deterministic fallback seed scale, then explain the real-data import path:

```bash
PYTHONPATH=backend python backend/scripts/import_amap_pois.py --radius 1800 --max-pages 3 --request-interval 0.5
```

Only run the import live when `AMAP_WEB_API_KEY` and network access are available.

## 3. Home Recommendation

Open home page and switch recommendation strategy.

## 4. Destination Search

Open destination page, search a keyword, filter category, and select one row.

## 5. Real Map Display

Open map guide, show roads, buildings, facilities, and category filter.

## 6. Route Planning

Open route planner, choose start/end by place search, show distance/time/steps and map polyline. Open advanced coordinates only if explaining graph-node snapping.

## 7. Nearby Facilities

Open nearby facilities, choose a category, show graph-distance ranking and route preview.

## 8. Diary Community

Publish a diary, open detail, increment view, rate, comment, and show compression stats.

## 9. Food Recommendation

Open food page, filter cuisine, search food, show nearby route preview.

## 10. AIGC Assistant

Generate diary draft and storyboard prompt.

## 11. Admin Dashboard

Open admin dashboard and show map/table counts.

## 12. Architecture And Future

Show architecture, algorithm traces, OSM/AMap boundary, and future improvements.
