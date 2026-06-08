<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>个人中心</h1>
        <p>登录、兴趣、收藏、评分和浏览行为会共同影响推荐结果。</p>
      </div>
      <el-button type="primary" :loading="saving" @click="saveInterests">保存兴趣</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="7">
        <el-card shadow="never">
          <template #header>账号登录</template>
          <el-form label-position="top">
            <el-form-item label="账号或邮箱">
              <el-input v-model="loginForm.username_or_email" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="loginForm.password" type="password" show-password />
            </el-form-item>
          </el-form>
          <div class="button-row">
            <el-button type="primary" :loading="authLoading" @click="login">登录</el-button>
            <el-button :disabled="!token" @click="verifyToken">校验 Token</el-button>
          </div>
          <p v-if="verifiedName" class="muted-text">Token 用户：{{ verifiedName }}</p>
        </el-card>

        <el-card shadow="never" class="result-card">
          <template #header>快速注册</template>
          <el-form label-position="top">
            <el-form-item label="用户名">
              <el-input v-model="registerForm.username" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="registerForm.email" />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="registerForm.nickname" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="registerForm.password" type="password" show-password />
            </el-form-item>
          </el-form>
          <el-button :loading="authLoading" @click="register">注册并登录</el-button>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never">
          <template #header>画像与行为</template>
          <el-form label-position="top">
            <el-form-item label="当前用户">
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
            <el-form-item label="景点/学校 ID">
              <el-input-number v-model="targetDestinationId" :min="1" :max="207" />
            </el-form-item>
            <el-form-item label="评分">
              <el-rate v-model="ratingValue" allow-half />
            </el-form-item>
          </el-form>
          <div class="button-row wrap">
            <el-button @click="addFavorite">收藏景点/学校</el-button>
            <el-button @click="rateDestination">提交评分</el-button>
            <el-button @click="recordView">记录浏览</el-button>
          </div>
        </el-card>

        <el-card shadow="never" class="result-card">
          <template #header>用户行为摘要</template>
          <div class="stat"><span>收藏</span><strong>{{ profile?.favorites?.length ?? 0 }}</strong></div>
          <div class="stat"><span>评分</span><strong>{{ profile?.ratings?.length ?? 0 }}</strong></div>
          <div class="stat"><span>行为日志</span><strong>{{ profile?.recent_behaviors?.length ?? 0 }}</strong></div>
          <el-tag
            v-for="item in profile?.favorites ?? []"
            :key="`${item.target_type}-${item.target_id}`"
            class="tag-item"
          >
            {{ item.target_name ?? `${item.target_type}#${item.target_id}` }}
          </el-tag>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>推荐预览</span>
              <el-segmented v-model="strategy" :options="strategyOptions" @change="() => loadRecommendations()" />
            </div>
          </template>
          <el-table :data="recommendations" size="small" v-loading="loadingRecommendations">
            <el-table-column prop="name" label="目的地" min-width="150" />
            <el-table-column prop="score" label="得分" width="80">
              <template #default="{ row }">{{ row.score?.toFixed(3) }}</template>
            </el-table-column>
            <el-table-column prop="behavior_score" label="行为" width="80">
              <template #default="{ row }">{{ row.behavior_score?.toFixed(2) ?? "-" }}</template>
            </el-table-column>
            <el-table-column prop="reason" label="推荐理由" min-width="220" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import {
  apiGet,
  apiGetWithAuth,
  apiPost,
  apiPut,
  type AuthPayload,
  type DestinationItem,
  type RecommendationPayload,
  type UserProfileItem,
  type UserListPayload,
  type UserProfilePayload,
} from "../services/api";

const users = ref<UserProfileItem[]>([]);
const profile = ref<UserProfilePayload | null>(null);
const userId = ref<number | null>(null);
const availableInterests = ref<string[]>([]);
const selectedInterests = ref<string[]>([]);
const recommendations = ref<DestinationItem[]>([]);
const saving = ref(false);
const authLoading = ref(false);
const loadingRecommendations = ref(false);
const token = ref(localStorage.getItem("smart-tour-token") ?? "");
const verifiedName = ref("");
const strategy = ref("behavior");
const targetDestinationId = ref(1);
const ratingValue = ref(5);

const loginForm = reactive({
  username_or_email: "user01",
  password: "demo123456",
});
const registerForm = reactive({
  username: `visitor_${Date.now().toString().slice(-5)}`,
  email: `visitor_${Date.now().toString().slice(-5)}@example.com`,
  nickname: "新游客",
  password: "demo123456",
});
const strategyOptions = [
  { label: "行为", value: "behavior" },
  { label: "兴趣", value: "interest" },
  { label: "综合", value: "composite" },
  { label: "热门", value: "hot" },
  { label: "高分", value: "rating" },
];

async function loadUsers() {
  const payload = await apiGet<UserListPayload>("/api/v1/users");
  users.value = payload.items;
  availableInterests.value = payload.available_interests;
  userId.value = userId.value ?? payload.items[0]?.id ?? null;
}

async function loadProfile() {
  if (!userId.value) return;
  const payload = await apiGet<UserProfilePayload>(`/api/v1/users/${userId.value}`);
  profile.value = payload;
  selectedInterests.value = [...payload.interests];
  availableInterests.value = payload.available_interests;
  await loadRecommendations();
}

async function login() {
  authLoading.value = true;
  try {
    const payload = await apiPost<AuthPayload>("/api/v1/users/login", loginForm);
    applyAuth(payload);
    ElMessage.success("登录成功");
  } finally {
    authLoading.value = false;
  }
}

async function register() {
  authLoading.value = true;
  try {
    const payload = await apiPost<AuthPayload>("/api/v1/users/register", {
      ...registerForm,
      interests: selectedInterests.value,
    });
    applyAuth(payload);
    await loadUsers();
    ElMessage.success("注册成功");
  } finally {
    authLoading.value = false;
  }
}

async function verifyToken() {
  if (!token.value) return;
  const payload = await apiGetWithAuth<UserProfilePayload>("/api/v1/users/me", token.value);
  verifiedName.value = `${payload.nickname} (${payload.username})`;
}

function applyAuth(payload: AuthPayload) {
  token.value = payload.access_token;
  localStorage.setItem("smart-tour-token", payload.access_token);
  userId.value = payload.user.id;
  verifiedName.value = `${payload.user.nickname} (${payload.user.username})`;
  void loadProfile();
}

async function saveInterests() {
  if (!userId.value) return;
  saving.value = true;
  try {
    const payload = await apiPut<UserProfilePayload>(`/api/v1/users/${userId.value}/interests`, {
      interests: selectedInterests.value,
    });
    profile.value = payload;
    selectedInterests.value = [...payload.interests];
    await loadRecommendations();
  } finally {
    saving.value = false;
  }
}

async function addFavorite() {
  if (!userId.value) return;
  await apiPost(`/api/v1/users/${userId.value}/favorites`, {
    target_type: "destination",
    target_id: targetDestinationId.value,
    note: "前端演示收藏",
  });
  await loadProfile();
  ElMessage.success("已收藏并写入行为日志");
}

async function rateDestination() {
  if (!userId.value) return;
  await apiPost(`/api/v1/users/${userId.value}/ratings`, {
    target_type: "destination",
    target_id: targetDestinationId.value,
    rating: ratingValue.value,
  });
  await loadProfile();
  ElMessage.success("评分已更新");
}

async function recordView() {
  if (!userId.value) return;
  await apiPost(`/api/v1/users/${userId.value}/behavior`, {
    target_type: "destination",
    target_id: targetDestinationId.value,
    action: "view",
    metadata_text: "profile demo view",
  });
  await loadProfile();
  ElMessage.success("浏览行为已记录");
}

async function loadRecommendations() {
  if (!userId.value) return;
  loadingRecommendations.value = true;
  try {
    const payload = await apiGet<RecommendationPayload>(
      `/api/v1/recommendations?user_id=${userId.value}&strategy=${strategy.value}&limit=10`,
    );
    recommendations.value = payload.items;
  } finally {
    loadingRecommendations.value = false;
  }
}

onMounted(async () => {
  await loadUsers();
  await loadProfile();
  if (token.value) {
    await verifyToken();
  }
});
</script>

<style scoped>
.card-header,
.button-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.button-row.wrap {
  flex-wrap: wrap;
  justify-content: flex-start;
}

.muted-text {
  margin: 12px 0 0;
  color: #667085;
}

.tag-item {
  margin: 0 6px 6px 0;
}
</style>
