<template>
  <main class="result-page">
    <!-- Header is provided by App.vue; remove duplicate NavBar to avoid UI duplication -->

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
          <div id="amap-container" style="width: 100%; height: 400px"></div>
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
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
// NavBar removed to prevent duplicate header
import AIChat from '@/components/AIChat.vue'
import OverviewAttractionCard from '@/components/OverviewAttractionCard.vue'
import type { ChatMessage } from '@/types'

const router = useRouter()
const { t } = useI18n()
const showChat = ref(false)
const chatMessages = ref<ChatMessage[]>([])

import { getCurrentPlan, setCurrentPlan } from '@/services/store'
import { generateDemoPlan } from '@/services/api'
import AMapLoader from '@amap/amap-jsapi-loader'
import axios from 'axios'

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

const map = ref<any>(null)

const initAMap = async () => {
  await nextTick()
  const mapJsKey = import.meta.env.VITE_AMAP_WEB_JS_KEY || ''
  if (!mapJsKey) {
    console.error('高德地图 JS Key 未配置，请在 .env 中设置 VITE_AMAP_WEB_JS_KEY')
    return
  }

  try {
    const AMap = await AMapLoader.load({
      key: mapJsKey,
      version: '2.0',
      plugins: ['AMap.Marker', 'AMap.Polyline', 'AMap.InfoWindow']
    })

    map.value = new AMap.Map('amap-container', {
      zoom: 12,
      center: [116.397128, 39.916527]
    })

    // 绘制路线（包含所有途经点）
    const items = attractions.value || []
    if (items.length >= 2) {
      const start = items[0]
      const end = items[items.length - 1]
      try {
        const res = await axios.get(`/api/routes/${start.id}/${end.id}`)
        const pathNodes = res.data.path_nodes || []
        const distance = res.data.distance || 0
        const estimatedHours = res.data.estimated_time_hours || 0
        const source = res.data.source || 'unknown'

        console.log(`[路线规划] 来源: ${source}, 距离: ${distance}km, 耗时: ${estimatedHours}h, 途经点: ${pathNodes.length}`)

        if (pathNodes && pathNodes.length > 1) {
          // 绘制完整的路线折线（包含所有途经点）
          const coords = pathNodes.map((p: any) => [p.longitude, p.latitude])
          const polyline = new AMap.Polyline({
            path: coords,
            borderWeight: 2,
            strokeColor: '#1890ff',
            lineJoin: 'round',
            isOutline: true,
            outlineColor: '#ffffff',
            outlineWeight: 1
          })
          map.value.add(polyline)

          // 优化：只为关键点创建标记（起点、终点、每 10 个点取一个）
          // 而不是为所有 50+ 个转折点创建标记
          const keyMarkerIndices = [0, pathNodes.length - 1] // 起点和终点
          // 添加中间的均匀采样点，每 10 个点取一个
          for (let i = 10; i < pathNodes.length - 1; i += Math.max(1, Math.floor((pathNodes.length - 2) / 5))) {
            if (!keyMarkerIndices.includes(i)) {
              keyMarkerIndices.push(i)
            }
          }
          keyMarkerIndices.sort((a, b) => a - b)

          const markers: any[] = []
          const infoWindows: any[] = []

          keyMarkerIndices.forEach((idx: number) => {
            const node = pathNodes[idx]
            const isStart = idx === 0
            const isEnd = idx === pathNodes.length - 1

            const marker = new AMap.Marker({
              position: [node.longitude, node.latitude],
              title: node.name,
              extData: { index: idx }
            })
            markers.push(marker)

            // 点击标记显示信息窗口
            marker.on('click', () => {
              // 关闭其他窗口
              infoWindows.forEach((iw: any) => iw.close())

              const content = `<div style="padding:8px; background:#f5f5f5; border-radius:4px;">
                <div style="font-weight:bold; margin-bottom:4px;">${node.name}</div>
                <div style="font-size:12px;">Lat: ${node.latitude.toFixed(5)}</div>
                <div style="font-size:12px;">Lon: ${node.longitude.toFixed(5)}</div>
                ${node.distance ? `<div style="font-size:12px;">距离: ${node.distance}m</div>` : ''}
                ${isStart ? '<div style="color:green; font-weight:bold;">📍 起点</div>' : ''}
                ${isEnd ? '<div style="color:red; font-weight:bold;">🎯 终点</div>' : ''}
              </div>`

              const infoWindow = new AMap.InfoWindow({
                content: content,
                position: [node.longitude, node.latitude],
                offset: new AMap.Pixel(0, -30)
              })
              infoWindow.open(map.value, [node.longitude, node.latitude])
              infoWindows.push(infoWindow)
            })
          })

          map.value.add(markers)

          // 自适应视野到折线范围
          if (markers.length > 0) {
            map.value.setFitView(markers, true, [50, 50, 50, 50])
          } else {
            map.value.setFitView([polyline])
          }

          // 显示路线统计信息
          console.log(`✅ 路线绘制完成: ${coords.length} 个点, ${distance.toFixed(2)}km, 约 ${(estimatedHours * 60).toFixed(0)} 分钟`)
        } else if (items.length >= 2) {
          // 降级：只有起终点
          const coords = [[start.longitude, start.latitude], [end.longitude, end.latitude]]
          const polyline = new AMap.Polyline({ path: coords, strokeColor: '#1890ff' })
          map.value.add(polyline)

          const startMarker = new AMap.Marker({ position: coords[0], title: 'Start' })
          const endMarker = new AMap.Marker({ position: coords[1], title: 'End' })
          map.value.add([startMarker, endMarker])
          map.value.setFitView([polyline, startMarker, endMarker])
        }
      } catch (e) {
        console.error('[路线规划] API 调用失败:', e)
      }
    }
  } catch (err) {
    console.error('AMap 初始化失败:', err)
  }
}

onMounted(() => {
  const plan = planRef.value
  if (!plan) {
    // fetch demo plan so map has attractions to render
    generateDemoPlan()
      .then((res: any) => {
        if (res && res.data) {
          // if backend demo has no attractions, fall back to using first two POIs
          const hasAttractions = Array.isArray(res.data.days) && res.data.days.some((d: any) => (d.attractions || []).length > 0)
          if (!hasAttractions) {
            // fetch first two POIs from API and build a tiny plan
            return axios.get('/api/pois?skip=0&limit=2').then((r) => {
              const pois = r.data.items || r.data || []
              if (Array.isArray(pois) && pois.length >= 2) {
                const demo = {
                  city: 'DemoCity',
                  start_date: '2026-05-01',
                  end_date: '2026-05-02',
                  days: [
                    {
                      day_index: 0,
                      attractions: [
                        {
                          id: pois[0].id,
                          name: pois[0].name,
                          latitude: pois[0].latitude,
                          longitude: pois[0].longitude,
                        },
                        {
                          id: pois[1].id,
                          name: pois[1].name,
                          latitude: pois[1].latitude,
                          longitude: pois[1].longitude,
                        },
                      ],
                    },
                  ],
                }
                setCurrentPlan(demo)
                initAMap()
                return
              }
              initAMap()
            })
          }
          setCurrentPlan(res.data)
        }
        initAMap()
      })
      .catch(() => initAMap())
  } else {
    initAMap()
  }
})
</script>
