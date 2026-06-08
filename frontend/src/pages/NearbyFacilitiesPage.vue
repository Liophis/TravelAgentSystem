<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>附近设施</h1>
        <p>以选中的内部场所为中心，按真实道路距离查询服务设施。</p>
      </div>
      <div class="heading-actions">
        <el-segmented v-model="selectedSceneKey" :options="sceneSegmentOptions" />
        <el-button type="primary" :loading="loading" @click="loadFacilities">查询</el-button>
      </div>
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon />

    <el-row :gutter="16">
      <el-col :span="7">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="当前位置">
              <el-select
                v-model="originPlaceId"
                filterable
                remote
                clearable
                reserve-keyword
                :remote-method="searchOrigins"
                :loading="originLoading"
                :placeholder="`搜索${currentScene.shortName}内场所`"
                @change="handleOriginChange"
              >
                <el-option
                  v-for="option in originOptions"
                  :key="option.id"
                  :label="placeLabel(option)"
                  :value="option.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="设施类别">
              <el-select v-model="category" clearable filterable allow-create placeholder="全部类别">
                <el-option label="厕所" value="厕所" />
                <el-option label="饮水点" value="饮水点" />
                <el-option label="便利店" value="超市" />
                <el-option label="食堂" value="食堂" />
                <el-option label="校门" value="校门" />
                <el-option label="图书馆服务" value="图书馆" />
                <el-option label="运动设施" value="运动" />
                <el-option label="医务室" value="医务室" />
                <el-option label="交通站点" value="交通" />
                <el-option label="ATM" value="atm" />
              </el-select>
            </el-form-item>
            <el-form-item label="搜索半径">
              <el-input-number v-model="radius" :min="100" :max="3000" :step="100" />
            </el-form-item>
            <el-collapse class="advanced-panel">
              <el-collapse-item title="调试坐标" name="coordinates">
                <el-form-item label="当前位置经度">
                  <el-input-number v-model="coordinateOrigin.lng" :precision="6" :step="0.0001" />
                </el-form-item>
                <el-form-item label="当前位置纬度">
                  <el-input-number v-model="coordinateOrigin.lat" :precision="6" :step="0.0001" />
                </el-form-item>
                <el-button @click="applyCoordinateOrigin">使用坐标</el-button>
              </el-collapse-item>
            </el-collapse>
          </el-form>
        </el-card>

        <el-card shadow="never" class="result-card">
          <div class="stat"><span>当前位置</span><strong>{{ selectedOrigin.name }}</strong></div>
          <div class="stat"><span>类别</span><strong>{{ resolvedCategory }}</strong></div>
          <div class="stat"><span>结果</span><strong>{{ facilities.length }}</strong></div>
        </el-card>

        <el-card shadow="never" class="result-card">
          <el-table :data="facilities" size="small">
            <el-table-column prop="name" label="设施" />
            <el-table-column prop="category_name" label="类别" width="96" />
            <el-table-column prop="distance" label="距离" width="88">
              <template #default="{ row }">{{ row.distance }}m</template>
            </el-table-column>
            <el-table-column label="路线" width="80">
              <template #default="{ row }">
                <el-button link type="primary" @click="routePath = row.routePath ?? []">绘制</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="17">
        <AMapView
          :facilities="facilities"
          :road-paths="roadPaths"
          :buildings="mapPayload?.buildings ?? []"
          :route-path="routePath"
          :center="mapPayload?.center ?? currentScene.center"
          :origin="selectedOrigin"
          @map-click="handleMapClick"
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
  type Coordinate,
  type FacilityItem,
  type MapGeoJsonPayload,
  type NearbyFacilitiesPayload,
  type RouteEndpointItem,
  type SearchPlaceItem,
  type SearchPlacesPayload,
} from "../services/api";

const category = ref("超市");
const radius = ref(1000);
const loading = ref(false);
const originLoading = ref(false);
const error = ref("");
const facilities = ref<FacilityItem[]>([]);
const routePath = ref<Coordinate[]>([]);
const mapPayload = ref<MapGeoJsonPayload | null>(null);
const originPlaceId = ref("");
const originOptions = ref<SearchPlaceItem[]>([]);
const originCache = reactive<Record<string, SearchPlaceItem>>({});
const selectedSceneKey = ref("bupt_shahe");
const scenes = [
  {
    key: "bupt_shahe",
    shortName: "北邮沙河",
    scope: "campus",
    center: [116.28333, 40.15608] as [number, number],
    defaultOriginKeyword: "图书馆",
    defaultOriginName: "北京邮电大学沙河校区",
  },
  {
    key: "summer_palace",
    shortName: "颐和园",
    scope: "scenic",
    center: [116.2755, 39.9996] as [number, number],
    defaultOriginKeyword: "仁寿殿",
    defaultOriginName: "北京颐和园",
  },
];
const coordinateOrigin = reactive({
  lng: 116.28333,
  lat: 40.15608,
});
const selectedOrigin = ref<RouteEndpointItem>({
  id: "",
  source: "coordinate",
  name: "北京邮电大学沙河校区",
  lng: coordinateOrigin.lng,
  lat: coordinateOrigin.lat,
});

const currentScene = computed(() => scenes.find((scene) => scene.key === selectedSceneKey.value) ?? scenes[0]);
const sceneSegmentOptions = scenes.map((scene) => ({ label: scene.shortName, value: scene.key }));
const roadPaths = computed(() => mapPayload.value?.roads.map((road) => road.path) ?? []);
const resolvedCategory = computed(() => facilities.value[0]?.category_name ?? (category.value || "全部"));

async function searchOrigins(query: string) {
  originLoading.value = true;
  try {
    const keyword = query.trim();
    const params = new URLSearchParams({
      keyword,
      limit: keyword ? "30" : "100",
      scope: currentScene.value.scope,
      scene_key: selectedSceneKey.value,
    });
    const payload = await apiGet<SearchPlacesPayload>(`/api/v1/search/places?${params}`);
    mergeOriginOptions(payload.items.filter(isCampusOrigin));
    error.value = "";
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "当前位置搜索失败";
  } finally {
    originLoading.value = false;
  }
}

function mergeOriginOptions(items: SearchPlaceItem[]) {
  const byId = new Map(originOptions.value.map((item) => [item.id, item]));
  for (const item of items) {
    originCache[item.id] = item;
    byId.set(item.id, item);
  }
  originOptions.value = Array.from(byId.values()).slice(0, 100);
}

function isCampusOrigin(item: SearchPlaceItem) {
  return item.source === "building" || item.source === "facility" || item.source === "node";
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

function handleOriginChange(placeId: string) {
  const item = originCache[placeId];
  if (!item) {
    return;
  }
  setOriginFromPlace(item);
  void loadFacilities();
}

function setOriginFromPlace(item: SearchPlaceItem) {
  selectedOrigin.value = {
    id: item.id,
    source: item.source,
    name: item.name,
    lng: item.lng,
    lat: item.lat,
  };
  coordinateOrigin.lng = item.lng;
  coordinateOrigin.lat = item.lat;
}

function handleMapClick(coordinate: Coordinate) {
  originPlaceId.value = "";
  coordinateOrigin.lng = coordinate[0];
  coordinateOrigin.lat = coordinate[1];
  selectedOrigin.value = {
    id: "",
    source: "coordinate",
    name: "地图选点",
    lng: coordinate[0],
    lat: coordinate[1],
  };
  void loadFacilities();
}

function applyCoordinateOrigin() {
  originPlaceId.value = "";
  selectedOrigin.value = {
    id: "",
    source: "coordinate",
    name: "调试坐标",
    lng: coordinateOrigin.lng,
    lat: coordinateOrigin.lat,
  };
  void loadFacilities();
}

async function loadFacilities() {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      radius: String(radius.value),
      limit: "10",
      scene_key: selectedSceneKey.value,
    });
    if (originPlaceId.value) {
      params.set("origin_place_id", originPlaceId.value);
    } else {
      params.set("current_lng", String(selectedOrigin.value.lng));
      params.set("current_lat", String(selectedOrigin.value.lat));
    }
    if (category.value) {
      params.set("category", category.value);
    }
    const payload = await apiGet<NearbyFacilitiesPayload>(`/api/v1/facilities/nearby?${params}`);
    facilities.value = payload.items;
    routePath.value = payload.items[0]?.routePath ?? [];
    if (payload.origin) {
      selectedOrigin.value = payload.origin;
      coordinateOrigin.lng = payload.origin.lng;
      coordinateOrigin.lat = payload.origin.lat;
    }
    error.value = "";
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "附近设施查询失败";
  } finally {
    loading.value = false;
  }
}

async function loadMap() {
  const params = new URLSearchParams({ scene_key: selectedSceneKey.value });
  mapPayload.value = await apiGet<MapGeoJsonPayload>(`/api/v1/map/geojson?${params}`);
}

async function primeOrigin() {
  await searchOrigins(currentScene.value.defaultOriginKeyword);
  const origin = originOptions.value.find((item) => item.name.includes(currentScene.value.defaultOriginKeyword)) ?? originOptions.value[0];
  if (origin) {
    originPlaceId.value = origin.id;
    setOriginFromPlace(origin);
  }
}

function resetSceneState() {
  facilities.value = [];
  routePath.value = [];
  originPlaceId.value = "";
  originOptions.value = [];
  Object.keys(originCache).forEach((key) => delete originCache[key]);
  const [lng, lat] = currentScene.value.center;
  coordinateOrigin.lng = lng;
  coordinateOrigin.lat = lat;
  selectedOrigin.value = {
    id: "",
    source: "coordinate",
    name: currentScene.value.defaultOriginName,
    lng,
    lat,
  };
}

async function loadScene() {
  resetSceneState();
  try {
    await loadMap();
    await searchOrigins("");
    await primeOrigin();
    await loadFacilities();
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "附近设施初始化失败";
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
</style>
