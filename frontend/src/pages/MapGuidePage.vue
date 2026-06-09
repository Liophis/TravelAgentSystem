<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>地图与目的地</h1>
        <p>可切换全国景点/学校 POI 浏览，或查看校区、景区内部道路、建筑和设施图层。</p>
      </div>
      <div class="heading-actions">
        <el-segmented v-model="viewMode" :options="viewModeOptions" />
        <el-segmented v-if="viewMode === 'scene'" v-model="selectedSceneKey" :options="sceneSegmentOptions" />
        <el-select
          v-if="viewMode === 'scene'"
          v-model="facilityCategory"
          placeholder="设施类别"
          clearable
          class="category-select"
        >
          <el-option
            v-for="item in categories"
            :key="item"
            :label="item"
            :value="item"
          />
        </el-select>
        <el-select
          v-if="viewMode === 'destinations'"
          v-model="destinationCategory"
          placeholder="目的地类别"
          clearable
          class="category-select"
        >
          <el-option
            v-for="item in destinationCategoryOptions"
            :key="item"
            :label="destinationCategoryLabel(item)"
            :value="item"
          />
        </el-select>
        <el-input
          v-if="viewMode === 'destinations'"
          v-model="destinationKeyword"
          clearable
          placeholder="搜索景点或学校"
          class="keyword-input"
          @keyup.enter="loadDestinationPois"
        />
        <el-button v-if="viewMode === 'destinations'" type="primary" :loading="loading" @click="loadDestinationPois">
          查询
        </el-button>
      </div>
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon />

    <el-row :gutter="16">
      <el-col :span="6">
        <el-card v-if="viewMode === 'scene'" shadow="never" class="stats-card">
          <div class="stat"><span>道路</span><strong>{{ payload?.statistics.roads ?? "-" }}</strong></div>
          <div class="stat"><span>建筑</span><strong>{{ payload?.statistics.buildings ?? "-" }}</strong></div>
          <div class="stat"><span>设施</span><strong>{{ filteredFacilities.length }}</strong></div>
          <div class="stat"><span>类别</span><strong>{{ payload?.statistics.categories ?? "-" }}</strong></div>
          <div class="stat"><span>隐藏演示建筑</span><strong>{{ payload?.statistics.hidden_demo_buildings ?? "-" }}</strong></div>
          <div class="stat"><span>隐藏演示道路</span><strong>{{ payload?.statistics.hidden_demo_roads ?? "-" }}</strong></div>
        </el-card>
        <el-card v-else shadow="never" class="stats-card">
          <div class="stat"><span>POI</span><strong>{{ destinationMarkers.length }}</strong></div>
          <div class="stat"><span>景区</span><strong>{{ destinationTypeCount.scenic }}</strong></div>
          <div class="stat"><span>学校</span><strong>{{ destinationTypeCount.school }}</strong></div>
          <div class="stat"><span>排序</span><strong>{{ destinationSortLabel }}</strong></div>
          <el-segmented v-model="destinationSort" :options="destinationSortOptions" @change="loadDestinationPois" />
          <el-divider />
          <el-table :data="destinations" size="small" height="300" @row-click="selectDestination">
            <el-table-column prop="name" label="名称" min-width="120" />
            <el-table-column label="类别" width="72">
              <template #default="{ row }">{{ destinationCategoryLabel(row.category) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
        <el-card v-if="viewMode === 'destinations' && selectedDestination" shadow="never" class="result-card">
          <h2>{{ selectedDestination.name }}</h2>
          <div class="stat"><span>类别</span><strong>{{ destinationCategoryLabel(selectedDestination.category) }}</strong></div>
          <div class="stat"><span>评分</span><strong>{{ selectedDestination.rating }}</strong></div>
          <div class="stat"><span>热度</span><strong>{{ selectedDestination.popularity }}</strong></div>
          <p class="destination-description">{{ selectedDestination.description }}</p>
          <el-tag v-for="tag in selectedDestination.tags" :key="tag" class="tag-item">{{ tag }}</el-tag>
          <el-divider />
          <el-rate v-model="ratingValue" allow-half />
          <div class="button-row">
            <el-button size="small" @click="favoriteSelected">收藏</el-button>
            <el-button size="small" type="primary" @click="rateSelected">评分</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="18">
        <AMapView
          v-loading="loading"
          :road-paths="activeRoadPaths"
          :buildings="activeBuildings"
          :facilities="activeFacilities"
          :center="activeCenter"
          @facility-click="handleMarkerClick"
        />
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";

import AMapView from "../components/AMapView.vue";
import {
  apiGet,
  apiPost,
  type BuildingItem,
  type DestinationItem,
  type DestinationListPayload,
  type FacilityItem,
  type MapGeoJsonPayload,
} from "../services/api";
import { authState } from "../services/auth";

const payload = ref<MapGeoJsonPayload | null>(null);
const destinations = ref<DestinationItem[]>([]);
const facilityCategory = ref("");
const destinationCategory = ref("");
const destinationKeyword = ref("");
const destinationSort = ref("popularity");
const selectedDestination = ref<DestinationItem | null>(null);
const ratingValue = ref(5);
const error = ref("");
const loading = ref(false);
const viewMode = ref<"scene" | "destinations">("destinations");
const selectedSceneKey = ref("bupt_shahe");
const scenes = [
  { key: "bupt_shahe", label: "北邮沙河", center: [116.28333, 40.15608] as [number, number] },
  { key: "summer_palace", label: "颐和园", center: [116.2755, 39.9996] as [number, number] },
];

const viewModeOptions = [
  { label: "景点/学校 POI", value: "destinations" },
  { label: "内部地图", value: "scene" },
];
const destinationSortOptions = [
  { label: "热度", value: "popularity" },
  { label: "评分", value: "rating" },
  { label: "名称", value: "name" },
];
const destinationCategoryOptions = ["scenic", "school"];
const currentScene = computed(() => scenes.find((scene) => scene.key === selectedSceneKey.value) ?? scenes[0]);
const sceneSegmentOptions = scenes.map((scene) => ({ label: scene.label, value: scene.key }));
const categories = computed(() => payload.value?.facility_categories ?? []);
const roadPaths = computed(() => payload.value?.roads.map((road) => road.path) ?? []);
const filteredFacilities = computed<FacilityItem[]>(() => {
  const facilities = payload.value?.facilities ?? [];
  if (!facilityCategory.value) return facilities;
  return facilities.filter((item) => item.category === facilityCategory.value);
});
const destinationMarkers = computed<FacilityItem[]>(() =>
  destinations.value.map((destination) => ({
    id: `destination-${destination.id}`,
    name: destination.name,
    category: destinationCategoryLabel(destination.category),
    category_name: destinationCategoryLabel(destination.category),
    lng: destination.lng,
    lat: destination.lat,
    description: `评分 ${destination.rating} · 热度 ${destination.popularity}`,
  })),
);
const destinationTypeCount = computed(() => ({
  scenic: destinations.value.filter((destination) => destination.category !== "school").length,
  school: destinations.value.filter((destination) => destination.category === "school").length,
}));
const destinationSortLabel = computed(() => {
  const option = destinationSortOptions.find((item) => item.value === destinationSort.value);
  return option?.label ?? "热度";
});
const activeRoadPaths = computed(() => (viewMode.value === "scene" ? roadPaths.value : []));
const activeBuildings = computed<BuildingItem[]>(() =>
  viewMode.value === "scene" ? payload.value?.buildings ?? [] : [],
);
const activeFacilities = computed<FacilityItem[]>(() =>
  viewMode.value === "scene" ? filteredFacilities.value : destinationMarkers.value,
);
const activeCenter = computed<[number, number]>(() =>
  viewMode.value === "scene" ? payload.value?.center ?? currentScene.value.center : [104.1954, 35.8617],
);

async function loadMap() {
  try {
    loading.value = true;
    facilityCategory.value = "";
    const params = new URLSearchParams({ scene_key: selectedSceneKey.value });
    payload.value = await apiGet<MapGeoJsonPayload>(`/api/v1/map/geojson?${params}`);
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "地图数据加载失败";
  } finally {
    loading.value = false;
  }
}

async function loadDestinationPois() {
  try {
    loading.value = true;
    error.value = "";
    const collected: DestinationItem[] = [];
    let offset = 0;
    let total = Number.POSITIVE_INFINITY;
    while (offset < total) {
      const params = new URLSearchParams({
        sort: destinationSort.value,
        limit: "100",
        offset: String(offset),
      });
      if (destinationCategory.value) {
        params.set("category", destinationCategory.value);
      }
      if (destinationKeyword.value.trim()) {
        params.set("q", destinationKeyword.value.trim());
      }
      const response = await apiGet<DestinationListPayload>(`/api/v1/destinations?${params}`);
      collected.push(...response.items);
      total = response.total;
      offset += response.items.length;
      if (response.items.length === 0) break;
    }
    destinations.value = collected;
    selectedDestination.value = collected[0] ?? null;
    ratingValue.value = selectedDestination.value?.rating ?? 5;
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "目的地 POI 加载失败";
  } finally {
    loading.value = false;
  }
}

function selectDestination(destination: DestinationItem) {
  selectedDestination.value = destination;
  ratingValue.value = destination.rating;
  void recordDestinationView(destination.id);
}

function handleMarkerClick(facility: FacilityItem) {
  if (!facility.id.startsWith("destination-")) return;
  const destinationId = Number(facility.id.replace("destination-", ""));
  const destination = destinations.value.find((item) => item.id === destinationId);
  if (destination) {
    selectDestination(destination);
  }
}

async function favoriteSelected() {
  if (!selectedDestination.value || !authState.user) return;
  await apiPost(`/api/v1/users/${authState.user.id}/favorites`, {
    target_type: "destination",
    target_id: selectedDestination.value.id,
    note: "地图与目的地页收藏",
  });
  ElMessage.success("已收藏，推荐会读取该行为");
}

async function rateSelected() {
  if (!selectedDestination.value || !authState.user) return;
  await apiPost(`/api/v1/users/${authState.user.id}/ratings`, {
    target_type: "destination",
    target_id: selectedDestination.value.id,
    rating: ratingValue.value,
  });
  await loadDestinationPois();
  ElMessage.success("评分已更新");
}

async function recordDestinationView(destinationId: number) {
  if (!authState.user) return;
  await apiPost(`/api/v1/users/${authState.user.id}/behavior`, {
    target_type: "destination",
    target_id: destinationId,
    action: "view",
    metadata_text: "map destination poi click",
  });
}

function destinationCategoryLabel(category: string) {
  return category === "school" ? "学校" : "景区";
}

watch(selectedSceneKey, () => {
  void loadMap();
});

watch(viewMode, (nextMode) => {
  if (nextMode === "scene" && !payload.value) {
    void loadMap();
  }
  if (nextMode === "destinations" && destinations.value.length === 0) {
    void loadDestinationPois();
  }
});

onMounted(async () => {
  await loadDestinationPois();
  await loadMap();
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

.keyword-input {
  width: 220px;
}

.destination-description {
  color: #667085;
  line-height: 1.7;
}

.tag-item {
  margin: 0 6px 6px 0;
}

.button-row {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
</style>
