# Stage 11 Mainline Hardening

## Scope

This stage fixes a mainline smoke-script conflict marker regression and adds small guardrails for final delivery stability.

## Delivered

- Removed merge conflict markers from `scripts/smoke_features.sh`.
- Added `scripts/check_merge_markers.sh`.
- Added merge-marker scanning to `scripts/check_all.sh`.
- Added frontend global API error notifications through Element Plus.
- Added a 401 message path for future login/session work.

## Validation

Run from repository root:

```bash
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

Expected backend result:

```text
28 passed
```

## Remaining Gaps

- Docker Compose end-to-end validation still needs to be run in an environment with Docker available.
- Login/register and production RBAC are still planned.
- Admin edit/moderation screens are still planned.
