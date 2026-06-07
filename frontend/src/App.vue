<template>
  <el-container class="app-shell">
    <el-aside width="236px" class="app-sidebar">
      <div class="brand">
        <span class="brand-mark">ST</span>
        <div>
          <strong>Smart Tour</strong>
          <small>Guide Console</small>
        </div>
      </div>
      <el-menu router :default-active="$route.path" class="nav-menu">
        <el-menu-item index="/">总览</el-menu-item>
        <el-menu-item index="/map">地图导览</el-menu-item>
        <el-menu-item index="/routes">路线规划</el-menu-item>
        <el-menu-item index="/facilities">附近设施</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <span>大型校园 / 景区智能导览平台</span>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
