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
            <h3 class="chart-title">访问趋势</h3>
            <el-radio-group v-model="timeRange" size="small" @change="loadVisitStats">
              <el-radio-button label="7">7天</el-radio-button>
              <el-radio-button label="30">30天</el-radio-button>
            </el-radio-group>
          </div>
          <div ref="trendChartRef" class="chart-container"></div>
        </div>
      </div>
    </div>

    <div v-else-if="activeTab === 'announcements'" class="announcements-section">
      <div class="section-header">
        <h2 class="section-title">公告管理</h2>
        <el-button type="primary" @click="showAddAnnouncement = true">
          <el-icon><Plus /></el-icon>
          发布公告
        </el-button>
      </div>

      <div class="announcements-list">
        <div v-for="announcement in announcements" :key="announcement.id" class="announcement-item">
          <div class="announcement-status">
            <el-tag v-if="announcement.is_pinned" type="warning" size="small">置顶</el-tag>
            <el-tag v-if="announcement.is_active" type="success" size="small">已激活</el-tag>
            <el-tag v-else type="info" size="small">未激活</el-tag>
          </div>
          <div class="announcement-content">
            <h3 class="announcement-title">{{ announcement.title }}</h3>
            <p class="announcement-text">{{ announcement.content }}</p>
            <div class="announcement-meta">
              <span>发布时间: {{ formatDate(announcement.published_at) }}</span>
            </div>
          </div>
          <div class="announcement-actions">
            <el-button 
              v-if="!announcement.is_active" 
              type="primary" 
              size="small"
              @click="activateAnnouncement(announcement)"
            >
              <el-icon><Select /></el-icon>
              激活
            </el-button>
            <el-button 
              type="warning" 
              size="small"
              @click="togglePinAnnouncement(announcement)"
            >
              <el-icon><ArrowUp v-if="!announcement.is_pinned" /><ArrowDown v-else /></el-icon>
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

    <div v-else class="logs-section">
      <div class="logs-container" ref="logsContainerRef">
        <div v-for="(log, index) in logs" :key="index" :class="['log-item', 'log-' + log.level]">
          <span class="log-time">{{ log.datetime }}</span>
          <span :class="['log-level', 'level-' + log.level]">{{ log.level.toUpperCase() }}</span>
          <span class="log-module">{{ log.module }}</span>
          <span class="log-message">{{ log.message }}</span>
          <span v-if="log.user" class="log-user">@{{ log.user }}</span>
        </div>
      </div>
    </div>

    <!-- 发布公告对话框 -->
    <el-dialog
      v-model="showAddAnnouncement" 
      title="发布公告" 
      width="500px"
    >
      <el-form :model="newAnnouncementForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="newAnnouncementForm.title" placeholder="请输入公告标题" />
        </el-form-item>
        <el-form-item label="内容">
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
        <el-form-item label="置顶">
          <el-switch v-model="newAnnouncementForm.is_pinned" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddAnnouncement = false">取消</el-button>
        <el-button type="primary" :loading="addAnnouncementLoading" @click="addAnnouncement">
          发布
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, ArrowUp, ArrowDown, ChatDotRound, Monitor, Clock, Cpu, Select, Plus } from '@element-plus/icons-vue'
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

interface Announcement {
  id: string
  title: string
  content: string
  is_active: boolean
  is_pinned: boolean
  published_at: string
  created_at: string
  updated_at: string
}

interface VisitStats {
  total_visits: number
  today_visits: number
  seven_days_visits: number
}

const userStore = useUserStore()
const activeTab = ref('logs')
const logs = ref<LogEntry[]>([])
const loading = ref(false)
const logsContainerRef = ref<HTMLElement>()

const stats = ref({
  memoryUsed: 0,
  memoryTotal: 0,
  cpuUsage: 0
})

const timeRange = ref('7')
const trendChartRef = ref<HTMLElement>()
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

onMounted(() => {
  fetchLogs()
  loadAnnouncements()
  loadVisitStats()
  initCharts()
  
  const interval = setInterval(() => {
    if (activeTab.value === 'logs') {
      fetchLogs()
    }
  }, 5000)
  
  return () => clearInterval(interval)
})

onUnmounted(() => {
  if (trendChart) {
    trendChart.dispose()
  }
})

async function fetchLogs() {
  loading.value = true
  try {
    const response = await api.get('/admin/logs?limit=200')
    const fetchedLogs = response.logs || []
    
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
    const data = await api.get('/announcements')
    // 验证返回数据是否为数组
    if (Array.isArray(data)) {
      announcements.value = data
    } else {
      console.warn('公告API返回非数组数据:', data)
      announcements.value = []
      ElMessage.warning({ message: '公告数据加载异常', duration: 2000 })
    }
  } catch (error) {
    console.error('加载公告失败:', error)
    announcements.value = []
    ElMessage.error({ message: '加载公告列表失败', duration: 2000 })
  }
}

async function loadVisitStats() {
  try {
    const [summaryData, hourlyData] = await Promise.all([
      api.get('/visit-stats/summary'),
      api.get('/visit-stats/hourly?days=' + timeRange.value)
    ])
    
    visitStats.value = summaryData
    updateTrendChart(hourlyData)
  } catch (error) {
    console.error('加载访问统计失败:', error)
  }
}

async function addAnnouncement() {
  if (!newAnnouncementForm.value.title || !newAnnouncementForm.value.content) {
    ElMessage.error({ message: '请填写完整的公告信息', duration: 2000 })
    return
  }
  
  addAnnouncementLoading.value = true
  try {
    await api.post('/announcements', newAnnouncementForm.value)
    
    ElMessage.success({ message: '公告发布成功！', duration: 2000 })
    showAddAnnouncement.value = false
    newAnnouncementForm.value = { title: '', content: '', is_active: true, is_pinned: false }
    loadAnnouncements()
  } catch (error: any) {
    console.error('发布公告失败:', error)
    ElMessage.error({ message: error.response?.data?.detail || '发布公告失败', duration: 2000 })
  } finally {
    addAnnouncementLoading.value = false
  }
}

async function activateAnnouncement(announcement: Announcement) {
  try {
    await api.put('/announcements/' + announcement.id, { is_active: true })
    
    ElMessage.success({ message: '公告已激活！', duration: 2000 })
    loadAnnouncements()
  } catch (error: any) {
    console.error('激活公告失败:', error)
    ElMessage.error({ message: error.response?.data?.detail || '激活公告失败', duration: 2000 })
  }
}

async function togglePinAnnouncement(announcement: Announcement) {
  try {
    await api.put('/announcements/' + announcement.id, { is_pinned: !announcement.is_pinned })
    
    ElMessage.success({ message: announcement.is_pinned ? '已取消置顶' : '已置顶', duration: 2000 })
    loadAnnouncements()
  } catch (error: any) {
    console.error('操作失败:', error)
    ElMessage.error({ message: error.response?.data?.detail || '操作失败', duration: 2000 })
  }
}

async function deleteAnnouncement(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除这条公告吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete('/announcements/' + id)
    
    ElMessage.success({ message: '公告已删除！', duration: 2000 })
    loadAnnouncements()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除公告失败:', error)
      ElMessage.error({ message: error.response?.data?.detail || '删除公告失败', duration: 2000 })
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
        hour: time.toISOString().slice(0, 13) + ':00:00',
        count: 0
      })
    }
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: chartData.map(item => {
        const date = new Date(item.hour)
        return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:00`
      }),
      axisLabel: {
        rotate: 45,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      name: '访问量'
    },
    series: [{
      name: '访问数',
      type: 'line',
      smooth: true,
      data: chartData.map(item => item.count),
      areaStyle: {
        opacity: 0.3
      },
      lineStyle: {
        width: 2
      }
    }]
  }
  
  trendChart.setOption(option)
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.admin-logs {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.logs-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.header-tabs {
  margin: 0;
}

:deep(.header-tabs .el-tabs__header) {
  margin: 0;
}

:deep(.header-tabs .el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.header-tabs .el-tabs__item) {
  color: #808090;
  font-size: 14px;
}

:deep(.header-tabs .el-tabs__item.is-active) {
  color: #4dabf7;
}

:deep(.header-tabs .el-tabs__active-bar) {
  background-color: #4dabf7;
}

.statistics-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #1a1a28;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid #2a2a3a;
}

.stat-purple { border-left: 4px solid #a855f7; }
.stat-blue { border-left: 4px solid #3b82f6; }
.stat-green { border-left: 4px solid #22c55e; }
.stat-orange { border-left: 4px solid #f97316; }

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-purple .stat-icon { background: rgba(168, 85, 247, 0.2); }
.stat-blue .stat-icon { background: rgba(59, 130, 246, 0.2); }
.stat-green .stat-icon { background: rgba(34, 197, 94, 0.2); }
.stat-orange .stat-icon { background: rgba(249, 115, 22, 0.2); }

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 13px;
  color: #808090;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
}

.stat-subvalue {
  font-size: 12px;
  color: #606070;
  margin-top: 4px;
}

.charts-section {
  background: #1a1a28;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #2a2a3a;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.chart-container {
  height: 300px;
}

.announcements-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.announcements-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.announcement-item {
  background: #1a1a28;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #2a2a3a;
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.announcement-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 60px;
}

.announcement-content {
  flex: 1;
}

.announcement-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 8px 0;
}

.announcement-text {
  font-size: 14px;
  color: #b0b0c0;
  margin: 0 0 8px 0;
  line-height: 1.5;
}

.announcement-meta {
  font-size: 12px;
  color: #606070;
}

.announcement-actions {
  display: flex;
  gap: 8px;
}

.logs-section {
  background: #1a1a28;
  border-radius: 8px;
  border: 1px solid #2a2a3a;
  overflow: hidden;
}

.logs-container {
  height: 600px;
  overflow-y: auto;
  padding: 16px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.log-item {
  display: flex;
  gap: 12px;
  padding: 4px 0;
  border-bottom: 1px solid #2a2a3a;
}

.log-time {
  color: #606070;
  min-width: 140px;
  flex-shrink: 0;
}

.log-level {
  min-width: 50px;
  font-weight: 600;
  flex-shrink: 0;
}

.level-info { color: #3b82f6; }
.level-warn { color: #f59e0b; }
.level-error { color: #ef4444; }
.level-debug { color: #6b7280; }
.level-critical { color: #dc2626; }

.log-module {
  min-width: 50px;
  color: #a855f7;
  flex-shrink: 0;
}

.log-message {
  flex: 1;
  color: #e0e0e0;
  word-break: break-all;
}

.log-user {
  color: #22c55e;
  min-width: 80px;
  flex-shrink: 0;
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .admin-logs {
    padding: 16px;
  }
  
  .logs-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .announcement-item {
    flex-direction: column;
  }
  
  .announcement-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
