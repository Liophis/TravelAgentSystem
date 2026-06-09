<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>发布游记与 AIGC</h1>
        <p>撰写景区或学校目的地游记，并把正文和媒体素材交给 AIGC Agent 生成草稿、分镜和模拟视频。</p>
      </div>
      <el-button @click="$router.push('/diaries')">返回游记列表</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="10">
        <el-card shadow="never">
          <template #header>发布游记</template>
          <el-form label-position="top">
            <el-form-item label="标题">
              <el-input v-model="form.title" maxlength="160" />
            </el-form-item>
            <el-form-item label="正文">
              <el-input v-model="form.body" type="textarea" :rows="10" />
            </el-form-item>
            <el-form-item label="媒体 URL">
              <el-input v-model="form.media_url" clearable placeholder="/media/demo/scenic-photo.jpg" />
            </el-form-item>
          </el-form>
          <div class="action-row">
            <el-button type="primary" :loading="creating" @click="createDiary">发布</el-button>
            <el-button @click="syncAgentFromForm">同步到 AIGC</el-button>
          </div>
          <el-alert
            v-if="createdDiary"
            class="created-alert"
            type="success"
            :closable="false"
            :title="`已发布：${createdDiary.title}`"
          />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="14">
        <el-card shadow="never">
          <template #header>AIGC Agent</template>
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
                <el-form-item label="目的地">
                  <el-input v-model="agentForm.destination_name" />
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
                  <el-input v-model="agentForm.text" type="textarea" :rows="7" />
                </el-form-item>
                <el-form-item label="媒体素材">
                  <el-input v-model="mediaText" type="textarea" :rows="3" placeholder="/media/demo/scenic-photo.jpg" />
                </el-form-item>
              </el-form>
              <el-button type="primary" :loading="agentLoading" @click="runAgent">生成 AIGC 内容</el-button>
            </section>

            <section v-if="agentResult" class="agent-result">
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
              <div class="metric-grid">
                <div class="metric"><span>工具步骤</span><strong>{{ agentResult.agent_trace.steps.length }}</strong></div>
                <div class="metric"><span>媒体数量</span><strong>{{ agentResult.result.media_analysis.media_count }}</strong></div>
                <div class="metric"><span>耗时</span><strong>{{ agentResult.agent_trace.total_duration_ms }}ms</strong></div>
              </div>
              <el-collapse class="trace-collapse">
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
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";

import { apiPost, type AigcAgentPayload, type DiaryItem } from "../services/api";
import { authState } from "../services/auth";

const creating = ref(false);
const agentLoading = ref(false);
const createdDiary = ref<DiaryItem | null>(null);
const mediaText = ref("/media/demo/scenic-photo.jpg");
const agentResult = ref<AigcAgentPayload | null>(null);

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

async function createDiary() {
  creating.value = true;
  try {
    const diary = await apiPost<DiaryItem>("/api/v1/diaries", {
      user_id: authState.user?.id ?? 1,
      destination_id: 1,
      title: form.title,
      body: form.body,
    });
    createdDiary.value = diary;
    if (form.media_url.trim()) {
      await apiPost(`/api/v1/diaries/${diary.id}/media`, {
        media_type: "image",
        url: form.media_url.trim(),
        caption: "游记媒体",
      });
    }
    syncAgentFromForm();
  } finally {
    creating.value = false;
  }
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

function syncAgentFromForm() {
  agentForm.text = form.body;
  agentForm.destination_name = inferDestinationName(form.title);
  mediaText.value = form.media_url.trim() || mediaText.value;
}

function inferDestinationName(title: string) {
  const match = title.match(/^(.+?)(旅行日记|游记|半日|一日|：|:)/);
  return match?.[1]?.trim() || agentForm.destination_name;
}

function parseMediaUrls() {
  return mediaText.value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}
</script>

<style scoped>
.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.created-alert {
  margin-top: 14px;
}

.aigc-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.8fr) minmax(0, 1.2fr);
  gap: 18px;
  align-items: start;
}

.agent-result h2 {
  margin: 0;
  color: #101828;
  font-size: 18px;
}

.text-block,
.trace-line {
  color: #475467;
  line-height: 1.7;
  white-space: pre-wrap;
}

.trace-line {
  margin: 0 0 8px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
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

.trace-collapse {
  margin-top: 12px;
}

@media (max-width: 1200px) {
  .aigc-grid,
  .metric-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
