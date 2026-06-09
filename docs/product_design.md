# Product Design

## Positioning

Smart Tour Guide is an attraction/school recommendation system plus a campus-internal navigation demo for 北京邮电大学沙河校区. It emphasizes destination recommendation explainability, real campus map data, graph routing, diary/community interaction, food discovery, and admin visibility.

## Target Users

- Visitor: searches attractions/schools, selects a destination, finds diaries and food information.
- Student/staff: uses campus-internal map, food recommendation, and route planning repeatedly.
- Admin/demo operator: logs in with `role=admin`, checks data scale, imports map data, edits content, and moderates diaries.

## Core User Flows

1. Log in or register through the application-level account gate.
2. Open the overview page and choose a service module.
3. Search attractions/schools by name, category, or keyword.
4. Edit personal interests and inspect recommended attractions/schools in the personal center.
5. Open map guide to browse nationwide attraction/school POIs or switch to internal roads, buildings, and facilities.
6. Plan an internal campus route and inspect distance/time/steps.
7. Plan an indoor route across entrance, elevator/stairs, floors, and rooms/exhibition halls.
8. Query nearby facilities by category and graph distance.
9. Browse all-user diaries, open details to increase heat, rate/comment after reading, and search by destination/title/body.
10. Recommend foods by cuisine, rating, heat, and distance.
11. Generate Agent-style AIGC diary/storyboard output from text and scenic/school media URLs, including a visible tool execution trace.
12. Log in as admin to access management tools; normal users should not see or call admin features.

## Demo Boundary

The system is optimized for course demonstration. Real external AIGC calls remain future work; current AIGC should be presented as deterministic local Agent simulation with a mock video artifact.
