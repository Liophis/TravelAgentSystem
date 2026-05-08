<template>
  <section class="hero-page">
    <div class="hero-glow hero-glow-a"></div>
    <div class="hero-glow hero-glow-b"></div>

    <div class="hero-content">
      <div class="hero-copy">
        <span class="hero-badge">{{ t('home.heroBadge') }}</span>
        <h1>
          <span>{{ t('home.titleLine1') }}</span>
          <strong>{{ t('home.titleLine2') }}</strong>
        </h1>
        <p>{{ t('home.heroDesc') }}</p>
      </div>

      <a-card class="hero-card" :bordered="false">
        <a-form layout="vertical" :model="formData" @finish="handleSubmit">
          <div class="grid grid-2">
            <a-form-item :label="t('home.cityLabel')" name="city" :rules="[{ required: true, message: t('home.cityRequired') }]">
              <a-input v-model:value="formData.city" :placeholder="t('home.cityPlaceholder')" />
            </a-form-item>

            <a-form-item :label="t('home.travelDaysLabel')">
              <a-input-number v-model:value="formData.travel_days" :min="1" :max="30" style="width: 100%" />
            </a-form-item>

            <a-form-item :label="t('home.startDateLabel')" name="start_date" :rules="[{ required: true, message: t('home.startDateRequired') }]">
              <a-input v-model:value="formData.start_date" :placeholder="t('home.startDatePlaceholder')" />
            </a-form-item>

            <a-form-item :label="t('home.endDateLabel')" name="end_date" :rules="[{ required: true, message: t('home.endDateRequired') }]">
              <a-input v-model:value="formData.end_date" :placeholder="t('home.endDatePlaceholder')" />
            </a-form-item>
          </div>

          <div class="grid grid-2">
            <a-form-item :label="t('home.transportationLabel')">
              <a-select v-model:value="formData.transportation">
                <a-select-option value="公共交通">{{ t('home.transportation.public') }}</a-select-option>
                <a-select-option value="自驾">{{ t('home.transportation.drive') }}</a-select-option>
                <a-select-option value="步行">{{ t('home.transportation.walk') }}</a-select-option>
                <a-select-option value="混合">{{ t('home.transportation.mixed') }}</a-select-option>
              </a-select>
            </a-form-item>

            <a-form-item :label="t('home.accommodationLabel')">
              <a-select v-model:value="formData.accommodation">
                <a-select-option value="经济型酒店">{{ t('home.accommodation.budget') }}</a-select-option>
                <a-select-option value="舒适型酒店">{{ t('home.accommodation.comfort') }}</a-select-option>
                <a-select-option value="豪华酒店">{{ t('home.accommodation.luxury') }}</a-select-option>
                <a-select-option value="民宿">{{ t('home.accommodation.homestay') }}</a-select-option>
              </a-select>
            </a-form-item>
          </div>

          <a-form-item :label="t('home.interestsLabel')">
            <div class="tag-list">
              <button
                v-for="interest in interests"
                :key="interest.value"
                type="button"
                class="tag-pill"
                :class="{ active: formData.preferences.includes(interest.value) }"
                @click="toggleInterest(interest.value)"
              >
                {{ t(interest.labelKey) }}
              </button>
            </div>
          </a-form-item>

          <a-form-item :label="t('home.specialNeedsPlaceholder')">
            <a-textarea v-model:value="formData.free_text_input" :rows="4" />
          </a-form-item>

          <a-form-item>
            <a-button type="primary" html-type="submit" size="large" block>{{ t('home.submit') }}</a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import type { TripFormData } from '@/types'
import { generateTrip } from '@/services/api'
import { setCurrentPlan } from '@/services/store'

const router = useRouter()
const { t } = useI18n()

const interests = [
  { value: '历史文化', labelKey: 'home.interests.history' },
  { value: '自然风光', labelKey: 'home.interests.nature' },
  { value: '美食', labelKey: 'home.interests.food' },
  { value: '购物', labelKey: 'home.interests.shopping' },
  { value: '艺术', labelKey: 'home.interests.art' },
  { value: '休闲', labelKey: 'home.interests.leisure' },
]

const formData = reactive<TripFormData>({
  city: '',
  start_date: '',
  end_date: '',
  travel_days: 3,
  transportation: '公共交通',
  accommodation: '经济型酒店',
  preferences: [],
  free_text_input: '',
})

const toggleInterest = (value: string) => {
  const index = formData.preferences.indexOf(value)
  if (index === -1) {
    formData.preferences.push(value)
    return
  }

  formData.preferences.splice(index, 1)
}

const handleSubmit = async () => {
  const payload = {
    city: formData.city,
    start_date: formData.start_date,
    end_date: formData.end_date,
    travel_days: formData.travel_days,
    transportation: formData.transportation,
    accommodation: formData.accommodation,
    preferences: formData.preferences,
    free_text_input: formData.free_text_input,
  }

  try {
    const res = await generateTrip(payload)
    if (res?.success && res.data) {
      setCurrentPlan(res.data)
    }
  } catch (err) {
    console.error('generateTrip error', err)
  } finally {
    void router.push('/result')
  }
}
</script>
