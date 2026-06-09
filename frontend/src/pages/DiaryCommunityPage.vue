<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>景点游记与 AIGC</h1>
        <p>围绕景区和学校目的地发布、搜索、浏览和交流游记，并用 AIGC Agent 生成草稿、分镜和模拟视频。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadDiaries">刷新</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="diary-action-card">
          <el-tabs v-model="leftPanel" stretch>
            <el-tab-pane label="查询游记" name="search">
              <el-form label-position="top">
                <el-form-item label="关键词">
                  <el-input v-model="keyword" clearable placeholder="目的地、标题或正文" @keyup.enter="loadDiaries" />
                </el-form-item>
                <el-form-item label="搜索模式">
                  <el-segmented v-model="searchMode" :options="searchModeOptions" />
                </el-form-item>
              </el-form>
              <el-button type="primary" :loading="loading" @click="loadDiaries">查询</el-button>
            </el-tab-pane>
            <el-tab-pane label="发布游记" name="publish">
              <el-form label-position="top">
                <el-form-item label="标题">
                  <el-input v-model="form.title" maxlength="160" />
                </el-form-item>
                <el-form-item label="正文">
                  <el-input v-model="form.body" type="textarea" :rows="7" />
                </el-form-item>
                <el-form-item label="媒体 URL">
                  <el-input v-model="form.media_url" clearable placeholder="/media/demo/scenic-photo.jpg" />
                </el-form-item>
              </el-form>
              <el-button type="primary" :loading="creating" @click="createDiary">发布</el-button>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <el-card shadow="never" class="result-card">
          <template #header>游记列表</template>
          <el-table :data="diaries" v-loading="loading" size="small" @row-click="selectDiary">
            <el-table-column prop="title" label="标题" min-width="160" />
            <el-table-column prop="views" label="浏览" width="80" />
            <el-table-column prop="rating_avg" label="评分" width="80" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card shadow="never">
          <el-tabs v-model="activePanel">
            <el-tab-pane label="游记详情" name="detail">
              <div v-if="selected" class="detail-grid">
                <section>
                  <div class="card-header">
                    <h2>{{ selected.title }}</h2>
                    <div class="inline-actions">
                      <el-button link type="primary" @click="prepareAigcFromSelected">同步到 AIGC</el-button>
                      <el-button link type="primary" @click="viewSelected">浏览 +1</el-button>
                    </div>
                  </div>
                  <p class="diary-body">{{ selected.body }}</p>
                  <div v-if="selected.media?.length" class="media-list">
                    <div v-for="media in selected.media" :key="media.id" class="media-item">
                      <el-image
                        v-if="media.media_type === 'image'"
                        :src="media.url"
                        fit="cover"
                        class="media-image"
                      />
                      <div v-else class="media-video">{{ media.url }}</div>
                      <span>{{ media.caption || media.media_type }}</span>
                    </div>
                  </div>
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
                </section>
                <aside v-if="compression" class="compression-panel">
                  <h3>压缩存储</h3>
                  <div class="metric-grid">
                    <div class="metric"><span>算法</span><strong>{{ compression.algorithm }}</strong></div>
                    <div class="metric"><span>原始大小</span><strong>{{ compression.original_size }} B</strong></div>
                    <div class="metric"><span>压缩大小</span><strong>{{ compression.compressed_size }} B</strong></div>
                    <div class="metric"><span>压缩率</span><strong>{{ compression.compression_ratio }}</strong></div>
                  </div>
                </aside>
              </div>
            </el-tab-pane>

            <el-tab-pane label="AIGC 增强" name="aigc">
              <div class="aigc-grid">
                <section>
                  <el-form label-position="top">
                    <el-form-item label="任务">
                      <el-select v-model="agentForm.task">
                        <el-option label="游记动画" value="diary_animation" />
                        <el-option label="游记草稿" value="diary_draft" />
                        <el-option label="分镜脚本" value="storyboard" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="风格">
                      <el-select v-model="agentForm.style">
                        <el-option label="自然" value="natural" />
                        <el-option label="轻快" value="lively" />
                        <el-option label="正式" value="formal" />
                        <el-option label="电影感" value="cinematic" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="镜头数">
                      <el-input-number v-model="agentForm.scene_count" :min="1" :max="8" />
                    </el-form-item>
                    <el-form-item label="文本">
                      <el-input v-model="agentForm.text" type="textarea" :rows="6" />
                    </el-form-item>
                    <el-form-item label="媒体素材">
                      <el-input v-model="mediaText" type="textarea" :rows="3" placeholder="/media/demo/campus-photo.jpg" />
                    </el-form-item>
                  </el-form>
                  <el-button type="primary" :loading="agentLoading" @click="runAgent">生成 AIGC 内容</el-button>
                </section>
                <section v-if="agentResult">
                  <h2>{{ agentResult.result.title }}</h2>
                  <p class="text-block">{{ agentResult.result.draft }}</p>
                  <el-divider />
                  <el-timeline>
                    <el-timeline-item v-for="scene in agentResult.result.storyboard" :key="scene.index">
                      <strong>{{ scene.title }}</strong>
                      <p>{{ scene.description }}</p>
                      <small>{{ scene.narration }} · {{ scene.duration_seconds }}s</small>
                    </el-timeline-item>
                  </el-timeline>
                  <el-link type="primary" :href="agentResult.result.simulated_video_url" target="_blank">模拟视频链接</el-link>
                  <el-divider />
                  <div class="stat"><span>工具</span><strong>{{ agentResult.agent_trace.steps.length }}</strong></div>
                  <div class="stat"><span>媒体</span><strong>{{ agentResult.result.media_analysis.media_count }}</strong></div>
                  <div class="stat"><span>耗时</span><strong>{{ agentResult.agent_trace.total_duration_ms }}ms</strong></div>
                  <el-collapse>
                    <el-collapse-item
                      v-for="step in agentResult.agent_trace.steps"
                      :key="step.step"
                      :title="`${step.step}. ${step.tool}`"
                      :name="step.step"
                    >
                      <p class="trace-line">{{ step.input_summary }}</p>
                      <p class="trace-line">{{ step.output_summary }}</p>
                    </el-collapse-item>
                  </el-collapse>
                </section>
              </div>
            </el-tab-pane>
          </el-tabs>
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
  type AigcAgentPayload,
  type DiaryCommentItem,
  type DiaryCompressionPayload,
  type DiaryItem,
  type DiaryListPayload,
} from "../services/api";
import { authState } from "../services/auth";

const loading = ref(false);
const creating = ref(false);
const keyword = ref("");
const searchMode = ref("fulltext");
const leftPanel = ref("search");
const activePanel = ref("detail");
const diaries = ref<DiaryItem[]>([]);
const selected = ref<DiaryItem | null>(null);
const compression = ref<DiaryCompressionPayload | null>(null);
const rating = ref(5);
const comment = ref("");
const agentLoading = ref(false);
const mediaText = ref("/media/demo/campus-photo.jpg");
const agentResult = ref<AigcAgentPayload | null>(null);
const searchModeOptions = [
  { label: "全文", value: "fulltext" },
  { label: "精确标题", value: "exact_title" },
  { label: "包含", value: "contains" },
];
const form = reactive({
  title: "颐和园旅行日记",
  body: "今天沿着颐和园的湖边步道游览，先看仁寿殿，再到佛香阁附近远眺昆明湖。路线节奏比较舒缓，适合把景点、餐饮和休息点串成半日行程。",
  media_url: "/media/demo/scenic-photo.jpg",
});
const agentForm = reactive({
  task: "diary_animation",
  text: form.body,
  destination_name: "颐和园",
  style: "cinematic",
  scene_count: 4,
});

async function loadDiaries() {
  loading.value = true;
  try {
    const params = new URLSearchParams({ limit: "30", offset: "0" });
    if (keyword.value.trim()) {
      params.set("keyword", keyword.value.trim());
      params.set("mode", searchMode.value);
      const payload = await apiGet<DiaryListPayload>(`/api/v1/diaries/search?${params}`);
      diaries.value = payload.items;
      if (!selected.value && payload.items[0]) {
        await selectDiary(payload.items[0]);
      }
      return;
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
      user_id: authState.user?.id ?? 1,
      destination_id: 1,
      title: form.title,
      body: form.body,
    });
    diaries.value = [diary, ...diaries.value];
    if (form.media_url.trim()) {
      await apiPost(`/api/v1/diaries/${diary.id}/media`, {
        media_type: "image",
        url: form.media_url.trim(),
        caption: "游记媒体",
      });
    }
    await selectDiary(diary);
  } finally {
    creating.value = false;
  }
}

async function selectDiary(row: DiaryItem) {
  selected.value = await apiGet<DiaryItem>(`/api/v1/diaries/${row.id}`);
  compression.value = await apiGet<DiaryCompressionPayload>(`/api/v1/diaries/${row.id}/compression`);
  syncAgentFromSelected();
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

async function runAgent() {
  agentLoading.value = true;
  try {
    agentResult.value = await apiPost<AigcAgentPayload>("/api/v1/aigc/agent/run", {
      ...agentForm,
      media_urls: parseMediaUrls(),
    });
  } finally {
    agentLoading.value = false;
  }
}

function syncAgentFromSelected() {
  if (!selected.value) return;
  agentForm.text = selected.value.body ?? selected.value.summary;
  agentForm.destination_name = selected.value.title;
  const mediaUrls = selected.value.media?.map((item) => item.url).filter(Boolean) ?? [];
  if (mediaUrls.length > 0) {
    mediaText.value = mediaUrls.join("\n");
  }
}

function prepareAigcFromSelected() {
  syncAgentFromSelected();
  activePanel.value = "aigc";
}

function parseMediaUrls() {
  return mediaText.value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
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

.diary-action-card :deep(.el-tabs__header) {
  margin-bottom: 18px;
}

.card-header h2,
.aigc-grid h2 {
  margin: 0;
  color: #101828;
  font-size: 18px;
}

.detail-grid,
.aigc-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.aigc-grid {
  grid-template-columns: minmax(280px, 0.8fr) minmax(0, 1.2fr);
}

.compression-panel {
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

.diary-body {
  color: #475467;
  line-height: 1.7;
  white-space: pre-wrap;
}

.text-block,
.trace-line {
  color: #475467;
  line-height: 1.7;
  white-space: pre-wrap;
}

.trace-line {
  margin: 0 0 8px;
  line-height: 1.6;
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
  .aigc-grid {
    grid-template-columns: minmax(0, 1fr);
  }

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
