<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>景点与学校</h1>
        <p>浏览、筛选和搜索全国真实景区与高校目的地。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadDestinations">查询</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="7">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="关键词">
              <el-input v-model="keyword" clearable placeholder="名称、类别、标签" @keyup.enter="loadDestinations" />
            </el-form-item>
            <el-form-item label="分类">
              <el-select v-model="category" clearable placeholder="全部分类">
                <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="排序">
              <el-segmented v-model="sort" :options="sortOptions" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="selected" shadow="never" class="result-card">
          <h2>{{ selected.name }}</h2>
          <div class="stat"><span>分类</span><strong>{{ selected.category }}</strong></div>
          <div class="stat"><span>评分</span><strong>{{ selected.rating }}</strong></div>
          <div class="stat"><span>热度</span><strong>{{ selected.popularity }}</strong></div>
          <p class="destination-description">{{ selected.description }}</p>
          <el-tag v-for="tag in selected.tags" :key="tag" class="tag-item">{{ tag }}</el-tag>
          <el-divider />
          <el-rate v-model="ratingValue" allow-half />
          <div class="button-row">
            <el-button size="small" @click="favoriteSelected">收藏</el-button>
            <el-button size="small" type="primary" @click="rateSelected">评分</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="17">
        <el-card shadow="never">
          <el-table :data="destinations" v-loading="loading" size="small" @row-click="selectDestination">
            <el-table-column prop="name" label="名称" min-width="180" />
            <el-table-column prop="category" label="分类" width="104" />
            <el-table-column prop="rating" label="评分" width="88" />
            <el-table-column prop="popularity" label="热度" width="96" />
            <el-table-column label="标签" min-width="180">
              <template #default="{ row }">
                <el-tag v-for="tag in row.tags" :key="tag" size="small" class="tag-item">{{ tag }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { apiGet, apiPost, type DestinationItem, type DestinationListPayload } from "../services/api";

const loading = ref(false);
const keyword = ref("");
const category = ref("");
const sort = ref("popularity");
const destinations = ref<DestinationItem[]>([]);
const categories = ref<string[]>([]);
const selected = ref<DestinationItem | null>(null);
const ratingValue = ref(5);
const demoUserId = 1;

const sortOptions = [
  { label: "热度", value: "popularity" },
  { label: "评分", value: "rating" },
  { label: "名称", value: "name" },
];
const categoryOptions = computed(() => categories.value.length > 0 ? categories.value : ["school", "scenic"]);

async function loadDestinations() {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      sort: sort.value,
      limit: "30",
      offset: "0",
    });
    if (keyword.value.trim()) {
      params.set("q", keyword.value.trim());
    }
    if (category.value) {
      params.set("category", category.value);
    }
    const payload = await apiGet<DestinationListPayload>(`/api/v1/destinations?${params}`);
    destinations.value = payload.items;
    categories.value = payload.categories;
    selected.value = payload.items[0] ?? null;
    ratingValue.value = selected.value?.rating ?? 5;
  } finally {
    loading.value = false;
  }
}

function selectDestination(row: DestinationItem) {
  selected.value = row;
  ratingValue.value = row.rating;
  void recordDestinationView(row.id);
}

async function favoriteSelected() {
  if (!selected.value) return;
  await apiPost(`/api/v1/users/${demoUserId}/favorites`, {
    target_type: "destination",
    target_id: selected.value.id,
    note: "目的地页收藏",
  });
  ElMessage.success("已收藏，推荐会读取该行为");
}

async function rateSelected() {
  if (!selected.value) return;
  await apiPost(`/api/v1/users/${demoUserId}/ratings`, {
    target_type: "destination",
    target_id: selected.value.id,
    rating: ratingValue.value,
  });
  await loadDestinations();
  ElMessage.success("评分已更新");
}

async function recordDestinationView(destinationId: number) {
  await apiPost(`/api/v1/users/${demoUserId}/behavior`, {
    target_type: "destination",
    target_id: destinationId,
    action: "view",
    metadata_text: "destination row click",
  });
}

onMounted(() => {
  void loadDestinations();
});
</script>

<style scoped>
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
