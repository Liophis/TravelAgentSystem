<template>
  <main class="landing-page">
    <NavBar @brand-click="scrollToTop" @cta-click="scrollToForm" />

    <section class="landing-hero">
      <div class="landing-hero-inner">
        <p class="landing-kicker">{{ t('home.heroBadge') }}</p>
        <h1 class="landing-title">{{ t('home.titleLine1') }} <span>{{ t('home.titleLine2') }}</span></h1>
        <p class="landing-desc">{{ t('home.heroDesc') }}</p>
      </div>
    </section>

    <section ref="formRef" class="landing-form-section">
      <Home />
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import NavBar from '@/components/NavBar.vue'
import Home from './Home.vue'

const { t } = useI18n()
const formRef = ref<HTMLElement | null>(null)

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const scrollToForm = () => {
  formRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>
