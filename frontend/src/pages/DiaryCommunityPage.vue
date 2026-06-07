<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>游记社区</h1>
        <p>发布、搜索和浏览沙河校区游记。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadDiaries">刷新</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="7">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="搜索">
              <el-input v-model="keyword" clearable placeholder="标题或正文" @keyup.enter="loadDiaries" />
            </el-form-item>
            <el-form-item label="标题">
              <el-input v-model="form.title" maxlength="160" />
            </el-form-item>
            <el-form-item label="正文">
              <el-input v-model="form.body" type="textarea" :rows="5" />
            </el-form-item>
          </el-form>
          <el-button type="primary" :loading="creating" @click="createDiary">发布</el-button>
        </el-card>

        <el-card v-if="compression" shadow="never" class="result-card">
          <div class="stat"><span>压缩算法</span><strong>{{ compression.algorithm }}</strong></div>
          <div class="stat"><span>原始大小</span><strong>{{ compression.original_size }} B</strong></div>
          <div class="stat"><span>压缩大小</span><strong>{{ compression.compressed_size }} B</strong></div>
          <div class="stat"><span>压缩率</span><strong>{{ compression.compression_ratio }}</strong></div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never">
          <el-table :data="diaries" v-loading="loading" size="small" @row-click="selectDiary">
            <el-table-column prop="title" label="标题" min-width="160" />
            <el-table-column prop="views" label="浏览" width="80" />
            <el-table-column prop="rating_avg" label="评分" width="80" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card v-if="selected" shadow="never">
          <template #header>
            <div class="card-header">
              <span>{{ selected.title }}</span>
              <el-button link type="primary" @click="viewSelected">浏览 +1</el-button>
            </div>
          </template>
          <p class="diary-body">{{ selected.body }}</p>
          <div class="diary-actions">
            <el-rate v-model="rating" />
            <el-button type="primary" @click="rateSelected">评分</el-button>
          </div>
          <el-divider />
          <el-input v-model="comment" type="textarea" :rows="2" placeholder="评论" />
          <el-button class="comment-button" @click="commentSelected">评论</el-button>
          <div v-for="item in selected.comments ?? []" :key="item.id" class="comment-item">
            {{ item.content }}
          </div>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import {
  apiGet,
  apiPost,
  type DiaryCommentItem,
  type DiaryCompressionPayload,
  type DiaryItem,
  type DiaryListPayload,
} from "../services/api";

const loading = ref(false);
const creating = ref(false);
const keyword = ref("");
const diaries = ref<DiaryItem[]>([]);
const selected = ref<DiaryItem | null>(null);
const compression = ref<DiaryCompressionPayload | null>(null);
const rating = ref(5);
const comment = ref("");
const form = reactive({
  title: "沙河校区新游记",
  body: "今天在沙河校区完成了一次路线和设施查询体验，地图路径很清晰。",
});

async function loadDiaries() {
  loading.value = true;
  try {
    const params = new URLSearchParams({ limit: "30", offset: "0" });
    if (keyword.value.trim()) {
      params.set("q", keyword.value.trim());
    }
    const payload = await apiGet<DiaryListPayload>(`/api/v1/diaries?${params}`);
    diaries.value = payload.items;
    if (!selected.value && payload.items[0]) {
      await selectDiary(payload.items[0]);
    }
  } finally {
    loading.value = false;
  }
}

async function createDiary() {
  creating.value = true;
  try {
    const diary = await apiPost<DiaryItem>("/api/v1/diaries", {
      user_id: 1,
      destination_id: 1,
      title: form.title,
      body: form.body,
    });
    diaries.value = [diary, ...diaries.value];
    await selectDiary(diary);
  } finally {
    creating.value = false;
  }
}

async function selectDiary(row: DiaryItem) {
  selected.value = await apiGet<DiaryItem>(`/api/v1/diaries/${row.id}`);
  compression.value = await apiGet<DiaryCompressionPayload>(`/api/v1/diaries/${row.id}/compression`);
}

async function viewSelected() {
  if (!selected.value) return;
  const updated = await apiPost<DiaryItem>(`/api/v1/diaries/${selected.value.id}/view`, {});
  mergeSelectedSummary(updated);
}

async function rateSelected() {
  if (!selected.value) return;
  const updated = await apiPost<DiaryItem>(`/api/v1/diaries/${selected.value.id}/rating`, {
    user_id: 1,
    value: rating.value,
  });
  mergeSelectedSummary(updated);
}

async function commentSelected() {
  if (!selected.value || !comment.value.trim()) return;
  const created = await apiPost<DiaryCommentItem>(`/api/v1/diaries/${selected.value.id}/comments`, {
    user_id: 1,
    content: comment.value.trim(),
  });
  selected.value.comments = [...(selected.value.comments ?? []), created];
  comment.value = "";
}

function mergeSelectedSummary(updated: DiaryItem) {
  if (!selected.value) return;
  selected.value = {
    ...selected.value,
    views: updated.views,
    rating_avg: updated.rating_avg,
    rating_count: updated.rating_count,
  };
  diaries.value = diaries.value.map((item) =>
    item.id === updated.id
      ? {
          ...item,
          views: updated.views,
          rating_avg: updated.rating_avg,
          rating_count: updated.rating_count,
        }
      : item,
  );
}

onMounted(() => {
  void loadDiaries();
});
</script>

<style scoped>
.card-header,
.diary-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.diary-body {
  color: #475467;
  line-height: 1.7;
  white-space: pre-wrap;
}

.comment-button {
  margin-top: 8px;
}

.comment-item {
  margin-top: 10px;
  padding: 10px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  color: #475467;
}
</style>
