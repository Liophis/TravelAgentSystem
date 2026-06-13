<template>
  <div class="amap-shell">
    <div class="amap-layer-bar">
      <span>AMap</span>
      <strong>{{ layerSummary }}</strong>
    </div>
    <div ref="mapElement" class="amap-container" />
    <div v-if="loadError" class="amap-fallback">
      <strong>地图渲染待配置</strong>
      <span>{{ loadError }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

import type { BuildingItem, Coordinate, FacilityItem } from "../services/api";
import { loadAMap } from "../utils/amap";
import { gcj02ToWgs84, pathToGcj02, pathsToGcj02, wgs84ToGcj02 } from "../utils/coordinates";

const props = withDefaults(
  defineProps<{
    facilities?: FacilityItem[];
    buildings?: BuildingItem[];
    roadPaths?: Coordinate[][];
    routePath?: Coordinate[];
    center?: Coordinate;
    origin?: { lng: number; lat: number; name?: string } | null;
    selectedPoint?: Coordinate | null; // 新增：当前选中的点
  }>(),
  {
    facilities: () => [],
    buildings: () => [],
    roadPaths: () => [],
    routePath: () => [],
    center: () => [116.28333, 40.15608],
    origin: null,
    selectedPoint: null,
  },
);
const emit = defineEmits<{
  (event: "map-click", coordinate: Coordinate, gcjCoordinate: Coordinate): void;
  (event: "facility-click", facility: FacilityItem): void;
}>();

const mapElement = ref<HTMLElement | null>(null);
const loadError = ref("");

let AMap: any = null;
let map: any = null;
let infoWindow: any = null;
let overlays: any[] = [];

const layerSummary = computed(() => {
  const parts = [
    `${props.roadPaths.length} 路段`,
    `${props.buildings.length} 建筑`,
    `${props.facilities.length} POI`,
  ];
  if (props.routePath.length > 0) {
    parts.push(`${props.routePath.length} 路线点`);
  }
  return parts.join(" · ");
});

function clearOverlays() {
  if (map && overlays.length > 0) {
    map.remove(overlays);
  }
  overlays = [];
}

function drawOverlays() {
  if (!AMap || !map) return;

  clearOverlays();

  pathsToGcj02(props.roadPaths).forEach((path) => {
    if (path.length < 2) return;
    const polyline = new AMap.Polyline({
      path,
      strokeColor: "#5f6c7b",
      strokeWeight: 4,
      strokeOpacity: 0.72,
    });
    overlays.push(polyline);
  });

  props.buildings.forEach((building) => {
    const polygon = new AMap.Polygon({
      path: pathToGcj02(building.polygon),
      fillColor: "#8fd3c7",
      fillOpacity: 0.38,
      strokeColor: "#188f7a",
      strokeWeight: 2,
    });
    overlays.push(polygon);
  });

  props.facilities.forEach((facility) => {
    const position = wgs84ToGcj02([facility.lng, facility.lat]);
    const marker = new AMap.Marker({
      position,
      title: facility.name,
      content: `<div class="facility-dot"></div>`,
      offset: new AMap.Pixel(-5, -5),
    });
    marker.on("click", () => {
      emit("facility-click", facility);
      if (!infoWindow) {
        infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -28) });
      }
      const description = facility.description ? `<div>${facility.description}</div>` : "";
      infoWindow.setContent(
        `<strong>${facility.name}</strong><div>${facility.category}</div>${description}`,
      );
      infoWindow.open(map, position);
    });
    overlays.push(marker);
  });

  if (props.origin) {
    const originPosition = wgs84ToGcj02([props.origin.lng, props.origin.lat]);
    const originMarker = new AMap.Marker({
      position: originPosition,
      title: props.origin.name || "当前位置",
      content: `<div class="origin-dot"></div>`,
      offset: new AMap.Pixel(-8, -8),
      zIndex: 120,
    });
    overlays.push(originMarker);
  }

  // 绘制用户选中的点
  if (props.selectedPoint) {
    const pointPosition = wgs84ToGcj02(props.selectedPoint);
    const selectedMarker = new AMap.Marker({
      position: pointPosition,
      title: "选中的位置",
      content: `<div class="selected-dot"></div>`,
      offset: new AMap.Pixel(-10, -10),
      zIndex: 130,
      animation: "AMAP_ANIMATION_DROP",
    });
    overlays.push(selectedMarker);
  }

  let routePolyline: any = null;
  if (props.routePath.length >= 2) {
    routePolyline = new AMap.Polyline({
      path: pathToGcj02(props.routePath),
      strokeColor: "#2563eb",
      strokeWeight: 7,
      strokeOpacity: 0.92,
      lineJoin: "round",
    });
    overlays.push(routePolyline);
  }

  if (overlays.length > 0) {
    map.add(overlays);
  }

  if (routePolyline) {
    map.setFitView([routePolyline], false, [48, 48, 48, 48]);
  } else if (overlays.length > 0) {
    map.setFitView(overlays, false, [56, 56, 56, 56]);
  } else {
    map.setCenter(wgs84ToGcj02(props.center));
  }
}

onMounted(async () => {
  await nextTick();
  try {
    AMap = await loadAMap();
    map = new AMap.Map(mapElement.value, {
      center: wgs84ToGcj02(props.center),
      zoom: 16,
      viewMode: "2D",
    });
    map.addControl(new AMap.Scale());
    map.addControl(new AMap.ToolBar({ position: "RB" }));
    map.on("click", (event: any) => {
      const lngLat = event.lnglat;
      const gcjLng = lngLat.getLng();
      const gcjLat = lngLat.getLat();
      const wgs84Coord = gcj02ToWgs84([gcjLng, gcjLat]);
      // 同时发送 WGS84（给后端）和 GCJ02（给高德逆地理编码）
      emit("map-click", wgs84Coord, [gcjLng, gcjLat]);
    });
    drawOverlays();
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "AMap failed to load";
  }
});

onBeforeUnmount(() => {
  clearOverlays();
  if (map) {
    map.destroy();
  }
});

watch(
  () => [props.facilities, props.buildings, props.roadPaths, props.routePath, props.center, props.origin, props.selectedPoint],
  () => drawOverlays(),
  { deep: true },
);
</script>

<style scoped>
.amap-shell {
  position: relative;
  min-height: 520px;
  height: 100%;
  overflow: hidden;
  border: 1px solid #d0d5dd;
  border-radius: 8px;
  background: #f8fafc;
  box-shadow: 0 12px 32px rgba(16, 24, 40, 0.08);
}

.amap-container {
  width: 100%;
  min-height: 620px;
  height: 100%;
}

.amap-layer-bar {
  position: absolute;
  top: 14px;
  left: 14px;
  z-index: 5;
  display: inline-flex;
  align-items: center;
  max-width: calc(100% - 28px);
  overflow: hidden;
  border: 1px solid rgba(208, 213, 221, 0.86);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 8px 22px rgba(16, 24, 40, 0.12);
  backdrop-filter: blur(12px);
}

.amap-layer-bar span {
  padding: 8px 10px;
  background: #0f766e;
  color: #ffffff;
  font-size: 12px;
  font-weight: 900;
}

.amap-layer-bar strong {
  overflow: hidden;
  padding: 8px 12px;
  color: #344054;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.amap-fallback {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  gap: 8px;
  padding: 24px;
  color: #344054;
  text-align: center;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.86)),
    repeating-linear-gradient(45deg, #eef4f3 0, #eef4f3 10px, #e2e8f0 10px, #e2e8f0 20px);
}

:global(.facility-dot) {
  width: 10px;
  height: 10px;
  border: 2px solid #ffffff;
  border-radius: 50%;
  background: #0f766e;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.28);
}

:global(.origin-dot) {
  width: 16px;
  height: 16px;
  border: 3px solid #ffffff;
  border-radius: 50%;
  background: #dc2626;
  box-shadow: 0 2px 8px rgba(127, 29, 29, 0.35);
}

:global(.selected-dot) {
  width: 20px;
  height: 20px;
  border: 3px solid #ffffff;
  border-radius: 50%;
  background: #2563eb;
  box-shadow: 0 2px 10px rgba(37, 99, 235, 0.5);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.5);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(37, 99, 235, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0);
  }
}
</style>
