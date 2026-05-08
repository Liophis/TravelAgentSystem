import { ref } from 'vue'
import type { TripPlan } from '@/types'

const currentPlan = ref<TripPlan | null>(null)

export const setCurrentPlan = (plan: TripPlan | null) => {
  currentPlan.value = plan
}

export const getCurrentPlan = () => currentPlan
