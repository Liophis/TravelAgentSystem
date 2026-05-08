import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import App from './App.vue'
import { i18n } from './i18n'
import './styles/global.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Landing', component: () => import('./views/Landing.vue') },
    { path: '/result', name: 'Result', component: () => import('./views/Result.vue') },
  ],
})

createApp(App).use(router).use(Antd).use(i18n).mount('#app')
