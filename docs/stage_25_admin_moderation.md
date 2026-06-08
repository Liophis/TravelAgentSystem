# Stage 25 Admin Moderation

## Scope

This stage closes the admin management gap:

- edit destination metadata and tags
- edit facility metadata and category
- edit food metadata
- list and delete diaries for moderation

## Delivered

- `PATCH /api/v1/admin/destinations/{id}`
- `PATCH /api/v1/admin/facilities/{id}`
- `PATCH /api/v1/admin/foods/{id}`
- `GET /api/v1/admin/diaries`
- `DELETE /api/v1/admin/diaries/{id}`
- AdminDashboardPage now has edit panels and diary moderation table.

## Validation

```bash
PYTHONPATH=backend pytest backend/tests/test_stage9_food_aigc_admin.py
npm run typecheck
```

Expected:

- destination edits update tags and popularity
- facility edits update category/name/description
- food edits update name/price/rating/heat
- diary delete removes related comments, ratings, media, and search-index rows

## Remaining Limits

- Admin auth is not separated from demo user auth yet; the role-aware plan is documented in `docs/stage_31_admin_user_auth_plan.md`.
- Deletes are hard deletes for course demonstration; production would usually use soft delete and audit logs.
