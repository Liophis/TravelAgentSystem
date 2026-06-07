<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>美食推荐</h1>
        <p>按菜系、热度、评分和距离推荐沙河校区美食。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadRecommendations">推荐</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="7">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="关键词">
              <el-input v-model="keyword" clearable placeholder="菜名、菜系、餐厅" @keyup.enter="searchFoods" />
            </el-form-item>
            <el-form-item label="菜系">
              <el-select v-model="cuisine" clearable placeholder="全部菜系">
                <el-option v-for="item in cuisineOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="搜索半径">
              <el-input-number v-model="radius" :min="100" :max="5000" :step="100" />
            </el-form-item>
          </el-form>
          <div class="button-row">
            <el-button @click="searchFoods">搜索</el-button>
            <el-button @click="loadNearby">附近</el-button>
          </div>
        </el-card>

        <el-card shadow="never" class="result-card">
          <div class="stat"><span>餐厅</span><strong>{{ restaurants.length }}</strong></div>
          <div class="stat"><span>结果</span><strong>{{ foods.length }}</strong></div>
          <div class="stat"><span>路线</span><strong>{{ routePath.length > 0 ? "已绘制" : "未选择" }}</strong></div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never">
          <el-table :data="foods" v-loading="loading" size="small">
            <el-table-column prop="name" label="菜品" min-width="136" />
            <el-table-column prop="restaurant_name" label="餐厅" min-width="128" />
            <el-table-column prop="cuisine" label="菜系" width="96" />
            <el-table-column prop="rating" label="评分" width="76" />
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

      <el-col :span="7">
        <AMapView :facilities="foodMarkers" :route-path="routePath" />
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
  type FacilityItem,
  type FoodItem,
  type FoodListPayload,
  type RestaurantItem,
  type RestaurantListPayload,
} from "../services/api";

const loading = ref(false);
const keyword = ref("");
const cuisine = ref("");
const radius = ref(1200);
const restaurants = ref<RestaurantItem[]>([]);
const foods = ref<FoodItem[]>([]);
const cuisines = ref<string[]>([]);
const routePath = ref<Coordinate[]>([]);

const cuisineOptions = computed(() => cuisines.value.length > 0 ? cuisines.value : ["home-style", "noodle", "cafe", "halal", "snack"]);
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
  const payload = await apiGet<RestaurantListPayload>("/api/v1/foods/restaurants?limit=30");
  restaurants.value = payload.items;
}

async function loadItems() {
  const payload = await apiGet<FoodListPayload>("/api/v1/foods/items?limit=30");
  cuisines.value = payload.cuisines ?? [];
}

async function loadRecommendations() {
  loading.value = true;
  try {
    const params = buildBaseParams();
    params.set("limit", "10");
    const payload = await apiGet<FoodListPayload>(`/api/v1/foods/recommend?${params}`);
    foods.value = payload.items;
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
    params.set("limit", "20");
    const payload = await apiGet<FoodListPayload>(`/api/v1/foods/search?${params}`);
    foods.value = payload.items;
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
    routePath.value = payload.items[0]?.routePath ?? [];
  } finally {
    loading.value = false;
  }
}

function buildBaseParams() {
  const params = new URLSearchParams({
    current_lng: "116.28333",
    current_lat: "40.15608",
  });
  if (cuisine.value) {
    params.set("cuisine", cuisine.value);
  }
  return params;
}

onMounted(async () => {
  await Promise.all([loadRestaurants(), loadItems()]);
  await loadRecommendations();
});
</script>

<style scoped>
.button-row {
  display: flex;
  gap: 8px;
}
</style>
