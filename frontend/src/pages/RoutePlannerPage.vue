<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>路线规划</h1>
        <p>路线接口返回 OSM 图路径，前端使用高德 Polyline 绘制。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="planRoute">规划路线</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="7">
        <el-card shadow="never">
          <el-form label-position="top">
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
            <el-form-item label="多终点">
              <el-input
                v-model="multiPointText"
                type="textarea"
                :rows="4"
                placeholder="名称,经度,纬度"
              />
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="returnToStart">回到起点</el-checkbox>
            </el-form-item>
          </el-form>
          <el-button :loading="loading" @click="planMultiPointRoute">规划多点路线</el-button>
        </el-card>

        <el-card v-if="route" shadow="never" class="result-card">
          <div class="stat"><span>总距离</span><strong>{{ route.distance }} m</strong></div>
          <div class="stat"><span>预计时间</span><strong>{{ Math.round(route.duration / 60) }} min</strong></div>
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
import { apiPost, type RoutePlanPayload } from "../services/api";

const loading = ref(false);
const route = ref<RoutePlanPayload | null>(null);
const returnToStart = ref(false);
const multiPointText = ref("教学楼,116.2842,40.1567\n图书馆,116.2862,40.1582");
const form = reactive({
  start_lng: 116.28333,
  start_lat: 40.15608,
  end_lng: 116.28620,
  end_lat: 40.15820,
  strategy: "shortest_distance",
  mode: "walk",
});

async function planRoute() {
  loading.value = true;
  try {
    route.value = await apiPost<RoutePlanPayload>("/api/v1/routes/plan", form);
  } finally {
    loading.value = false;
  }
}

async function planMultiPointRoute() {
  const points = parseMultiPointText();
  if (points.length === 0) {
    return;
  }
  loading.value = true;
  try {
    route.value = await apiPost<RoutePlanPayload>("/api/v1/routes/multi-point", {
      start_lng: form.start_lng,
      start_lat: form.start_lat,
      points,
      return_to_start: returnToStart.value,
      strategy: form.strategy,
      mode: form.mode,
    });
  } finally {
    loading.value = false;
  }
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

onMounted(() => {
  void planRoute();
});
</script>

<style scoped>
.visit-order {
  margin: 12px 0;
}

.visit-tag {
  margin: 0 6px 6px 0;
}
</style>
