import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import App from './App.vue'
import Landing from './views/Landing.vue'
import Result from './views/Result.vue'
import { i18n } from './i18n'
import './styles/global.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Landing', component: Landing },
    { path: '/result', name: 'Result', component: Result },
  ],
})

createApp(App).use(router).use(Antd).use(i18n).mount('#app')
