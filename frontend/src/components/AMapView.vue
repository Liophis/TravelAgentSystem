<template>
  <div class="amap-shell">
    <div ref="mapElement" class="amap-container" />
    <div v-if="loadError" class="amap-fallback">
      <strong>地图渲染待配置</strong>
      <span>{{ loadError }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

import type { BuildingItem, Coordinate, FacilityItem } from "../services/api";
import { loadAMap } from "../utils/amap";

const props = withDefaults(
  defineProps<{
    facilities?: FacilityItem[];
    buildings?: BuildingItem[];
    roadPaths?: Coordinate[][];
    routePath?: Coordinate[];
  }>(),
  {
    facilities: () => [],
    buildings: () => [],
    roadPaths: () => [],
    routePath: () => [],
  },
);

const mapElement = ref<HTMLElement | null>(null);
const loadError = ref("");

let AMap: any = null;
let map: any = null;
let infoWindow: any = null;
let overlays: any[] = [];

function clearOverlays() {
  if (map && overlays.length > 0) {
    map.remove(overlays);
  }
  overlays = [];
}

function drawOverlays() {
  if (!AMap || !map) return;

  clearOverlays();

  props.roadPaths.forEach((path) => {
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
      path: building.polygon,
      fillColor: "#8fd3c7",
      fillOpacity: 0.38,
      strokeColor: "#188f7a",
      strokeWeight: 2,
    });
    overlays.push(polygon);
  });

  props.facilities.forEach((facility) => {
    const marker = new AMap.Marker({
      position: [facility.lng, facility.lat],
      title: facility.name,
    });
    marker.on("click", () => {
      if (!infoWindow) {
        infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -28) });
      }
      const description = facility.description ? `<div>${facility.description}</div>` : "";
      infoWindow.setContent(
        `<strong>${facility.name}</strong><div>${facility.category}</div>${description}`,
      );
      infoWindow.open(map, [facility.lng, facility.lat]);
    });
    overlays.push(marker);
  });

  let routePolyline: any = null;
  if (props.routePath.length >= 2) {
    routePolyline = new AMap.Polyline({
      path: props.routePath,
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
  }
}

onMounted(async () => {
  await nextTick();
  try {
    AMap = await loadAMap();
    map = new AMap.Map(mapElement.value, {
      center: [116.3260, 40.0030],
      zoom: 16,
      viewMode: "2D",
    });
    map.addControl(new AMap.Scale());
    map.addControl(new AMap.ToolBar({ position: "RB" }));
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
  () => [props.facilities, props.buildings, props.roadPaths, props.routePath],
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
  border: 1px solid #d8dee4;
  border-radius: 8px;
  background: #f6f8fa;
}

.amap-container {
  width: 100%;
  min-height: 520px;
  height: 100%;
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
    linear-gradient(90deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.82)),
    repeating-linear-gradient(45deg, #eef2f7 0, #eef2f7 10px, #e2e8f0 10px, #e2e8f0 20px);
}
</style>
