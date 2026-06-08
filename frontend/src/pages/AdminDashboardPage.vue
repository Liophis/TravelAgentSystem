<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>管理后台</h1>
        <p>查看核心数据规模和 OSM 导入状态。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadStats">刷新</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>数据表</template>
          <el-table :data="tableRows" size="small">
            <el-table-column prop="name" label="表" />
            <el-table-column prop="count" label="数量" width="120" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header>地图数据</template>
          <el-table :data="mapRows" size="small">
            <el-table-column prop="name" label="项目" />
            <el-table-column prop="count" label="数量" width="120" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { apiGet, type AdminStatsPayload } from "../services/api";

const loading = ref(false);
const stats = ref<AdminStatsPayload | null>(null);
const tableRows = computed(() => toRows(stats.value?.tables ?? {}));
const mapRows = computed(() => toRows(stats.value?.map ?? {}));

async function loadStats() {
  loading.value = true;
  try {
    stats.value = await apiGet<AdminStatsPayload>("/api/v1/admin/stats");
  } finally {
    loading.value = false;
  }
}

function toRows(record: Record<string, number>) {
  return Object.entries(record).map(([name, count]) => ({ name, count }));
}

onMounted(() => {
  void loadStats();
});
</script>
