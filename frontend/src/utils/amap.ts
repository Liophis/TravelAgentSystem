import AMapLoader from "@amap/amap-jsapi-loader";

let amapLoading: Promise<any> | null = null;

export function loadAMap(): Promise<any> {
  const key = import.meta.env.VITE_AMAP_KEY;

  if (!key) {
    throw new Error("VITE_AMAP_KEY is not configured");
  }

  if (!amapLoading) {
    amapLoading = AMapLoader.load({
      key,
      version: "2.0",
      plugins: ["AMap.Scale", "AMap.ToolBar"],
    });
  }

  return amapLoading;
}
