<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>美食推荐</h1>
        <p>选择景点或学校范围后，按菜系、热度、评分和距离输出 Top-10 美食。</p>
      </div>
      <div class="heading-actions">
        <el-segmented v-model="sort" :options="sortOptions" />
        <el-button type="primary" :loading="loading" @click="loadRecommendations">推荐</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="7">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="关键词">
              <el-input v-model="keyword" clearable placeholder="菜名、菜系、饭店或窗口" @keyup.enter="searchFoods" />
            </el-form-item>
            <el-form-item label="目的地范围">
              <el-select v-model="selectedDestinationId" clearable placeholder="全部目的地" @change="reloadScopedFood">
                <el-option
                  v-for="item in destinationOptions"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="菜系">
              <el-select v-model="cuisine" clearable placeholder="全部菜系">
                <el-option v-for="item in cuisineOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="搜索半径">
              <el-input-number v-model="radius" :min="100" :max="5000" :step="100" />
            </el-form-item>
            <el-collapse class="advanced-panel">
              <el-collapse-item title="当前位置" name="current-location">
                <el-form-item label="经度">
                  <el-input-number v-model="currentLng" :precision="6" :step="0.0001" />
                </el-form-item>
                <el-form-item label="纬度">
                  <el-input-number v-model="currentLat" :precision="6" :step="0.0001" />
                </el-form-item>
                <el-button :disabled="!selectedDestination" @click="useDestinationCenter">使用目的地中心</el-button>
              </el-collapse-item>
            </el-collapse>
          </el-form>
          <div class="button-row">
            <el-button type="primary" plain @click="searchFoods">模糊搜索</el-button>
            <el-button @click="loadNearby">附近 Top-10</el-button>
          </div>
        </el-card>

        <el-card shadow="never" class="result-card">
          <div class="stat"><span>餐厅</span><strong>{{ restaurants.length }}</strong></div>
          <div class="stat"><span>结果</span><strong>{{ foods.length }}</strong></div>
          <div class="stat"><span>候选</span><strong>{{ lastTrace?.candidate_count ?? totalCandidates }}</strong></div>
          <div class="stat"><span>排序</span><strong>{{ sortLabel(lastTrace?.sort ?? sort) }}</strong></div>
          <div class="stat"><span>路线</span><strong>{{ routePath.length > 0 ? "已绘制" : "未选择" }}</strong></div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never">
          <el-table :data="foods" v-loading="loading" size="small">
            <el-table-column prop="name" label="菜品" min-width="136" />
            <el-table-column prop="restaurant_name" label="饭店/窗口" min-width="128" />
            <el-table-column prop="cuisine" label="菜系" width="96" />
            <el-table-column prop="score" label="得分" width="82">
              <template #default="{ row }">{{ row.score ? row.score.toFixed(3) : "-" }}</template>
            </el-table-column>
            <el-table-column prop="rating" label="评分" width="76" />
            <el-table-column prop="heat" label="热度" width="76" />
            <el-table-column prop="distance" label="距离" width="88">
              <template #default="{ row }">{{ row.distance ? `${row.distance}m` : "-" }}</template>
            </el-table-column>
            <el-table-column prop="price" label="价格" width="76">
              <template #default="{ row }">¥{{ row.price }}</template>
            </el-table-column>
            <el-table-column label="路线" width="76">
              <template #default="{ row }">
                <el-button link type="primary" :disabled="!row.routePath" @click="routePath = row.routePath ?? []">
                  绘制
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="7">
        <AMapView :facilities="foodMarkers" :route-path="routePath" />
        <el-card v-if="lastTrace" shadow="never" class="result-card">
          <template #header>算法记录</template>
          <p class="trace-line">{{ lastTrace.algorithm }}</p>
          <p class="trace-line">{{ lastTrace.ranking }}</p>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import AMapView from "../components/AMapView.vue";
import {
  apiGet,
  type Coordinate,
  type DestinationItem,
  type DestinationListPayload,
  type FacilityItem,
  type FoodItem,
  type FoodListPayload,
  type RestaurantItem,
  type RestaurantListPayload,
} from "../services/api";

const loading = ref(false);
const keyword = ref("");
const cuisine = ref("");
const sort = ref("composite");
const radius = ref(1200);
const restaurants = ref<RestaurantItem[]>([]);
const foods = ref<FoodItem[]>([]);
const cuisines = ref<string[]>([]);
const routePath = ref<Coordinate[]>([]);
const destinationOptions = ref<DestinationItem[]>([]);
const selectedDestinationId = ref<number | null>(1);
const lastTrace = ref<Record<string, string> | null>(null);
const totalCandidates = ref(0);
const currentLng = ref(116.28333);
const currentLat = ref(40.15608);

const cuisineOptions = computed(() => cuisines.value.length > 0 ? cuisines.value : ["home-style", "noodle", "cafe", "halal", "snack"]);
const selectedDestination = computed(() =>
  destinationOptions.value.find((destination) => destination.id === selectedDestinationId.value) ?? null,
);
const sortOptions = [
  { label: "综合", value: "composite" },
  { label: "匹配", value: "match" },
  { label: "热度", value: "hot" },
  { label: "评分", value: "rating" },
  { label: "距离", value: "distance" },
];
const foodMarkers = computed<FacilityItem[]>(() =>
  foods.value.map((food) => ({
    id: `food-${food.id}`,
    name: `${food.restaurant_name} · ${food.name}`,
    category: food.cuisine,
    category_name: food.cuisine,
    lng: food.restaurant_lng,
    lat: food.restaurant_lat,
    description: food.reason ?? `评分 ${food.rating}，热度 ${food.heat}`,
    distance: food.distance,
    duration: food.duration,
    routePath: food.routePath,
    node_ids: food.node_ids,
  })),
);

async function loadRestaurants() {
  const params = new URLSearchParams({ limit: "30" });
  if (selectedDestinationId.value) {
    params.set("destination_id", String(selectedDestinationId.value));
  }
  const payload = await apiGet<RestaurantListPayload>(`/api/v1/foods/restaurants?${params}`);
  restaurants.value = payload.items;
}

async function loadItems() {
  const params = new URLSearchParams({ limit: "30" });
  if (selectedDestinationId.value) {
    params.set("destination_id", String(selectedDestinationId.value));
  }
  const payload = await apiGet<FoodListPayload>(`/api/v1/foods/items?${params}`);
  cuisines.value = payload.cuisines ?? [];
}

async function loadDestinations() {
  const payload = await apiGet<DestinationListPayload>("/api/v1/destinations?limit=100&sort=popularity");
  destinationOptions.value = payload.items;
  const bupt = payload.items.find((item) => item.name.includes("北京邮电大学沙河校区"));
  selectedDestinationId.value = bupt?.id ?? payload.items[0]?.id ?? null;
  useDestinationCenter();
}

async function loadRecommendations() {
  loading.value = true;
  try {
    const params = buildBaseParams();
    params.set("limit", "10");
    params.set("sort", sort.value === "match" ? "composite" : sort.value);
    const payload = await apiGet<FoodListPayload>(`/api/v1/foods/recommend?${params}`);
    foods.value = payload.items;
    totalCandidates.value = payload.total;
    lastTrace.value = payload.algorithm_trace ?? null;
    routePath.value = [];
  } finally {
    loading.value = false;
  }
}

async function searchFoods() {
  if (!keyword.value.trim()) {
    await loadRecommendations();
    return;
  }
  loading.value = true;
  try {
    const params = buildBaseParams();
    params.set("q", keyword.value.trim());
    params.set("sort", sort.value);
    params.set("limit", "20");
    const payload = await apiGet<FoodListPayload>(`/api/v1/foods/search?${params}`);
    foods.value = payload.items;
    totalCandidates.value = payload.total;
    lastTrace.value = payload.algorithm_trace ?? null;
    routePath.value = [];
  } finally {
    loading.value = false;
  }
}

async function loadNearby() {
  loading.value = true;
  try {
    const params = buildBaseParams();
    params.set("radius", String(radius.value));
    params.set("limit", "10");
    const payload = await apiGet<FoodListPayload>(`/api/v1/foods/nearby?${params}`);
    foods.value = payload.items;
    totalCandidates.value = payload.total;
    lastTrace.value = payload.algorithm_trace ?? null;
    routePath.value = payload.items[0]?.routePath ?? [];
  } finally {
    loading.value = false;
  }
}

function sortLabel(value: string) {
  return {
    composite: "综合",
    match: "匹配",
    hot: "热度",
    rating: "评分",
    distance: "距离",
  }[value] ?? value;
}

function buildBaseParams() {
  const params = new URLSearchParams({
    current_lng: String(currentLng.value),
    current_lat: String(currentLat.value),
  });
  if (selectedDestinationId.value) {
    params.set("destination_id", String(selectedDestinationId.value));
  }
  if (cuisine.value) {
    params.set("cuisine", cuisine.value);
  }
  return params;
}

function useDestinationCenter() {
  if (!selectedDestination.value) return;
  currentLng.value = selectedDestination.value.lng;
  currentLat.value = selectedDestination.value.lat;
}

async function reloadScopedFood() {
  useDestinationCenter();
  await Promise.all([loadRestaurants(), loadItems()]);
  await loadRecommendations();
}

onMounted(async () => {
  await loadDestinations();
  await Promise.all([loadRestaurants(), loadItems()]);
  await loadRecommendations();
});
</script>

<style scoped>
.button-row {
  display: flex;
  gap: 8px;
}

.trace-line {
  margin: 0 0 8px;
  color: #475467;
  line-height: 1.6;
}
</style>
