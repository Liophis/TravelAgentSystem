# Database Design

## Core Tables

| Table | Purpose |
| --- | --- |
| `users` | demo accounts |
| `user_profiles` | nickname/avatar |
| `user_interests` | recommendation interests |
| `destinations` | searchable/recommendable places |
| `destination_tags` | destination interest tags |
| `map_nodes` | route graph nodes |
| `map_edges` | route graph edges and geometry |
| `buildings` | map polygon overlays |
| `facility_categories` | facility category dictionary |
| `facilities` | service POIs |
| `diaries` | compressed diary records |
| `diary_comments` | comments |
| `diary_ratings` | ratings |
| `restaurants` | food locations |
| `foods` | food items |

## Demo Seed Counts

```text
users: 10
destinations: 200
map_nodes: 80
map_edges: 220
buildings: 20
facility_categories: 10
facilities: 50
restaurants: 5
foods: 30
diaries: 20
```

## Migration Strategy

Current demo uses SQLAlchemy `create_all` and deterministic reset scripts. The model layer is kept portable for PostgreSQL/PostGIS migration, but no Alembic migration chain is required for the course demo yet.
