<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>个人偏好</h1>
        <p>选择兴趣标签后，推荐结果会按用户画像重新计算。</p>
      </div>
      <el-button type="primary" :loading="saving" @click="saveInterests">保存兴趣</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="用户">
              <el-select v-model="userId" @change="loadProfile">
                <el-option
                  v-for="user in users"
                  :key="user.id"
                  :label="`${user.nickname} (${user.username})`"
                  :value="user.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="兴趣">
              <el-checkbox-group v-model="selectedInterests">
                <el-checkbox-button
                  v-for="tag in availableInterests"
                  :key="tag"
                  :label="tag"
                  :value="tag"
                />
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>兴趣推荐预览</span>
              <el-button :loading="loadingRecommendations" @click="loadRecommendations">刷新</el-button>
            </div>
          </template>
          <el-table :data="recommendations" size="small">
            <el-table-column prop="name" label="目的地" min-width="160" />
            <el-table-column prop="category" label="类别" width="90" />
            <el-table-column prop="score" label="得分" width="90">
              <template #default="{ row }">{{ row.score?.toFixed(3) }}</template>
            </el-table-column>
            <el-table-column prop="reason" label="推荐理由" min-width="220" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import {
  apiGet,
  apiPut,
  type DestinationItem,
  type RecommendationPayload,
  type UserListPayload,
  type UserProfileItem,
  type UserProfilePayload,
} from "../services/api";

const users = ref<UserProfileItem[]>([]);
const userId = ref<number | null>(null);
const availableInterests = ref<string[]>([]);
const selectedInterests = ref<string[]>([]);
const recommendations = ref<DestinationItem[]>([]);
const saving = ref(false);
const loadingRecommendations = ref(false);

async function loadUsers() {
  const payload = await apiGet<UserListPayload>("/api/v1/users");
  users.value = payload.items;
  availableInterests.value = payload.available_interests;
  userId.value = payload.items[0]?.id ?? null;
}

async function loadProfile() {
  if (!userId.value) return;
  const payload = await apiGet<UserProfilePayload>(`/api/v1/users/${userId.value}`);
  selectedInterests.value = [...payload.interests];
  availableInterests.value = payload.available_interests;
  await loadRecommendations();
}

async function saveInterests() {
  if (!userId.value) return;
  saving.value = true;
  try {
    const payload = await apiPut<UserProfilePayload>(`/api/v1/users/${userId.value}/interests`, {
      interests: selectedInterests.value,
    });
    selectedInterests.value = [...payload.interests];
    await loadRecommendations();
  } finally {
    saving.value = false;
  }
}

async function loadRecommendations() {
  if (!userId.value) return;
  loadingRecommendations.value = true;
  try {
    const payload = await apiGet<RecommendationPayload>(
      `/api/v1/recommendations?user_id=${userId.value}&strategy=interest&limit=10`,
    );
    recommendations.value = payload.items;
  } finally {
    loadingRecommendations.value = false;
  }
}

onMounted(async () => {
  await loadUsers();
  await loadProfile();
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
