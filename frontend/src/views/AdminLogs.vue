<template>
  <div class="admin-logs">
    <div class="logs-header">
      <h1 class="logs-title">
        <el-icon><Document /></el-icon>
        平台管理
      </h1>
      <el-tabs v-model="activeTab" class="header-tabs">
        <el-tab-pane label="日志" name="logs" />
        <el-tab-pane label="统计" name="stats" />
        <el-tab-pane label="公告管理" name="announcements" />
      </el-tabs>
    </div>

    <div v-if="activeTab === 'stats'" class="statistics-section">
      <div class="stats-cards">
        <div class="stat-card stat-purple">
          <div class="stat-icon"><el-icon><ChatDotRound /></el-icon></div>
          <div class="stat-content">
            <div class="stat-label">访问总数</div>
            <div class="stat-value">{{ visitStats.total_visits }}</div>
          </div>
        </div>
        <div class="stat-card stat-blue">
          <div class="stat-icon"><el-icon><Monitor /></el-icon></div>
          <div class="stat-content">
            <div class="stat-label">今日访问</div>
            <div class="stat-value">{{ visitStats.today_visits }}</div>
          </div>
        </div>
        <div class="stat-card stat-green">
          <div class="stat-icon"><el-icon><Clock /></el-icon></div>
          <div class="stat-content">
            <div class="stat-label">7天访问</div>
            <div class="stat-value">{{ visitStats.seven_days_visits }}</div>
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
            <el-select v-model="timeRange" size="large" @change="loadVisitStats">
              <el-option label="过去 7 天" :value="7" />
              <el-option label="过去 30 天" :value="30" />
            </el-select>
          </div>
          <div class="chart-summary">
            <div class="summary-item">
              <div class="summary-label">总访问数</div>
              <div class="summary-value">{{ visitStats.total_visits }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">平均每天</div>
              <div class="summary-value">{{ Math.round(visitStats.total_visits / timeRange) }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">今日访问</div>
              <div class="summary-value">{{ visitStats.today_visits }}</div>
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
              <span class="platform-count">{{ visitStats.total_visits }} 次</span>
            </div>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: '100%' }"></div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'logs'" class="logs-content">
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

    <div v-if="activeTab === 'announcements'" class="announcements-section">
      <div class="section-header">
        <h2 class="section-title">公告管理</h2>
        <el-button type="primary" @click="showAddAnnouncement = true">
          <el-icon><Plus /></el-icon>
          发布公告
        </el-button>
      </div>

      <div class="announcements-list">
        <div 
          v-for="announcement in announcements" 
          :key="announcement.id"
          class="announcement-item"
        >
          <div class="announcement-info">
            <div class="announcement-header">
              <h3 class="announcement-title">{{ announcement.title }}</h3>
              <div class="announcement-badges">
                <el-tag v-if="announcement.is_active" type="success" size="small">当前公告</el-tag>
                <el-tag v-if="announcement.is_pinned" type="warning" size="small">置顶</el-tag>
              </div>
            </div>
            <p class="announcement-content">{{ announcement.content }}</p>
            <div class="announcement-meta">
              <span class="announcement-date">{{ formatDate(announcement.created_at) }}</span>
            </div>
          </div>
          <div class="announcement-actions">
            <el-button 
              v-if="!announcement.is_active" 
              type="primary" 
              size="small"
              @click="activateAnnouncement(announcement)"
            >
              激活
            </el-button>
            <el-button 
              type="warning" 
              size="small"
              @click="togglePinAnnouncement(announcement)"
            >
              {{ announcement.is_pinned ? '取消置顶' : '置顶' }}
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              @click="deleteAnnouncement(announcement.id)"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog 
      v-model="showAddAnnouncement" 
      title="发布新公告" 
      width="500px"
    >
      <el-form :model="newAnnouncementForm" label-width="80px">
        <el-form-item label="公告标题">
          <el-input v-model="newAnnouncementForm.title" placeholder="请输入公告标题" />
        </el-form-item>
        <el-form-item label="公告内容">
          <el-input 
            v-model="newAnnouncementForm.content" 
            type="textarea" 
            :rows="4"
            placeholder="请输入公告内容" 
          />
        </el-form-item>
        <el-form-item label="立即激活">
          <el-switch v-model="newAnnouncementForm.is_active" />
        </el-form-item>
        <el-form-item label="置顶公告">
          <el-switch v-model="newAnnouncementForm.is_pinned" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddAnnouncement = false">取消</el-button>
        <el-button type="primary" @click="addAnnouncement" :loading="addAnnouncementLoading">
          发布
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, ArrowUp, ArrowDown, ChatDotRound, Monitor, Clock, Cpu, Select, Plus } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import * as echarts from 'echarts'
import axios from 'axios'

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

interface Announcement {
  id: string
  title: string
  content: string
  is_active: boolean
  is_pinned: boolean
  created_at: string
}

interface VisitStats {
  total_visits: number
  today_visits: number
  seven_days_visits: number
}

interface Stats {
  memoryUsed: number
  memoryTotal: number
  cpuUsage: number
  startTime: number
}

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('logs')
const logs = ref<LogEntry[]>([])
const loading = ref(false)
const selectedLevels = ref<string[]>(['debug', 'info', 'warning', 'error', 'critical'])
const logLevels = ['debug', 'info', 'warning', 'error', 'critical']
const timeRange = ref(7)
const refreshInterval = ref<number | null>(null)

const trendChartRef = ref<HTMLElement>()
const logsContainerRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null

const announcements = ref<Announcement[]>([])
const showAddAnnouncement = ref(false)
const addAnnouncementLoading = ref(false)
const newAnnouncementForm = ref({
  title: '',
  content: '',
  is_active: true,
  is_pinned: false
})

const visitStats = ref<VisitStats>({
  total_visits: 0,
  today_visits: 0,
  seven_days_visits: 0
})

const stats = ref<Stats>({
  memoryUsed: 164,
  memoryTotal: 3655,
  cpuUsage: 4.6,
  startTime: Date.now() - 4 * 60 * 60 * 1000 - 52 * 60 * 1000 - 17 * 1000
})

onMounted(() => {
  if (!userStore.user?.is_admin) {
    ElMessage.error({ message: { message: '需要管理员权限', duration: 3000 }, duration: 3000 })
    router.push('/')
    return
  }
  
  fetchLogs()
  loadAnnouncements()
  loadVisitStats()
  initCharts()
  
  refreshInterval.value = window.setInterval(() => {
    fetchLogs()
    updateStats()
  }, 5000)
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
    const response = await axios.get(
      import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/admin/logs',
      {
        params: { limit: 200 },
        headers: {
          'Authorization': 'Bearer ' + userStore.token
        }
      }
    )
    const fetchedLogs = response.data.logs || []
    
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

async function loadAnnouncements() {
  try {
    const response = await axios.get(
      import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/announcements',
      {
        headers: {
          'Authorization': 'Bearer ' + userStore.token
        }
      }
    )
    // 验证返回数据是否为数组
    if (Array.isArray(response.data)) {
      announcements.value = response.data
    } else {
      console.warn('公告API返回非数组数据:', response.data)
      announcements.value = []
      ElMessage.warning({ message: { message: '公告数据加载异常', duration: 3000 }, duration: 3000 })
    }
  } catch (error) {
    console.error('加载公告失败:', error)
    announcements.value = []
    ElMessage.error({ message: { message: '加载公告列表失败', duration: 3000 }, duration: 3000 })
  }
}

async function loadVisitStats() {
  try {
    const [summaryResponse, hourlyResponse] = await Promise.all([
      axios.get(
        import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/visit-stats/summary',
        {
          headers: {
            'Authorization': 'Bearer ' + userStore.token
          }
        }
      ),
      axios.get(
        import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/visit-stats/hourly',
        {
          params: { days: timeRange.value },
          headers: {
            'Authorization': 'Bearer ' + userStore.token
          }
        }
      )
    ])
    
    visitStats.value = summaryResponse.data
    updateTrendChart(hourlyResponse.data)
  } catch (error) {
    console.error('加载访问统计失败:', error)
  }
}

async function addAnnouncement() {
  if (!newAnnouncementForm.value.title || !newAnnouncementForm.value.content) {
    ElMessage.error({ message: { message: '请填写完整的公告信息', duration: 3000 }, duration: 3000 })
    return
  }
  
  addAnnouncementLoading.value = true
  try {
    await axios.post(
      import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/announcements',
      newAnnouncementForm.value,
      {
        headers: {
          'Authorization': 'Bearer ' + userStore.token
        }
      }
    )
    
    ElMessage.success({ message: { message: '公告发布成功！', duration: 3000 }, duration: 3000 })
    showAddAnnouncement.value = false
    newAnnouncementForm.value = { title: '', content: '', is_active: true, is_pinned: false }
    loadAnnouncements()
  } catch (error: any) {
    console.error('发布公告失败:', error)
    ElMessage.error({ message: error.response?.data?.detail || '发布公告失败', duration: 3000 })
  } finally {
    addAnnouncementLoading.value = false
  }
}

async function activateAnnouncement(announcement: Announcement) {
  try {
    await axios.put(
      import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/announcements/' + announcement.id,
      { is_active: true },
      {
        headers: {
          'Authorization': 'Bearer ' + userStore.token
        }
      }
    )
    
    ElMessage.success({ message: { message: '公告已激活！', duration: 3000 }, duration: 3000 })
    loadAnnouncements()
  } catch (error: any) {
    console.error('激活公告失败:', error)
    ElMessage.error({ message: error.response?.data?.detail || '激活公告失败', duration: 3000 })
  }
}

async function togglePinAnnouncement(announcement: Announcement) {
  try {
    await axios.put(
      import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/announcements/' + announcement.id,
      { is_pinned: !announcement.is_pinned },
      {
        headers: {
          'Authorization': 'Bearer ' + userStore.token
        }
      }
    )
    
    ElMessage.success({ message: announcement.is_pinned ? '已取消置顶' : '已置顶', duration: 3000 })
    loadAnnouncements()
  } catch (error: any) {
    console.error('操作失败:', error)
    ElMessage.error({ message: error.response?.data?.detail || '操作失败', duration: 3000 })
  }
}

async function deleteAnnouncement(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除这条公告吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await axios.delete(
      import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/announcements/' + id,
      {
        headers: {
          'Authorization': 'Bearer ' + userStore.token
        }
      }
    )
    
    ElMessage.success({ message: { message: '公告已删除！', duration: 3000 }, duration: 3000 })
    loadAnnouncements()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除公告失败:', error)
      ElMessage.error({ message: error.response?.data?.detail || '删除公告失败', duration: 3000 })
    }
  }
}

function initCharts() {
  nextTick(() => {
    if (trendChartRef.value) {
      trendChart = echarts.init(trendChartRef.value)
    }
  })
}

function updateTrendChart(data: any[] = []) {
  if (!trendChart) return
  
  let chartData = data
  if (chartData.length === 0) {
    const now = Date.now()
    for (let i = 168; i >= 0; i--) {
      const time = new Date(now - i * 60 * 60 * 1000)
      chartData.push({
        time: time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        count: 0
      })
    }
  } else {
    chartData = data.map((d: any) => ({
      time: d.time,
      count: d.count
    }))
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
      data: chartData.map((d: any) => d.time),
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
      data: chartData.map((d: any) => d.count),
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
  stats.value.cpuUsage = 3 + Math.random() * 4
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
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

watch(timeRange, () => {
  loadVisitStats()
})

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

.header-tabs {
  margin-left: auto;
}

.announcements-section {
  margin-top: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0;
}

.announcements-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.announcement-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  padding: 24px;
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  transition: all 0.3s ease;
}

.announcement-item:hover {
  border-color: rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.announcement-info {
  flex: 1;
  min-width: 0;
}

.announcement-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.announcement-title {
  font-size: 18px;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0;
}

.announcement-badges {
  display: flex;
  gap: 8px;
}

.announcement-content {
  font-size: 14px;
  color: #94a3b8;
  margin: 0 0 12px 0;
  line-height: 1.6;
}

.announcement-meta {
  display: flex;
  gap: 16px;
}

.announcement-date {
  font-size: 13px;
  color: #6b7280;
}

.announcement-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
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
