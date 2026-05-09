<template>
  <main class="result-page">
    <div class="result-shell">
      <section class="result-hero">
        <div>
          <p class="result-kicker">{{ t('result.overview.subtitle') }}</p>
          <h1>{{ t('result.overview.title') }}</h1>
          <p class="result-desc">{{ overviewText }}</p>
        </div>
        <div class="result-actions">
          <a-button type="primary" @click="goHome">{{ t('nav.cta') }}</a-button>
          <a-button :disabled="!planAvailable" @click="showChat = !showChat">AI Chat</a-button>
        </div>
      </section>

      <section class="result-grid">
        <a-card class="result-panel overview-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.overview') }}</h2>
            <span>{{ dateRangeText }}</span>
          </div>
          <div v-if="attractions.length > 0" class="overview-list">
            <OverviewAttractionCard
              v-for="item in attractions"
              :key="`${item.id}-${item.name}`"
              :item="item"
              :image-src="item.image_url || ''"
              :active="false"
              @hover="noop"
              @select-day="noop"
              @image-error="noop"
            />
          </div>
          <p v-else class="result-empty">{{ t('result.overview.empty') }}</p>
        </a-card>

        <a-card class="result-panel map-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.map') }}</h2>
          </div>
          <div v-if="planAvailable" id="amap-container" style="width: 100%; height: 400px"></div>
          <div v-else class="graph-placeholder">请先返回首页生成行程，再查看地图路线。</div>
        </a-card>

        <a-card class="result-panel days-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.days') }}</h2>
          </div>
          <a-timeline v-if="days.length > 0">
            <a-timeline-item v-for="day in days" :key="day.day_index">
              <strong>{{ t('common.dayNumber', { day: day.day_index + 1 }) }}</strong>
              <p>{{ day.description }}</p>
              <p>{{ day.attractions.map((item) => item.name).join('、') || t('common.noData') }}</p>
            </a-timeline-item>
          </a-timeline>
          <p v-else class="result-empty">{{ t('result.overview.empty') }}</p>
        </a-card>

        <a-card class="result-panel graph-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.budget') }}</h2>
          </div>
          <div v-if="budget" class="budget-summary">
            <p>{{ t('result.budget.attraction') }}: {{ budget.total_attractions }}</p>
            <p>{{ t('result.budget.hotel') }}: {{ budget.total_hotels }}</p>
            <p>{{ t('result.budget.meal') }}: {{ budget.total_meals }}</p>
            <p>{{ t('result.budget.transport') }}: {{ budget.total_transportation }}</p>
            <p><strong>Total: {{ budget.total }}</strong></p>
          </div>
          <p v-else class="result-empty">{{ t('common.noData') }}</p>
        </a-card>
      </section>
    </div>

    <div v-if="showChat" class="chat-drawer">
      <AIChat :messages="chatMessages" input-value="" @close="showChat = false" @send="sendChat" @quick-question="handleQuickQuestion" />
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AMapLoader from '@amap/amap-jsapi-loader'

import AIChat from '@/components/AIChat.vue'
import OverviewAttractionCard from '@/components/OverviewAttractionCard.vue'
import { askTripChat, findRoute } from '@/services/api'
import { getCurrentPlan } from '@/services/store'
import type { ChatMessage } from '@/types'

const router = useRouter()
const { t } = useI18n()
const showChat = ref(false)
const chatMessages = ref<ChatMessage[]>([])
const chatPending = ref(false)
const map = ref<any>(null)

const planRef = getCurrentPlan()

const plan = computed(() => planRef.value)
const planAvailable = computed(() => Boolean(plan.value))
const days = computed(() => plan.value?.days || [])
const attractions = computed(() => {
  return days.value.flatMap((day) => day.attractions.map((item) => ({ ...item, dayArrayIndex: day.day_index })))
})
const budget = computed(() => plan.value?.budget)
const dateRangeText = computed(() => {
  if (!plan.value) return t('common.noData')
  return t('result.dateRange', { start: plan.value.start_date, end: plan.value.end_date })
})
const overviewText = computed(() => {
  if (!plan.value) return '当前还没有可展示的行程，请先返回首页生成计划。'
  return plan.value.overall_suggestions || t('result.overview.empty')
})

const goHome = () => void router.push('/')
const noop = () => undefined

const sendChat = async (message: string) => {
  const content = message.trim()
  if (!content || !plan.value || chatPending.value) return

  chatMessages.value.push({ role: 'user', content })
  chatPending.value = true

  try {
    const response = await askTripChat({
      message: content,
      trip_plan: plan.value,
      history: chatMessages.value,
    })

    chatMessages.value.push({
      role: 'assistant',
      content: response.reply || '暂时没有生成回复，请稍后再试。',
    })
  } catch (error) {
    console.error('[AI Chat] 请求失败:', error)
    chatMessages.value.push({
      role: 'assistant',
      content: '当前问答服务暂时不可用，请稍后重试。',
    })
  } finally {
    chatPending.value = false
  }
}

const handleQuickQuestion = (message: string) => {
  void sendChat(message)
}

const initAMap = async () => {
  await nextTick()
  if (!plan.value || attractions.value.length === 0) return

  const mapJsKey = import.meta.env.VITE_AMAP_WEB_JS_KEY || ''
  if (!mapJsKey) {
    console.error('高德地图 JS Key 未配置，请在 .env.local 中设置 VITE_AMAP_WEB_JS_KEY')
    return
  }

  try {
    const AMap = await AMapLoader.load({
      key: mapJsKey,
      version: '2.0',
      plugins: ['AMap.Marker', 'AMap.Polyline', 'AMap.InfoWindow'],
    })

    const firstAttraction = attractions.value[0]
    map.value = new AMap.Map('amap-container', {
      zoom: 12,
      center: [firstAttraction.longitude, firstAttraction.latitude],
    })

    if (attractions.value.length === 1) {
      const marker = new AMap.Marker({
        position: [firstAttraction.longitude, firstAttraction.latitude],
        title: firstAttraction.name,
      })
      map.value.add(marker)
      map.value.setFitView([marker])
      return
    }

    const start = attractions.value[0]
    const end = attractions.value[attractions.value.length - 1]
    const res = await findRoute(start.id, end.id)
    const routeData = res as any
    const pathNodes = routeData.path_nodes || []

    if (pathNodes.length > 1) {
      const coords = pathNodes.map((point: any) => [point.longitude, point.latitude])
      const polyline = new AMap.Polyline({
        path: coords,
        borderWeight: 2,
        strokeColor: '#1890ff',
        lineJoin: 'round',
        isOutline: true,
        outlineColor: '#ffffff',
        outlineWeight: 1,
      })
      map.value.add(polyline)

      const markers = pathNodes
        .filter((_: any, index: number) => index === 0 || index === pathNodes.length - 1)
        .map((node: any) => new AMap.Marker({
          position: [node.longitude, node.latitude],
          title: node.name,
        }))

      if (markers.length > 0) {
        map.value.add(markers)
        map.value.setFitView([...markers, polyline], true, [50, 50, 50, 50])
      } else {
        map.value.setFitView([polyline])
      }
      return
    }

    const fallbackCoords = attractions.value.map((item) => [item.longitude, item.latitude])
    const fallbackPolyline = new AMap.Polyline({
      path: fallbackCoords,
      strokeColor: '#1890ff',
    })
    map.value.add(fallbackPolyline)
    map.value.setFitView([fallbackPolyline])
  } catch (error) {
    console.error('AMap 初始化失败:', error)
  }
}

onMounted(() => {
  if (plan.value) {
    void initAMap()
  }
})
</script>
