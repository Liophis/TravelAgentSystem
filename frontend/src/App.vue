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
          <a-form-item label="小红书样例 JSON 路径">
            <a-input v-model:value="settingsForm.xhs_sample_notes_path" placeholder="例如：/abs/path/to/xhs_notes.json" allow-clear />
          </a-form-item>
          <a-form-item label="外部内容导入">
            <div class="xhs-import-panel">
              <a-select v-model:value="xhsImportFormatHint" size="small">
                <a-select-option value="auto">自动识别</a-select-option>
                <a-select-option value="normalized_notes">规范化 notes 数组</a-select-option>
                <a-select-option value="xhs_search_response">小红书搜索原始响应 / TripStar bundle</a-select-option>
                <a-select-option value="xhs_detail_response">小红书详情原始响应</a-select-option>
                <a-select-option value="third_party_items">第三方中间数据</a-select-option>
              </a-select>
              <input type="file" accept="application/json,.json" @change="handleXhsFileChange" />
              <div class="xhs-import-actions">
                <a-button type="default" :loading="xhsImporting" @click="importSelectedXhsFile" :disabled="!selectedXhsFile">
                  导入 JSON 样例
                </a-button>
                <a-button danger :loading="xhsImporting" @click="clearImportedXhsNotes">
                  清空导入并回退
                </a-button>
              </div>
              <div class="xhs-live-refresh">
                <a-input v-model:value="xhsRefreshForm.city" placeholder="实时刷新城市，例如：北京" />
                <a-input v-model:value="xhsRefreshForm.keywords" placeholder="可选关键词，例如：历史文化 休闲" />
                <a-input-number v-model:value="xhsRefreshForm.max_items" :min="1" :max="8" style="width: 100%" />
                <a-button type="primary" :loading="xhsRefreshing" @click="refreshXhsFromTripStar">
                  通过 TripStar 实时刷新
                </a-button>
              </div>
              <div v-if="xhsSourceStatus" class="xhs-import-status">
                <strong>当前内容源：</strong>
                <span>{{ renderXhsSourceLabel(xhsSourceStatus.active_source) }}</span>
                <p>来源名：{{ xhsSourceStatus.source_name }}</p>
                <p>识别格式：{{ renderXhsFormatLabel(xhsSourceStatus.format_kind) }}</p>
                <p>笔记数：{{ xhsSourceStatus.note_count }}</p>
                <p v-if="xhsSourceStatus.path">路径：{{ xhsSourceStatus.path }}</p>
                <p v-if="xhsSourceStatus.updated_at">更新时间：{{ xhsSourceStatus.updated_at }}</p>
              </div>
            </div>
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
import type { RuntimeSettings, XHSContentSourceStatus } from '@/types'
import {
  clearXhsContentSourceImport,
  getRuntimeSettings,
  getXhsContentSourceStatus,
  importXhsContentSource,
  refreshXhsContentSource,
  saveRuntimeSettings,
} from '@/services/api'
import { message } from 'ant-design-vue'

const { t, locale } = useI18n()
const year = new Date().getFullYear()
const settingsVisible = ref(false)
const settingsLoading = ref(false)
const settingsSaving = ref(false)
const xhsImporting = ref(false)
const xhsRefreshing = ref(false)
const selectedXhsFile = ref<File | null>(null)
const xhsSourceStatus = ref<XHSContentSourceStatus | null>(null)
const xhsImportFormatHint = ref('auto')
const xhsRefreshForm = reactive({
  city: '',
  keywords: '',
  max_items: 4,
})
const settingsForm = reactive<RuntimeSettings>({
  api_base_url: '',
  amap_web_api_key: '',
  vite_amap_web_js_key: '',
  google_maps_api_key: '',
  google_maps_proxy: '',
  xhs_cookie: '',
  xhs_sample_notes_path: '',
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
  settingsForm.xhs_sample_notes_path = settings.xhs_sample_notes_path || ''
  settingsForm.openai_api_key = settings.openai_api_key || ''
  settingsForm.openai_base_url = settings.openai_base_url || ''
  settingsForm.openai_model = settings.openai_model || ''
  settingsForm.log_level = settings.log_level || ''
}

const renderXhsSourceLabel = (source: string) => {
  if (source === 'runtime_import') return '前端导入外部样例'
  if (source === 'configured_path') return '服务端配置路径'
  return '内置本地样例降级'
}

const renderXhsFormatLabel = (formatKind: string) => {
  if (formatKind === 'normalized_notes') return '规范化 notes'
  if (formatKind === 'xhs_search_items' || formatKind === 'xhs_search_response') return '小红书搜索结果 / TripStar bundle'
  if (formatKind === 'xhs_detail_response') return '小红书详情结果'
  if (formatKind === 'third_party_items' || formatKind === 'single_third_party_item') return '第三方中间数据'
  if (formatKind === 'configured_path') return '配置路径文件'
  if (formatKind === 'builtin_fallback') return '内置降级样例'
  return formatKind || '未知格式'
}

const refreshXhsSourceStatus = async () => {
  const response = await getXhsContentSourceStatus()
  xhsSourceStatus.value = response.data || null
}

const openSettings = async () => {
  settingsVisible.value = true
  settingsLoading.value = true
  try {
    applyRuntimeSettings(await getRuntimeSettings())
    await refreshXhsSourceStatus()
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
    await refreshXhsSourceStatus()
    message.success('设置已保存并应用')
    settingsVisible.value = false
  } catch (error: any) {
    message.error(error?.message || '保存设置失败')
  } finally {
    settingsSaving.value = false
  }
}

const handleXhsFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  selectedXhsFile.value = target.files?.[0] || null
}

const importSelectedXhsFile = async () => {
  if (!selectedXhsFile.value) {
    message.warning('请先选择一个 JSON 文件')
    return
  }

  xhsImporting.value = true
  try {
    const rawText = await selectedXhsFile.value.text()
    const parsed = JSON.parse(rawText)
    const response = await importXhsContentSource({
      source_name: selectedXhsFile.value.name,
      format_hint: xhsImportFormatHint.value,
      payload: parsed,
    })
    xhsSourceStatus.value = response.data || null
    message.success('外部小红书样例已导入')
  } catch (error: any) {
    message.error(error?.response?.data?.detail || error?.message || '导入失败，请检查 JSON 结构')
  } finally {
    xhsImporting.value = false
  }
}

const clearImportedXhsNotes = async () => {
  xhsImporting.value = true
  try {
    const response = await clearXhsContentSourceImport()
    xhsSourceStatus.value = response.data || null
    message.success('已清空导入样例，当前会回退到配置路径或内置样例')
  } catch (error: any) {
    message.error(error?.response?.data?.detail || error?.message || '清空导入失败')
  } finally {
    xhsImporting.value = false
  }
}

const refreshXhsFromTripStar = async () => {
  if (!xhsRefreshForm.city.trim()) {
    message.warning('请先填写要刷新的城市')
    return
  }

  xhsRefreshing.value = true
  try {
    const response = await refreshXhsContentSource({
      city: xhsRefreshForm.city,
      keywords: xhsRefreshForm.keywords,
      max_items: xhsRefreshForm.max_items,
    })
    xhsSourceStatus.value = response.data || null
    const rawCount = response.meta?.raw_note_count ?? 0
    message.success(`已刷新小红书内容源，命中 ${rawCount} 条原始笔记`)
  } catch (error: any) {
    message.error(error?.response?.data?.detail || error?.message || '实时刷新失败')
  } finally {
    xhsRefreshing.value = false
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
