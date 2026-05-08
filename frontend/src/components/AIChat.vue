<template>
  <aside class="chat-panel">
    <div class="chat-shell">
      <header class="chat-header">
        <div>
          <p class="chat-kicker">AI Chat</p>
          <h3>{{ t('result.chat.welcome') }}</h3>
        </div>
        <button type="button" class="chat-close" @click="emit('close')">×</button>
      </header>

      <section class="chat-history">
        <p v-if="messages.length === 0" class="chat-empty">{{ t('result.chat.welcome') }}</p>
        <div v-for="(message, index) in messages" :key="`${message.role}-${index}`" class="chat-message" :class="message.role">
          {{ message.content }}
        </div>
      </section>

      <footer class="chat-footer">
        <a-textarea
          v-model:value="draft"
          :placeholder="t('result.chat.placeholder')"
          :rows="3"
          class="chat-input"
        />
        <div class="chat-actions">
          <a-button type="default" block @click="emit('quick-question', t('result.chat.quickPriceQuestion'))">
            {{ t('result.chat.quickPriceLabel') }}
          </a-button>
          <a-button type="default" block @click="emit('quick-question', t('result.chat.quickSuitabilityQuestion'))">
            {{ t('result.chat.quickSuitabilityLabel') }}
          </a-button>
          <a-button type="primary" block :disabled="!inputValue.trim()" @click="emit('send', inputValue)">
            {{ t('common.submit') }}
          </a-button>
        </div>
      </footer>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ChatMessage } from '@/types'

const props = defineProps<{
  messages: ChatMessage[]
  inputValue: string
}>()

const draft = ref(props.inputValue)

watch(
  () => props.inputValue,
  (value) => {
    draft.value = value
  }
)

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'send', value: string): void
  (e: 'quick-question', value: string): void
}>()

const { t } = useI18n()
</script>
