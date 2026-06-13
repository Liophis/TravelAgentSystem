<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>美食推荐</h1>
        <p>选择景点或学校后，按周边餐厅、菜系、热度、评分和距离输出 Top-10。</p>
      </div>
      <div class="heading-actions">
        <el-segmented v-model="sort" :options="sortOptions" />
        <el-button type="primary" :loading="loading" @click="loadRecommendations">推荐</el-button>
      </div>
    </div>

    <el-row :gutter="18" class="food-top-layout">
      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="filter-card control-panel">
          <template #header>
            <div class="panel-header">
              <div>
                <strong>美食筛选</strong>
                <small>{{ selectedDestination?.name ?? "全部目的地" }}</small>
              </div>
              <el-tag effect="plain">{{ sortLabel(lastTrace?.sort ?? sort) }}</el-tag>
            </div>
          </template>
          <el-form label-position="top">
            <el-form-item label="关键词">
              <el-input v-model="keyword" clearable placeholder="餐厅、菜系、地址或窗口" @keyup.enter="searchFoods" />
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
          <div class="summary-grid">
            <div><span>餐厅</span><strong>{{ restaurants.length }}</strong></div>
            <div><span>结果</span><strong>{{ foods.length }}</strong></div>
            <div><span>候选</span><strong>{{ lastTrace?.candidate_count ?? totalCandidates }}</strong></div>
            <div><span>排序</span><strong>{{ sortLabel(lastTrace?.sort ?? sort) }}</strong></div>
            <div><span>来源</span><strong>{{ sourceLabel }}</strong></div>
            <div><span>路线</span><strong>{{ routePath.length > 0 ? "已绘制" : "未选择" }}</strong></div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <div class="map-workspace">
          <div class="map-workspace-header">
            <div>
              <h2>餐厅位置与路线预览</h2>
              <p v-if="selectedDestinationId">
                基于目的地：{{ selectedDestination?.name }} 的推荐
              </p>
              <p v-else-if="selectedLocationName">
                基于位置：{{ selectedLocationName }} 的附近推荐
                <small v-if="foods.length > 0 && foods[0]?.restaurant_source === 'amap_realtime'">
                  (实时 nationwide 数据)
                </small>
                <small>（点击地图可更改位置）</small>
              </p>
              <p v-else>
                基于地图选点的附近推荐
                <small>（点击地图选择位置，支持全国）</small>
              </p>
            </div>
            <div class="workspace-actions">
              <span class="data-chip">{{ foodMarkers.length }} 餐厅</span>
              <span class="data-chip">{{ routePath.length > 0 ? "已绘制路线" : "待选路线" }}</span>
            </div>
          </div>
          <AMapView
            v-if="foods.length > 0 || loading"
            :facilities="foodMarkers"
            :route-path="routePath"
            :selected-point="selectedDestinationId ? null : [currentLng, currentLat]"
            @map-click="onMapClick"
          />

          <!-- 空结果提示 -->
          <div v-else-if="!loading && foods.length === 0 && !selectedDestinationId" class="no-result-notice">
            <el-empty description="当前位置附近暂无餐厅数据">
              <template #default>
                <p class="no-result-tip">
                  该位置附近未找到餐厅，请尝试：<br />
                  1. 扩大搜索半径<br />
                  2. 选择其他城市的位置（支持全国实时搜索）<br />
                  3. 点击下方的北京目的地查看示例数据
                </p>
                <el-button type="primary" @click="goToBeijing">
                  切换到北邮沙河校区
                </el-button>
              </template>
            </el-empty>
          </div>

          <AMapView
            v-else
            :facilities="foodMarkers"
            :route-path="routePath"
            :selected-point="selectedDestinationId ? null : [currentLng, currentLat]"
            @map-click="onMapClick"
          />
          <div class="map-mode-toggle">
            <el-radio-group v-model="selectedDestinationId" @change="onDestinationChange">
              <el-radio-button :label="null">📍 地图选点模式</el-radio-button>
              <el-radio-button v-for="d in destinationOptions.slice(0, 5)" :key="d.id" :label="d.id">
                {{ d.name.slice(0, 8) }}
              </el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <el-card v-if="lastTrace" shadow="never" class="result-card">
          <template #header>算法记录</template>
          <p class="trace-line">{{ lastTrace.algorithm }}</p>
          <p class="trace-line">{{ lastTrace.ranking }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="18" class="food-bottom-layout">
      <el-col :xs="24" :lg="8">
        <el-card shadow="never">
          <template #header>特色店铺</template>
          <div class="restaurant-list">
            <article v-for="restaurant in featuredRestaurants" :key="restaurant.id" class="restaurant-card">
              <div class="food-cover small" :class="cuisineClass(restaurant.cuisines[0] ?? restaurant.category)">
                <span>{{ cuisineShortLabel(restaurant.cuisines[0] ?? restaurant.category) }}</span>
              </div>
              <div>
                <h3>{{ restaurant.name }}</h3>
                <p>{{ restaurant.address || restaurant.category || "目的地周边餐厅" }}</p>
                <div class="tag-row">
                  <el-tag v-for="item in restaurant.cuisines.slice(0, 3)" :key="item" size="small" effect="plain">
                    {{ item }}
                  </el-tag>
                  <el-tag v-if="restaurant.source === 'amap'" size="small" type="success" effect="plain">高德</el-tag>
                </div>
              </div>
            </article>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card shadow="never" class="food-results-card">
          <template #header>
            <div class="panel-header">
              <div>
                <strong>推荐结果</strong>
                <small>{{ selectedDestination?.name ?? "全部目的地" }} · {{ sortLabel(lastTrace?.sort ?? sort) }}</small>
              </div>
              <el-tag effect="plain">{{ foods.length }} 项</el-tag>
            </div>
          </template>
          <div v-loading="loading" class="food-grid">
            <article v-for="food in foods" :key="food.id" class="food-card">
              <div class="food-cover" :class="cuisineClass(food.cuisine)">
                <span>{{ cuisineShortLabel(food.cuisine) }}</span>
              </div>
              <div class="food-content">
                <div class="food-heading">
                  <div>
                    <h2>{{ food.restaurant_name }}</h2>
                    <p>{{ food.name }}</p>
                  </div>
                  <strong>¥{{ food.price }}</strong>
                </div>
                <div class="tag-row">
                  <el-tag size="small" effect="plain">{{ food.cuisine }}</el-tag>
                  <el-tag size="small" :type="food.restaurant_source === 'amap' ? 'success' : 'info'" effect="plain">
                    {{ food.restaurant_source === "amap" ? "高德真实 POI" : "Seed" }}
                  </el-tag>
                </div>
                <p class="food-address">{{ food.restaurant_address || food.reason || "暂无地址说明" }}</p>
                <div class="food-metrics">
                  <span>评分 {{ food.rating }}</span>
                  <span>热度 {{ food.heat }}</span>
                  <span>得分 {{ food.score ? food.score.toFixed(3) : "-" }}</span>
                  <span>{{ food.distance ? `${food.distance}m` : "距离待计算" }}</span>
                </div>
                <div class="food-actions">
                  <el-button size="small" :disabled="!food.routePath" @click="routePath = food.routePath ?? []">
                    绘制路线
                  </el-button>
                </div>
              </div>
            </article>
            <el-empty v-if="!loading && foods.length === 0" description="没有匹配的美食结果" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import AMapView from "../components/AMapView.vue";
import { reverseGeocode } from "../utils/amap";
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
const selectedLocationName = ref(""); // 新增：选中的地点名称

const cuisineOptions = computed(() =>
  cuisines.value.length > 0
    ? cuisines.value
    : ["中餐", "地方菜", "小吃快餐", "咖啡茶饮", "面食粉类", "火锅烧烤"],
);
const selectedDestination = computed(() =>
  destinationOptions.value.find((destination) => destination.id === selectedDestinationId.value) ?? null,
);
const sourceLabel = computed(() => {
  if (foods.value.some((food) => food.restaurant_source === "amap")) return "真实 POI";
  return "离线兜底";
});
const featuredRestaurants = computed(() => restaurants.value.slice(0, 6));
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
    description: food.restaurant_address ?? food.reason ?? `评分 ${food.rating}，热度 ${food.heat}`,
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
  const summerPalace = payload.items.find((item) => item.name.includes("颐和园"));
  const bupt = payload.items.find((item) => item.name.includes("北京邮电大学沙河校区"));
  selectedDestinationId.value = summerPalace?.id ?? bupt?.id ?? payload.items[0]?.id ?? null;
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

async function onMapClick(coordinate: Coordinate, gcjCoordinate: Coordinate) {
  // 清除目的地选择，使用坐标模式
  selectedDestinationId.value = null;
  currentLng.value = coordinate[0];
  currentLat.value = coordinate[1];

  // 显示加载状态
  selectedLocationName.value = "正在获取位置信息...";

  try {
    // 使用 GCJ02 坐标进行逆地理编码（高德 API 需要 GCJ02）
    const addressInfo = await reverseGeocode(gcjCoordinate[0], gcjCoordinate[1]);
    if (addressInfo) {
      // 优先显示 formattedAddress，如果太长则截取
      const address = addressInfo.formattedAddress || addressInfo.address;
      selectedLocationName.value = address.length > 30 ? address.slice(0, 30) + "..." : address;
    } else {
      selectedLocationName.value = "未知位置";
    }
  } catch (error) {
    console.error("获取地址失败:", error);
    selectedLocationName.value = "位置获取失败";
  }

  // 调用实时API获取全国美食
  await loadRealtimeRecommendations();
}

async function loadRealtimeRecommendations() {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      current_lng: String(currentLng.value),
      current_lat: String(currentLat.value),
      radius: String(radius.value),
      limit: "20",
    });
    if (cuisine.value) {
      params.set("cuisine", cuisine.value);
    }

    const payload = await apiGet<FoodListPayload>(`/api/v1/foods/realtime?${params}`);

    if (payload.error) {
      console.error("实时搜索失败:", payload.error);
      foods.value = [];
      totalCandidates.value = 0;
    } else {
      foods.value = payload.items;
      totalCandidates.value = payload.total;

      // 如果有菜品，使用第一个菜品的坐标来更新位置名称
      if (payload.items.length > 0 && !selectedLocationName.value.includes("市")) {
        const firstItem = payload.items[0];
        if (firstItem.restaurant_address) {
          const cityMatch = firstItem.restaurant_address.match(/^([^省]+省)?([^市]+市)?/);
          if (cityMatch) {
            const location = cityMatch[2] || cityMatch[1] || "当前位置";
            selectedLocationName.value = location + "附近";
          }
        }
      }
    }

    lastTrace.value = payload.algorithm_trace ?? null;
    routePath.value = [];
  } finally {
    loading.value = false;
  }
}

function onDestinationChange() {
  if (selectedDestinationId.value) {
    selectedLocationName.value = ""; // 清除地图选点的位置名称
    useDestinationCenter();
  }
  reloadScopedFood();
}

function goToBeijing() {
  // 切换到北邮沙河校区
  const bupt = destinationOptions.value.find((item) => item.name.includes("北京邮电大学沙河校区"));
  if (bupt) {
    selectedDestinationId.value = bupt.id;
    selectedLocationName.value = "";
    useDestinationCenter();
    reloadScopedFood();
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

function cuisineClass(value?: string | null) {
  const text = value ?? "";
  if (/咖啡|茶|饮|甜/.test(text)) return "cuisine-drink";
  if (/火锅|烧烤|烤|串/.test(text)) return "cuisine-grill";
  if (/面|粉|饺|包/.test(text)) return "cuisine-noodle";
  if (/西|披萨|汉堡|快餐/.test(text)) return "cuisine-western";
  if (/地方|川|湘|鲁|粤|京|江浙/.test(text)) return "cuisine-local";
  return "cuisine-chinese";
}

function cuisineShortLabel(value?: string | null) {
  const text = (value || "美食").replace(/\s+/g, "");
  return text.length > 4 ? text.slice(0, 4) : text;
}

function buildBaseParams() {
  const params = new URLSearchParams({
    current_lng: String(currentLng.value),
    current_lat: String(currentLat.value),
  });
  // 只有在选择了目的地时才传递 destination_id
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
.food-top-layout,
.food-bottom-layout {
  align-items: start;
}

.food-bottom-layout {
  margin-top: 2px;
}

.button-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.summary-grid div {
  min-height: 72px;
  padding: 12px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: #f9fafb;
}

.summary-grid span {
  display: block;
  color: #667085;
  font-size: 12px;
}

.summary-grid strong {
  display: block;
  margin-top: 8px;
  color: #101828;
  font-size: 18px;
  overflow-wrap: anywhere;
}

.panel-header,
.food-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-header strong {
  display: block;
  color: #101828;
  font-size: 16px;
}

.panel-header small {
  display: block;
  margin-top: 4px;
  color: #667085;
  font-size: 13px;
}

.restaurant-list {
  display: grid;
  gap: 12px;
}

.restaurant-card {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.restaurant-card h3,
.food-heading h2 {
  margin: 0;
  color: #101828;
  font-size: 15px;
  line-height: 1.35;
}

.restaurant-card p,
.food-heading p,
.food-address {
  margin: 5px 0 0;
  color: #667085;
  font-size: 13px;
  line-height: 1.5;
}

.food-results-card {
  min-height: 520px;
}

.food-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.food-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 14px;
  padding: 14px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff, #fcfcfd);
  transition:
    border-color 0.16s ease,
    box-shadow 0.16s ease,
    transform 0.16s ease;
}

.food-card:hover {
  border-color: #87d0c6;
  box-shadow: 0 12px 28px rgba(16, 24, 40, 0.08);
  transform: translateY(-1px);
}

.food-cover {
  display: grid;
  place-items: center;
  min-height: 170px;
  border-radius: 8px;
  color: #fff;
  font-weight: 900;
  letter-spacing: 0;
  overflow: hidden;
  position: relative;
  background-image: url("/images/food-cuisine-collage.png");
  background-repeat: no-repeat;
  background-size: 300% 200%;
  box-shadow: inset 0 -40px 70px rgba(16, 24, 40, 0.18);
}

.food-cover::before {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 22% 20%, rgba(255, 255, 255, 0.34), transparent 24%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent 46%);
  content: "";
}

.food-cover::after {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 35%, rgba(16, 24, 40, 0.48));
  content: "";
}

.food-cover span {
  align-self: end;
  justify-self: start;
  z-index: 1;
  margin: 0 0 12px 12px;
  padding: 8px 10px;
  border-radius: 999px;
  background: rgba(16, 24, 40, 0.62);
  font-size: 16px;
  text-align: center;
}

.food-cover.small {
  min-height: 76px;
}

.food-cover.small span {
  font-size: 13px;
}

.cuisine-chinese {
  background-position: 0 0;
}

.cuisine-local {
  background-position: 50% 0;
}

.cuisine-drink {
  background-position: 100% 0;
}

.cuisine-grill {
  background-position: 0 100%;
}

.cuisine-noodle {
  background-position: 50% 100%;
}

.cuisine-western {
  background-position: 100% 100%;
}

.food-content {
  display: grid;
  gap: 10px;
}

.food-heading strong {
  color: #b8323a;
  font-size: 18px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.food-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.food-metrics span {
  min-height: 34px;
  padding: 8px;
  border-radius: 8px;
  background: #f9fafb;
  color: #475467;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
}

.food-actions {
  display: flex;
  justify-content: flex-end;
}

.trace-line {
  margin: 0 0 8px;
  color: #475467;
  line-height: 1.6;
}

.map-mode-toggle {
  margin-top: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  text-align: center;
}

.map-mode-toggle :deep(.el-radio-group) {
  flex-wrap: wrap;
  justify-content: center;
}

.no-result-notice {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px dashed #d0d5dd;
}

.no-result-tip {
  color: #667085;
  font-size: 14px;
  line-height: 1.6;
  margin: 16px 0;
  text-align: center;
}

@media (max-width: 1200px) {
  .food-results-card {
    min-height: auto;
  }

  .food-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 720px) {
  .restaurant-card {
    grid-template-columns: minmax(0, 1fr);
  }

  .summary-grid,
  .food-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .food-cover {
    min-height: 150px;
  }
}
</style>
