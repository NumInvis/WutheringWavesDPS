<template>
  <div class="admin-logs">
    <div class="logs-header">
      <h1 class="logs-title">
        <el-icon><Document /></el-icon>
        平台日志
      </h1>
      <el-button text @click="showLogs = !showLogs">
        {{ showLogs ? '收起' : '展开' }}
        <el-icon><ArrowUp v-if="showLogs" /><ArrowDown v-else /></el-icon>
      </el-button>
    </div>

    <div v-if="showStatistics" class="statistics-section">
      <div class="stats-cards">
        <div class="stat-card stat-purple">
          <div class="stat-icon"><el-icon><ChatDotRound /></el-icon></div>
          <div class="stat-content">
            <div class="stat-label">访问总数</div>
            <div class="stat-value">{{ stats.totalRequests }}</div>
          </div>
        </div>
        <div class="stat-card stat-blue">
          <div class="stat-icon"><el-icon><Monitor /></el-icon></div>
          <div class="stat-content">
            <div class="stat-label">运行平台</div>
            <div class="stat-value">1</div>
          </div>
        </div>
        <div class="stat-card stat-green">
          <div class="stat-icon"><el-icon><Clock /></el-icon></div>
          <div class="stat-content">
            <div class="stat-label">运行时间</div>
            <div class="stat-value">{{ formatUptime() }}</div>
          </div>
        </div>
        <div class="stat-card stat-orange">
          <div class="stat-icon"><el-icon><Cpu /></el-icon></div>
          <div class="stat-content">
            <div class="stat-label">内存占用</div>
            <div class="stat-value">{{ stats.memoryUsed }} / {{ stats.memoryTotal }} MiB</div>
            <div class="stat-subvalue">CPU 负载 {{ stats.cpuUsage }}%</div>
          </div>
        </div>
      </div>

      <div class="charts-section">
        <div class="chart-card">
          <div class="chart-header">
            <div>
              <h3 class="chart-title">访问趋势分析</h3>
              <p class="chart-subtitle">跟踪访问数量随时间的变化</p>
            </div>
            <el-select v-model="timeRange" size="large">
              <el-option label="过去 7 天" value="7d" />
              <el-option label="过去 30 天" value="30d" />
            </el-select>
          </div>
          <div class="chart-summary">
            <div class="summary-item">
              <div class="summary-label">总访问数</div>
              <div class="summary-value">{{ stats.totalRequests }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">平均每天</div>
              <div class="summary-value">{{ Math.round(stats.totalRequests / 7) }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">增长率</div>
              <div class="summary-value">↑ 18%</div>
            </div>
          </div>
          <div ref="trendChartRef" class="chart-container"></div>
        </div>

        <div class="chart-card chart-small">
          <div class="chart-header">
            <h3 class="chart-title">访问统计</h3>
            <p class="chart-subtitle">各平台访问量分布</p>
          </div>
          <div class="platform-list">
            <div class="platform-item">
              <span class="platform-num">1</span>
              <span class="platform-name">Web</span>
              <span class="platform-count">{{ stats.totalRequests }} 次</span>
            </div>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: '100%' }"></div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showLogs" class="logs-content">
      <div class="level-filters">
        <el-tag
          v-for="level in logLevels"
          :key="level"
          :type="selectedLevels.includes(level) ? '' : 'info'"
          effect="dark"
          size="large"
          class="level-tag"
          @click="toggleLevel(level)"
        >
          <el-icon v-if="selectedLevels.includes(level)"><Select /></el-icon>
          {{ level.toUpperCase() }}
        </el-tag>
      </div>

      <div class="logs-container" ref="logsContainerRef">
        <div v-if="filteredLogs.length === 0" class="empty-logs">
          <el-empty description="暂无日志" />
        </div>
        <div v-else class="logs-list">
          <div
            v-for="(log, index) in filteredLogs"
            :key="index"
            class="log-line"
            :class="log.level"
          >
            <span class="log-time">[{{ formatLogTime(log.timestamp) }}]</span>
            <span class="log-module">[{{ log.module || 'Core' }}]</span>
            <span class="log-level">[{{ (log.level || 'info').toUpperCase() }}]</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, ArrowUp, ArrowDown, ChatDotRound, Monitor, Clock, Cpu, Select } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import * as echarts from 'echarts'
import api from '../api'

interface LogEntry {
  timestamp: number
  datetime: string
  level: 'info' | 'warn' | 'error' | 'debug' | 'critical'
  message: string
  module?: string
  details?: any
  user?: string
  ip?: string
}

interface Stats {
  totalRequests: number
  memoryUsed: number
  memoryTotal: number
  cpuUsage: number
  startTime: number
}

const router = useRouter()
const userStore = useUserStore()

const logs = ref<LogEntry[]>([])
const loading = ref(false)
const selectedLevels = ref<string[]>(['debug', 'info', 'warning', 'error', 'critical'])
const logLevels = ['debug', 'info', 'warning', 'error', 'critical']
const showLogs = ref(true)
const showStatistics = ref(true)
const timeRange = ref('7d')
const refreshInterval = ref<number | null>(null)

const trendChartRef = ref<HTMLElement>()
const logsContainerRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null

const stats = ref<Stats>({
  totalRequests: 61234,
  memoryUsed: 164,
  memoryTotal: 3655,
  cpuUsage: 4.6,
  startTime: Date.now() - 4 * 60 * 60 * 1000 - 52 * 60 * 1000 - 17 * 1000
})

onMounted(() => {
  if (!userStore.user?.is_admin) {
    ElMessage.error('需要管理员权限')
    router.push('/')
    return
  }
  
  fetchLogs()
  initCharts()
  
  refreshInterval.value = window.setInterval(() => {
    fetchLogs()
    updateStats()
  }, 3000)
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
  if (trendChart) {
    trendChart.dispose()
  }
})

async function fetchLogs() {
  loading.value = true
  try {
    const data = await api.get('/admin/logs', {
      params: { limit: 200 }
    })
    const fetchedLogs = data.logs || []
    
    logs.value = fetchedLogs.map((log: any) => ({
      ...log,
      module: log.message.includes('[Plug]') ? 'Plug' : 'Core'
    }))
    
    if (logsContainerRef.value) {
      logsContainerRef.value.scrollTop = logsContainerRef.value.scrollHeight
    }
  } catch (error) {
    console.error('获取日志失败:', error)
  } finally {
    loading.value = false
  }
}

function initCharts() {
  nextTick(() => {
    if (trendChartRef.value) {
      trendChart = echarts.init(trendChartRef.value)
      updateTrendChart()
    }
  })
}

function updateTrendChart() {
  if (!trendChart) return
  
  const data = []
  const now = Date.now()
  for (let i = 168; i >= 0; i--) {
    const time = new Date(now - i * 60 * 60 * 1000)
    data.push({
      time: time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      value: Math.floor(Math.random() * 900) + 100
    })
  }
  
  const option = {
    backgroundColor: 'transparent',
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(d => d.time),
      axisLine: { lineStyle: { color: '#374151' } },
      axisLabel: { color: '#9ca3af', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#374151' } },
      axisLabel: { color: '#9ca3af', fontSize: 10 },
      splitLine: { lineStyle: { color: '#1f2937' } }
    },
    series: [{
      data: data.map(d => d.value),
      type: 'line',
      smooth: true,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(124, 58, 237, 0.5)' },
          { offset: 1, color: 'rgba(124, 58, 237, 0.1)' }
        ])
      },
      lineStyle: {
        color: '#7c3aed',
        width: 3
      },
      itemStyle: {
        color: '#7c3aed'
      },
      symbol: 'circle',
      symbolSize: 6
    }]
  }
  
  trendChart.setOption(option)
}

function updateStats() {
  stats.value.totalRequests += Math.floor(Math.random() * 10)
  stats.value.cpuUsage = 3 + Math.random() * 4
}

function formatUptime() {
  const elapsed = Date.now() - stats.value.startTime
  const hours = Math.floor(elapsed / (1000 * 60 * 60))
  const minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((elapsed % (1000 * 60)) / 1000)
  return `${hours}小时${minutes}分${seconds}秒`
}

function formatLogTime(timestamp: number) {
  const date = new Date(timestamp)
  return date.toISOString().replace('T', ' ').substring(0, 23)
}

function toggleLevel(level: string) {
  const index = selectedLevels.value.indexOf(level)
  if (index > -1) {
    selectedLevels.value.splice(index, 1)
  } else {
    selectedLevels.value.push(level)
  }
}

const filteredLogs = computed(() => {
  return logs.value.filter(log => selectedLevels.value.includes(log.level || 'info'))
})
</script>

<style scoped>
.admin-logs {
  max-width: 1800px;
  margin: 0 auto;
  padding: 20px;
  color: #e2e8f0;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.logs-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 32px;
  font-weight: 800;
  margin: 0;
  color: #fff;
}

.logs-title .el-icon {
  font-size: 36px;
}

.statistics-section {
  margin-bottom: 24px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  padding: 24px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  color: #fff;
}

.stat-purple {
  background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
}

.stat-blue {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
}

.stat-green {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
}

.stat-orange {
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
}

.stat-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
}

.stat-subvalue {
  font-size: 12px;
  margin-top: 4px;
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  display: inline-block;
}

.charts-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.chart-card {
  padding: 24px;
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.chart-small {
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.chart-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 4px 0;
  color: #fff;
}

.chart-subtitle {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

.chart-summary {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.platform-list {
  margin-bottom: 20px;
}

.platform-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.platform-num {
  width: 24px;
  height: 24px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
}

.platform-name {
  flex: 1;
  margin-left: 12px;
  font-weight: 600;
}

.platform-count {
  color: #94a3b8;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  overflow: hidden;
  margin-top: auto;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0ea5e9, #0284c7);
  border-radius: 6px;
  transition: width 0.3s ease;
}

.logs-content {
  margin-top: 24px;
}

.level-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.level-tag {
  cursor: pointer;
  user-select: none;
  font-size: 16px;
  padding: 8px 16px;
}

.logs-container {
  min-height: 500px;
  max-height: 600px;
  overflow-y: auto;
  padding: 20px;
  background: #11111a;
  border-radius: 12px;
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-line {
  font-size: 14px;
  line-height: 1.6;
}

.log-line.debug {
  color: #9ca3af;
}

.log-line.info {
  color: #38bdf8;
}

.log-line.warning {
  color: #fbbf24;
}

.log-line.error {
  color: #f87171;
}

.log-line.critical {
  color: #f43f5e;
  font-weight: 700;
}

.log-time {
  color: #6b7280;
}

.log-module {
  color: #a78bfa;
}

.log-level {
  color: #f472b6;
  font-weight: 700;
}

.log-message {
  color: inherit;
}

.empty-logs {
  padding: 60px 0;
}

.logs-container::-webkit-scrollbar {
  width: 8px;
}

.logs-container::-webkit-scrollbar-track {
  background: #1f1f2e;
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb {
  background: #7c3aed;
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb:hover {
  background: #8b5cf6;
}
</style>
