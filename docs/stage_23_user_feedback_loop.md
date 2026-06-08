# Stage 23 User Feedback Loop

## Scope

This stage closes the user-account and recommendation-feedback gaps:

- registration, login, and token verification
- normal user login state for recommendation and feedback flows
- profile activity summary
- destination/food favorites
- destination/food ratings
- browse behavior logs
- behavior-aware destination recommendation

## Delivered

- New tables:
  - `user_favorites`
  - `user_ratings`
  - `user_behavior_logs`
- `POST /api/v1/users/register`
- `POST /api/v1/users/login`
- `GET /api/v1/users/me`
- `POST /api/v1/users/{id}/favorites`
- `GET /api/v1/users/{id}/favorites`
- `POST /api/v1/users/{id}/ratings`
- `POST /api/v1/users/{id}/behavior`
- `GET /api/v1/users/{id}/behavior`
- `GET /api/v1/recommendations?strategy=behavior`
- UserPreferencePage can register, log in, verify token, edit interests, favorite, rate, and record views.
- DestinationListPage can record view events, favorite destinations, and submit ratings.

## Validation

```bash
PYTHONPATH=backend pytest backend/tests/test_stage16_user_preferences.py
npm run typecheck
```

Expected:

- login returns a bearer token
- `/users/me` accepts the bearer token
- favorite/rating/view writes user feedback rows
- destination rating and popularity update after feedback
- behavior recommendations include the target destination in Top-K

## Remaining Limits

- Token auth is a deterministic course-demo HMAC token, not a full production OAuth/JWT stack.
- Frontend uses demo user `user01` by default so the system remains easy to demonstrate offline.
- Admin/user role separation is planned in `docs/stage_31_admin_user_auth_plan.md`.
