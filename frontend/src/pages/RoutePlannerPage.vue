<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>{{ currentScene.title }}</h1>
        <p>{{ currentScene.description }}</p>
      </div>
      <div class="heading-actions">
        <el-segmented v-model="selectedSceneKey" :options="sceneSegmentOptions" />
        <el-button type="primary" :loading="loading" @click="planRoute">规划路线</el-button>
      </div>
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
                :placeholder="`搜索${currentScene.shortName}内场所或节点`"
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
                :placeholder="`搜索${currentScene.shortName}内场所或节点`"
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
                :placeholder="`搜索并选择多个${currentScene.shortName}内场所或节点`"
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
          :buildings="sceneBuildings"
          :facilities="sceneFacilities"
          :route-path="route?.path ?? []"
          :center="mapCenter"
        />
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

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
const selectedSceneKey = ref("bupt_shahe");
const scenes = [
  {
    key: "bupt_shahe",
    shortName: "北邮沙河",
    title: "北邮校内导航",
    description: "选择北京邮电大学沙河校区内部场所，使用校园拓扑生成校内路线。",
    scope: "campus",
    center: [116.28333, 40.15608] as [number, number],
    defaultStartKeyword: "西门",
    defaultEndKeyword: "图书馆",
    defaultMultiPointText: "教学实验综合楼,116.2862632,40.1571249\n南区食堂,116.2845755,40.1548202",
  },
  {
    key: "summer_palace",
    shortName: "颐和园",
    title: "颐和园内部导航",
    description: "选择北京颐和园内部景点、建筑或服务设施，使用独立景区路网生成游览路线。",
    scope: "scenic",
    center: [116.2755, 39.9996] as [number, number],
    defaultStartKeyword: "仁寿殿",
    defaultEndKeyword: "佛香阁",
    defaultMultiPointText: "仁寿殿,116.2755,39.9996\n佛香阁,116.2732,39.9997",
  },
];
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

const currentScene = computed(() => scenes.find((scene) => scene.key === selectedSceneKey.value) ?? scenes[0]);
const sceneSegmentOptions = scenes.map((scene) => ({ label: scene.shortName, value: scene.key }));
const mapCenter = computed(() => mapPayload.value?.center ?? currentScene.value.center);
const roadPaths = computed(() => mapPayload.value?.roads.map((road) => road.path) ?? []);
const sceneBuildings = computed<BuildingItem[]>(() => mapPayload.value?.buildings ?? []);
const sceneFacilities = computed<FacilityItem[]>(() => mapPayload.value?.facilities ?? []);

async function searchRoutePlaces(query: string) {
  const keyword = query.trim();
  placeLoading.value = true;
  try {
    const params = new URLSearchParams({
      keyword,
      limit: keyword ? "30" : "100",
      scope: currentScene.value.scope,
      scene_key: selectedSceneKey.value,
    });
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
  return source === "local_graph" ? `${currentScene.value.shortName}拓扑` : source ?? `${currentScene.value.shortName}拓扑`;
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
      scene_key: selectedSceneKey.value,
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
      scene_key: selectedSceneKey.value,
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
  await searchRoutePlaces(currentScene.value.defaultStartKeyword);
  const start = routeOptions.value.find((item) => item.name.includes(currentScene.value.defaultStartKeyword)) ?? routeOptions.value[0];
  if (start) {
    startPlaceId.value = start.id;
    handlePlaceChange("start", start.id);
  }

  await searchRoutePlaces(currentScene.value.defaultEndKeyword);
  const end = routeOptions.value.find((item) => item.name.includes(currentScene.value.defaultEndKeyword));
  if (end) {
    endPlaceId.value = end.id;
    handlePlaceChange("end", end.id);
  }
}

function resetSceneState() {
  route.value = null;
  startPlaceId.value = "";
  endPlaceId.value = "";
  multiPlaceIds.value = [];
  routeOptions.value = [];
  Object.keys(optionCache).forEach((key) => delete optionCache[key]);
  const [lng, lat] = currentScene.value.center;
  form.start_lng = lng;
  form.start_lat = lat;
  form.end_lng = lng;
  form.end_lat = lat;
  multiPointText.value = currentScene.value.defaultMultiPointText;
}

async function loadMap() {
  const params = new URLSearchParams({ scene_key: selectedSceneKey.value });
  mapPayload.value = await apiGet<MapGeoJsonPayload>(`/api/v1/map/geojson?${params}`);
}

async function loadScene() {
  resetSceneState();
  try {
    await loadMap();
    await searchRoutePlaces("");
    await primeRouteOptions();
    if (startPlaceId.value || endPlaceId.value) {
      await planRoute();
    }
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "内部导航数据加载失败";
  }
}

watch(selectedSceneKey, () => {
  void loadScene();
});

onMounted(async () => {
  await loadScene();
});
</script>

<style scoped>
.heading-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

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
