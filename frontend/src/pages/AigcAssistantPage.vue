<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>AIGC 辅助</h1>
        <p>生成游记草稿、标题和短视频分镜提示词。</p>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="主题">
              <el-input v-model="draftForm.topic" />
            </el-form-item>
            <el-form-item label="关键词">
              <el-input v-model="keywordText" placeholder="图书馆, 食堂, 路线" />
            </el-form-item>
            <el-form-item label="语气">
              <el-select v-model="draftForm.tone">
                <el-option label="自然" value="自然" />
                <el-option label="轻松" value="轻松" />
                <el-option label="正式" value="正式" />
              </el-select>
            </el-form-item>
          </el-form>
          <el-button type="primary" :loading="draftLoading" @click="generateDraft">生成草稿</el-button>
        </el-card>

        <el-card shadow="never" class="result-card">
          <el-form label-position="top">
            <el-form-item label="分镜文本">
              <el-input v-model="storyText" type="textarea" :rows="5" />
            </el-form-item>
            <el-form-item label="镜头数">
              <el-input-number v-model="sceneCount" :min="1" :max="8" />
            </el-form-item>
            <el-form-item label="媒体素材">
              <el-input v-model="mediaText" type="textarea" :rows="3" placeholder="/media/demo/photo.jpg" />
            </el-form-item>
          </el-form>
          <el-button :loading="storyLoading" @click="generateStory">生成分镜</el-button>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card v-if="draft" shadow="never">
          <template #header>{{ draft.title }}</template>
          <p class="text-block">{{ draft.draft }}</p>
          <el-divider />
          <p class="text-block">{{ draft.prompt }}</p>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card v-if="storyboard" shadow="never">
          <template #header>短视频分镜</template>
          <el-timeline>
            <el-timeline-item v-for="scene in storyboard.scenes" :key="scene.index">
              <strong>{{ scene.title }}</strong>
              <p>{{ scene.description }}</p>
              <small>{{ scene.duration_seconds }}s</small>
            </el-timeline-item>
          </el-timeline>
          <el-divider />
          <p class="text-block">{{ storyboard.prompt }}</p>
          <el-link type="primary" :href="storyboard.simulated_video_url" target="_blank">模拟视频链接</el-link>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";

import { apiPost, type AigcDraftPayload, type AigcStoryboardPayload } from "../services/api";

const draftLoading = ref(false);
const storyLoading = ref(false);
const keywordText = ref("图书馆, 食堂, 路线");
const storyText = ref("从沙河校区校门出发，经过食堂，最后到图书馆完成一次导览。");
const mediaText = ref("/media/demo/campus-photo.jpg");
const sceneCount = ref(4);
const draft = ref<AigcDraftPayload | null>(null);
const storyboard = ref<AigcStoryboardPayload | null>(null);
const draftForm = reactive({
  topic: "沙河校区午后路线",
  tone: "自然",
});

async function generateDraft() {
  draftLoading.value = true;
  try {
    draft.value = await apiPost<AigcDraftPayload>("/api/v1/aigc/diary-draft", {
      ...draftForm,
      keywords: keywordText.value.split(",").map((item) => item.trim()).filter(Boolean),
    });
  } finally {
    draftLoading.value = false;
  }
}

async function generateStory() {
  storyLoading.value = true;
  try {
    storyboard.value = await apiPost<AigcStoryboardPayload>("/api/v1/aigc/storyboard", {
      text: storyText.value,
      scene_count: sceneCount.value,
      media_urls: mediaText.value.split("\n").map((item) => item.trim()).filter(Boolean),
    });
  } finally {
    storyLoading.value = false;
  }
}
</script>

<style scoped>
.text-block {
  color: #475467;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>
