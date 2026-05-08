<template>
  <main class="result-page">
    <NavBar @brand-click="goHome" @cta-click="goHome" />

    <div class="result-shell">
      <section class="result-hero">
        <div>
          <p class="result-kicker">{{ t('result.overview.subtitle') }}</p>
          <h1>{{ t('result.overview.title') }}</h1>
          <p class="result-desc">{{ t('result.overview.empty') }}</p>
        </div>
        <div class="result-actions">
          <a-button type="primary" @click="goHome">{{ t('nav.cta') }}</a-button>
          <a-button @click="showChat = !showChat">AI Chat</a-button>
        </div>
      </section>

      <section class="result-grid">
        <a-card class="result-panel overview-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.overview') }}</h2>
            <span>{{ t('result.dateRange', { start: '2026-05-01', end: '2026-05-03' }) }}</span>
          </div>
          <div class="overview-list">
            <OverviewAttractionCard
              v-for="item in attractions"
              :key="item.name"
              :item="item"
              :image-src="item.imageSrc"
              :active="false"
              @hover="noop"
              @select-day="noop"
              @image-error="noop"
            />
          </div>
        </a-card>

        <a-card class="result-panel map-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.map') }}</h2>
          </div>
          <div class="map-placeholder">Map canvas placeholder</div>
        </a-card>

        <a-card class="result-panel days-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.days') }}</h2>
          </div>
          <a-timeline>
            <a-timeline-item v-for="day in days" :key="day.day_index">
              <strong>{{ t('common.dayNumber', { day: day.day_index + 1 }) }}</strong>
              <p>{{ day.description }}</p>
            </a-timeline-item>
          </a-timeline>
        </a-card>

        <a-card class="result-panel graph-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.graph') }}</h2>
          </div>
          <div class="graph-placeholder">Knowledge graph placeholder</div>
        </a-card>
      </section>
    </div>

    <div v-if="showChat" class="chat-drawer">
      <AIChat :messages="chatMessages" input-value="" @close="showChat = false" @send="noop" @quick-question="noop" />
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import NavBar from '@/components/NavBar.vue'
import AIChat from '@/components/AIChat.vue'
import OverviewAttractionCard from '@/components/OverviewAttractionCard.vue'
import type { ChatMessage } from '@/types'

const router = useRouter()
const { t } = useI18n()
const showChat = ref(false)
const chatMessages = ref<ChatMessage[]>([])

import { getCurrentPlan } from '@/services/store'

const planRef = getCurrentPlan()

const attractions = computed(() => {
  const plan = planRef.value
  if (!plan) return []
  // flatten attractions from days
  return (plan.days || []).flatMap((d: any) => (d.attractions || []).map((a: any) => ({ ...a, dayArrayIndex: d.day_index })))
})

const days = computed(() => {
  const plan = planRef.value
  if (!plan) return []
  return plan.days || []
})

const goHome = () => void router.push('/')
const noop = () => undefined
</script>
