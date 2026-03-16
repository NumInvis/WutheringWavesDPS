<template>
  <div class="data-observer">
    <header class="page-header">
      <div class="header-left">
        <h1><el-icon><DataLine /></el-icon> 数据观察</h1>
        <span class="update-time">{{ currentTime }}</span>
      </div>
      <div class="header-right">
        <el-button type="default" size="small" @click="showSettingsDialog = true">
          <el-icon><Setting /></el-icon> 设置
        </el-button>
        <el-button type="primary" @click="downloadData" :loading="downloadLoading" :disabled="!userStore.isAuthenticated" size="small">
          <el-icon><Download /></el-icon> 下载贴吧json
        </el-button>
        <el-button v-if="userStore.user?.is_admin" type="success" @click="crawlData" :loading="crawlLoading" size="small">
          <el-icon><Refresh /></el-icon> 爬取
        </el-button>
      </div>
    </header>

    <div class="stats-row">
      <div class="stat-item"><el-icon><Document /></el-icon><span class="v">{{ totalPosts }}</span><span class="l">本周发帖</span></div>
      <div class="stat-item"><el-icon><TrendCharts /></el-icon><span class="v">{{ avgPosts }}</span><span class="l">日均</span></div>
      <div class="stat-item"><el-icon><Trophy /></el-icon><span class="v">{{ topTieba.name || '-' }}</span><span class="l">最活跃</span></div>
      <div class="stat-item"><el-icon><Monitor /></el-icon><span class="v">{{ monitoredForums.length }}</span><span class="l">监控数</span></div>
      <div class="stat-item" :class="schedulerStatus.running ? 'running' : 'stopped'">
        <el-icon><Timer /></el-icon><span class="v">{{ schedulerStatus.running ? '运行中' : '已停止' }}</span><span class="l">调度器</span>
      </div>
    </div>

    <div class="content-grid">
      <div class="left-column">
        <div class="panel chart-panel">
          <div class="panel-header">
            <h3><el-icon><DataLine /></el-icon> 发帖量堆叠统计</h3>
            <el-radio-group v-model="chartDays" size="small" @change="loadStackedData">
              <el-radio-button :value="7">7天</el-radio-button>
              <el-radio-button :value="14">14天</el-radio-button>
              <el-radio-button :value="30">30天</el-radio-button>
            </el-radio-group>
          </div>
          <div ref="stackedChartRef" class="chart-area stacked-chart"></div>
        </div>

        <div class="panel daily-panel">
          <div class="panel-header">
            <h3><el-icon><Sunny /></el-icon> 今日热帖 TOP 3</h3>
            <el-tag type="danger" size="small">实时</el-tag>
          </div>
          <div class="daily-grid">
            <div v-for="(post, index) in dailyHotPosts" :key="post.post_id" class="daily-card" :class="'c'+(index+1)">
              <span class="badge">{{ index+1 }}</span>
              <el-tag size="small" :color="post.color" effect="dark">{{ post.tieba_name }}</el-tag>
              <h4>{{ post.title }}</h4>
              <div class="meta">
                <span class="hot"><el-icon><Sunny /></el-icon>{{ post.hot_index }}</span>
              </div>
              <a :href="post.post_url" target="_blank" class="link">详情</a>
            </div>
            <el-empty v-if="dailyHotPosts.length === 0" description="暂无今日热帖" :image-size="40" />
          </div>
        </div>
      </div>

      <div class="right-column">
        <div class="panel rank-panel">
          <div class="panel-header"><h3><el-icon><Histogram /></el-icon> 活跃度排行</h3></div>
          <div ref="barChartRef" class="chart-area bar-chart"></div>
        </div>

        <div class="panel hot-panel">
          <div class="panel-header">
            <h3><el-icon><Sunny /></el-icon> 每周热帖 TOP 10</h3>
          </div>
          <div class="hot-list">
            <div v-for="(post, index) in weeklyHotPosts" :key="post.post_id" class="hot-item">
              <span class="rank" :class="'r'+(index+1)">{{ index+1 }}</span>
              <el-tag size="small" :color="post.color" effect="dark">{{ post.tieba_name }}</el-tag>
              <span class="title">{{ post.title }}</span>
              <span class="meta hot"><el-icon><Sunny /></el-icon>{{ post.hot_index }}</span>
              <a :href="post.post_url" target="_blank" class="link">查看</a>
            </div>
            <el-empty v-if="weeklyHotPosts.length === 0" description="暂无热帖" :image-size="40" />
          </div>
        </div>
      </div>
    </div>

    <div class="section-divider">
      <h2><el-icon><Iphone /></el-icon> iOS畅销榜排行</h2>
      <div class="header-controls">
        <span class="update-time">更新: {{ appRankingLastUpdated || '-' }}</span>
        <el-button v-if="userStore.user?.is_admin" type="primary" size="small" @click="showAddGameDialog = true">
          <el-icon><Plus /></el-icon> 添加游戏
        </el-button>
      </div>
    </div>

    <div class="app-ranking-section">
      <div class="app-ranking-compact">
        <div class="ranking-table">
          <div class="table-header">
            <div class="col-game">游戏</div>
            <div class="col-country">🇨🇳 中国</div>
            <div class="col-country">🇯🇵 日本</div>
            <div class="col-country">🇺🇸 美国</div>
            <div class="col-country">🇰🇷 韩国</div>
            <div v-if="userStore.user?.is_admin" class="col-actions">操作</div>
          </div>
          <div v-for="app in appRankingData" :key="app.id" class="table-row">
            <div class="col-game">
              <span class="game-name">{{ app.name_cn }}</span>
            </div>
            <div class="col-country">
              <span class="rank-badge" :class="getAppRankClass(app.rankings['cn']?.rank)">
                {{ app.rankings['cn']?.rank > 100 ? '>100' : app.rankings['cn']?.rank || '-' }}
              </span>
            </div>
            <div class="col-country">
              <span class="rank-badge" :class="getAppRankClass(app.rankings['jp']?.rank)">
                {{ app.rankings['jp']?.rank > 100 ? '>100' : app.rankings['jp']?.rank || '-' }}
              </span>
            </div>
            <div class="col-country">
              <span class="rank-badge" :class="getAppRankClass(app.rankings['us']?.rank)">
                {{ app.rankings['us']?.rank > 100 ? '>100' : app.rankings['us']?.rank || '-' }}
              </span>
            </div>
            <div class="col-country">
              <span class="rank-badge" :class="getAppRankClass(app.rankings['kr']?.rank)">
                {{ app.rankings['kr']?.rank > 100 ? '>100' : app.rankings['kr']?.rank || '-' }}
              </span>
            </div>
            <div v-if="userStore.user?.is_admin" class="col-actions">
              <el-button type="danger" size="small" link @click="deleteGame(app.id, app.name_cn)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          <el-empty v-if="appRankingData.length === 0" description="暂无排名数据" :image-size="60" />
        </div>
      </div>

      <div class="app-ranking-chart">
        <div class="panel-header">
          <h3><el-icon><TrendCharts /></el-icon> 排名趋势</h3>
          <div class="chart-controls">
            <el-radio-group v-model="chartTimeRange" size="small" @change="loadRankingHistory">
              <el-radio-button value="24h">24h</el-radio-button>
              <el-radio-button value="30d">30天</el-radio-button>
              <el-radio-button value="365d">365天</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div class="chart-selectors">
          <el-select v-model="selectedGames" multiple placeholder="选择游戏" size="small" style="width: 48%;" @change="updateRankingChart">
            <el-option v-for="app in appRankingData" :key="app.id" :label="app.name_cn" :value="app.id" />
          </el-select>
          <el-select v-model="selectedCountries" multiple placeholder="选择Country" size="small" style="width: 48%;" @change="updateRankingChart">
            <el-option label="🇨🇳 中国" value="cn" />
            <el-option label="🇯🇵 日本" value="jp" />
            <el-option label="🇺🇸 美国" value="us" />
            <el-option label="🇰🇷 韩国" value="kr" />
          </el-select>
        </div>
        <div ref="rankingChartRef" class="ranking-chart-area"></div>
      </div>
    </div>

    <el-dialog v-model="showAddGameDialog" title="添加游戏" width="500px">
      <el-input v-model="searchGameQuery" placeholder="搜索游戏（输入iTunes应用ID或名称）" clearable @keyup.enter="searchGames">
        <template #append>
          <el-button @click="searchGames">搜索</el-button>
        </template>
      </el-input>
      <div v-if="searchGameResults.length > 0" class="search-results" style="margin-top: 12px;">
        <div v-for="result in searchGameResults" :key="result.trackId" class="search-result-item" @click="addGame(result)">
          <img :src="result.artworkUrl60" class="app-icon" />
          <div class="app-info">
            <div class="app-name">{{ result.trackName }}</div>
            <div class="app-id">ID: {{ result.trackId }}</div>
          </div>
          <el-icon class="add-icon"><Plus /></el-icon>
        </div>
      </div>
      <el-empty v-else-if="searchGameQuery" description="未找到相关游戏" :image-size="40" style="margin-top: 12px;" />
      <template #footer>
        <el-button @click="showAddGameDialog = false">取消</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showSettingsDialog" title="界面自定义" width="500px">
      <el-form label-position="top">
        <el-divider content-position="left">基础效果</el-divider>
        <el-form-item label="背景透明度 (0-1)">
          <el-slider v-model="localSettings.bgOpacity" :min="0" :max="1" :step="0.05" show-input @change="applySettings" />
        </el-form-item>
        <el-form-item label="面板透明度 (0-1)">
          <el-slider v-model="localSettings.panelOpacity" :min="0" :max="1" :step="0.05" show-input @change="applySettings" />
        </el-form-item>
        <el-form-item label="模糊程度 (0-20)">
          <el-slider v-model="localSettings.blurAmount" :min="0" :max="20" :step="1" show-input @change="applySettings" />
        </el-form-item>
        <el-form-item label="圆角大小 (0-20)">
          <el-slider v-model="localSettings.borderRadius" :min="0" :max="20" :step="1" show-input @change="applySettings" />
        </el-form-item>
        <el-form-item label="阴影强度 (0-0.5)">
          <el-slider v-model="localSettings.shadowIntensity" :min="0" :max="0.5" :step="0.01" show-input @change="applySettings" />
        </el-form-item>
        
        <el-divider content-position="left">尺寸调整</el-divider>
        <el-form-item label="字体缩放 (0.8-1.5)">
          <el-slider v-model="localSettings.fontSizeScale" :min="0.8" :max="1.5" :step="0.05" show-input @change="applySettings" />
        </el-form-item>
        <el-form-item label="图表高度缩放 (0.7-1.5)">
          <el-slider v-model="localSettings.chartHeightScale" :min="0.7" :max="1.5" :step="0.05" show-input @change="applySettings" />
        </el-form-item>
        
        <el-divider content-position="left">颜色主题</el-divider>
        <el-form-item label="主色调">
          <el-color-picker v-model="localSettings.primaryColor" @change="applySettings" />
        </el-form-item>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
          <el-form-item label="颜色1">
            <el-color-picker v-model="localSettings.accentColor1" @change="applySettings" />
          </el-form-item>
          <el-form-item label="颜色2">
            <el-color-picker v-model="localSettings.accentColor2" @change="applySettings" />
          </el-form-item>
          <el-form-item label="颜色3">
            <el-color-picker v-model="localSettings.accentColor3" @change="applySettings" />
          </el-form-item>
          <el-form-item label="颜色4">
            <el-color-picker v-model="localSettings.accentColor4" @change="applySettings" />
          </el-form-item>
          <el-form-item label="颜色5">
            <el-color-picker v-model="localSettings.accentColor5" @change="applySettings" />
          </el-form-item>
          <el-form-item label="颜色6">
            <el-color-picker v-model="localSettings.accentColor6" @change="applySettings" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="resetSettings">重置默认</el-button>
        <el-button type="primary" @click="showSettingsDialog = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  DataLine, Download, Refresh, Document, Monitor,
  TrendCharts, Sunny, Timer, Trophy, Iphone, Plus, Setting, Delete
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const Histogram = TrendCharts

const monitoredForums = ref<string[]>([])
const forumColors = ref<Record<string, string>>({})
const weeklyHotPosts = ref<any[]>([])
const dailyHotPosts = ref<any[]>([])
const leaderboard = ref<any[]>([])
const stackedData = ref<any[]>([])
const weeklyStats = ref<any>({})
const currentTime = ref('')
const chartDays = ref(7)
const downloadLoading = ref(false)
const crawlLoading = ref(false)
const schedulerStatus = ref<{running: boolean, has_aiotieba: boolean}>({running: false, has_aiotieba: false})

const stackedChartRef = ref<HTMLElement>()
const barChartRef = ref<HTMLElement>()
let stackedChart: echarts.ECharts | null = null
let barChart: echarts.ECharts | null = null

const appRankingData = ref<any[]>([])
const appRankingLastUpdated = ref('')

const rankingChartRef = ref<HTMLElement>()
let rankingChart: echarts.ECharts | null = null

const chartTimeRange = ref('24h')
const selectedGames = ref<number[]>([])
const selectedCountries = ref<string[]>(['cn'])
const rankingHistoryData = ref<any[]>([])

const showAddGameDialog = ref(false)
const searchGameQuery = ref('')
const searchGameResults = ref<any[]>([])

const showSettingsDialog = ref(false)
const defaultSettings = {
  bgOpacity: 1,
  panelOpacity: 0.92,
  blurAmount: 0,
  primaryColor: '#6366f1',
  borderRadius: 8,
  shadowIntensity: 0.15,
  fontSizeScale: 1,
  chartHeightScale: 1,
  accentColor1: '#6366f1',
  accentColor2: '#ec4899',
  accentColor3: '#10b981',
  accentColor4: '#f59e0b',
  accentColor5: '#8b5cf6',
  accentColor6: '#06b6d4'
}
const localSettings = ref({ ...defaultSettings })

const totalPosts = computed(() => {
  let total = 0
  for (const forum of monitoredForums.value) {
    total += weeklyStats.value[forum]?.total_posts || 0
  }
  return total
})

const avgPosts = computed(() => Math.round(totalPosts.value / 7))

const topTieba = computed(() => {
  if (leaderboard.value.length === 0) return { name: '-', posts: 0 }
  return { name: leaderboard.value[0].tieba_name, posts: leaderboard.value[0].total_posts }
})

function updateTime() {
  const now = new Date()
  const beijingTime = new Date(now.getTime() + 8 * 60 * 60 * 1000)
  currentTime.value = beijingTime.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function getAppRankClass(rank: number) {
  if (!rank || rank > 100) return 'rank-low'
  if (rank <= 10) return 'rank-high'
  if (rank <= 50) return 'rank-mid'
  return 'rank-low'
}

async function loadForums() {
  try {
    const data = await api.get('/tieba/forums')
    monitoredForums.value = data.forums || []
    forumColors.value = data.colors || {}
  } catch (error) { console.error('加载贴吧列表失败:', error) }
}

async function loadWeeklyStats() {
  try {
    const data = await api.get('/tieba/stats/weekly')
    weeklyStats.value = data.stats || {}
  } catch (error) { console.error('加载周统计失败:', error) }
}

async function loadStackedData() {
  try {
    const data = await api.get(`/tieba/stats/stacked?days=${chartDays.value}`)
    stackedData.value = data.data || []
    updateStackedChart()
  } catch (error) { console.error('加载堆叠数据失败:', error) }
}

async function loadWeeklyHotPosts() {
  try {
    const data = await api.get('/tieba/hot/weekly?limit=10')
    weeklyHotPosts.value = data.posts || []
  } catch (error) { console.error('加载周热帖失败:', error) }
}

async function loadDailyHotPosts() {
  try {
    const data = await api.get('/tieba/hot/daily?limit=3')
    dailyHotPosts.value = data.posts || []
  } catch (error) { console.error('加载日热帖失败:', error) }
}

async function loadLeaderboard() {
  try {
    const data = await api.get('/tieba/leaderboard?days=7')
    leaderboard.value = data.leaderboard || []
    updateBarChart()
  } catch (error) { console.error('加载排行榜失败:', error) }
}

async function loadSchedulerStatus() {
  try {
    const data = await api.get('/tieba/crawl-status')
    schedulerStatus.value = data
  } catch (error) { console.error('加载调度器状态失败:', error) }
}

async function loadAppRanking() {
  try {
    const data = await api.get('/ranking/current')
    appRankingData.value = data.apps || []
    appRankingLastUpdated.value = data.last_updated || ''
    if (appRankingData.value.length > 0 && selectedGames.value.length === 0) {
      selectedGames.value = appRankingData.value.map(app => app.id)
    }
  } catch (error) { console.error('加载畅销榜失败:', error) }
}

async function downloadData() {
  if (!userStore.isAuthenticated) { ElMessage.warning('请先登录'); return }
  downloadLoading.value = true
  try {
    const response = await fetch('/WutheringWavesDPS/api/tieba/download', { headers: { 'Authorization': `Bearer ${userStore.token}` } })
    if (!response.ok) { const error = await response.json(); throw new Error(error.detail || '下载失败') }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `tieba_data_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a); a.click()
    window.URL.revokeObjectURL(url); document.body.removeChild(a)
    ElMessage.success('下载成功')
  } catch (error: any) { ElMessage.error(error.message || '下载失败') }
  finally { downloadLoading.value = false }
}

async function crawlData() {
  crawlLoading.value = true
  try {
    await api.post('/tieba/crawl')
    ElMessage.success('爬取任务已启动')
    setTimeout(() => loadAllData(), 5000)
  } catch (error: any) { ElMessage.error(error.response?.data?.detail || '爬取失败') }
  finally { crawlLoading.value = false }
}

function initCharts() {
  nextTick(() => {
    if (stackedChartRef.value) stackedChart = echarts.init(stackedChartRef.value)
    if (barChartRef.value) barChart = echarts.init(barChartRef.value)
  })
}

function updateStackedChart() {
  if (!stackedChart || !stackedData.value.length) return
  const dates = stackedData.value.map((d: any) => d.label)
  const series = monitoredForums.value.map(tieba => ({
    name: tieba, type: 'bar', stack: 'total', emphasis: { focus: 'series' },
    data: stackedData.value.map((d: any) => d[tieba] || 0),
    itemStyle: { 
      color: forumColors.value[tieba] || '#6366f1',
      borderRadius: [2, 2, 0, 0]
    },
    barMaxWidth: 40
  }))
  stackedChart.setOption({
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'shadow' }, 
      backgroundColor: 'rgba(15, 23, 42, 0.98)', 
      borderColor: 'rgba(99, 102, 241, 0.35)', 
      borderWidth: 1,
      textStyle: { color: '#e2e8f0', fontSize: 11 },
      padding: [8, 12]
    },
    legend: { 
      type: 'scroll', 
      bottom: 2, 
      textStyle: { color: '#94a3b8', fontSize: 10 }, 
      pageIconColor: '#6366f1', 
      itemWidth: 10, 
      itemHeight: 8,
      pageIconSize: 10
    },
    grid: { left: '3%', right: '3%', top: '3%', bottom: '18%', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: dates, 
      axisLine: { lineStyle: { color: '#334155' } }, 
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      axisTick: { show: false }
    },
    yAxis: { 
      type: 'value', 
      axisLine: { show: false }, 
      axisLabel: { color: '#94a3b8', fontSize: 10 }, 
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }
    },
    series
  })
}

function updateBarChart() {
  if (!barChart || !leaderboard.value.length) return
  const top10 = leaderboard.value.slice(0, 10).reverse()
  barChart.setOption({
    tooltip: { 
      trigger: 'axis', 
      backgroundColor: 'rgba(15, 23, 42, 0.98)', 
      borderColor: 'rgba(99, 102, 241, 0.35)', 
      borderWidth: 1,
      textStyle: { color: '#e2e8f0', fontSize: 11 },
      padding: [8, 12],
      axisPointer: { type: 'shadow' } 
    },
    grid: { left: '3%', right: '4%', top: '4%', bottom: '4%', containLabel: true },
    xAxis: { 
      type: 'value', 
      axisLine: { show: false }, 
      axisLabel: { color: '#94a3b8', fontSize: 10 }, 
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } } 
    },
    yAxis: { 
      type: 'category', 
      data: top10.map((d: any) => d.tieba_name), 
      axisLine: { show: false }, 
      axisLabel: { color: '#e2e8f0', fontSize: 10 },
      axisTick: { show: false }
    },
    series: [{ 
      type: 'bar', 
      data: top10.map((item: any) => ({ 
        value: item.total_posts, 
        itemStyle: { 
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: item.color }, { offset: 1, color: item.color + '99' }]), 
          borderRadius: [0, 3, 3, 0] 
        } 
      })), 
      barWidth: '50%' 
    }]
  })
}

async function loadRankingHistory() {
  try {
    const data = await api.get(`/ranking/history?range=${chartTimeRange.value}`)
    rankingHistoryData.value = data.records || []
    console.log('Ranking history data loaded:', rankingHistoryData.value.length, 'records')
    await nextTick()
    updateRankingChart()
  } catch (error) { console.error('加载排名历史失败:', error) }
}

function updateRankingChart() {
  console.log('updateRankingChart called')
  console.log('rankingChart:', rankingChart)
  console.log('rankingHistoryData.length:', rankingHistoryData.value.length)
  console.log('selectedGames:', selectedGames.value)
  console.log('selectedCountries:', selectedCountries.value)
  console.log('appRankingData:', appRankingData.value)
  
  if (!rankingChart) {
    console.log('rankingChart not initialized, trying to init...')
    initRankingChart()
    setTimeout(() => updateRankingChart(), 100)
    return
  }
  
  if (rankingHistoryData.value.length === 0) {
    console.log('No ranking history data')
    rankingChart.setOption({
      title: {
        text: '暂无历史数据',
        left: 'center',
        top: 'center',
        textStyle: { color: '#94a3b8', fontSize: 14 }
      }
    })
    return
  }
  
  const gamesToShow = selectedGames.value.length > 0 
    ? appRankingData.value.filter(app => selectedGames.value.includes(app.id))
    : appRankingData.value
  
  console.log('gamesToShow:', gamesToShow)
  
  if (gamesToShow.length === 0) {
    console.log('No games to show')
    return
  }
  
  const countriesToShow = selectedCountries.value.length > 0 
    ? selectedCountries.value 
    : ['cn']
  
  console.log('countriesToShow:', countriesToShow)
  
  const dates = [...new Set(rankingHistoryData.value.map((r: any) => {
    const d = new Date(r.recorded_at)
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  }))].sort()
  
  console.log('dates:', dates)
  
  const series: any[] = []
  const colors = ['#6366f1', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4']
  
  gamesToShow.forEach((app, appIndex) => {
    countriesToShow.forEach((country, countryIndex) => {
      const colorIndex = (appIndex * countriesToShow.length + countryIndex) % colors.length
      const data = dates.map(date => {
        const record = rankingHistoryData.value.find((r: any) => {
          const recordDate = new Date(r.recorded_at)
          const recordDateStr = recordDate.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
          return r.app_id === app.id && 
                 r.country === country &&
                 recordDateStr === date
        })
        return record ? record.rank : null
      })
      
      console.log(`Data for ${app.name_cn} (${country}):`, data)
      
      if (data.some((d: any) => d !== null)) {
        series.push({
          name: `${app.name_cn} (${country.toUpperCase()})`,
          type: 'line',
          data,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2, color: colors[colorIndex] },
          itemStyle: { color: colors[colorIndex] },
          emphasis: { focus: 'series' }
        })
      }
    })
  })
  
  console.log('Final series:', series)
  
  rankingChart.setOption({
    title: { show: false },
    tooltip: { 
      trigger: 'axis', 
      backgroundColor: 'rgba(15, 23, 42, 0.98)', 
      borderColor: 'rgba(99, 102, 241, 0.35)', 
      borderWidth: 1,
      textStyle: { color: '#e2e8f0', fontSize: 11 },
      padding: [8, 12],
      formatter: (params: any) => {
        let result = params[0].axisValue + '<br/>'
        params.forEach((param: any) => {
          if (param.data !== null) {
            result += `${param.marker} ${param.seriesName}: #${param.data}<br/>`
          }
        })
        return result
      }
    },
    legend: { 
      type: 'scroll', 
      top: 2, 
      textStyle: { color: '#94a3b8', fontSize: 10 }, 
      pageIconColor: '#6366f1', 
      itemWidth: 10, 
      itemHeight: 8,
      pageIconSize: 10
    },
    grid: { left: '3%', right: '3%', top: '15%', bottom: '5%', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: dates, 
      axisLine: { lineStyle: { color: '#334155' } }, 
      axisLabel: { color: '#94a3b8', fontSize: 9, rotate: 30 },
      axisTick: { show: false }
    },
    yAxis: { 
      type: 'value', 
      axisLine: { show: false }, 
      axisLabel: { color: '#94a3b8', fontSize: 10 }, 
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      min: 1,
      max: 100,
      inverse: true
    },
    series
  })
}

async function searchGames() {
  if (!searchGameQuery.value) return
  try {
    const data = await api.get(`/ranking/search?query=${encodeURIComponent(searchGameQuery.value)}`)
    searchGameResults.value = data.results || []
  } catch (error) { 
    console.error('搜索游戏失败:', error) 
    ElMessage.error('搜索失败')
  }
}

async function deleteGame(appId: number, appName: string) {
  try {
    await ElMessageBox.confirm(`确定要删除游戏 "${appName}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/ranking/apps/${appId}`)
    ElMessage.success('删除成功')
    await loadAppRanking()
    await loadRankingHistory()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

async function addGame(game: any) {
  try {
    await api.post(`/ranking/apps?itunes_id=${game.trackId}&name_cn=${encodeURIComponent(game.trackName)}&name_en=${encodeURIComponent(game.trackName)}`)
    ElMessage.success('添加成功')
    showAddGameDialog.value = false
    searchGameQuery.value = ''
    searchGameResults.value = []
    await loadAppRanking()
  } catch (error: any) { 
    ElMessage.error(error.response?.data?.detail || '添加失败')
  }
}

function initRankingChart() {
  nextTick(() => {
    if (rankingChartRef.value) rankingChart = echarts.init(rankingChartRef.value)
  })
}

function loadSettings() {
  const saved = localStorage.getItem('dataObserverSettings')
  if (saved) {
    try {
      localSettings.value = JSON.parse(saved)
      applySettings()
    } catch (e) {}
  }
}

function applySettings() {
  localStorage.setItem('dataObserverSettings', JSON.stringify(localSettings.value))
  
  const root = document.documentElement
  const observer = document.querySelector('.data-observer') as HTMLElement
  
  root.style.setProperty('--bg-opacity', localSettings.value.bgOpacity)
  root.style.setProperty('--panel-opacity', localSettings.value.panelOpacity)
  root.style.setProperty('--blur-amount', `${localSettings.value.blurAmount}px`)
  root.style.setProperty('--border-radius', `${localSettings.value.borderRadius}px`)
  root.style.setProperty('--shadow-intensity', localSettings.value.shadowIntensity)
  root.style.setProperty('--font-size-scale', localSettings.value.fontSizeScale)
  root.style.setProperty('--chart-height-scale', localSettings.value.chartHeightScale)
  root.style.setProperty('--primary-color', localSettings.value.primaryColor)
  root.style.setProperty('--accent-color-1', localSettings.value.accentColor1)
  root.style.setProperty('--accent-color-2', localSettings.value.accentColor2)
  root.style.setProperty('--accent-color-3', localSettings.value.accentColor3)
  root.style.setProperty('--accent-color-4', localSettings.value.accentColor4)
  root.style.setProperty('--accent-color-5', localSettings.value.accentColor5)
  root.style.setProperty('--accent-color-6', localSettings.value.accentColor6)
  
  if (observer) {
    observer.style.background = `linear-gradient(180deg, rgba(13, 13, 24, ${localSettings.value.bgOpacity}) 0%, rgba(15, 18, 32, ${localSettings.value.bgOpacity}) 100%)`
    observer.style.backdropFilter = `blur(${localSettings.value.blurAmount}px)`
  }
  
  updateStackedChart()
  updateBarChart()
  updateRankingChart()
}

function resetSettings() {
  localSettings.value = { ...defaultSettings }
  applySettings()
}

function handleResize() { 
  stackedChart?.resize(); 
  barChart?.resize();
  rankingChart?.resize();
}

async function loadAllData() {
  await Promise.all([loadForums(), loadWeeklyStats(), loadStackedData(), loadWeeklyHotPosts(), loadDailyHotPosts(), loadLeaderboard(), loadSchedulerStatus(), loadAppRanking()])
  await loadRankingHistory()
}

onMounted(() => { 
  updateTime(); 
  setInterval(updateTime, 1000); 
  initCharts(); 
  initRankingChart();
  loadSettings();
  loadAllData(); 
  window.addEventListener('resize', handleResize) 
})
onUnmounted(() => { 
  stackedChart?.dispose(); 
  barChart?.dispose(); 
  rankingChart?.dispose();
  window.removeEventListener('resize', handleResize) 
})
</script>

<style scoped>
:root {
  --bg-opacity: 1;
  --panel-opacity: 0.92;
  --blur-amount: 0px;
  --border-radius: 8px;
  --shadow-intensity: 0.15;
  --font-size-scale: 1;
  --chart-height-scale: 1;
  --primary-color: #6366f1;
  --accent-color-1: #6366f1;
  --accent-color-2: #ec4899;
  --accent-color-3: #10b981;
  --accent-color-4: #f59e0b;
  --accent-color-5: #8b5cf6;
  --accent-color-6: #06b6d4;
}

.data-observer { min-height: 100vh; padding: 12px 16px; }

.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 10px 14px; background: rgba(22, 24, 38, var(--panel-opacity)); border-radius: var(--border-radius); border: 1px solid rgba(99, 102, 241, 0.2); box-shadow: 0 2px 8px rgba(0, 0, 0, calc(0.2 * var(--shadow-intensity))); }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { display: flex; align-items: center; gap: 6px; font-size: calc(18px * var(--font-size-scale)); font-weight: 600; color: #f8fafc; margin: 0; letter-spacing: 0.3px; }
.header-left h1 .el-icon { color: var(--primary-color); font-size: calc(20px * var(--font-size-scale)); }
.update-time { font-size: calc(12px * var(--font-size-scale)); color: #94a3b8; font-family: 'SF Mono', 'Monaco', monospace; }
.header-right { display: flex; gap: 6px; }

.stats-row { display: flex; gap: 8px; margin-bottom: 10px; }
.stat-item { display: flex; align-items: center; gap: 6px; padding: 8px 12px; background: rgba(22, 24, 38, var(--panel-opacity)); border-radius: calc(var(--border-radius) - 2px); border: 1px solid rgba(99, 102, 241, 0.15); flex: 1; transition: all 0.2s ease; }
.stat-item:hover { border-color: rgba(99, 102, 241, 0.35); transform: translateY(-1px); }
.stat-item .el-icon { font-size: calc(16px * var(--font-size-scale)); color: var(--primary-color); }
.stat-item .v { font-size: calc(17px * var(--font-size-scale)); font-weight: 700; color: #f8fafc; font-family: 'SF Mono', 'Monaco', monospace; }
.stat-item .l { font-size: calc(11px * var(--font-size-scale)); color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
.stat-item.running .el-icon { color: #22c55e; }
.stat-item.stopped .el-icon { color: #ef4444; }

.content-grid { display: grid; grid-template-columns: 1.3fr 1fr; gap: 10px; }

.left-column, .right-column { display: flex; flex-direction: column; gap: 10px; }

.panel { background: rgba(22, 24, 38, var(--panel-opacity)); border-radius: var(--border-radius); border: 1px solid rgba(99, 102, 241, 0.15); overflow: hidden; box-shadow: 0 2px 12px rgba(0, 0, 0, calc(0.15 * var(--shadow-intensity))); }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; border-bottom: 1px solid rgba(99, 102, 241, 0.1); background: linear-gradient(180deg, rgba(99, 102, 241, 0.08) 0%, transparent 100%); }
.panel-header h3 { display: flex; align-items: center; gap: 5px; font-size: calc(13px * var(--font-size-scale)); font-weight: 600; color: #e2e8f0; margin: 0; letter-spacing: 0.2px; }
.panel-header h3 .el-icon { color: var(--primary-color); font-size: calc(14px * var(--font-size-scale)); }

.chart-area { padding: 8px; }
.stacked-chart { height: calc(210px * var(--chart-height-scale)); }
.bar-chart { height: calc(190px * var(--chart-height-scale)); }

.hot-list { padding: 8px 10px; display: flex; flex-direction: column; gap: 4px; max-height: 200px; overflow-y: auto; }
.hot-list::-webkit-scrollbar { width: 4px; }
.hot-list::-webkit-scrollbar-track { background: rgba(30, 30, 50, 0.5); border-radius: 2px; }
.hot-list::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.4); border-radius: 2px; }
.hot-item { display: flex; align-items: center; gap: 6px; padding: 6px 8px; background: rgba(15, 23, 42, 0.7); border-radius: 5px; font-size: 12px; transition: all 0.15s ease; }
.hot-item:hover { background: rgba(99, 102, 241, 0.12); transform: translateX(2px); }
.hot-item .rank { width: 20px; height: 20px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #f8fafc; background: #334155; flex-shrink: 0; font-family: 'SF Mono', 'Monaco', monospace; }
.hot-item .rank.r1 { background: linear-gradient(135deg, #fbbf24, #f59e0b); box-shadow: 0 0 8px rgba(251, 191, 36, 0.3); }
.hot-item .rank.r2 { background: linear-gradient(135deg, #cbd5e1, #94a3b8); box-shadow: 0 0 8px rgba(148, 163, 184, 0.25); }
.hot-item .rank.r3 { background: linear-gradient(135deg, #fb923c, #ea580c); box-shadow: 0 0 8px rgba(251, 146, 60, 0.25); }
.hot-item .title { flex: 1; color: #e2e8f0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; font-weight: 400; }
.hot-item .meta { color: #94a3b8; display: flex; align-items: center; gap: 2px; flex-shrink: 0; font-family: 'SF Mono', 'Monaco', monospace; font-size: 11px; }
.hot-item .meta.hot { color: #f97316; }
.hot-item .link { color: #6366f1; text-decoration: none; flex-shrink: 0; font-weight: 500; font-size: 11px; }

.daily-grid { padding: 10px 10px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.daily-card { position: relative; padding: 10px; background: rgba(15, 23, 42, 0.75); border-radius: 6px; border: 1px solid rgba(99, 102, 241, 0.12); transition: all 0.2s ease; }
.daily-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); }
.daily-card.c1 { border-color: rgba(251, 191, 36, 0.35); background: linear-gradient(180deg, rgba(251, 191, 36, 0.08) 0%, rgba(15, 23, 42, 0.75) 100%); }
.daily-card.c2 { border-color: rgba(148, 163, 184, 0.35); background: linear-gradient(180deg, rgba(148, 163, 184, 0.06) 0%, rgba(15, 23, 42, 0.75) 100%); }
.daily-card.c3 { border-color: rgba(251, 146, 60, 0.35); background: linear-gradient(180deg, rgba(251, 146, 60, 0.06) 0%, rgba(15, 23, 42, 0.75) 100%); }
.daily-card .badge { position: absolute; top: -6px; left: 10px; padding: 1px 7px; border-radius: 6px; font-size: 10px; font-weight: 700; color: #0f172a; letter-spacing: 0.3px; font-family: 'SF Mono', 'Monaco', monospace; }
.daily-card.c1 .badge { background: linear-gradient(135deg, #fbbf24, #f59e0b); box-shadow: 0 2px 6px rgba(251, 191, 36, 0.4); }
.daily-card.c2 .badge { background: linear-gradient(135deg, #cbd5e1, #94a3b8); box-shadow: 0 2px 6px rgba(148, 163, 184, 0.35); }
.daily-card.c3 .badge { background: linear-gradient(135deg, #fb923c, #ea580c); box-shadow: 0 2px 6px rgba(251, 146, 60, 0.35); }
.daily-card h4 { font-size: 12px; font-weight: 500; color: #e2e8f0; margin: 6px 0 4px; line-height: 1.35; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.daily-card .meta { display: flex; gap: 8px; margin-bottom: 4px; }
.daily-card .meta span { display: flex; align-items: center; gap: 2px; font-size: 11px; color: #94a3b8; font-family: 'SF Mono', 'Monaco', monospace; }
.daily-card .meta span.hot { color: #f97316; }
.daily-card .link { font-size: 11px; color: #6366f1; text-decoration: none; font-weight: 500; }

.section-divider { display: flex; justify-content: space-between; align-items: center; margin: 14px 0 10px; padding: 10px 14px; background: rgba(22, 24, 38, 0.9); border-radius: 8px; border: 1px solid rgba(99, 102, 241, 0.2); box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); }
.section-divider h2 { display: flex; align-items: center; gap: 6px; font-size: 16px; font-weight: 600; color: #f8fafc; margin: 0; letter-spacing: 0.3px; }
.section-divider h2 .el-icon { color: #6366f1; }
.header-controls { display: flex; align-items: center; gap: 10px; }

.app-ranking-section { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.app-ranking-compact { margin-bottom: 0; max-width: 100%; }
.app-ranking-chart { background: rgba(22, 24, 38, 0.92); border-radius: 8px; border: 1px solid rgba(99, 102, 241, 0.15); overflow: hidden; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15); }
.app-ranking-chart .panel-header { padding: 8px 12px; }
.chart-selectors { display: flex; justify-content: space-between; padding: 6px 12px; border-bottom: 1px solid rgba(99, 102, 241, 0.08); }
.ranking-chart-area { height: 280px; padding: 8px; }

.search-results { max-height: 300px; overflow-y: auto; }
.search-result-item { display: flex; align-items: center; gap: 12px; padding: 10px; border-radius: 6px; cursor: pointer; transition: background 0.15s ease; }
.search-result-item:hover { background: rgba(99, 102, 241, 0.1); }
.app-icon { width: 48px; height: 48px; border-radius: 10px; }
.app-info { flex: 1; }
.app-name { font-size: 14px; font-weight: 500; color: #e2e8f0; }
.app-id { font-size: 12px; color: #94a3b8; font-family: 'SF Mono', 'Monaco', monospace; }
.add-icon { color: #6366f1; font-size: 20px; }
.ranking-table { background: rgba(22, 24, 38, 0.92); border-radius: 8px; border: 1px solid rgba(99, 102, 241, 0.15); overflow: hidden; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15); }
.table-header { display: flex; background: linear-gradient(180deg, rgba(99, 102, 241, 0.12) 0%, rgba(99, 102, 241, 0.06) 100%); padding: 10px 14px; border-bottom: 1px solid rgba(99, 102, 241, 0.18); }
.table-header .col-game { flex: 1; font-size: 14px; font-weight: 600; color: #cbd5e1; }
.table-header .col-country { width: 75px; text-align: center; font-size: 14px; font-weight: 600; color: #cbd5e1; }
.table-header .col-actions { width: 50px; text-align: center; font-size: 14px; font-weight: 600; color: #cbd5e1; }
.table-row { display: flex; padding: 9px 14px; border-bottom: 1px solid rgba(99, 102, 241, 0.08); align-items: center; transition: background 0.15s ease; }
.table-row:last-child { border-bottom: none; }
.table-row:hover { background: rgba(99, 102, 241, 0.08); }
.table-row .col-game { flex: 1; }
.table-row .game-name { font-size: 14px; font-weight: 500; color: #e2e8f0; }
.table-row .col-country { width: 75px; text-align: center; }
.table-row .col-actions { width: 50px; text-align: center; }
.rank-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 14px; font-weight: 700; min-width: 40px; text-align: center; font-family: 'SF Mono', 'Monaco', monospace; }
.rank-badge.rank-high { background: rgba(34, 197, 94, 0.18); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.25); }
.rank-badge.rank-mid { background: rgba(245, 158, 11, 0.18); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.25); }
.rank-badge.rank-low { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.2); }

@media (max-width: 1200px) {
  .app-ranking-section { grid-template-columns: 1fr; }
}
@media (max-width: 1000px) {
  .content-grid { grid-template-columns: 1fr; }
  .stats-row { flex-wrap: wrap; }
  .stat-item { min-width: calc(33% - 6px); }
  .table-header .col-country, .table-row .col-country { width: 65px; }
  .app-ranking-compact { max-width: 100%; }
}
</style>
