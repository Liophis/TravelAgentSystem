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

    <el-row :gutter="18" class="community-layout">
      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="browse-panel">
          <template #header>
            <div class="panel-header">
              <div>
                <strong>社区游记</strong>
                <small>{{ diaries.length }} 条结果</small>
              </div>
            </div>
          </template>
          <el-form label-position="top">
            <el-form-item label="关键词">
              <el-input v-model="keyword" clearable placeholder="目的地、标题或正文" @keyup.enter="loadDiaries" />
            </el-form-item>
            <el-form-item label="搜索模式">
              <el-segmented v-model="searchMode" :options="searchModeOptions" />
            </el-form-item>
          </el-form>
          <div class="search-actions">
            <el-button type="primary" :loading="loading" @click="loadDiaries">查询</el-button>
            <el-button @click="resetSearch">全部游记</el-button>
          </div>

          <el-divider />

          <div v-loading="loading" class="diary-list">
            <button
              v-for="diary in diaries"
              :key="diary.id"
              class="diary-list-item"
              :class="{ active: selected?.id === diary.id }"
              type="button"
              @click="selectDiary(diary)"
            >
              <span class="diary-title">{{ diary.title }}</span>
              <span class="diary-summary">{{ summarizeDiary(diary) }}</span>
              <span class="diary-meta">
                <span>{{ diary.views }} 浏览</span>
                <span>{{ formatRating(diary.rating_avg) }} 分</span>
                <span>{{ diary.rating_count }} 评</span>
              </span>
            </button>
            <el-empty v-if="!loading && diaries.length === 0" description="没有匹配的游记" />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card v-if="selected" shadow="never" class="reader-panel">
          <div class="reader-hero">
            <div>
              <el-tag effect="plain" type="success">目的地游记</el-tag>
              <h2>{{ selected.title }}</h2>
              <div class="reader-stats">
                <span>{{ selected.views }} 浏览</span>
                <span>{{ formatRating(selected.rating_avg) }} 分</span>
                <span>{{ selected.rating_count }} 人评分</span>
              </div>
            </div>
            <div class="inline-actions">
              <el-button @click="$router.push('/diaries/create')">发布 / AIGC</el-button>
              <el-button type="primary" @click="viewSelected">浏览 +1</el-button>
            </div>
          </div>

          <p class="diary-body">{{ selected.body }}</p>

          <div v-if="selected.media?.length" class="media-list">
            <div v-for="media in selected.media" :key="media.id" class="media-item">
              <el-image v-if="media.media_type === 'image'" :src="media.url" fit="cover" class="media-image" />
              <div v-else class="media-video">{{ media.url }}</div>
              <span>{{ media.caption || media.media_type }}</span>
            </div>
          </div>

          <aside v-if="compression" class="compression-panel">
            <div class="compression-title">
              <h3>压缩存储</h3>
              <span>正文读取时自动解压</span>
            </div>
            <div class="metric-grid compact">
              <div class="metric"><span>算法</span><strong>{{ compression.algorithm }}</strong></div>
              <div class="metric"><span>原始大小</span><strong>{{ compression.original_size }} B</strong></div>
              <div class="metric"><span>压缩大小</span><strong>{{ compression.compressed_size }} B</strong></div>
              <div class="metric"><span>压缩率</span><strong>{{ compression.compression_ratio }}</strong></div>
            </div>
          </aside>

          <section class="interaction-panel">
            <div class="diary-actions">
              <div>
                <strong>给这篇游记评分</strong>
                <p>评分会参与游记推荐排序。</p>
              </div>
              <div class="rating-actions">
                <el-rate v-model="rating" />
                <el-button type="primary" @click="rateSelected">提交评分</el-button>
              </div>
            </div>

            <el-divider />

            <div class="comment-editor">
              <el-input v-model="comment" type="textarea" :rows="3" placeholder="写下你的补充、建议或体验" />
              <el-button type="primary" class="comment-button" @click="commentSelected">发布评论</el-button>
            </div>
            <div class="comment-list">
              <div v-for="item in selected.comments ?? []" :key="item.id" class="comment-item">
                {{ item.content }}
              </div>
            </div>
          </section>
        </el-card>

        <el-card v-else shadow="never" class="reader-panel empty-reader">
          <el-empty description="请选择一篇游记">
            <el-button type="primary" @click="$router.push('/diaries/create')">发布第一篇游记</el-button>
          </el-empty>
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

async function resetSearch() {
  keyword.value = "";
  searchMode.value = "fulltext";
  await loadDiaries();
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

function summarizeDiary(diary: DiaryItem) {
  const source = diary.summary || diary.body || "暂无摘要";
  return source.length > 78 ? `${source.slice(0, 78)}...` : source;
}

function formatRating(value: number | null | undefined) {
  return Number(value ?? 0).toFixed(1);
}

onMounted(() => {
  void loadDiaries();
});
</script>

<style scoped>
.community-layout {
  align-items: stretch;
}

.browse-panel,
.reader-panel {
  min-height: calc(100vh - 190px);
}

.panel-header,
.reader-hero,
.diary-actions,
.inline-actions,
.compression-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-header strong {
  display: block;
  color: #101828;
  font-size: 16px;
}

.panel-header small,
.compression-title span,
.reader-stats {
  color: #667085;
  font-size: 13px;
}

.search-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.diary-list {
  display: grid;
  gap: 10px;
  max-height: calc(100vh - 470px);
  min-height: 320px;
  overflow: auto;
  padding-right: 2px;
}

.diary-list-item {
  display: grid;
  width: 100%;
  gap: 8px;
  padding: 14px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: #fff;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.16s ease,
    background 0.16s ease,
    box-shadow 0.16s ease;
}

.diary-list-item:hover,
.diary-list-item.active {
  border-color: #87d0c6;
  background: #f4fbfa;
  box-shadow: 0 10px 26px rgba(16, 24, 40, 0.08);
}

.diary-title {
  color: #101828;
  font-size: 15px;
  font-weight: 800;
  line-height: 1.45;
}

.diary-summary {
  display: -webkit-box;
  overflow: hidden;
  color: #667085;
  font-size: 13px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.diary-meta,
.reader-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.diary-meta span,
.reader-stats span {
  padding: 4px 8px;
  border-radius: 999px;
  background: #f2f4f7;
  color: #475467;
  font-size: 12px;
  font-weight: 700;
}

.reader-hero {
  align-items: flex-start;
  padding-bottom: 18px;
  border-bottom: 1px solid #edf1f5;
}

.reader-hero h2 {
  max-width: 880px;
  margin: 12px 0 10px;
  color: #101828;
  font-size: 24px;
  line-height: 1.35;
}

.diary-body {
  margin: 22px 0;
  color: #475467;
  font-size: 15px;
  line-height: 1.85;
  white-space: pre-wrap;
}

.compression-panel {
  margin: 18px 0;
  padding: 14px 16px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: #f9fafb;
}

.compression-panel h3 {
  margin: 0;
  color: #101828;
  font-size: 15px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.metric {
  min-height: 68px;
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

.interaction-panel {
  margin-top: 18px;
  padding: 16px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: #fcfcfd;
}

.diary-actions strong {
  color: #101828;
}

.diary-actions p {
  margin: 5px 0 0;
  color: #667085;
  font-size: 13px;
}

.rating-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.comment-editor {
  display: grid;
  gap: 10px;
}

.comment-button {
  justify-self: end;
}

.comment-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.comment-item {
  padding: 10px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  color: #475467;
}

.media-list {
  display: grid;
  gap: 8px;
  margin: 12px 0 18px;
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

.empty-reader {
  display: grid;
  place-items: center;
}

@media (max-width: 1200px) {
  .browse-panel,
  .reader-panel {
    min-height: auto;
  }

  .diary-list {
    max-height: none;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .reader-hero,
  .diary-actions,
  .inline-actions,
  .compression-title,
  .rating-actions {
    align-items: flex-start;
    flex-direction: column;
    justify-content: flex-start;
  }

  .reader-hero h2 {
    font-size: 20px;
  }

  .metric-grid,
  .media-item {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
