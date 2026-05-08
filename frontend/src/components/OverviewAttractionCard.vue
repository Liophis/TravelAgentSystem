<template>
  <article class="overview-card" :class="{ active }" @mouseenter="emit('hover')" @focusin="emit('hover')">
    <div class="overview-image-wrap">
      <img :src="imageSrc" :alt="item.name" loading="lazy" @error="emit('image-error', $event)" />
    </div>
    <div class="overview-body">
      <h3>{{ item.name }}</h3>
      <p>{{ item.description || item.address || t('common.noData') }}</p>
      <button type="button" class="overview-link" @click.prevent="emit('select-day', item.dayArrayIndex)">
        {{ t('common.viewMore') }}
      </button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

export type OverviewAttractionItem = {
  name: string
  address: string
  visit_duration: number
  description: string
  dayArrayIndex: number
}

defineProps<{
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
</script>
