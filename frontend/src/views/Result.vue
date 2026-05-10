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

      <section v-if="requestSummary" class="result-summary-strip">
        <div class="summary-chip">{{ requestSummary.city }}</div>
        <div class="summary-chip">{{ requestSummary.travel_days }} 天</div>
        <div class="summary-chip">{{ requestSummary.transportation }}</div>
        <div class="summary-chip">{{ requestSummary.accommodation }}</div>
        <div v-for="preference in requestSummary.preferences" :key="preference" class="summary-chip soft">{{ preference }}</div>
      </section>

      <section v-if="requestSummary" class="result-note-card">
        <strong>数据说明</strong>
        <p>{{ requestSummary.data_note }}</p>
        <p v-if="requestSummary.free_text_input">额外需求：{{ requestSummary.free_text_input }}</p>
      </section>

      <section class="result-switcher">
        <button
          v-for="panel in panels"
          :key="panel.key"
          type="button"
          class="result-switcher-btn"
          :class="{ active: activePanel === panel.key }"
          @click="activePanel = panel.key"
        >
          {{ panel.label }}
        </button>
      </section>

      <section class="result-grid">
        <a-card v-if="activePanel === 'route'" class="result-panel route-panel" :bordered="false">
          <div class="panel-head">
            <h2>路线摘要</h2>
            <span>{{ routeSummary?.sourceLabel || '等待路线生成' }}</span>
          </div>
          <div v-if="routeSummary" class="route-summary">
            <p><strong>起点：</strong>{{ routeSummary.startName }}</p>
            <p><strong>终点：</strong>{{ routeSummary.endName }}</p>
            <p><strong>总距离：</strong>{{ routeSummary.distanceText }}</p>
            <p><strong>预计耗时：</strong>{{ routeSummary.durationText }}</p>
            <p><strong>路线点数：</strong>{{ routeSummary.nodeCount }}</p>
          </div>
          <p v-else class="result-empty">当前行程还没有足够的景点来生成路线摘要。</p>
        </a-card>

        <a-card v-if="activePanel === 'overview'" class="result-panel overview-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.overview') }}</h2>
            <span>{{ dateRangeText }}</span>
          </div>
          <div v-if="planAvailable" class="overview-hero-grid">
            <article class="overview-stat-card">
              <span class="overview-stat-label">城市</span>
              <strong>{{ requestSummary?.city || plan?.city }}</strong>
            </article>
            <article class="overview-stat-card">
              <span class="overview-stat-label">天数</span>
              <strong>{{ requestSummary?.travel_days || days.length }} 天</strong>
            </article>
            <article class="overview-stat-card">
              <span class="overview-stat-label">景点数</span>
              <strong>{{ attractions.length }}</strong>
            </article>
            <article class="overview-stat-card">
              <span class="overview-stat-label">预算</span>
              <strong>{{ budget ? `¥${budget.total}` : '待生成' }}</strong>
            </article>
          </div>

          <div v-if="previewDays.length > 0" class="overview-day-preview">
            <article
              v-for="day in previewDays"
              :key="day.day_index"
              class="overview-day-preview-card"
              :class="{ active: selectedDayIndex === day.day_index }"
            >
              <div class="overview-day-preview-head">
                <strong>{{ t('common.dayNumber', { day: day.day_index + 1 }) }}</strong>
                <span>{{ day.date }}</span>
              </div>
              <p>{{ day.description }}</p>
              <div class="overview-day-preview-tags">
                <span v-for="item in day.attractions.slice(0, 3)" :key="`${day.day_index}-${item.id}`">{{ item.name }}</span>
              </div>
              <button type="button" class="overview-inline-link" @click="focusDay(day.day_index)">查看这一天详情</button>
            </article>
          </div>

          <div v-if="planAvailable" class="overview-insight-grid">
            <article class="overview-insight-card">
              <h3>为什么这样推荐</h3>
              <ul class="overview-insight-list">
                <li v-for="reason in recommendationReasons" :key="reason">{{ reason }}</li>
              </ul>
            </article>

            <article class="overview-insight-card">
              <h3>行程节奏</h3>
              <div class="overview-pacing-block">
                <strong>{{ pacingHeadline }}</strong>
                <p>{{ pacingDescription }}</p>
              </div>
            </article>

            <article class="overview-insight-card">
              <h3>预算判断</h3>
              <div class="overview-pacing-block">
                <strong>{{ budgetHeadline }}</strong>
                <p>{{ budgetDescription }}</p>
              </div>
            </article>

            <article class="overview-insight-card">
              <h3>内容来源</h3>
              <ul class="overview-insight-list">
                <li v-for="source in contentSources" :key="`${source.source_type}-${source.source_label}-${source.origin}`">
                  {{ source.source_label }} · {{ source.origin === 'external' ? '外部内容' : '本地样例降级' }}
                </li>
              </ul>
            </article>
          </div>

          <div v-if="attractions.length > 0" class="overview-list">
            <OverviewAttractionCard
              v-for="item in attractions"
              :key="`${item.id}-${item.name}`"
              :item="item"
              :image-src="item.image_url || ''"
              :active="selectedDayIndex === item.dayArrayIndex"
              @hover="noop"
              @select-day="focusDay"
              @image-error="noop"
            />
          </div>
          <p v-else class="result-empty">{{ t('result.overview.empty') }}</p>
        </a-card>

        <a-card v-if="activePanel === 'map'" class="result-panel map-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.map') }}</h2>
          </div>
          <div v-if="planAvailable" id="amap-container" style="width: 100%; height: 400px"></div>
          <div v-else class="graph-placeholder">请先返回首页生成行程，再查看地图路线。</div>
        </a-card>

        <a-card v-if="activePanel === 'days'" class="result-panel days-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.days') }}</h2>
          </div>
          <div v-if="days.length > 0" class="day-cards">
            <article v-for="day in orderedDaysForDisplay" :key="day.day_index" class="day-card" :class="{ selected: selectedDayIndex === day.day_index }">
              <div class="day-card-head">
                <strong>{{ t('common.dayNumber', { day: day.day_index + 1 }) }}</strong>
                <span>{{ day.date }}</span>
              </div>
              <p class="day-card-desc">{{ day.description }}</p>
              <div class="day-card-meta">
                <span>{{ day.transportation }}</span>
                <span>{{ day.accommodation }}</span>
              </div>
              <div class="day-itinerary">
                <article
                  v-for="slot in buildDayTimeline(day)"
                  :key="`${day.day_index}-${slot.label}`"
                  class="day-slot-card"
                >
                  <div class="day-slot-time">
                    <strong>{{ slot.time }}</strong>
                    <span>{{ slot.label }}</span>
                  </div>
                  <div class="day-slot-body">
                    <h3>{{ slot.title }}</h3>
                    <p>{{ slot.description }}</p>
                    <div v-if="slot.tags.length > 0" class="day-slot-tags">
                      <span v-for="tag in slot.tags" :key="`${day.day_index}-${slot.label}-${tag}`">{{ tag }}</span>
                    </div>
                  </div>
                </article>
              </div>
            </article>
          </div>
          <p v-else class="result-empty">{{ t('result.overview.empty') }}</p>
        </a-card>

        <a-card v-if="activePanel === 'budget'" class="result-panel graph-panel" :bordered="false">
          <div class="panel-head">
            <h2>{{ t('result.side.budget') }}</h2>
          </div>
          <div v-if="budget" class="budget-shell">
            <section class="budget-hero-card">
              <div>
                <p class="budget-kicker">预算概览</p>
                <h3>总预算约 ¥{{ budget.total }}</h3>
                <p>{{ budgetDescription }}</p>
              </div>
              <div class="budget-hero-metrics">
                <article>
                  <span>日均预算</span>
                  <strong>¥{{ dailyBudget }}</strong>
                </article>
                <article>
                  <span>单点位成本</span>
                  <strong>¥{{ attractionUnitCost }}</strong>
                </article>
              </div>
            </section>

            <section class="budget-breakdown-grid">
              <article v-for="item in budgetBreakdown" :key="item.key" class="budget-breakdown-card">
                <div class="budget-breakdown-head">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.percent }}%</span>
                </div>
                <h3>¥{{ item.amount }}</h3>
                <p>{{ item.description }}</p>
                <div class="budget-bar-track">
                  <div class="budget-bar-fill" :style="{ width: `${item.percent}%` }"></div>
                </div>
              </article>
            </section>

            <section class="budget-insight-grid">
              <article class="budget-insight-card">
                <h3>预算判断</h3>
                <p>{{ budgetHeadline }}</p>
              </article>
              <article class="budget-insight-card">
                <h3>住宿与交通</h3>
                <p>{{ stayTransportNote }}</p>
              </article>
              <article class="budget-insight-card">
                <h3>展示建议</h3>
                <p>{{ budgetPresentationNote }}</p>
              </article>
            </section>
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
type ResultPanelKey = 'overview' | 'days' | 'route' | 'map' | 'budget'

const activePanel = ref<ResultPanelKey>('overview')
const selectedDayIndex = ref<number | null>(null)
const routeSummary = ref<{
  startName: string
  endName: string
  distanceText: string
  durationText: string
  nodeCount: number
  sourceLabel: string
} | null>(null)

const planRef = getCurrentPlan()

const plan = computed(() => planRef.value)
const planAvailable = computed(() => Boolean(plan.value))
const days = computed(() => plan.value?.days || [])
const attractions = computed(() => {
  return days.value.flatMap((day) => day.attractions.map((item) => ({ ...item, dayArrayIndex: day.day_index })))
})
const budget = computed(() => plan.value?.budget)
const requestSummary = computed(() => plan.value?.request_summary)
const previewDays = computed(() => days.value)
const contentSources = computed(() => plan.value?.content_sources || [])
const orderedDaysForDisplay = computed(() => {
  if (selectedDayIndex.value == null) return days.value
  const selected = days.value.find((day) => day.day_index === selectedDayIndex.value)
  const rest = days.value.filter((day) => day.day_index !== selectedDayIndex.value)
  return selected ? [selected, ...rest] : days.value
})
const panels = computed<Array<{ key: ResultPanelKey; label: string }>>(() => [
  { key: 'overview', label: t('result.side.overview') },
  { key: 'days', label: t('result.side.days') },
  { key: 'route', label: '路线' },
  { key: 'map', label: t('result.side.map') },
  { key: 'budget', label: t('result.side.budget') },
])
const dateRangeText = computed(() => {
  if (!plan.value) return t('common.noData')
  return t('result.dateRange', { start: plan.value.start_date, end: plan.value.end_date })
})
const overviewText = computed(() => {
  if (!plan.value) return '当前还没有可展示的行程，请先返回首页生成计划。'
  return plan.value.overall_suggestions || t('result.overview.empty')
})
const attractionsPerDay = computed(() => {
  if (days.value.length === 0) return 0
  return Math.round((attractions.value.length / days.value.length) * 10) / 10
})
const recommendationReasons = computed(() => {
  if (!plan.value) return []
  if (plan.value.recommendation_reasons?.length) {
    return plan.value.recommendation_reasons
  }

  const reasons = [
    `优先围绕 ${requestSummary.value?.city || plan.value.city} 的可用本地景点数据生成，便于形成真实可展示的闭环。`,
    `当前行程共安排 ${attractions.value.length} 个景点，平均每天约 ${attractionsPerDay.value || 0} 个点位，节奏相对清晰。`,
  ]

  if (requestSummary.value?.preferences?.length) {
    reasons.push(`已结合你的偏好：${requestSummary.value.preferences.join('、')}。`)
  }

  if (requestSummary.value?.data_mode === 'local_sample') {
    reasons.push('当前目标城市样例还不完整，因此系统使用现有本地景点数据生成了可用行程。')
  } else {
    reasons.push('当前推荐优先命中了目标城市样例数据，结果更接近真实城市内游览。')
  }

  return reasons
})
const pacingHeadline = computed(() => {
  if (days.value.length <= 1) return '单日轻量体验'
  if (attractionsPerDay.value <= 2) return '慢节奏游览'
  if (attractionsPerDay.value <= 3) return '均衡节奏'
  return '相对紧凑的打卡路线'
})
const pacingDescription = computed(() => {
  if (!plan.value) return '请先生成行程。'
  return `本次安排覆盖 ${days.value.length} 天，概览区会展示全部天数预览，适合先看整体节奏，再进入每日详情做确认。`
})
const budgetHeadline = computed(() => {
  if (!budget.value) return '预算待生成'
  if (budget.value.total <= 1200) return '预算相对友好'
  if (budget.value.total <= 2500) return '预算处于常规范围'
  return '预算偏高，建议重点确认住宿与门票'
})
const budgetDescription = computed(() => {
  if (!budget.value) return '当前没有预算数据。'
  return `总预算约 ¥${budget.value.total}，其中住宿 ¥${budget.value.total_hotels}、门票 ¥${budget.value.total_attractions}、交通 ¥${budget.value.total_transportation}。`
})
const dailyBudget = computed(() => {
  if (!budget.value || days.value.length === 0) return 0
  return Math.round(budget.value.total / days.value.length)
})
const attractionUnitCost = computed(() => {
  if (!budget.value || attractions.value.length === 0) return 0
  return Math.round((budget.value.total_attractions + budget.value.total_transportation) / attractions.value.length)
})
const budgetBreakdown = computed(() => {
  if (!budget.value || budget.value.total <= 0) return []

  const buildPercent = (amount: number) => Math.max(4, Math.round((amount / budget.value!.total) * 100))
  return [
    {
      key: 'hotel',
      label: '住宿',
      amount: budget.value.total_hotels,
      percent: buildPercent(budget.value.total_hotels),
      description: `${requestSummary.value?.accommodation || '当前住宿方案'} 是预算中的主要组成部分。`,
    },
    {
      key: 'attraction',
      label: '门票',
      amount: budget.value.total_attractions,
      percent: buildPercent(budget.value.total_attractions),
      description: `当前共覆盖 ${attractions.value.length} 个景点，门票开销随景点数量增长。`,
    },
    {
      key: 'meal',
      label: '餐饮',
      amount: budget.value.total_meals,
      percent: buildPercent(budget.value.total_meals),
      description: `按 ${days.value.length} 天基础餐饮估算，可作为当前行程的基础预算参考。`,
    },
    {
      key: 'transport',
      label: '交通',
      amount: budget.value.total_transportation,
      percent: buildPercent(budget.value.total_transportation),
      description: `${requestSummary.value?.transportation || '当前交通方式'} 会直接影响路线移动成本。`,
    },
  ]
})
const stayTransportNote = computed(() => {
  if (!budget.value) return '当前没有住宿和交通预算。'
  return `住宿 ¥${budget.value.total_hotels}，交通 ¥${budget.value.total_transportation}。如果后续想压缩预算，优先调整住宿档位和跨点位移动强度最有效。`
})
const budgetPresentationNote = computed(() => {
  if (!budget.value) return '当前没有可展示的预算信息。'
  return '这份预算已经覆盖门票、住宿、餐饮和交通拆分，适合用来快速判断行程成本结构。'
})

const goHome = () => void router.push('/')
const noop = () => undefined
const focusDay = (dayIndex: number) => {
  selectedDayIndex.value = dayIndex
  activePanel.value = 'days'
}

const buildDayTimeline = (day: (typeof days.value)[number]) => {
  const attractionsForDay = day.attractions || []
  const morningAttractions = attractionsForDay.slice(0, Math.max(1, Math.ceil(attractionsForDay.length / 2)))
  const afternoonAttractions = attractionsForDay.slice(morningAttractions.length)
  const headlineAttraction = attractionsForDay[0]
  const closingAttraction = afternoonAttractions[0] || attractionsForDay[attractionsForDay.length - 1]

  return [
    {
      time: '08:30',
      label: '出发准备',
      title: `从住宿点出发，开启第 ${day.day_index + 1} 天`,
      description: `建议早餐后出发，今日以 ${day.transportation} 为主，保持轻量节奏进入行程。`,
      tags: [day.accommodation, day.transportation],
    },
    {
      time: '10:00',
      label: '上午游览',
      title: morningAttractions.length > 0 ? `上午重点：${morningAttractions.map((item) => item.name).join('、')}` : '上午自由活动',
      description: headlineAttraction?.description || '上午时段可安排核心景点或城市漫步。',
      tags: morningAttractions.map((item) => item.name),
    },
    {
      time: '12:30',
      label: '午间休整',
      title: '午餐与短暂休息',
      description: '建议在上午景点附近安排午餐，适当休整后再进入下午路线。',
      tags: ['午餐', '休息'],
    },
    {
      time: '14:30',
      label: '下午路线',
      title: afternoonAttractions.length > 0 ? `下午继续：${afternoonAttractions.map((item) => item.name).join('、')}` : '下午慢节奏延展',
      description: closingAttraction?.description || '下午适合继续补充景点，或转入更轻松的城市体验。',
      tags: afternoonAttractions.map((item) => item.name),
    },
    {
      time: '19:00',
      label: '晚间收尾',
      title: '返回住宿点，整理今日行程',
      description: `建议晚上回到${day.accommodation}附近休息，也可以顺路安排夜景或晚餐。`,
      tags: ['晚餐', '返程'],
    },
  ]
}

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
    routeSummary.value = {
      startName: routeData.start_poi?.name || start.name,
      endName: routeData.end_poi?.name || end.name,
      distanceText: routeData.distance ? `${routeData.distance.toFixed(2)} km` : '暂无距离数据',
      durationText: routeData.estimated_time_hours ? `${(routeData.estimated_time_hours * 60).toFixed(0)} 分钟` : '暂无耗时数据',
      nodeCount: pathNodes.length,
      sourceLabel: routeData.source === 'amap' ? '高德路径' : '本地图算法路径',
    }

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
    routeSummary.value = null
  }
}

onMounted(() => {
  if (plan.value) {
    void initAMap()
  }
})
</script>
