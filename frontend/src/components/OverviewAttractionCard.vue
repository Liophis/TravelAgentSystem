<template>
  <article class="overview-card" :class="{ active }" @mouseenter="emit('hover')" @focusin="emit('hover')">
    <div class="overview-image-wrap">
      <img :src="imageSrc" :alt="item.name" loading="lazy" @error="emit('image-error', $event)" />
    </div>
    <div class="overview-body">
      <h3>{{ item.name }}</h3>
      <p>{{ item.description || item.address || t('common.noData') }}</p>
      <p v-if="sourceText" class="overview-card-meta">来源：{{ sourceText }}</p>
      <p v-if="reasonText" class="overview-card-meta">{{ reasonText }}</p>
      <button type="button" class="overview-link" @click.prevent="emit('select-day', item.dayArrayIndex)">
        {{ t('common.viewMore') }}
      </button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { ContentSource } from '@/types'

export type OverviewAttractionItem = {
  name: string
  address: string
  visit_duration: number
  description: string
  dayArrayIndex: number
  content_sources?: ContentSource[]
  recommendation_reasons?: string[]
}

const props = defineProps<{
  item: OverviewAttractionItem
  imageSrc: string
  active: boolean
}>()

const emit = defineEmits<{
  (e: 'hover'): void
  (e: 'select-day', dayArrayIndex: number): void
  (e: 'image-error', event: Event): void
}>()

const { t } = useI18n()
const sourceText = computed(() => props.item.content_sources?.map((item) => item.source_label).filter(Boolean).join(' / ') || '')
const reasonText = computed(() => props.item.recommendation_reasons?.[0] || '')
</script>
