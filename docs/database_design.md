# Database Design

## Core Tables

| Table | Purpose |
| --- | --- |
| `users` | demo accounts; planned `role=user|admin` |
| `user_profiles` | nickname/avatar |
| `user_interests` | recommendation interests |
| `destinations` | searchable/recommendable real attractions and schools |
| `destination_tags` | destination interest tags |
| `map_nodes` | route graph nodes |
| `map_edges` | route graph edges and geometry |
| `buildings` | map polygon overlays |
| `facility_categories` | facility category dictionary |
| `facilities` | service POIs |
| `indoor_nodes` | indoor route graph nodes |
| `indoor_edges` | indoor route graph edges |
| `diaries` | compressed diary records |
| `diary_media` | image/video URL metadata for diary records |
| `diary_comments` | comments |
| `diary_ratings` | ratings |
| `diary_title_indexes` | normalized exact-title lookup |
| `diary_search_tokens` | lightweight inverted index tokens for title/body |
| `restaurants` | food locations |
| `foods` | food items |

## User Role Strategy

The target auth model keeps one account table and one login endpoint:

```text
users.role = user | admin
```

Normal users can browse, rate, favorite, publish diaries, and use recommendations. Admin users can also access `/api/v1/admin/*` for data dashboard, map import, content editing, and diary moderation.

The deterministic seed should include:

```text
user01: role=user
admin01: role=admin
```

## Map Edge Strategy Fields

`map_edges` stores the route topology plus strategy metadata:

```text
distance
walk_time
congestion
walk_speed
bike_speed
electric_cart_speed
allowed_modes
geometry
```

Route duration is computed as:

```text
duration = distance / (ideal_speed * congestion)
```

## Demo Seed Counts

```text
users: 10
destinations: 207 real attraction/university rows
map_nodes: 180
map_edges: 641
buildings: 60
facility_categories: 10
facilities: 120
indoor_nodes: 19
indoor_edges: 20
restaurants: 12
foods: 72
diaries: 20
```

## Migration Strategy

Current demo uses SQLAlchemy `create_all` and deterministic reset scripts. The model layer is kept portable for PostgreSQL/PostGIS migration, but no Alembic migration chain is required for the course demo yet.
