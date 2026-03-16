<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="header-left">
        <h1 class="dashboard-title">
          <el-icon class="title-icon"><Monitor /></el-icon>
          系统监控中心
        </h1>
        <div class="header-time">{{ currentTime }}</div>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="refreshAllData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-select v-model="refreshInterval" size="default" @change="updateRefreshInterval">
          <el-option label="实时" :value="1000" />
          <el-option label="5秒" :value="5000" />
          <el-option label="10秒" :value="10000" />
          <el-option label="30秒" :value="30000" />
        </el-select>
      </div>
    </div>

    <div class="stats-overview">
      <div class="stat-card stat-card-primary">
        <div class="stat-icon-bg">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">活跃用户</div>
          <div class="stat-value">{{ stats.activeUsers }}</div>
          <div class="stat-trend positive">
            <el-icon><TrendCharts /></el-icon>
            +12.5%
          </div>
        </div>
      </div>

      <div class="stat-card stat-card-success">
        <div class="stat-icon-bg">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">表格总数</div>
          <div class="stat-value">{{ stats.totalSpreadsheets }}</div>
          <div class="stat-trend positive">
            <el-icon><TrendCharts /></el-icon>
            +8.3%
          </div>
        </div>
      </div>

      <div class="stat-card stat-card-warning">
        <div class="stat-icon-bg">
          <el-icon><View /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">今日访问</div>
          <div class="stat-value">{{ stats.todayVisits }}</div>
          <div class="stat-trend positive">
            <el-icon><TrendCharts /></el-icon>
            +23.1%
          </div>
        </div>
      </div>

      <div class="stat-card stat-card-danger">
        <div class="stat-icon-bg">
          <el-icon><DataLine /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">排行使用</div>
          <div class="stat-value">{{ stats.tierListUsage }}</div>
          <div class="stat-trend negative">
            <el-icon><TrendCharts /></el-icon>
            -2.7%
          </div>
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <div class="grid-item large">
        <div class="card-header">
          <h3 class="card-title">
            <el-icon><TrendCharts /></el-icon>
            访问趋势分析
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
            系统资源监控
          </h3>
        </div>
        <div class="resource-monitor">
          <div class="resource-item">
            <div class="resource-info">
              <span class="resource-label">CPU 使用率</span>
              <span class="resource-value">{{ systemStats.cpu }}%</span>
            </div>
            <el-progress :percentage="systemStats.cpu" :color="getProgressColor(systemStats.cpu)" :stroke-width="8" />
          </div>
          <div class="resource-item">
            <div class="resource-info">
              <span class="resource-label">内存使用</span>
              <span class="resource-value">{{ systemStats.memoryUsed }} / {{ systemStats.memoryTotal }} GB</span>
            </div>
            <el-progress :percentage="systemStats.memoryPercent" :color="getProgressColor(systemStats.memoryPercent)" :stroke-width="8" />
          </div>
          <div class="resource-item">
            <div class="resource-info">
              <span class="resource-label">磁盘空间</span>
              <span class="resource-value">{{ systemStats.diskUsed }} / {{ systemStats.diskTotal }} GB</span>
            </div>
            <el-progress :percentage="systemStats.diskPercent" :color="getProgressColor(systemStats.diskPercent)" :stroke-width="8" />
          </div>
          <div class="resource-item">
            <div class="resource-info">
              <span class="resource-label">网络流量</span>
              <span class="resource-value">{{ systemStats.networkIn }}↓ / {{ systemStats.networkOut }}↑ MB/s</span>
            </div>
            <div class="network-bars">
              <div class="network-bar incoming" :style="{ width: Math.min(100, systemStats.networkIn * 10) + '%' }"></div>
              <div class="network-bar outgoing" :style="{ width: Math.min(100, systemStats.networkOut * 10) + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="grid-item">
        <div class="card-header">
          <h3 class="card-title">
            <el-icon><Rank /></el-icon>
            热门功能排行
          </h3>
        </div>
        <div class="feature-ranking">
          <div v-for="(item, index) in featureRanking" :key="item.name" class="rank-item">
            <div class="rank-number" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
            <div class="rank-info">
              <div class="rank-name">{{ item.name }}</div>
              <div class="rank-bar">
                <div class="rank-bar-fill" :style="{ width: item.percent + '%' }"></div>
              </div>
            </div>
            <div class="rank-value">{{ item.usage }}次</div>
          </div>
        </div>
      </div>

      <div class="grid-item">
        <div class="card-header">
          <h3 class="card-title">
            <el-icon><PieChart /></el-icon>
            用户分布
          </h3>
        </div>
        <div ref="userDistributionChartRef" class="chart-container"></div>
      </div>

      <div class="grid-item large">
        <div class="card-header">
          <h3 class="card-title">
            <el-icon><DocumentChecked /></el-icon>
            表格使用统计
          </h3>
          <el-button size="small" @click="loadSpreadsheetStats">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        <div class="spreadsheet-stats">
          <el-table :data="spreadsheetData" style="width: 100%" stripe>
            <el-table-column prop="name" label="表格名称" min-width="200" />
            <el-table-column prop="author" label="创建者" width="120" />
            <el-table-column prop="views" label="浏览数" width="100" sortable>
              <template #default="{ row }">
                <span class="stat-number">{{ row.views }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="downloads" label="下载数" width="100" sortable>
              <template #default="{ row }">
                <span class="stat-number">{{ row.downloads }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="createdAt" label="创建时间" width="180" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button size="small" type="primary" link>查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="grid-item">
        <div class="card-header">
          <h3 class="card-title">
            <el-icon><Warning /></el-icon>
            实时告警
          </h3>
          <el-badge :value="alerts.length" class="alarm-badge" />
        </div>
        <div class="alerts-list">
          <div v-for="alert in alerts" :key="alert.id" :class="['alert-item', 'alert-' + alert.level]">
            <div class="alert-icon">
              <el-icon v-if="alert.level === 'critical'"><CircleClose /></el-icon>
              <el-icon v-else-if="alert.level === 'warning'"><WarningFilled /></el-icon>
              <el-icon v-else><InfoFilled /></el-icon>
            </div>
            <div class="alert-content">
              <div class="alert-title">{{ alert.title }}</div>
              <div class="alert-time">{{ alert.time }}</div>
            </div>
          </div>
          <div v-if="alerts.length === 0" class="no-alerts">
            <el-icon><CircleCheck /></el-icon>
            <span>暂无告警</span>
          </div>
        </div>
      </div>

      <div class="grid-item large">
        <div class="card-header">
          <h3 class="card-title">
            <el-icon><FolderOpened /></el-icon>
            数据备份管理
          </h3>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Monitor, Refresh, User, Document, View, DataLine,
  TrendCharts, Cpu, Rank, PieChart, DocumentChecked,
  Warning, CircleClose, WarningFilled, InfoFilled, CircleCheck,
  FolderOpened, ChatDotRound
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../api'

const loading = ref(false)
const refreshInterval = ref(5000)
const timeRange = ref('24h')
const currentTime = ref('')

const stats = ref({
  activeUsers: 128,
  totalSpreadsheets: 256,
  todayVisits: 3847,
  tierListUsage: 892
})

const systemStats = ref({
  cpu: 45,
  memoryUsed: 8.5,
  memoryTotal: 16,
  memoryPercent: 53,
  diskUsed: 128,
  diskTotal: 512,
  diskPercent: 25,
  networkIn: 2.5,
  networkOut: 1.8
})

const featureRanking = ref([
  { name: '工作区表格', usage: 3847, percent: 100 },
  { name: '排行榜', usage: 2892, percent: 75 },
  { name: '社区', usage: 1923, percent: 50 },
  { name: '角色管理', usage: 1234, percent: 32 },
  { name: '素材管理', usage: 856, percent: 22 }
])

const alerts = ref([
  { id: 1, level: 'warning', title: 'CPU使用率偏高', time: '2分钟前' },
  { id: 2, level: 'info', title: '新用户注册', time: '5分钟前' }
])

const spreadsheetData = ref([
  { name: '椿伤害计算表', author: 'Admin', views: 1234, downloads: 567, createdAt: '2026-03-15 10:30:00' },
  { name: '今汐循环DPS', author: 'User1', views: 892, downloads: 345, createdAt: '2026-03-14 15:20:00' },
  { name: '长离配队分析', author: 'User2', views: 654, downloads: 234, createdAt: '2026-03-13 09:15:00' }
])

const maxBackupSize = ref(50)
const currentBackupSize = ref(0)
const backupLoading = ref({
  spreadsheet: false,
  tieba: false,
  ranking: false
})

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

const visitTrendChartRef = ref<HTMLElement>()
const userDistributionChartRef = ref<HTMLElement>()
let visitTrendChart: echarts.ECharts | null = null
let userDistributionChart: echarts.ECharts | null = null
let refreshTimer: any = null

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
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
      loadVisitTrend(),
      loadSystemStats(),
      loadSpreadsheetStats()
    ])
    ElMessage.success({ message: '数据已刷新', duration: 500 })
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error({ message: '刷新数据失败', duration: 500 })
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

async function loadVisitTrend() {
  if (!visitTrendChart) return
  
  const hours = []
  const data = []
  const now = Date.now()
  
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now - i * 60 * 60 * 1000)
    hours.push(`${time.getHours()}:00`)
    data.push(Math.floor(Math.random() * 200) + 100)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(26, 26, 46, 0.95)',
      borderColor: 'rgba(102, 126, 234, 0.5)',
      textStyle: { color: '#fff' }
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
      data: hours,
      axisLine: { lineStyle: { color: '#2a2a3a' } },
      axisLabel: { color: '#808090' }
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
      data: data,
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
      },
      emphasis: {
        itemStyle: {
          color: '#a855f7',
          borderColor: '#fff',
          borderWidth: 2
        }
      }
    }]
  }
  
  visitTrendChart.setOption(option)
}

async function loadSystemStats() {
  systemStats.value.cpu = Math.floor(Math.random() * 30) + 30
  systemStats.value.memoryPercent = Math.floor(Math.random() * 20) + 45
  systemStats.value.memoryUsed = (systemStats.value.memoryTotal * systemStats.value.memoryPercent / 100).toFixed(1) as any
  systemStats.value.networkIn = (Math.random() * 3 + 1).toFixed(1) as any
  systemStats.value.networkOut = (Math.random() * 2 + 0.5).toFixed(1) as any
}

async function loadSpreadsheetStats() {
  ElMessage.info({ message: '表格统计已更新', duration: 500 })
}

function initCharts() {
  nextTick(() => {
    if (visitTrendChartRef.value) {
      visitTrendChart = echarts.init(visitTrendChartRef.value)
      loadVisitTrend()
    }
    
    if (userDistributionChartRef.value) {
      userDistributionChart = echarts.init(userDistributionChartRef.value)
      
      const option = {
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(26, 26, 46, 0.95)',
          borderColor: 'rgba(102, 126, 234, 0.5)',
          textStyle: { color: '#fff' }
        },
        legend: {
          orient: 'vertical',
          right: '5%',
          top: 'center',
          textStyle: { color: '#808090' }
        },
        series: [{
          name: '用户分布',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['35%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#1a1a28',
            borderWidth: 2
          },
          label: {
            show: false
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
              color: '#fff'
            }
          },
          data: [
            { value: 1048, name: '工作区用户', itemStyle: { color: '#667eea' } },
            { value: 735, name: '排行榜用户', itemStyle: { color: '#a855f7' } },
            { value: 580, name: '社区用户', itemStyle: { color: '#22c55e' } },
            { value: 484, name: '素材用户', itemStyle: { color: '#f59e0b' } }
          ]
        }]
      }
      
      userDistributionChart.setOption(option)
    }
  })
}

function handleResize() {
  if (visitTrendChart) visitTrendChart.resize()
  if (userDistributionChart) userDistributionChart.resize()
}

onMounted(() => {
  initCharts()
  updateTime()
  setInterval(updateTime, 1000)
  updateRefreshInterval()
  loadBackupSettings()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (visitTrendChart) visitTrendChart.dispose()
  if (userDistributionChart) userDistributionChart.dispose()
  if (refreshTimer) clearInterval(refreshTimer)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  max-width: 1800px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
  border-radius: 16px;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.dashboard-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-icon {
  font-size: 32px;
}

.header-time {
  font-size: 14px;
  color: #808090;
  font-family: 'Consolas', monospace;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, currentColor, transparent);
  opacity: 0.5;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.stat-card-primary { color: #667eea; }
.stat-card-success { color: #22c55e; }
.stat-card-warning { color: #f59e0b; }
.stat-card-danger { color: #ef4444; }

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

.stat-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  margin-top: 8px;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 600;
}

.stat-trend.positive {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.stat-trend.negative {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
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

.network-bars {
  display: flex;
  gap: 8px;
  height: 20px;
}

.network-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.network-bar.incoming {
  background: linear-gradient(90deg, #22c55e, #16a34a);
}

.network-bar.outgoing {
  background: linear-gradient(90deg, #667eea, #4f46e5);
}

.feature-ranking {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.rank-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.rank-number {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.1);
  color: #808090;
}

.rank-1 {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: #1a1a28;
}

.rank-2 {
  background: linear-gradient(135deg, #9ca3af, #6b7280);
  color: #1a1a28;
}

.rank-3 {
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: #1a1a28;
}

.rank-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rank-name {
  font-size: 14px;
  color: #fff;
  font-weight: 500;
}

.rank-bar {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.rank-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #a855f7);
  border-radius: 3px;
  transition: width 0.5s ease;
}

.rank-value {
  font-size: 14px;
  color: #a5b4fc;
  font-weight: 600;
  min-width: 60px;
  text-align: right;
}

.spreadsheet-stats {
  max-height: 350px;
  overflow-y: auto;
}

.stat-number {
  font-weight: 600;
  color: #a5b4fc;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 320px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.alert-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.alert-item.alert-critical {
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.05);
}

.alert-item.alert-warning {
  border-color: rgba(245, 158, 11, 0.3);
  background: rgba(245, 158, 11, 0.05);
}

.alert-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.alert-item.alert-critical .alert-icon { color: #ef4444; }
.alert-item.alert-warning .alert-icon { color: #f59e0b; }
.alert-item.alert-info .alert-icon { color: #3b82f6; }

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 14px;
  color: #fff;
  font-weight: 500;
  margin-bottom: 4px;
}

.alert-time {
  font-size: 12px;
  color: #606070;
}

.no-alerts {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #606070;
  gap: 12px;
}

.no-alerts .el-icon {
  font-size: 48px;
  color: #22c55e;
}

.alarm-badge {
  margin-left: 8px;
}

:deep(.el-table) {
  background: transparent;
}

:deep(.el-table th),
:deep(.el-table tr) {
  background: transparent !important;
}

:deep(.el-table td),
:deep(.el-table th.is-leaf) {
  border-bottom: 1px solid #2a2a3a;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: rgba(255, 255, 255, 0.02);
}

:deep(.el-table__inner-wrapper::before) {
  display: none;
}

.backup-management {
  padding: 10px 0;
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

@media (max-width: 1400px) {
  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .grid-item.large {
    grid-column: span 2;
  }
}

@media (max-width: 900px) {
  .stats-overview {
    grid-template-columns: 1fr;
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .grid-item.large {
    grid-column: span 1;
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}
</style>
