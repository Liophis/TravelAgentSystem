# Stage 26 Optional Map Smoke

## Scope

This stage adds browser-level verification harness for the AMap page without making normal checks depend on a real map key or external JS SDK availability.

## Delivered

- `scripts/check_map_frontend_optional.sh`
- `frontend/playwright.config.ts`
- `frontend/tests/amap-smoke.spec.ts`
- `npm run test:e2e:amap`

## Validation

```bash
bash scripts/check_map_frontend_optional.sh
```

Expected in an unprepared local environment:

- skips with a clear reason when `VITE_AMAP_KEY` is missing
- skips with a clear reason when Playwright is not installed
- skips with a clear reason when backend is not running

Expected in a prepared demo environment:

- opens `/map`
- waits for AMap container
- checks map canvas/marker rendering
- writes `frontend/test-results/amap-map-smoke.png`

## Remaining Limits

- The smoke is intentionally not part of `bash scripts/check_all.sh`.
- It needs a valid Web JS API key and network access to the AMap JS SDK.
