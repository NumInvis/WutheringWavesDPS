<template>
  <div class="app-ranking">
    <header class="page-header">
      <div class="header-left">
        <h1><el-icon><Iphone /></el-icon> iOS畅销榜排行</h1>
        <span class="update-time">更新时间: {{ lastUpdated || '-' }}</span>
      </div>
      <div class="header-right">
        <el-button v-if="userStore.user?.is_admin" type="success" @click="crawlData" :loading="crawlLoading" size="small">
          <el-icon><Refresh /></el-icon> 爬取
        </el-button>
      </div>
    </header>

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
          <h3>{{ app.name_cn }}</h3>
          <span class="en-name">{{ app.name_en }}</span>
        </div>
        <div class="card-body">
          <div v-for="(country, code) in countries" :key="code" class="country-row">
            <span class="flag">{{ flags[code] }}</span>
            <span class="country-name">{{ country }}</span>
            <span class="rank" :class="getRankClass(app.rankings[code]?.rank)">
              {{ app.rankings[code]?.rank > 100 ? '>100' : app.rankings[code]?.rank || '-' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="content-grid">
      <div class="panel chart-panel">
        <div class="panel-header">
          <h3><el-icon><TrendCharts /></el-icon> 排名趋势</h3>
          <div class="chart-controls">
            <el-select v-model="selectedAppId" placeholder="选择游戏" size="small" style="width: 140px;">
              <el-option v-for="app in apps" :key="app.id" :label="app.name_cn" :value="app.id" />
            </el-select>
            <el-select v-model="selectedCountry" placeholder="选择地区" size="small" style="width: 100px;">
              <el-option label="全部" value="" />
              <el-option v-for="(name, code) in countries" :key="code" :label="name" :value="code" />
            </el-select>
          </div>
        </div>
        <div ref="chartRef" class="chart-area"></div>
      </div>

      <div class="panel top-panel">
        <div class="panel-header">
          <h3><el-icon><Trophy /></el-icon> 各地区畅销榜 TOP 10</h3>
        </div>
        <el-tabs v-model="activeCountry" class="country-tabs">
          <el-tab-pane v-for="(name, code) in countries" :key="code" :label="flags[code] + ' ' + name" :name="code">
            <div class="top-list">
              <div v-for="app in topApps[code]?.apps || []" :key="app.app_id" class="top-item">
                <span class="rank" :class="'r' + app.rank">{{ app.rank }}</span>
                <img v-if="app.icon" :src="app.icon" class="app-icon" />
                <div class="app-info">
                  <span class="app-name">{{ app.name }}</span>
                  <span class="developer">{{ app.developer }}</span>
                </div>
              </div>
              <el-empty v-if="!topApps[code]?.apps?.length" description="暂无数据" :image-size="50" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Iphone, Refresh, Monitor, Location, Timer, TrendCharts, Trophy } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

const apps = ref<any[]>([])
const appsWithRankings = ref<any[]>([])
const topApps = ref<any>({})
const lastUpdated = ref('')
const crawlLoading = ref(false)
const schedulerStatus = ref({ running: false })
const selectedAppId = ref('')
const selectedCountry = ref('')
const activeCountry = ref('cn')
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const countries: Record<string, string> = {
  cn: '中国',
  jp: '日本',
  us: '美国',
  kr: '韩国'
}

const flags: Record<string, string> = {
  cn: '🇨🇳',
  jp: '🇯🇵',
  us: '🇺🇸',
  kr: '🇰🇷'
}

function getRankClass(rank: number) {
  if (!rank || rank > 100) return 'rank-low'
  if (rank <= 10) return 'rank-high'
  if (rank <= 50) return 'rank-mid'
  return 'rank-low'
}

async function loadCurrentRanking() {
  try {
    const data = await api.get('/ranking/current')
    apps.value = data.apps || []
    appsWithRankings.value = data.apps || []
    lastUpdated.value = data.last_updated || ''
    if (apps.value.length && !selectedAppId.value) {
      selectedAppId.value = apps.value[0].id
    }
  } catch (error) {
    console.error('加载排名数据失败:', error)
  }
}

async function loadTopApps() {
  try {
    const data = await api.get('/ranking/top-all')
    topApps.value = data
  } catch (error) {
    console.error('加载TOP应用失败:', error)
  }
}

async function loadSchedulerStatus() {
  try {
    const data = await api.get('/ranking/crawl-status')
    schedulerStatus.value = data
  } catch (error) {
    console.error('加载调度器状态失败:', error)
  }
}

async function loadHistory() {
  if (!selectedAppId.value || !chartRef.value) return
  
  try {
    const params = new URLSearchParams({ days: '7' })
    if (selectedCountry.value) {
      params.append('country', selectedCountry.value)
    }
    
    const data = await api.get(`/ranking/history/${selectedAppId.value}?${params}`)
    updateChart(data)
  } catch (error) {
    console.error('加载历史数据失败:', error)
  }
}

async function crawlData() {
  crawlLoading.value = true
  try {
    await api.post('/ranking/crawl')
    ElMessage.success('爬取完成')
    setTimeout(() => {
      loadCurrentRanking()
      loadTopApps()
    }, 2000)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '爬取失败')
  } finally {
    crawlLoading.value = false
  }
}

function initChart() {
  nextTick(() => {
    if (chartRef.value) {
      chart = echarts.init(chartRef.value)
    }
  })
}

function updateChart(data: any) {
  if (!chart) return
  
  const series: any[] = []
  const legendData: string[] = []
  
  for (const [country, records] of Object.entries(data.history)) {
    const countryName = countries[country] || country
    legendData.push(countryName)
    
    series.push({
      name: countryName,
      type: 'line',
      data: (records as any[]).map((r: any) => [r.recorded_at, r.rank]),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6
    })
  }
  
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 15, 26, 0.95)',
      borderColor: 'rgba(102, 126, 234, 0.3)',
      textStyle: { color: '#fff' },
      formatter: (params: any) => {
        let result = params[0].axisValue + '<br/>'
        params.forEach((item: any) => {
          result += `${item.marker} ${item.seriesName}: ${item.value[1] > 100 ? '>100' : item.value[1]}<br/>`
        })
        return result
      }
    },
    legend: {
      data: legendData,
      bottom: 0,
      textStyle: { color: '#a0a0b0', fontSize: 12 }
    },
    grid: {
      left: '3%',
      right: '4%',
      top: '3%',
      bottom: '12%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      axisLine: { lineStyle: { color: '#3a3a4a' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      inverse: true,
      min: 1,
      max: 100,
      axisLine: { lineStyle: { color: '#3a3a4a' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 },
      splitLine: { lineStyle: { color: '#2a2a3a' } }
    },
    series
  })
}

function handleResize() {
  chart?.resize()
}

watch([selectedAppId, selectedCountry], () => {
  loadHistory()
})

async function loadAllData() {
  await Promise.all([loadCurrentRanking(), loadTopApps(), loadSchedulerStatus()])
  if (selectedAppId.value) {
    loadHistory()
  }
}

onMounted(() => {
  initChart()
  loadAllData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.app-ranking {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a14 0%, #12121e 50%, #0f1525 100%);
  padding: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding: 14px 18px;
  background: rgba(26, 26, 40, 0.85);
  border-radius: 10px;
  border: 1px solid rgba(102, 126, 234, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-left h1 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.header-left h1 .el-icon {
  color: #667eea;
  font-size: 20px;
}

.update-time {
  font-size: 13px;
  color: #808090;
}

.stats-row {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(26, 26, 40, 0.85);
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.12);
  flex: 1;
}

.stat-item .el-icon {
  font-size: 18px;
  color: #667eea;
}

.stat-item .v {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.stat-item .l {
  font-size: 12px;
  color: #808090;
}

.stat-item.running .el-icon {
  color: #22c55e;
}

.stat-item.stopped .el-icon {
  color: #ef4444;
}

.ranking-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.ranking-card {
  background: rgba(26, 26, 40, 0.85);
  border-radius: 10px;
  border: 1px solid rgba(102, 126, 234, 0.12);
  overflow: hidden;
}

.card-header {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(102, 126, 234, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.card-header .en-name {
  font-size: 11px;
  color: #808090;
}

.card-body {
  padding: 10px 14px;
}

.country-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
}

.country-row .flag {
  font-size: 18px;
}

.country-row .country-name {
  flex: 1;
  font-size: 13px;
  color: #a0a0b0;
}

.country-row .rank {
  font-size: 16px;
  font-weight: 600;
  min-width: 40px;
  text-align: right;
}

.rank-high {
  color: #22c55e;
}

.rank-mid {
  color: #f59e0b;
}

.rank-low {
  color: #808090;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.panel {
  background: rgba(26, 26, 40, 0.85);
  border-radius: 10px;
  border: 1px solid rgba(102, 126, 234, 0.12);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(102, 126, 234, 0.08);
}

.panel-header h3 {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  margin: 0;
}

.panel-header h3 .el-icon {
  color: #667eea;
  font-size: 14px;
}

.chart-controls {
  display: flex;
  gap: 8px;
}

.chart-area {
  height: 280px;
  padding: 10px;
}

.country-tabs {
  padding: 0 10px;
}

.country-tabs :deep(.el-tabs__item) {
  color: #a0a0b0;
  font-size: 12px;
}

.country-tabs :deep(.el-tabs__item.is-active) {
  color: #667eea;
}

.top-list {
  padding: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.top-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 6px;
  margin-bottom: 6px;
  background: rgba(20, 20, 32, 0.6);
}

.top-item:hover {
  background: rgba(102, 126, 234, 0.1);
}

.top-item .rank {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  background: #3a3a4a;
}

.top-item .rank.r1 {
  background: linear-gradient(135deg, #ffd700, #ffaa00);
}

.top-item .rank.r2 {
  background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
}

.top-item .rank.r3 {
  background: linear-gradient(135deg, #cd7f32, #b87333);
}

.top-item .app-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  object-fit: cover;
}

.top-item .app-info {
  flex: 1;
  min-width: 0;
}

.top-item .app-name {
  display: block;
  font-size: 13px;
  color: #e0e0e8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-item .developer {
  display: block;
  font-size: 11px;
  color: #808090;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 1000px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .ranking-cards {
    grid-template-columns: 1fr;
  }
}
</style>
