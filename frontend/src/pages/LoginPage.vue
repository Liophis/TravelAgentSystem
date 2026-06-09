<template>
  <section class="login-page">
    <aside class="login-intro">
      <div class="intro-top">
        <span class="login-mark">游</span>
        <div>
          <strong>Smart Tour Guide</strong>
          <small>算法旅游服务平台</small>
        </div>
      </div>
      <div class="intro-copy">
        <span class="intro-kicker">Account Gateway</span>
        <h1>统一账号入口</h1>
        <p>登录后进入总览页，再选择推荐、导航、设施、游记、美食或 AIGC 服务。</p>
      </div>
      <div class="intro-metrics">
        <div>
          <strong>207</strong>
          <span>目的地</span>
        </div>
        <div>
          <strong>2</strong>
          <span>地图场景</span>
        </div>
        <div>
          <strong>11</strong>
          <span>演示用户</span>
        </div>
      </div>
    </aside>

    <main class="login-main">
      <el-card shadow="never" class="login-card">
        <template #header>
          <div class="card-header">
            <div>
              <span>账号登录</span>
              <small>使用系统账号进入工作台</small>
            </div>
            <el-tag type="success" effect="plain">全应用</el-tag>
          </div>
        </template>

        <el-tabs v-model="activeTab" stretch>
          <el-tab-pane label="登录" name="login">
            <el-form label-position="top" class="auth-form">
              <el-form-item label="账号或邮箱">
                <el-input v-model="loginForm.username_or_email" size="large" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="loginForm.password" type="password" size="large" show-password />
              </el-form-item>
            </el-form>
            <el-button class="submit-button" type="primary" size="large" :loading="authLoading" @click="login">
              登录并进入系统
            </el-button>
            <div class="quick-row">
              <el-button plain @click="fillDemoLogin">普通用户</el-button>
              <el-button plain type="warning" @click="fillAdminLogin">管理员</el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form label-position="top" class="auth-form">
              <el-form-item label="用户名">
                <el-input v-model="registerForm.username" size="large" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="registerForm.email" size="large" />
              </el-form-item>
              <el-form-item label="昵称">
                <el-input v-model="registerForm.nickname" size="large" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="registerForm.password" type="password" size="large" show-password />
              </el-form-item>
            </el-form>
            <el-button class="submit-button" type="primary" size="large" :loading="authLoading" @click="register">
              注册并进入系统
            </el-button>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </main>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { apiPost, type AuthPayload } from "../services/api";
import { applyAuthPayload } from "../services/auth";

const route = useRoute();
const router = useRouter();
const activeTab = ref("login");
const authLoading = ref(false);
const loginForm = reactive({
  username_or_email: "user01",
  password: "demo123456",
});
const registerSeed = Date.now().toString().slice(-5);
const registerForm = reactive({
  username: `visitor_${registerSeed}`,
  email: `visitor_${registerSeed}@example.com`,
  nickname: "新游客",
  password: "demo123456",
});

async function login() {
  authLoading.value = true;
  try {
    const payload = await apiPost<AuthPayload>("/api/v1/users/login", loginForm);
    await enterApp(payload);
    ElMessage.success("登录成功");
  } finally {
    authLoading.value = false;
  }
}

async function register() {
  authLoading.value = true;
  try {
    const payload = await apiPost<AuthPayload>("/api/v1/users/register", {
      ...registerForm,
      interests: [],
    });
    await enterApp(payload);
    ElMessage.success("注册成功");
  } finally {
    authLoading.value = false;
  }
}

async function enterApp(payload: AuthPayload) {
  applyAuthPayload(payload);
  const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/";
  await router.replace(redirect);
}

function fillDemoLogin() {
  loginForm.username_or_email = "user01";
  loginForm.password = "demo123456";
}

function fillAdminLogin() {
  loginForm.username_or_email = "admin01";
  loginForm.password = "admin123456";
}
</script>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  grid-template-columns: minmax(420px, 0.88fr) minmax(520px, 1.12fr);
  background:
    linear-gradient(90deg, rgba(15, 118, 110, 0.08) 1px, transparent 1px),
    linear-gradient(rgba(15, 118, 110, 0.08) 1px, transparent 1px),
    #f6f7f9;
  background-size: 44px 44px;
}

.login-intro {
  display: grid;
  min-height: 100vh;
  align-content: space-between;
  padding: 42px;
  color: #ffffff;
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(19, 78, 74, 0.94)),
    #0f172a;
}

.intro-top {
  display: flex;
  align-items: center;
  gap: 14px;
}

.login-mark {
  display: grid;
  width: 46px;
  height: 46px;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.12);
  font-weight: 800;
}

.intro-top strong,
.intro-top small {
  display: block;
}

.intro-top strong {
  font-size: 17px;
}

.intro-top small {
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.68);
}

.intro-copy {
  max-width: 420px;
}

.intro-kicker {
  color: #f6d365;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}

.intro-copy h1 {
  margin: 14px 0 12px;
  font-size: 42px;
  line-height: 1.12;
  letter-spacing: 0;
}

.intro-copy p {
  margin: 0;
  color: rgba(255, 255, 255, 0.72);
  line-height: 1.7;
}

.intro-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.intro-metrics div {
  min-height: 86px;
  padding: 15px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
}

.intro-metrics strong,
.intro-metrics span {
  display: block;
}

.intro-metrics strong {
  font-size: 24px;
}

.intro-metrics span {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
}

.login-main {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 42px;
}

.login-card {
  width: min(520px, 100%);
  border-color: #d8e0ea !important;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.12) !important;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.card-header span,
.card-header small {
  display: block;
}

.card-header span {
  color: #101828;
  font-size: 18px;
  font-weight: 800;
}

.card-header small {
  margin-top: 4px;
  color: #667085;
  font-size: 12px;
}

.auth-form {
  padding-top: 8px;
}

.submit-button {
  width: 100%;
}

.quick-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 12px;
}

.quick-row .el-button {
  width: 100%;
  margin: 0;
}

@media (max-width: 980px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .login-intro {
    min-height: auto;
    gap: 28px;
  }

  .login-main {
    min-height: auto;
  }
}
</style>
