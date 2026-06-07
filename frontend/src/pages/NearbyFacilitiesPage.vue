<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>附近设施</h1>
        <p>按类别查询附近设施，后续替换为 OSM 道路最短路径距离排序。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadFacilities">查询</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="7">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="设施类别">
              <el-select v-model="category" clearable placeholder="全部类别">
                <el-option label="toilet" value="toilet" />
                <el-option label="water" value="water" />
                <el-option label="shop" value="shop" />
              </el-select>
            </el-form-item>
            <el-form-item label="搜索半径">
              <el-input-number v-model="radius" :min="100" :max="3000" :step="100" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never" class="result-card">
          <el-table :data="facilities" size="small">
            <el-table-column prop="name" label="设施" />
            <el-table-column prop="category" label="类别" width="88" />
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
        <AMapView :facilities="facilities" :route-path="routePath" />
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import AMapView from "../components/AMapView.vue";
import { apiGet, type Coordinate, type FacilityItem, type NearbyFacilitiesPayload } from "../services/api";

const category = ref("");
const radius = ref(1000);
const loading = ref(false);
const facilities = ref<FacilityItem[]>([]);
const routePath = ref<Coordinate[]>([]);

async function loadFacilities() {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      radius: String(radius.value),
      limit: "10",
    });
    if (category.value) {
      params.set("category", category.value);
    }
    const payload = await apiGet<NearbyFacilitiesPayload>(`/api/v1/facilities/nearby?${params}`);
    facilities.value = payload.items;
    routePath.value = payload.items[0]?.routePath ?? [];
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadFacilities();
});
</script>
