<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>路线规划</h1>
        <p>选择校园地点，生成道路图路线。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="planRoute">规划路线</el-button>
    </div>

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
                placeholder="搜索校门、楼宇、设施"
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
                placeholder="搜索校门、楼宇、设施"
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
            <el-form-item label="路线数据">
              <el-segmented v-model="form.route_source" :options="routeSourceOptions" />
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
                placeholder="搜索并选择多个地点"
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
              <el-collapse-item title="高级坐标" name="coordinates">
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
                <el-form-item label="多终点坐标">
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
        <AMapView :route-path="route?.path ?? []" />
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import AMapView from "../components/AMapView.vue";
import {
  apiGet,
  apiPost,
  type RoutePlanPayload,
  type SearchPlaceItem,
  type SearchPlacesPayload,
} from "../services/api";

const loading = ref(false);
const placeLoading = ref(false);
const route = ref<RoutePlanPayload | null>(null);
const returnToStart = ref(false);
const startPlaceId = ref("");
const endPlaceId = ref("");
const multiPlaceIds = ref<string[]>([]);
const routeOptions = ref<SearchPlaceItem[]>([]);
const optionCache = reactive<Record<string, SearchPlaceItem>>({});
const multiPointText = ref("教学楼,116.2842,40.1567\n图书馆,116.2862,40.1582");
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
const routeSourceOptions = [
  { label: "真实路线", value: "auto" },
  { label: "本地图", value: "local_graph" },
];
const form = reactive({
  start_lng: 116.28333,
  start_lat: 40.15608,
  end_lng: 116.28620,
  end_lat: 40.15820,
  strategy: "shortest_distance",
  mode: "walk",
  route_source: "auto",
});

async function searchRoutePlaces(query: string) {
  const keyword = query.trim();
  if (!keyword) {
    return;
  }
  placeLoading.value = true;
  try {
    const params = new URLSearchParams({ keyword, limit: "20" });
    const payload = await apiGet<SearchPlacesPayload>(`/api/v1/search/places?${params}`);
    mergeRouteOptions(payload.items);
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
      destination: "景点",
      building: "楼宇",
      facility: "设施",
    }[item.source] ?? item.source;
  return `${item.name} · ${source}`;
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
  await searchRoutePlaces("校门");
  const gate = routeOptions.value.find((item) => item.category === "gate") ?? routeOptions.value[0];
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
