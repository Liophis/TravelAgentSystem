<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>游记列表与查询</h1>
        <p>浏览所有用户的目的地游记，按标题、正文或全文索引查询，并进行浏览、评分和评论交流。</p>
      </div>
      <div class="heading-actions">
        <el-button :loading="loading" @click="loadDiaries">刷新</el-button>
        <el-button type="primary" @click="$router.push('/diaries/create')">发布游记</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="8">
        <el-card shadow="never">
          <template #header>查询条件</template>
          <el-form label-position="top">
            <el-form-item label="关键词">
              <el-input v-model="keyword" clearable placeholder="目的地、标题或正文" @keyup.enter="loadDiaries" />
            </el-form-item>
            <el-form-item label="搜索模式">
              <el-segmented v-model="searchMode" :options="searchModeOptions" />
            </el-form-item>
          </el-form>
          <el-button type="primary" :loading="loading" @click="loadDiaries">查询</el-button>
        </el-card>

        <el-card shadow="never" class="result-card">
          <template #header>游记列表</template>
          <el-table :data="diaries" v-loading="loading" size="small" @row-click="selectDiary">
            <el-table-column prop="title" label="标题" min-width="180" />
            <el-table-column prop="views" label="浏览" width="76" />
            <el-table-column prop="rating_avg" label="评分" width="76" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card v-if="selected" shadow="never">
          <template #header>
            <div class="card-header">
              <span>{{ selected.title }}</span>
              <div class="inline-actions">
                <el-button link type="primary" @click="$router.push('/diaries/create')">去创作页生成 AIGC</el-button>
                <el-button link type="primary" @click="viewSelected">浏览 +1</el-button>
              </div>
            </div>
          </template>

          <p class="diary-body">{{ selected.body }}</p>

          <div v-if="selected.media?.length" class="media-list">
            <div v-for="media in selected.media" :key="media.id" class="media-item">
              <el-image v-if="media.media_type === 'image'" :src="media.url" fit="cover" class="media-image" />
              <div v-else class="media-video">{{ media.url }}</div>
              <span>{{ media.caption || media.media_type }}</span>
            </div>
          </div>

          <aside v-if="compression" class="compression-panel">
            <h3>压缩存储</h3>
            <div class="metric-grid">
              <div class="metric"><span>算法</span><strong>{{ compression.algorithm }}</strong></div>
              <div class="metric"><span>原始大小</span><strong>{{ compression.original_size }} B</strong></div>
              <div class="metric"><span>压缩大小</span><strong>{{ compression.compressed_size }} B</strong></div>
              <div class="metric"><span>压缩率</span><strong>{{ compression.compression_ratio }}</strong></div>
            </div>
          </aside>

          <div class="diary-actions">
            <el-rate v-model="rating" />
            <el-button type="primary" @click="rateSelected">评分</el-button>
          </div>

          <el-divider />
          <el-input v-model="comment" type="textarea" :rows="3" placeholder="评论" />
          <el-button class="comment-button" @click="commentSelected">评论</el-button>
          <div v-for="item in selected.comments ?? []" :key="item.id" class="comment-item">
            {{ item.content }}
          </div>
        </el-card>

        <el-card v-else shadow="never">
          <el-empty description="请选择一篇游记" />
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import {
  apiGet,
  apiPost,
  type DiaryCommentItem,
  type DiaryCompressionPayload,
  type DiaryItem,
  type DiaryListPayload,
} from "../services/api";
import { authState } from "../services/auth";

const loading = ref(false);
const keyword = ref("");
const searchMode = ref("fulltext");
const diaries = ref<DiaryItem[]>([]);
const selected = ref<DiaryItem | null>(null);
const compression = ref<DiaryCompressionPayload | null>(null);
const rating = ref(5);
const comment = ref("");
const searchModeOptions = [
  { label: "全文", value: "fulltext" },
  { label: "精确标题", value: "exact_title" },
  { label: "包含", value: "contains" },
];

async function loadDiaries() {
  loading.value = true;
  try {
    const params = new URLSearchParams({ limit: "30", offset: "0" });
    if (keyword.value.trim()) {
      params.set("keyword", keyword.value.trim());
      params.set("mode", searchMode.value);
      const payload = await apiGet<DiaryListPayload>(`/api/v1/diaries/search?${params}`);
      diaries.value = payload.items;
      await selectFirstIfNeeded(payload.items);
      return;
    }
    const payload = await apiGet<DiaryListPayload>(`/api/v1/diaries?${params}`);
    diaries.value = payload.items;
    await selectFirstIfNeeded(payload.items);
  } finally {
    loading.value = false;
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
    user_id: authState.user?.id ?? 1,
    value: rating.value,
  });
  mergeSelectedSummary(updated);
}

async function commentSelected() {
  if (!selected.value || !comment.value.trim()) return;
  const created = await apiPost<DiaryCommentItem>(`/api/v1/diaries/${selected.value.id}/comments`, {
    user_id: authState.user?.id ?? 1,
    content: comment.value.trim(),
  });
  selected.value.comments = [...(selected.value.comments ?? []), created];
  comment.value = "";
}

async function selectFirstIfNeeded(items: DiaryItem[]) {
  if (items.length === 0) {
    selected.value = null;
    compression.value = null;
    return;
  }
  if (!selected.value || !items.some((item) => item.id === selected.value?.id)) {
    await selectDiary(items[0]);
  }
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
.diary-actions,
.inline-actions {
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

.compression-panel {
  margin: 16px 0;
  padding: 14px 16px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: #f9fafb;
}

.compression-panel h3 {
  margin: 0 0 12px;
  color: #101828;
  font-size: 15px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.metric {
  min-height: 72px;
  padding: 12px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: #fff;
}

.metric span {
  display: block;
  color: #667085;
  font-size: 12px;
}

.metric strong {
  display: block;
  margin-top: 8px;
  color: #101828;
  font-size: 16px;
  overflow-wrap: anywhere;
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

.media-list {
  display: grid;
  gap: 8px;
  margin: 12px 0;
}

.media-item {
  display: grid;
  grid-template-columns: 80px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  font-size: 13px;
  color: #475467;
}

.media-image,
.media-video {
  width: 80px;
  height: 54px;
  border-radius: 6px;
  background: #f2f4f7;
}

.media-video {
  display: flex;
  align-items: center;
  overflow: hidden;
  padding: 6px;
  font-size: 11px;
}

@media (max-width: 1200px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .card-header,
  .diary-actions,
  .inline-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-grid,
  .media-item {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
