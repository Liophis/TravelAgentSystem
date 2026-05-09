<template>
  <div id="app-shell">
    <a-layout class="shell-layout">
      <a-layout-header class="shell-header">
        <div class="shell-header-inner">
          <button type="button" class="brand" @click="$router.push('/')">
            <img src="/brand-mark.png" alt="TS" class="brand-mark" />
            <span class="brand-copy">
              <strong>{{ t('app.brand') }}</strong>
              <small>{{ t('app.subBrand') }}</small>
            </span>
          </button>

          <div class="shell-header-actions">
            <a-select v-model:value="locale" size="small" class="locale-select" :aria-label="t('app.language.label')">
              <a-select-option value="zh-CN">{{ t('app.language.zh') }}</a-select-option>
              <a-select-option value="ja-JP">{{ t('app.language.ja') }}</a-select-option>
              <a-select-option value="en-US">{{ t('app.language.en') }}</a-select-option>
            </a-select>
            <a-button type="default" ghost class="header-pill" @click="$router.push('/result')">
              {{ t('app.badge') }}
            </a-button>
            <a-button type="default" ghost class="header-pill" @click="openSettings">
              运行时设置
            </a-button>
          </div>
        </div>
      </a-layout-header>

      <a-layout-content class="shell-content">
        <router-view />
      </a-layout-content>

      <a-layout-footer class="shell-footer">
        <div class="shell-footer-inner">
          <span>{{ t('app.footerBrand') }}</span>
          <span>{{ t('app.footerCopy', { year }) }}</span>
        </div>
      </a-layout-footer>
    </a-layout>

    <a-modal
      v-model:open="settingsVisible"
      title="运行时设置"
      :confirm-loading="settingsSaving"
      ok-text="保存并应用"
      cancel-text="取消"
      @ok="saveSettingsNow"
    >
      <a-spin :spinning="settingsLoading">
        <a-form layout="vertical" :model="settingsForm">
          <a-form-item label="后端地址">
            <a-input v-model:value="settingsForm.api_base_url" placeholder="例如：http://localhost:8000" allow-clear />
          </a-form-item>
          <a-form-item label="高德 Web Service Key">
            <a-input-password v-model:value="settingsForm.amap_web_api_key" allow-clear />
          </a-form-item>
          <a-form-item label="高德 JS Key">
            <a-input-password v-model:value="settingsForm.vite_amap_web_js_key" allow-clear />
          </a-form-item>
          <a-form-item label="小红书 Cookie">
            <a-textarea v-model:value="settingsForm.xhs_cookie" :rows="4" allow-clear />
          </a-form-item>
          <a-form-item label="OpenAI API Key">
            <a-input-password v-model:value="settingsForm.openai_api_key" allow-clear />
          </a-form-item>
          <a-form-item label="OpenAI Base URL">
            <a-input v-model:value="settingsForm.openai_base_url" allow-clear />
          </a-form-item>
          <a-form-item label="OpenAI Model">
            <a-input v-model:value="settingsForm.openai_model" allow-clear />
          </a-form-item>
        </a-form>
      </a-spin>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { setAppLocale, type AppLocale } from '@/i18n'
import type { RuntimeSettings } from '@/types'
import { getRuntimeSettings, saveRuntimeSettings } from '@/services/api'
import { message } from 'ant-design-vue'

const { t, locale } = useI18n()
const year = new Date().getFullYear()
const settingsVisible = ref(false)
const settingsLoading = ref(false)
const settingsSaving = ref(false)
const settingsForm = reactive<RuntimeSettings>({
  api_base_url: '',
  amap_web_api_key: '',
  vite_amap_web_js_key: '',
  google_maps_api_key: '',
  google_maps_proxy: '',
  xhs_cookie: '',
  openai_api_key: '',
  openai_base_url: '',
  openai_model: '',
  log_level: '',
})

const applyRuntimeSettings = (settings: RuntimeSettings) => {
  settingsForm.api_base_url = settings.api_base_url || ''
  settingsForm.amap_web_api_key = settings.amap_web_api_key || ''
  settingsForm.vite_amap_web_js_key = settings.vite_amap_web_js_key || ''
  settingsForm.google_maps_api_key = settings.google_maps_api_key || ''
  settingsForm.google_maps_proxy = settings.google_maps_proxy || ''
  settingsForm.xhs_cookie = settings.xhs_cookie || ''
  settingsForm.openai_api_key = settings.openai_api_key || ''
  settingsForm.openai_base_url = settings.openai_base_url || ''
  settingsForm.openai_model = settings.openai_model || ''
  settingsForm.log_level = settings.log_level || ''
}

const openSettings = async () => {
  settingsVisible.value = true
  settingsLoading.value = true
  try {
    applyRuntimeSettings(await getRuntimeSettings())
  } catch (error: any) {
    message.error(error?.message || '读取设置失败')
  } finally {
    settingsLoading.value = false
  }
}

const saveSettingsNow = async () => {
  settingsSaving.value = true
  try {
    const saved = await saveRuntimeSettings(settingsForm)
    applyRuntimeSettings(saved)
    message.success('设置已保存并应用')
    settingsVisible.value = false
  } catch (error: any) {
    message.error(error?.message || '保存设置失败')
  } finally {
    settingsSaving.value = false
  }
}

watch(
  locale,
  (nextLocale) => {
    setAppLocale(nextLocale as AppLocale)
    document.title = t('app.title')
  },
  { immediate: true }
)
</script>
