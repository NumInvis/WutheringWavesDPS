<template>
  <el-dropdown trigger="click" placement="bottom">
    <div class="dropdown-button">
      <span>应用排行</span>
      <el-icon class="el-icon--right"><ArrowDown /></el-icon>
    </div>
    <template #dropdown>
      <el-dropdown-menu class="app-ranking-dropdown">
        <div class="dropdown-content">
          <div class="dropdown-header">
            <h3><el-icon><Iphone /></el-icon> iOS畅销榜排行</h3>
            <span class="update-time">更新时间: {{ lastUpdated || '-' }}</span>
          </div>
          
          <div class="stats-row">
            <div class="stat-item">
              <el-icon><Monitor /></el-icon>
              <span class="v">{{ apps.length }}</span>
              <span class="l">监控游戏</span>
            </div>
            <div class="stat-item">
              <el-icon><Location /></el-icon>
              <span class="v">4</span>
              <span class="l">地区</span>
            </div>
            <div class="stat-item" :class="schedulerStatus.running ? 'running' : 'stopped'">
              <el-icon><Timer /></el-icon>
              <span class="v">{{ schedulerStatus.running ? '运行中' : '已停止' }}</span>
              <span class="l">调度器</span>
            </div>
          </div>
          
          <div class="ranking-cards">
            <div v-for="app in appsWithRankings" :key="app.id" class="ranking-card">
              <div class="card-header">
                <