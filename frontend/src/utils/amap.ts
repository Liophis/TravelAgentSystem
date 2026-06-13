import AMapLoader from "@amap/amap-jsapi-loader";

let amapLoading: Promise<any> | null = null;
let AMapInstance: any = null;

export function loadAMap(): Promise<any> {
  const key = import.meta.env.VITE_AMAP_KEY;

  if (!key) {
    throw new Error("VITE_AMAP_KEY is not configured");
  }

  if (amapLoading) {
    return amapLoading;
  }

  const loading = AMapLoader.load({
    key,
    version: "2.0",
    plugins: ["AMap.Scale", "AMap.ToolBar", "AMap.Geocoder"],
  }).then((AMap) => {
    AMapInstance = AMap;
    return AMap;
  });
  amapLoading = loading;
  return loading;
}

export function getAMap(): any {
  return AMapInstance;
}

/**
 * 逆地理编码：将坐标转换为中文地址
 */
export async function reverseGeocode(lng: number, lat: number): Promise<{ address: string; formattedAddress: string } | null> {
  const AMap = await loadAMap();
  return new Promise((resolve) => {
    const geocoder = new AMap.Geocoder({
      radius: 1000,
      extensions: "all",
    });
    geocoder.getAddress([lng, lat], (status: string, result: any) => {
      if (status === "complete" && result.regeocode) {
        resolve({
          address: result.regeocode.addressComponent?.street || result.regeocode.address,
          formattedAddress: result.regeocode.formattedAddress,
        });
      } else {
        resolve(null);
      }
    });
  });
}
