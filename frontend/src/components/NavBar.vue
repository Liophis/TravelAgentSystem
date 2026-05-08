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
