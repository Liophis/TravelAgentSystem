# Stage 31 Admin/User Auth Plan

## Scope

This is a documentation-only stage. It defines the target login-state split between normal users and administrators.

The project should keep one account system and one login endpoint. User/admin separation should be role-based, not two independent login systems.

## Current State

- `POST /api/v1/users/register`, `POST /api/v1/users/login`, and `GET /api/v1/users/me` exist.
- Login returns a demo HMAC bearer token.
- Admin APIs under `/api/v1/admin/*` exist for stats, map import, content edits, and diary moderation.
- Admin APIs are not yet protected by an admin role.
- Frontend shows the admin dashboard entry without checking whether the current account is an admin.

## Target Contract

| Area | Target Behavior |
| --- | --- |
| User table | Add `users.role` with allowed values `user` and `admin`; default is `user` |
| Login API | Reuse `POST /api/v1/users/login`; response includes user profile and `role` |
| Token | Include `user_id`, `role`, and expiry in the signed token payload |
| Current user | `GET /api/v1/users/me` returns `role` |
| Admin guard | `/api/v1/admin/*` requires a valid bearer token whose role is `admin` |
| Frontend state | Store `{ token, user, role }`; hide or block admin page for normal users |
| Seed data | Provide at least one normal demo account and one admin demo account |

## Planned Demo Accounts

Use deterministic seed accounts for offline demonstration:

```text
user01 / demo123456 / role=user
admin01 / admin123456 / role=admin
```

Do not hard-code these passwords in frontend source. They belong in seed data and documentation only.

## Backend Implementation Tasks

1. Add `role` to `User` model and seed data.
2. Backfill existing users as `role=user`.
3. Mark `admin01` as `role=admin`.
4. Extend token creation and verification to carry role.
5. Add reusable dependencies:
   - `get_current_user`
   - `require_admin`
6. Apply `require_admin` to `/api/v1/admin/*`.
7. Return `401` for missing/invalid token and `403` for non-admin users.
8. Add tests for user token, admin token, and forbidden admin access.

## Frontend Implementation Tasks

1. Add a small auth state helper for token, user id, username, and role.
2. Show normal user login state in the user preference page.
3. Hide the admin navigation item unless `role=admin`.
4. Add an admin login path or use the same login form with the admin seed account.
5. Attach bearer token to admin API calls.
6. Show a clear no-permission state on `/admin` when a normal user opens the route directly.

## Acceptance Criteria

- Normal user can log in and continue using recommendation, rating, favorites, diaries, and food flows.
- Admin user can log in and access the admin dashboard.
- Normal user cannot call admin stats, map import, content edit, or diary moderation APIs.
- Missing token on admin API returns `401`.
- Valid normal-user token on admin API returns `403`.
- Valid admin token on admin API succeeds.
- Frontend does not show the admin menu for normal users.
- Documentation lists both seed accounts and explains that one login endpoint is role-aware.

## Validation

After implementation:

```bash
PYTHONPATH=backend pytest backend/tests/test_stage23_user_feedback_loop.py backend/tests/test_stage31_admin_auth.py
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```
