# Stage 16 User Preference Loop

## Scope

This stage implements the minimum user-preference loop required for demonstrable personalized recommendation:

- list demo users
- read user profile and interests
- edit user interest tags
- refresh interest-based recommendations after the update

It does not implement token authentication yet.

## Delivered

- Added user APIs:
  - `GET /api/v1/users`
  - `GET /api/v1/users/{user_id}`
  - `PUT /api/v1/users/{user_id}/interests`
- Added `UserPreferencePage`.
- Added a reusable frontend `apiPut` helper.
- Added smoke coverage for interest update followed by interest recommendation.
- Added backend tests for user profile APIs and recommendation trace changes.

## Acceptance

Run:

```bash
PYTHONPATH=backend pytest backend/tests/test_stage16_user_preferences.py
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

Expected:

- user list returns 10 seeded users
- profile returns available interest tags
- saving interests replaces the user's tags
- recommendation trace reflects the new interest tags

## Remaining Gaps

- Registration/login/token auth is still planned.
- Favorites, ratings, and behavior logs are still planned.
- Home page still defaults to `user_id=1`; the editable recommendation preview lives on `/profile`.
