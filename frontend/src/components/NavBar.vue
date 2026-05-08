<template>
  <nav class="top-nav">
    <div class="nav-inner">
      <button type="button" class="nav-brand" @click="emit('brand-click')">
        <span class="nav-mark">TS</span>
        <span class="nav-text">
          <strong>{{ t('app.brand') }}</strong>
          <small>{{ t('app.subBrand') }}</small>
        </span>
      </button>

      <div class="nav-actions">
        <a-select v-model:value="locale" size="small" class="nav-locale" :aria-label="t('app.language.label')">
          <a-select-option value="zh-CN">{{ t('app.language.zh') }}</a-select-option>
          <a-select-option value="ja-JP">{{ t('app.language.ja') }}</a-select-option>
          <a-select-option value="en-US">{{ t('app.language.en') }}</a-select-option>
        </a-select>
        <a-button type="primary" class="nav-cta" @click="emit('cta-click')">
          {{ t('nav.cta') }}
        </a-button>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

const emit = defineEmits<{
  (e: 'brand-click'): void
  (e: 'cta-click'): void
}>()
</script>
