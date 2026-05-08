<template>
  <div id="app-shell">
    <a-layout class="shell-layout">
      <a-layout-header class="shell-header">
        <div class="shell-header-inner">
          <button type="button" class="brand" @click="$router.push('/')">
            <img src="/brand-placeholder.svg" alt="TS" class="brand-mark" />
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
  </div>
</template>

<script setup lang="ts">
import { watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { setAppLocale, type AppLocale } from '@/i18n'

const { t, locale } = useI18n()
const year = new Date().getFullYear()

watch(
  locale,
  (nextLocale) => {
    setAppLocale(nextLocale as AppLocale)
    document.title = t('app.title')
  },
  { immediate: true }
)
</script>
