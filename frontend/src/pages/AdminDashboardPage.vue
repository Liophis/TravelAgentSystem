<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>管理后台</h1>
        <p>查看核心数据规模，编辑内容，并执行游记审核删除。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="refreshAll">刷新</el-button>
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

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>目的地编辑</template>
          <el-form label-position="top">
            <el-form-item label="ID">
              <el-input-number v-model="destinationForm.id" :min="1" :max="200" />
            </el-form-item>
            <el-form-item label="名称">
              <el-input v-model="destinationForm.name" />
            </el-form-item>
            <el-form-item label="分类">
              <el-input v-model="destinationForm.category" />
            </el-form-item>
            <el-form-item label="热度">
              <el-input-number v-model="destinationForm.popularity" :min="0" />
            </el-form-item>
            <el-form-item label="标签">
              <el-input v-model="destinationForm.tags" placeholder="food,study" />
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="updateDestination">保存目的地</el-button>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never">
          <template #header>设施编辑</template>
          <el-form label-position="top">
            <el-form-item label="ID">
              <el-input-number v-model="facilityForm.id" :min="1" />
            </el-form-item>
            <el-form-item label="名称">
              <el-input v-model="facilityForm.name" />
            </el-form-item>
            <el-form-item label="类别代码">
              <el-input v-model="facilityForm.category_code" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="facilityForm.description" />
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="updateFacility">保存设施</el-button>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never">
          <template #header>美食编辑</template>
          <el-form label-position="top">
            <el-form-item label="ID">
              <el-input-number v-model="foodForm.id" :min="1" />
            </el-form-item>
            <el-form-item label="名称">
              <el-input v-model="foodForm.name" />
            </el-form-item>
            <el-form-item label="菜系">
              <el-input v-model="foodForm.cuisine" />
            </el-form-item>
            <el-form-item label="价格">
              <el-input-number v-model="foodForm.price" :min="0" :step="1" />
            </el-form-item>
            <el-form-item label="热度">
              <el-input-number v-model="foodForm.heat" :min="0" />
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="updateFood">保存美食</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>游记审核</span>
          <el-button :loading="loadingDiaries" @click="loadDiaries">刷新游记</el-button>
        </div>
      </template>
      <el-table :data="diaries" size="small" v-loading="loadingDiaries">
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column prop="title" label="标题" min-width="220" />
        <el-table-column prop="user_id" label="用户" width="80" />
        <el-table-column prop="views" label="浏览" width="80" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-popconfirm title="确认删除这篇游记？" @confirm="deleteDiary(row.id)">
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import {
  apiDelete,
  apiGet,
  apiPatch,
  type AdminDiaryItem,
  type AdminDiaryListPayload,
  type AdminStatsPayload,
} from "../services/api";

const loading = ref(false);
const loadingDiaries = ref(false);
const stats = ref<AdminStatsPayload | null>(null);
const diaries = ref<AdminDiaryItem[]>([]);
const tableRows = computed(() => toRows(stats.value?.tables ?? {}));
const mapRows = computed(() => toRows(stats.value?.map ?? {}));
const destinationForm = reactive({
  id: 1,
  name: "后台更新目的地",
  category: "school",
  popularity: 999,
  tags: "food,study",
});
const facilityForm = reactive({
  id: 1,
  name: "后台更新设施",
  category_code: "toilet",
  description: "后台编辑后的设施描述",
});
const foodForm = reactive({
  id: 1,
  name: "后台更新美食",
  cuisine: "home-style",
  price: 18,
  heat: 888,
});

async function refreshAll() {
  await Promise.all([loadStats(), loadDiaries()]);
}

async function loadStats() {
  loading.value = true;
  try {
    stats.value = await apiGet<AdminStatsPayload>("/api/v1/admin/stats");
  } finally {
    loading.value = false;
  }
}

async function loadDiaries() {
  loadingDiaries.value = true;
  try {
    const payload = await apiGet<AdminDiaryListPayload>("/api/v1/admin/diaries?limit=10");
    diaries.value = payload.items;
  } finally {
    loadingDiaries.value = false;
  }
}

async function updateDestination() {
  await apiPatch(`/api/v1/admin/destinations/${destinationForm.id}`, {
    name: destinationForm.name,
    category: destinationForm.category,
    popularity: destinationForm.popularity,
    tags: destinationForm.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
  });
  await loadStats();
  ElMessage.success("目的地已更新");
}

async function updateFacility() {
  await apiPatch(`/api/v1/admin/facilities/${facilityForm.id}`, {
    name: facilityForm.name,
    category_code: facilityForm.category_code,
    description: facilityForm.description,
  });
  await loadStats();
  ElMessage.success("设施已更新");
}

async function updateFood() {
  await apiPatch(`/api/v1/admin/foods/${foodForm.id}`, {
    name: foodForm.name,
    cuisine: foodForm.cuisine,
    price: foodForm.price,
    heat: foodForm.heat,
  });
  await loadStats();
  ElMessage.success("美食已更新");
}

async function deleteDiary(diaryId: number) {
  await apiDelete(`/api/v1/admin/diaries/${diaryId}`);
  await refreshAll();
  ElMessage.success("游记已删除");
}

function toRows(record: Record<string, number>) {
  return Object.entries(record).map(([name, count]) => ({ name, count }));
}

onMounted(() => {
  void refreshAll();
});
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
</style>
