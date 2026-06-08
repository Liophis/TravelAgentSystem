<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>地图导览</h1>
        <p>高德地图负责展示，后端提供真实优先的道路、OSM 建筑和高德/OSM 设施图层。</p>
      </div>
      <el-select v-model="category" placeholder="设施类别" clearable class="category-select">
        <el-option
          v-for="item in categories"
          :key="item"
          :label="item"
          :value="item"
        />
      </el-select>
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon />

    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="never" class="stats-card">
          <div class="stat"><span>道路</span><strong>{{ payload?.statistics.roads ?? "-" }}</strong></div>
          <div class="stat"><span>建筑</span><strong>{{ payload?.statistics.buildings ?? "-" }}</strong></div>
          <div class="stat"><span>设施</span><strong>{{ filteredFacilities.length }}</strong></div>
          <div class="stat"><span>类别</span><strong>{{ payload?.statistics.categories ?? "-" }}</strong></div>
          <div class="stat"><span>隐藏演示建筑</span><strong>{{ payload?.statistics.hidden_demo_buildings ?? "-" }}</strong></div>
          <div class="stat"><span>隐藏演示道路</span><strong>{{ payload?.statistics.hidden_demo_roads ?? "-" }}</strong></div>
        </el-card>
      </el-col>
      <el-col :span="18">
        <AMapView
          :road-paths="roadPaths"
          :buildings="payload?.buildings ?? []"
          :facilities="filteredFacilities"
        />
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import AMapView from "../components/AMapView.vue";
import { apiGet, type FacilityItem, type MapGeoJsonPayload } from "../services/api";

const payload = ref<MapGeoJsonPayload | null>(null);
const category = ref("");
const error = ref("");

const categories = computed(() => payload.value?.facility_categories ?? []);
const roadPaths = computed(() => payload.value?.roads.map((road) => road.path) ?? []);
const filteredFacilities = computed<FacilityItem[]>(() => {
  const facilities = payload.value?.facilities ?? [];
  if (!category.value) return facilities;
  return facilities.filter((item) => item.category === category.value);
});

onMounted(async () => {
  try {
    payload.value = await apiGet<MapGeoJsonPayload>("/api/v1/map/geojson");
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "地图数据加载失败";
  }
});
</script>
