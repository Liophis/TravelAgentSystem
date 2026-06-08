import { expect, test } from "@playwright/test";

test("AMap guide renders map container and overlays", async ({ page }) => {
  test.skip(!process.env.VITE_AMAP_KEY, "VITE_AMAP_KEY is required for AMap browser smoke.");

  await page.goto("/map");
  await expect(page.locator(".amap-container")).toBeVisible({ timeout: 30_000 });
  await expect(page.locator("text=地图导览")).toBeVisible();

  const markerCount = await page.locator(".amap-marker").count();
  const canvasCount = await page.locator("canvas").count();
  expect(markerCount + canvasCount).toBeGreaterThan(0);

  await page.screenshot({ path: "test-results/amap-map-smoke.png", fullPage: true });
});
