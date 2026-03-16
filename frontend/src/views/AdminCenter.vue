<template>
  <div class="admin-container">
    <div class="admin-sidebar">
      <div class="sidebar-header">
        <el-icon class="admin-icon"><Setting /></el-icon>
        <span class="admin-title">管理中心</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item index="dashboard">
          <el-icon><DataLine /></el-icon>
          <span>监控中心</span>
        </el-menu-item>
        <el-menu-item index="backup">
          <el-icon><FolderOpened /></el-icon>
          <span>数据备份</span>
        </el-menu-item>
        <el-menu-item index="logs">
          <el-icon><Document /></el-icon>
          <span>系统日志</span>
        </el-menu-item>
        <el-menu-item index="announcements">
          <el-icon><ChatDotRound /></el-icon>
          <span>公告管理</span>
        </el-menu-item>
        <el-menu-item index="security">
          <el-icon><Lock /></el-icon>
          <span>安全配置</span>
        </el-menu-item>
      </el-menu>
    </div>

    <div class="admin-content">
      <div v-if="activeMenu === 'dashboard'" class="dashboard-section">
        <div class="content-header">
          <h2 class="section-title">
            <el-icon><Monitor /></el-icon>
            系统监控
          </h2>
          <div class="header-actions">
            <el-button type="primary" @click="refreshAllData" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新数据
            </el-button>
            <el-select v-model="refreshInterval" size="default" @change="updateRefreshInterval">
              <el-option label="5秒" :value="5000" />
              <el-option label="10秒" :value="10000" />
              <el-option label="30秒" :value="30000" />
              <el-option label="手动" :value="0" />
            </el-select>
          </div>
        </div>

        <div class="stats-overview">
          <div class="stat-card stat-card-primary">
            <div class="stat-icon-bg">
              <el-icon><View /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">总浏览量 (PV)</div>
              <div class="stat-value">{{ visitStats.total_visits || 0 }}</div>
            </div>
          </div>

          <div class="stat-card stat-card-info">
            <div class="stat-icon-bg">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">总访客数 (UV)</div>
              <div class="stat-value">{{ visitStats.total_visitors || 0 }}</div>
            </div>
          </div>

          <div class="stat-card stat-card-success">
            <div class="stat-icon-bg">
              <el-icon><Sunny /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">今日 PV</div>
              <div class="stat-value">{{ visitStats.today_visits || 0 }}</div>
              <div class="stat-sub">UV: {{ visitStats.today_visitors || 0 }}</div>
            </div>
          </div>

          <div class="stat-card stat-card-warning">
            <div class="stat-icon-bg">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">7天 PV</div>
              <div class="stat-value">{{ visitStats.seven_days_visits || 0 }}</div>
              <div class="stat-sub">UV: {{ visitStats.seven_days_visitors || 0 }}</div>
            </div>
          </div>

          <div class="stat-card stat-card-danger">
            <div class="stat-icon-bg">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">运行时间</div>
              <div class="stat-value">{{ healthChecks.uptime?.uptime_human || '0秒' }}</div>
            </div>
          </div>
        </div>

        <div class="dashboard-grid">
          <div class="grid-item large">
            <div class="card-header">
              <h3 class="card-title">
                <el-icon><TrendCharts /></el-icon>
                访问趋势
              </h3>
              <el-radio-group v-model="timeRange" size="small" @change="loadVisitTrend">
                <el-radio-button label="24h">24小时</el-radio-button>
                <el-radio-button label="7d">7天</el-radio-button>
                <el-radio-button label="30d">30天</el-radio-button>
              </el-radio-group>
            </div>
            <div ref="visitTrendChartRef" class="chart-container"></div>
          </div>

          <div class="grid-item">
            <div class="card-header">
              <h3 class="card-title">
                <el-icon><Cpu /></el-icon>
                系统资源
              </h3>
            </div>
            <div class="resource-monitor">
              <div class="resource-item">
                <div class="resource-info">
                  <span class="resource-label">内存使用</span>
                  <span class="resource-value">
                    {{ formatBytes(healthChecks.memory?.total_bytes || 0) }} / 
                    {{ formatBytes(healthChecks.memory?.available_bytes || 0) }}
                  </span>
                </div>
                <el-progress 
                  :percentage="healthChecks.memory?.usage_percent || 0" 
                  :color="getProgressColor(healthChecks.memory?.usage_percent || 0)" 
                  :stroke-width="8" 
                />
              </div>
              <div class="resource-item">
                <div class="resource-info">
                  <span class="resource-label">磁盘空间</span>
                  <span class="resource-value">
                    {{ formatBytes(healthChecks.disk?.used_bytes || 0) }} / 
                    {{ formatBytes(healthChecks.disk?.total_bytes || 0) }}
                  </span>
                </div>
                <el-progress 
                  :percentage="healthChecks.disk?.usage_percent || 0" 
                  :color="getProgressColor(healthChecks.disk?.usage_percent || 0)" 
                  :stroke-width="8" 
                />
              </div>
              <div class="resource-item">
                <div class="resource-info">
                  <span class="resource-label">数据库</span>
                  <span class="resource-value" :class="healthChecks.database?.status === 'healthy' ? 'text-success' : 'text-danger'">
                    {{ healthChecks.database?.status === 'healthy' ? '正常' : '异常' }}
                  </span>
                </div>
                <div class="db-info">
                  <span class="db-detail">延迟: {{ healthChecks.database?.latency_ms || 0 }}ms</span>
                  <span class="db-detail">大小: {{ formatBytes(healthChecks.database?.size_bytes || 0) }}</span>
                </div>
              </div>
              <div class="resource-item">
                <div class="resource-info">
                  <span class="resource-label">上传目录</span>
                  <span class="resource-value" :class="healthChecks.uploads?.status === 'healthy' ? 'text-success' : 'text-danger'">
                    {{ healthChecks.uploads?.status === 'healthy' ? '正常' : '异常' }}
                  </span>
                </div>
                <div class="db-info">
                  <span class="db-detail">文件: {{ healthChecks.uploads?.file_count || 0 }}个</span>
                  <span class="db-detail">大小: {{ formatBytes(healthChecks.uploads?.total_size_bytes || 0) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeMenu === 'logs'" class="logs-section">
        <div class="content-header">
          <h2 class="section-title">
            <el-icon><Document /></el-icon>
            系统日志
          </h2>
          <div class="header-actions">
            <el-select v-model="logLevel" size="default" placeholder="日志级别" clearable @change="fetchLogs">
              <el-option label="全部" value="" />
              <el-option label="INFO" value="info" />
              <el-option label="WARN" value="warn" />
              <el-option label="ERROR" value="error" />
              <el-option label="DEBUG" value="debug" />
            </el-select>
            <el-button type="danger" @click="clearLogs">
              <el-icon><Delete /></el-icon>
              清空日志
            </el-button>
          </div>
        </div>

        <div class="logs-container" ref="logsContainerRef">
          <div v-for="(log, index) in logs" :key="index" :class="['log-item', 'log-' + log.level]">
            <span class="log-time">{{ log.datetime }}</span>
            <span :class="['log-level', 'level-' + log.level]">{{ log.level.toUpperCase() }}</span>
            <span class="log-module">{{ log.module || 'Core' }}</span>
            <span class="log-message">{{ log.message }}</span>
            <span v-if="log.user" class="log-user">@{{ log.user }}</span>
          </div>
          <div v-if="logs.length === 0" class="no-logs">
            <el-icon><Document /></el-icon>
            <span>暂无日志</span>
          </div>
        </div>
      </div>

      <div v-else-if="activeMenu === 'announcements'" class="announcements-section">
        <div class="content-header">
          <h2 class="section-title">
            <el-icon><ChatDotRound /></el-icon>
            公告管理
          </h2>
          <div class="header-actions">
            <el-button type="primary" @click="showAddAnnouncement = true">
              <el-icon><Plus /></el-icon>
              发布公告
            </el-button>
          </div>
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

      <div v-else-if="activeMenu === 'backup'" class="backup-section">
        <div class="content-header">
          <h2 class="section-title">
            <el-icon><FolderOpened /></el-icon>
            数据备份管理
          </h2>
        </div>
        
        <div class="backup-management">
          <div class="backup-settings">
            <div class="setting-item">
              <span class="setting-label">最大备份大小 (MB)</span>
              <el-input-number v-model="maxBackupSize" :min="10" :max="500" :step="10" size="small" @change="saveBackupSettings" />
            </div>
            <div class="setting-info">当前已使用: {{ currentBackupSize }} MB / {{ maxBackupSize }} MB</div>
          </div>
          <el-divider />
          <div class="backup-actions">
            <el-button type="primary" @click="exportSpreadsheetBackup" :loading="backupLoading.spreadsheet">
              <el-icon><Document /></el-icon>
              导出表格备份
            </el-button>
            <el-button type="success" @click="exportTiebaBackup" :loading="backupLoading.tieba">
              <el-icon><ChatDotRound /></el-icon>
              导出贴吧备份
            </el-button>
            <el-button type="warning" @click="exportRankingBackup" :loading="backupLoading.ranking">
              <el-icon><TrendCharts /></el-icon>
              导出iOS排行榜备份
            </el-button>
          </div>
        </div>
      </div>
      
      <div v-else-if="activeMenu === 'security'" class="security-section">
        <SecurityConfig />
      </div>
    </div>

    <el-dialog v-model="showAddAnnouncement" title="发布公告" width="500px">
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
import {
  Setting, DataLine, Document, ChatDotRound, Monitor, Refresh,
  User, Sunny, Calendar, Timer, Cpu, TrendCharts, View,
  Delete, Plus, Select, ArrowUp, ArrowDown, Lock, FolderOpened
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../api'
import SecurityConfig from './SecurityConfig.vue'

const activeMenu = ref('dashboard')
const loading = ref(false)
const refreshInterval = ref(5000)
const timeRange = ref<'24h' | '7d' | '30d'>('7d')
const logLevel = ref('')

const visitStats = ref({
  total_visits: 0,
  today_visits: 0,
  seven_days_visits: 0
})

const healthChecks = ref({
  database: {},
  disk: {},
  memory: {},
  uptime: {},
  uploads: {}
})

const logs = ref<any[]>([])
const announcements = ref<any[]>([])
const showAddAnnouncement = ref(false)
const addAnnouncementLoading = ref(false)
const newAnnouncementForm = ref({
  title: '',
  content: '',
  is_active: true,
  is_pinned: false
})

const maxBackupSize = ref(50)
const currentBackupSize = ref(0)
const backupLoading = ref({
  spreadsheet: false,
  tieba: false,
  ranking: false
})

const visitTrendChartRef = ref<HTMLElement>()
const logsContainerRef = ref<HTMLElement>()
let visitTrendChart: echarts.ECharts | null = null
let refreshTimer: any = null

function handleMenuSelect(index: string) {
  activeMenu.value = index
  if (index === 'dashboard') {
    refreshAllData()
  } else if (index === 'logs') {
    fetchLogs()
  } else if (index === 'announcements') {
    loadAnnouncements()
  } else if (index === 'backup') {
    loadBackupSettings()
  }
}

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function getProgressColor(percent: number) {
  if (percent < 50) return '#22c55e'
  if (percent < 80) return '#f59e0b'
  return '#ef4444'
}

async function refreshAllData() {
  loading.value = true
  try {
    await Promise.all([
      loadVisitStats(),
      loadHealthCheck(),
      loadVisitTrend()
    ])
  } catch (error) {
    console.error('刷新数据失败:', error)
  } finally {
    loading.value = false
  }
}

function updateRefreshInterval() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  if (refreshInterval.value > 0) {
    refreshTimer = setInterval(() => {
      refreshAllData()
    }, refreshInterval.value)
  }
}

async function loadVisitStats() {
  try {
    const data = await api.get('/visit-stats/summary')
    visitStats.value = data
  } catch (error) {
    console.error('加载访问统计失败:', error)
  }
}

async function loadHealthCheck() {
  try {
    const data = await api.get('/health/detailed')
    healthChecks.value = data.checks || {}
  } catch (error) {
    console.error('加载健康检查失败:', error)
  }
}

async function loadVisitTrend() {
  try {
    const data = await api.get(`/visit-stats/trend?range_type=${timeRange.value}`)
    
    const chartData = data || []
    if (chartData.length === 0) {
      if (visitTrendChart) {
        visitTrendChart.setOption({
          xAxis: { data: [] },
          series: [{ data: [] }]
        })
      }
      return
    }
    
    const labels = chartData.map((item: any) => item.label || item.time)
    const counts = chartData.map((item: any) => item.count || 0)
    
    if (visitTrendChart) {
      visitTrendChart.setOption({
        xAxis: { data: labels },
        series: [{ data: counts }]
      })
    }
  } catch (error) {
    console.error('加载访问趋势失败:', error)
  }
}

async function fetchLogs() {
  try {
    let url = '/admin/logs?limit=200'
    if (logLevel.value) {
      url += '&level=' + logLevel.value
    }
    const response = await api.get(url)
    logs.value = response.logs || []
    
    if (logsContainerRef.value) {
      logsContainerRef.value.scrollTop = logsContainerRef.value.scrollHeight
    }
  } catch (error) {
    console.error('获取日志失败:', error)
  }
}

async function clearLogs() {
  try {
    await ElMessageBox.confirm('确定要清空所有日志吗？', '确认清空', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete('/admin/logs')
    logs.value = []
    ElMessage.success({ message: '日志已清空', duration: 500 })
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('清空日志失败:', error)
    }
  }
}

async function loadAnnouncements() {
  try {
    const data = await api.get('/announcements')
    if (Array.isArray(data)) {
      announcements.value = data
    } else {
      announcements.value = []
    }
  } catch (error) {
    console.error('加载公告失败:', error)
    announcements.value = []
  }
}

async function addAnnouncement() {
  if (!newAnnouncementForm.value.title || !newAnnouncementForm.value.content) {
    ElMessage.error({ message: '请填写完整的公告信息', duration: 500 })
    return
  }
  
  addAnnouncementLoading.value = true
  try {
    await api.post('/announcements', newAnnouncementForm.value)
    
    ElMessage.success({ message: '公告发布成功！', duration: 500 })
    showAddAnnouncement.value = false
    newAnnouncementForm.value = { title: '', content: '', is_active: true, is_pinned: false }
    loadAnnouncements()
  } catch (error: any) {
    console.error('发布公告失败:', error)
    ElMessage.error({ message: error.response?.data?.detail || '发布公告失败', duration: 500 })
  } finally {
    addAnnouncementLoading.value = false
  }
}

async function activateAnnouncement(announcement: any) {
  try {
    await api.put('/announcements/' + announcement.id, { is_active: true })
    
    ElMessage.success({ message: '公告已激活！', duration: 500 })
    loadAnnouncements()
  } catch (error: any) {
    console.error('激活公告失败:', error)
    ElMessage.error({ message: error.response?.data?.detail || '激活公告失败', duration: 500 })
  }
}

async function togglePinAnnouncement(announcement: any) {
  try {
    await api.put('/announcements/' + announcement.id, { is_pinned: !announcement.is_pinned })
    
    ElMessage.success({ message: announcement.is_pinned ? '已取消置顶' : '已置顶', duration: 500 })
    loadAnnouncements()
  } catch (error: any) {
    console.error('操作失败:', error)
    ElMessage.error({ message: error.response?.data?.detail || '操作失败', duration: 500 })
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
    
    ElMessage.success({ message: '公告已删除！', duration: 500 })
    loadAnnouncements()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除公告失败:', error)
      ElMessage.error({ message: error.response?.data?.detail || '删除公告失败', duration: 500 })
    }
  }
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

async function saveBackupSettings() {
  try {
    await api.post('/admin/backup/settings', { max_size: maxBackupSize.value })
    ElMessage.success('备份设置已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

async function loadBackupSettings() {
  try {
    const data = await api.get('/admin/backup/settings')
    maxBackupSize.value = data.max_size || 50
    currentBackupSize.value = data.current_size || 0
  } catch (error) {
    console.error('加载备份设置失败')
  }
}

async function exportSpreadsheetBackup() {
  backupLoading.value.spreadsheet = true
  try {
    const response = await api.get('/admin/backup/spreadsheet', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response]))
    const a = document.createElement('a')
    a.href = url
    a.download = `spreadsheet_backup_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success('表格备份下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  } finally {
    backupLoading.value.spreadsheet = false
  }
}

async function exportTiebaBackup() {
  backupLoading.value.tieba = true
  try {
    const response = await api.get('/admin/backup/tieba', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response]))
    const a = document.createElement('a')
    a.href = url
    a.download = `tieba_backup_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success('贴吧备份下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  } finally {
    backupLoading.value.tieba = false
  }
}

async function exportRankingBackup() {
  backupLoading.value.ranking = true
  try {
    const response = await api.get('/admin/backup/ranking', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response]))
    const a = document.createElement('a')
    a.href = url
    a.download = `ranking_backup_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success('iOS排行榜备份下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  } finally {
    backupLoading.value.ranking = false
  }
}

function initCharts() {
  nextTick(() => {
    if (visitTrendChartRef.value) {
      if (visitTrendChart) {
        visitTrendChart.dispose()
      }
      visitTrendChart = echarts.init(visitTrendChartRef.value)
      visitTrendChart.setOption({
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(26, 26, 46, 0.95)',
          borderColor: 'rgba(102, 126, 234, 0.5)',
          textStyle: { color: '#fff' }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: [],
          axisLine: { lineStyle: { color: '#2a2a3a' } },
          axisLabel: { color: '#808090', rotate: 45, fontSize: 10 }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: '#2a2a3a' } },
          axisLabel: { color: '#808090' },
          splitLine: { lineStyle: { color: '#2a2a3a' } }
        },
        series: [{
          name: '访问量',
          type: 'line',
          smooth: true,
          data: [],
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
              { offset: 1, color: 'rgba(102, 126, 234, 0)' }
            ])
          },
          lineStyle: {
            color: '#667eea',
            width: 3
          },
          itemStyle: {
            color: '#667eea'
          }
        }]
      })
    }
  })
}

function handleResize() {
  if (visitTrendChart) visitTrendChart.resize()
}

onMounted(() => {
  initCharts()
  refreshAllData()
  loadBackupSettings()
  updateRefreshInterval()
  window.addEventListener('resize', handleResize)
  
  const interval = setInterval(() => {
    if (activeMenu.value === 'logs') {
      fetchLogs()
    }
  }, 5000)
  
  return () => clearInterval(interval)
})

onUnmounted(() => {
  if (visitTrendChart) visitTrendChart.dispose()
  if (refreshTimer) clearInterval(refreshTimer)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.admin-container {
  display: flex;
  height: 100%;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
}

.admin-sidebar {
  width: 240px;
  background: rgba(15, 15, 26, 0.95);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.admin-icon {
  font-size: 28px;
  color: #667eea;
}

.admin-title {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}

.sidebar-menu {
  flex: 1;
  border: none;
  background: transparent;
}

:deep(.sidebar-menu .el-menu-item) {
  margin: 4px 12px;
  border-radius: 8px;
  color: #808090;
  transition: all 0.2s ease;
}

:deep(.sidebar-menu .el-menu-item:hover) {
  background: rgba(102, 126, 234, 0.1);
  color: #fff;
}

:deep(.sidebar-menu .el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%);
  color: #667eea;
}

.admin-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: linear-gradient(135deg, #1a1a28 0%, #161622 100%);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  border: 1px solid #2a2a3a;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.stat-card-primary { border-left: 4px solid #667eea; }
.stat-card-info { border-left: 4px solid #3b82f6; }
.stat-card-success { border-left: 4px solid #22c55e; }
.stat-card-warning { border-left: 4px solid #f59e0b; }
.stat-card-danger { border-left: 4px solid #ef4444; }

.stat-icon-bg {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  background: currentColor;
  opacity: 0.15;
}

.stat-icon-bg .el-icon {
  color: currentColor;
  opacity: 1;
}

.stat-card-primary .stat-icon-bg { color: #667eea; }
.stat-card-info .stat-icon-bg { color: #3b82f6; }
.stat-card-success .stat-icon-bg { color: #22c55e; }
.stat-card-warning .stat-icon-bg { color: #f59e0b; }
.stat-card-danger .stat-icon-bg { color: #ef4444; }

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #808090;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  line-height: 1;
}

.stat-sub {
  font-size: 14px;
  color: #808090;
  margin-top: 4px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.grid-item {
  background: linear-gradient(135deg, #1a1a28 0%, #161622 100%);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #2a2a3a;
}

.grid-item.large {
  grid-column: span 2;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #2a2a3a;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.chart-container {
  height: 300px;
}

.resource-monitor {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.resource-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.resource-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.resource-label {
  font-size: 14px;
  color: #808090;
}

.resource-value {
  font-size: 14px;
  color: #fff;
  font-weight: 600;
}

.text-success {
  color: #22c55e !important;
}

.text-danger {
  color: #ef4444 !important;
}

.db-info {
  display: flex;
  gap: 16px;
  margin-top: 4px;
}

.db-detail {
  font-size: 12px;
  color: #606070;
}

.logs-container {
  height: calc(100vh - 200px);
  overflow-y: auto;
  padding: 16px;
  background: rgba(26, 26, 40, 0.5);
  border-radius: 12px;
  border: 1px solid #2a2a3a;
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

.no-logs {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #606070;
  gap: 12px;
}

.no-logs .el-icon {
  font-size: 48px;
  color: #606070;
}

.announcements-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.announcement-item {
  background: rgba(26, 26, 40, 0.5);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #2a2a3a;
  display: flex;
  gap: 16px;
  align-items: flex-start;
  transition: all 0.2s ease;
}

.announcement-item:hover {
  background: rgba(26, 26, 40, 0.8);
  border-color: rgba(102, 126, 234, 0.3);
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

@media (max-width: 1400px) {
  .stats-overview {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .grid-item.large {
    grid-column: span 2;
  }
}

@media (max-width: 900px) {
  .admin-container {
    flex-direction: column;
  }
  
  .admin-sidebar {
    width: 100%;
    height: auto;
  }
  
  .stats-overview {
    grid-template-columns: 1fr;
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .grid-item.large {
    grid-column: span 1;
  }
  
  .content-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}

.backup-management {
  background: rgba(26, 26, 40, 0.5);
  border-radius: 12px;
  border: 1px solid #2a2a3a;
  padding: 24px;
}

.backup-settings {
  margin-bottom: 16px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.setting-label {
  font-size: 14px;
  color: #e2e8f0;
  font-weight: 500;
}

.setting-info {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 8px;
  font-family: 'SF Mono', 'Monaco', monospace;
}

.backup-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
