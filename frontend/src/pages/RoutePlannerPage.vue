<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>北邮校内导航</h1>
        <p>选择北京邮电大学沙河校区内部场所，使用校园拓扑生成校内路线。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="planRoute">规划路线</el-button>
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon />

    <el-row :gutter="16">
      <el-col :span="7">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="起点">
              <el-select
                v-model="startPlaceId"
                filterable
                remote
                clearable
                reserve-keyword
                :remote-method="searchRoutePlaces"
                :loading="placeLoading"
                placeholder="搜索北邮沙河校区内场所或校内点"
                @change="handlePlaceChange('start', startPlaceId)"
              >
                <el-option
                  v-for="option in routeOptions"
                  :key="option.id"
                  :label="placeLabel(option)"
                  :value="option.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="终点">
              <el-select
                v-model="endPlaceId"
                filterable
                remote
                clearable
                reserve-keyword
                :remote-method="searchRoutePlaces"
                :loading="placeLoading"
                placeholder="搜索北邮沙河校区内场所或校内点"
                @change="handlePlaceChange('end', endPlaceId)"
              >
                <el-option
                  v-for="option in routeOptions"
                  :key="option.id"
                  :label="placeLabel(option)"
                  :value="option.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="路线策略">
              <el-segmented v-model="form.strategy" :options="strategyOptions" />
            </el-form-item>
            <el-form-item label="交通方式">
              <el-select v-model="form.mode">
                <el-option
                  v-for="option in modeOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="多终点">
              <el-select
                v-model="multiPlaceIds"
                multiple
                filterable
                remote
                clearable
                reserve-keyword
                :remote-method="searchRoutePlaces"
                :loading="placeLoading"
                placeholder="搜索并选择多个校内场所或校内点"
              >
                <el-option
                  v-for="option in routeOptions"
                  :key="option.id"
                  :label="placeLabel(option)"
                  :value="option.id"
                />
              </el-select>
            </el-form-item>
            <el-collapse class="advanced-panel">
              <el-collapse-item title="调试坐标" name="coordinates">
                <el-form-item label="起点经度">
                  <el-input-number v-model="form.start_lng" :precision="4" :step="0.001" />
                </el-form-item>
                <el-form-item label="起点纬度">
                  <el-input-number v-model="form.start_lat" :precision="4" :step="0.001" />
                </el-form-item>
                <el-form-item label="终点经度">
                  <el-input-number v-model="form.end_lng" :precision="4" :step="0.001" />
                </el-form-item>
                <el-form-item label="终点纬度">
                  <el-input-number v-model="form.end_lat" :precision="4" :step="0.001" />
                </el-form-item>
                <el-form-item label="调试多终点坐标">
                  <el-input
                    v-model="multiPointText"
                    type="textarea"
                    :rows="4"
                    placeholder="名称,经度,纬度"
                  />
                </el-form-item>
              </el-collapse-item>
            </el-collapse>
            <el-form-item>
              <el-checkbox v-model="returnToStart">回到起点</el-checkbox>
            </el-form-item>
          </el-form>
          <el-button :loading="loading" @click="planMultiPointRoute">规划多点路线</el-button>
        </el-card>

        <el-card v-if="route" shadow="never" class="result-card">
          <div v-if="route.start && route.end" class="route-endpoints">
            <span>{{ route.start.name }}</span>
            <strong>→</strong>
            <span>{{ route.end.name }}</span>
          </div>
          <div class="stat"><span>总距离</span><strong>{{ route.distance }} m</strong></div>
          <div class="stat"><span>预计时间</span><strong>{{ Math.round(route.duration / 60) }} min</strong></div>
          <div class="stat"><span>策略</span><strong>{{ route.strategy }} / {{ route.mode }}</strong></div>
          <div class="stat"><span>数据源</span><strong>{{ routeSourceLabel(route.route_source) }}</strong></div>
          <div v-if="route.visit_order?.length" class="visit-order">
            <el-tag v-for="item in route.visit_order" :key="item.index" class="visit-tag">
              {{ item.name }}
            </el-tag>
          </div>
          <el-timeline>
            <el-timeline-item v-for="step in route.steps" :key="step.text">
              {{ step.text }} · {{ step.distance }} m
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>

      <el-col :span="17">
        <AMapView
          :road-paths="roadPaths"
          :buildings="campusBuildings"
          :facilities="campusFacilities"
          :route-path="route?.path ?? []"
        />
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import AMapView from "../components/AMapView.vue";
import {
  apiGet,
  apiPost,
  type BuildingItem,
  type FacilityItem,
  type MapGeoJsonPayload,
  type RoutePlanPayload,
  type SearchPlaceItem,
  type SearchPlacesPayload,
} from "../services/api";

const loading = ref(false);
const placeLoading = ref(false);
const route = ref<RoutePlanPayload | null>(null);
const mapPayload = ref<MapGeoJsonPayload | null>(null);
const error = ref("");
const returnToStart = ref(false);
const startPlaceId = ref("");
const endPlaceId = ref("");
const multiPlaceIds = ref<string[]>([]);
const routeOptions = ref<SearchPlaceItem[]>([]);
const optionCache = reactive<Record<string, SearchPlaceItem>>({});
const multiPointText = ref("教学实验综合楼,116.2862632,40.1571249\n南区食堂,116.2845755,40.1548202");
const buptShaheBounds = {
  minLng: 116.2770,
  maxLng: 116.2896,
  minLat: 40.1534,
  maxLat: 40.1602,
};
const strategyOptions = [
  { label: "最短距离", value: "shortest_distance" },
  { label: "最短时间", value: "shortest_time" },
];
const modeOptions = [
  { label: "步行", value: "walk" },
  { label: "自行车", value: "bike" },
  { label: "电瓶车", value: "electric_cart" },
  { label: "混合交通", value: "mixed" },
];
const form = reactive({
  start_lng: 116.28333,
  start_lat: 40.15608,
  end_lng: 116.28620,
  end_lat: 40.15820,
  strategy: "shortest_distance",
  mode: "walk",
  route_source: "local_graph",
});

const roadPaths = computed(() => mapPayload.value?.roads.map((road) => road.path) ?? []);
const campusBuildings = computed<BuildingItem[]>(() =>
  (mapPayload.value?.buildings ?? []).filter((building) => {
    const center = buildingCenter(building.polygon);
    return isInBuptShaheCampus(center[0], center[1]);
  }),
);
const campusFacilities = computed<FacilityItem[]>(() =>
  (mapPayload.value?.facilities ?? []).filter((facility) => isInBuptShaheCampus(facility.lng, facility.lat)),
);

async function searchRoutePlaces(query: string) {
  const keyword = query.trim();
  placeLoading.value = true;
  try {
    const params = new URLSearchParams({ keyword, limit: keyword ? "30" : "100", scope: "campus" });
    const payload = await apiGet<SearchPlacesPayload>(`/api/v1/search/places?${params}`);
    mergeRouteOptions(payload.items.filter(isCampusRoutePlace));
    error.value = "";
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "校内地点搜索失败";
  } finally {
    placeLoading.value = false;
  }
}

function mergeRouteOptions(items: SearchPlaceItem[]) {
  const byId = new Map(routeOptions.value.map((item) => [item.id, item]));
  for (const item of items) {
    optionCache[item.id] = item;
    byId.set(item.id, item);
  }
  routeOptions.value = Array.from(byId.values()).slice(0, 80);
}

function placeLabel(item: SearchPlaceItem) {
  const source =
    {
      building: "楼宇",
      facility: "设施",
      node: "校内点",
    }[item.source] ?? item.source;
  return `${item.name} · ${source}`;
}

function isCampusRoutePlace(item: SearchPlaceItem) {
  return item.source === "building" || item.source === "facility" || item.source === "node";
}

function routeSourceLabel(source?: string) {
  return source === "local_graph" ? "北邮校园拓扑" : source ?? "北邮校园拓扑";
}

function buildingCenter(polygon: Array<[number, number]> | number[][]) {
  if (!polygon.length) {
    return [0, 0];
  }
  return [
    polygon.reduce((sum, point) => sum + point[0], 0) / polygon.length,
    polygon.reduce((sum, point) => sum + point[1], 0) / polygon.length,
  ];
}

function isInBuptShaheCampus(lng: number, lat: number) {
  return (
    lng >= buptShaheBounds.minLng &&
    lng <= buptShaheBounds.maxLng &&
    lat >= buptShaheBounds.minLat &&
    lat <= buptShaheBounds.maxLat
  );
}

function handlePlaceChange(kind: "start" | "end", placeId: string) {
  const item = optionCache[placeId];
  if (!item) {
    return;
  }
  if (kind === "start") {
    form.start_lng = item.lng;
    form.start_lat = item.lat;
    return;
  }
  form.end_lng = item.lng;
  form.end_lat = item.lat;
}

async function planRoute() {
  loading.value = true;
  try {
    route.value = await apiPost<RoutePlanPayload>("/api/v1/routes/plan", {
      start_place_id: startPlaceId.value || null,
      end_place_id: endPlaceId.value || null,
      ...form,
    });
    error.value = "";
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "校内路线规划失败";
  } finally {
    loading.value = false;
  }
}

async function planMultiPointRoute() {
  const selectedPoints = selectedMultiPoints();
  const points = selectedPoints.length > 0 ? selectedPoints : parseMultiPointText();
  if (points.length === 0) {
    return;
  }
  loading.value = true;
  try {
    route.value = await apiPost<RoutePlanPayload>("/api/v1/routes/multi-point", {
      start_place_id: startPlaceId.value || null,
      start_lng: form.start_lng,
      start_lat: form.start_lat,
      points,
      return_to_start: returnToStart.value,
      strategy: form.strategy,
      mode: form.mode,
      route_source: form.route_source,
    });
    error.value = "";
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "校内多点路线规划失败";
  } finally {
    loading.value = false;
  }
}

function selectedMultiPoints() {
  return multiPlaceIds.value
    .map((placeId, index) => {
      const item = optionCache[placeId];
      if (!item) {
        return null;
      }
      return {
        place_id: item.id,
        name: item.name || `终点 ${index + 1}`,
        lng: item.lng,
        lat: item.lat,
      };
    })
    .filter((item): item is { place_id: string; name: string; lng: number; lat: number } => item !== null);
}

function parseMultiPointText() {
  return multiPointText.value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const [name, lng, lat] = line.split(",").map((item) => item.trim());
      return {
        name: name || `终点 ${index + 1}`,
        lng: Number(lng),
        lat: Number(lat),
      };
    })
    .filter((item) => Number.isFinite(item.lng) && Number.isFinite(item.lat));
}

async function primeRouteOptions() {
  await searchRoutePlaces("西门");
  const gate = routeOptions.value.find((item) => item.category === "gate" || item.name.includes("西门")) ?? routeOptions.value[0];
  if (gate) {
    startPlaceId.value = gate.id;
    handlePlaceChange("start", gate.id);
  }

  await searchRoutePlaces("图书馆");
  const library = routeOptions.value.find((item) => item.category === "library" || item.name.includes("图书馆"));
  if (library) {
    endPlaceId.value = library.id;
    handlePlaceChange("end", library.id);
  }
}

onMounted(async () => {
  try {
    mapPayload.value = await apiGet<MapGeoJsonPayload>("/api/v1/map/geojson");
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "校园地图数据加载失败";
  }
  await searchRoutePlaces("");
  await primeRouteOptions();
  void planRoute();
});
</script>

<style scoped>
.advanced-panel {
  margin: 4px 0 14px;
}

.route-endpoints {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
}

.route-endpoints span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.visit-order {
  margin: 12px 0;
}

.visit-tag {
  margin: 0 6px 6px 0;
}
</style>
