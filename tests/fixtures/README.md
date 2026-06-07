# Test Fixtures

This directory stores small deterministic fixtures used by backend and frontend tests.

## `mini_map.json`

Tiny road graph for route/facility tests:

- 5 road nodes
- 6 directed edges
- 2 buildings
- 3 facilities

Rules:

- Keep fixture data small and deterministic.
- Do not put production OSM exports here.
- Use this fixture for unit tests that must not depend on network, OSMnx, PostgreSQL, or Redis.

