<template>
  <div class="data-observer">
    <header class="page-header">
      <div class="header-left">
        <h1><el-icon><DataLine /></el-icon> 数据观察</h1>
        <span class="update-time">{{ currentTime }}</span>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="downloadData" :loading="downloadLoading" :disabled="!userStore.isAuthenticated">
          <el-icon><Download /></el-icon> 下载数据
        </el-button>
        <el-button v-if="isAdmin" type="success" @click="crawlData" :loading="crawlLoading">
          <el-icon><Download /></el-icon> 立即爬取
        </el-button>
        <el-dropdown @command="handleSettingsCommand">
          <el-button type="default">
            <el-icon><Setting /></el-icon> 设置
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="personal">个人设置</el-dropdown-item>
              <el-dropdown-item v-if="isAdmin" command="global">页面设置</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <div class="stats-row">
      <div class="stat-item">
        <el-icon><Document /></el-icon>
        <div class="stat-content">
          <span class="stat-value">{{ totalPosts }}</span>
          <span class="stat-label">本周发帖</span>
        </div>
      </div>
      <div class="stat-item">
        <el-icon><TrendCharts /></el-icon>
        <div class="stat-content">
          <span class="stat-value">{{ avgPosts }}</span>
          <span class="stat-label">日均发帖</span>
        </div>
      </div>
      <div class="stat-item">
        <el-icon><Trophy /></el-icon>
        <div class="stat-content">
          <span class="stat-value">{{ topTieba.name || '-' }}</span>
          <span class="stat-label">最活跃</span>
        </div>
      </div>
      <div class="stat-item">
        <el-icon><Monitor /></el-icon>
        <div class="stat-content">
          <span class="stat-value">{{ monitoredForums.length }}</span>
          <span class="stat-label">监控贴吧</span>
        </div>
      </div>
      <div class="stat-item" :class="schedulerStatus.running ? 'running' : 'stopped'">
        <el-icon><Timer /></el-icon>
        <div class="stat-content">
          <span class="stat-value">{{ schedulerStatus.running ? '运行中' : '已停止' }}</span>
          <span class="stat-label">调度器</span>
        </div>
      </div>
    </div>

    <div class="content-grid">
      <div class="left-column">
        <div class="panel chart-panel">
          <div class="panel-header">
            <h3><el-icon><DataLine /></el-icon> 发帖量统计</h3>
            <span class="chart-days-label">3天</span>
          </div>
          <div class="stats-table-container">
            <table class="stats-table">
              <thead>
                <tr>
                  <th class="rank-col">排名</th>
                  <th class="tieba-col">贴吧</th>
                  <th v-for="date in stackedDates" :key="date" class="date-col">{{ date }}</th>
                  <th class="total-col">总计</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(stat, index) in sortedStats" :key="stat.tieba_name">
                  <td class="rank-cell"><span class="rank-badge" :class="getRankClass(index + 1)">{{ index + 1 }}</span></td>
                  <td class="tieba-cell"><el-tag :color="stat.color" effect="dark">{{ stat.tieba_name }}</el-tag></td>
                  <td v-for="date in stackedDates" :key="date" class="date-cell">{{ stat.daily[date] || 0 }}</td>
                  <td class="total-cell">{{ stat.total }}</td>
                </tr>
              </tbody>
            </table>
            <el-empty v-if="sortedStats.length === 0" description="暂无数据" :image-size="60" />
          </div>
        </div>

        <div class="panel daily-panel">
          <div class="panel-header">
            <h3><el-icon><Sunny /></el-icon> 今日热帖 TOP 3</h3>
            <el-tag type="danger">实时</el-tag>
          </div>
          <div class="daily-grid">
            <div v-for="(post, index) in dailyHotPosts" :key="post.post_id" class="daily-card" :class="'c'+(index+1)">
              <span class="badge">{{ index+1 }}</span>
              <el-tag :color="post.color" effect="dark">{{ post.tieba_name }}</el-tag>
              <h4>{{ post.title }}</h4>
              <div class="meta">
                <span class="hot"><el-icon><Sunny /></el-icon>{{ post.hotness || post.hot_index }}</span>
              </div>
              <a :href="post.post_url" target="_blank" class="link">查看详情</a>
            </div>
            <el-empty v-if="dailyHotPosts.length === 0" description="暂无今日热帖" :image-size="60" />
          </div>
        </div>
      </div>

      <div class="right-column">
        <div class="panel rank-panel">
          <div class="panel-header">
            <h3><el-icon><Histogram /></el-icon> 当日活跃度排行</h3>
          </div>
          <div ref="barChartRef" class="chart-area bar-chart"></div>
        </div>

        <div class="panel hot-panel">
          <div class="panel-header">
            <h3><el-icon><Sunny /></el-icon> 每周热帖 TOP 10</h3>
          </div>
          <div class="hot-list">
            <div v-for="(post, index) in weeklyHotPosts" :key="post.post_id" class="hot-item">
              <span class="rank" :class="'r'+(index+1)">{{ index+1 }}</span>
              <el-tag :color="post.color" effect="dark">{{ post.tieba_name }}</el-tag>
              <span class="title">{{ post.title }}</span>
              <span class="meta hot"><el-icon><Sunny /></el-icon>{{ post.hotness || post.hot_index }}</span>
              <a :href="post.post_url" target="_blank" class="link">查看</a>
            </div>
            <el-empty v-if="weeklyHotPosts.length === 0" description="暂无热帖" :image-size="60" />
          </div>
        </div>
      </div>
    </div>

    <div class="section-divider">
      <h2><el-icon><Iphone /></el-icon> iOS畅销榜排行</h2>
      <div class="header-controls">
        <span class="update-time">更新：{{ appRankingLastUpdated || '-' }}</span>
        <el-radio-group v-model="sortCountry" size="small" @change="sortAppRanking">
          <el-radio-button label="cn">🇨🇳 国服</el-radio-button>
          <el-radio-button label="jp">🇯🇵 日服</el-radio-button>
          <el-radio-button label="us">🇺🇸 美服</el-radio-button>
          <el-radio-button label="kr">🇰🇷 韩服</el-radio-button>
        </el-radio-group>
        <el-button v-if="isAdmin" type="primary" @click="showAddGameDialog = true">
          <el-icon><Plus /></el-icon> 添加游戏
        </el-button>
      </div>
    </div>

    <div class="app-ranking-section">
      <div class="app-ranking-list">
        <div v-for="(app, index) in appRankingData" :key="app.id" class="app-ranking-row">
          <span class="app-index">{{ index + 1 }}</span>
          <img :src="app.icon_url" class="app-icon" />
          <span class="app-name">{{ app.name_cn }}</span>
          <div class="app-ranks-inline">
            <div class="rank-item" :class="{ active: sortCountry === 'cn' }" @click="sortCountry = 'cn'; sortAppRanking()">
              <span class="flag">🇨🇳</span>
              <span class="rank-num" :class="getAppRankClass(app.rankings['cn']?.rank)">
                {{ app.rankings['cn']?.rank > 100 ? '>100' : app.rankings['cn']?.rank || '-' }}
              </span>
            </div>
            <div class="rank-item" :class="{ active: sortCountry === 'jp' }" @click="sortCountry = 'jp'; sortAppRanking()">
              <span class="flag">🇯🇵</span>
              <span class="rank-num" :class="getAppRankClass(app.rankings['jp']?.rank)">
                {{ app.rankings['jp']?.rank > 100 ? '>100' : app.rankings['jp']?.rank || '-' }}
              </span>
            </div>
            <div class="rank-item" :class="{ active: sortCountry === 'us' }" @click="sortCountry = 'us'; sortAppRanking()">
              <span class="flag">🇺🇸</span>
              <span class="rank-num" :class="getAppRankClass(app.rankings['us']?.rank)">
                {{ app.rankings['us']?.rank > 100 ? '>100' : app.rankings['us']?.rank || '-' }}
              </span>
            </div>
            <div class="rank-item" :class="{ active: sortCountry === 'kr' }" @click="sortCountry = 'kr'; sortAppRanking()">
              <span class="flag">🇰🇷</span>
              <span class="rank-num" :class="getAppRankClass(app.rankings['kr']?.rank)">
                {{ app.rankings['kr']?.rank > 100 ? '>100' : app.rankings['kr']?.rank || '-' }}
              </span>
            </div>
          </div>
          <el-button v-if="isAdmin" type="danger" size="small" link @click="deleteGame(app.id, app.name_cn)" class="delete-btn">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <el-empty v-if="appRankingData.length === 0" description="暂无排名数据" :image-size="60" />
      </div>

      <div class="app-ranking-chart">
        <div class="panel-header">
          <h3><el-icon><TrendCharts /></el-icon> 排名趋势</h3>
          <div class="chart-controls">
            <el-select v-model="chartTimeRange" size="small" @change="loadRankingHistory" class="time-range-select">
              <el-option label="24小时" value="24h" />
              <el-option label="30天" value="30d" />
              <el-option label="180天" value="180d" />
            </el-select>
          </div>
        </div>
        <div class="chart-selection-grid">
          <div class="selection-panel">
            <h4><el-icon><Collection /></el-icon> 选择游戏</h4>
            <el-select
              v-model="selectedGames"
              multiple
              filterable
              collapse-tags
              collapse-tags-tooltip
              placeholder="请选择游戏"
              class="selection-select"
              @change="updateRankingChart"
            >
              <el-option
                v-for="app in appRankingData"
                :key="app.id"
                :label="app.name_cn"
                :value="app.id"
              />
            </el-select>
          </div>
          <div class="selection-panel">
            <h4><el-icon><Flag /></el-icon> 选择国家</h4>
            <el-select
              v-model="selectedCountries"
              multiple
              filterable
              collapse-tags
              collapse-tags-tooltip
              placeholder="请选择国家"
              class="selection-select"
              @change="updateRankingChart"
            >
              <el-option
                v-for="country in countries"
                :key="country.value"
                :label="country.label"
                :value="country.value"
              />
            </el-select>
          </div>
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

    <el-dialog v-model="showGlobalSettingsDialog" title="页面全局设置" width="600px">
      <el-form label-position="top">
        <el-divider content-position="left">布局设置</el-divider>
        <el-form-item label="左侧列宽度比例">
          <el-slider v-model="globalSettings.leftColumnWidth" :min="0.5" :max="2" :step="0.1" show-input @change="saveGlobalSettings" />
        </el-form-item>
        <el-form-item label="右侧列宽度比例">
          <el-slider v-model="globalSettings.rightColumnWidth" :min="0.5" :max="2" :step="0.1" show-input @change="saveGlobalSettings" />
        </el-form-item>
        <el-form-item label="活跃度排行高度 (px)">
          <el-input-number v-model="globalSettings.barChartHeight" :min="200" :max="500" :step="20" @change="saveGlobalSettings" />
        </el-form-item>
        <el-form-item label="热帖列表最大高度 (px)">
          <el-input-number v-model="globalSettings.hotListHeight" :min="200" :max="600" :step="20" @change="saveGlobalSettings" />
        </el-form-item>
        
        <el-divider content-position="left">数据设置</el-divider>
        <el-form-item label="统计天数">
          <el-select v-model="globalSettings.statsDays" @change="saveGlobalSettings">
            <el-option label="3天" :value="3" />
            <el-option label="7天" :value="7" />
            <el-option label="14天" :value="14" />
            <el-option label="30天" :value="30" />
          </el-select>
        </el-form-item>
        <el-form-item label="热帖数量限制">
          <el-input-number v-model="globalSettings.hotPostsLimit" :min="5" :max="20" :step="1" @change="saveGlobalSettings" />
        </el-form-item>
        
        <el-divider content-position="left">视觉设置</el-divider>
        <el-form-item label="字体大小缩放">
          <el-slider v-model="globalSettings.fontSizeScale" :min="0.8" :max="1.5" :step="0.05" show-input @change="saveGlobalSettings" />
        </el-form-item>
        <el-form-item label="图表高度缩放">
          <el-slider v-model="globalSettings.chartHeightScale" :min="0.7" :max="1.5" :step="0.05" show-input @change="saveGlobalSettings" />
        </el-form-item>
        <el-form-item label="面板透明度">
          <el-slider v-model="globalSettings.panelOpacity" :min="0.5" :max="1" :step="0.05" show-input @change="saveGlobalSettings" />
        </el-form-item>
        <el-form-item label="边框圆角 (px)">
          <el-slider v-model="globalSettings.borderRadius" :min="0" :max="20" :step="1" show-input @change="saveGlobalSettings" />
        </el-form-item>
        
        <el-divider content-position="left">表格设置</el-divider>
        <el-form-item label="表格高度 (px)">
          <el-input-number v-model="globalSettings.tableHeight" :min="200" :max="800" :step="20" @change="saveGlobalSettings" />
        </el-form-item>
        <el-form-item label="表格字体大小 (px)">
          <el-input-number v-model="globalSettings.tableFontSize" :min="10" :max="20" :step="1" @change="saveGlobalSettings" />
        </el-form-item>
        
        <el-divider content-position="left">热帖设置</el-divider>
        <el-form-item label="今日热帖数量限制">
          <el-input-number v-model="globalSettings.dailyHotPostsLimit" :min="1" :max="10" :step="1" @change="saveGlobalSettings" />
        </el-form-item>
        <el-form-item label="今日热帖面板高度 (px)">
          <el-input-number v-model="globalSettings.dailyPanelHeight" :min="100" :max="400" :step="20" @change="saveGlobalSettings" />
        </el-form-item>
        <el-form-item label="每周热帖列表高度 (px)">
          <el-input-number v-model="globalSettings.weeklyHotListHeight" :min="200" :max="600" :step="20" @change="saveGlobalSettings" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetGlobalSettings">重置默认</el-button>
        <el-button type="primary" @click="showGlobalSettingsDialog = false">确定</el-button>
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

// 计算属性：是否为管理员
const isAdmin = computed(() => {
  return userStore.user?.is_admin === true
})

const monitoredForums = ref<string[]>([])
const forumColors = ref<Record<string, string>>({})
const weeklyHotPosts = ref<any[]>([])
const dailyHotPosts = ref<any[]>([])
const leaderboard = ref<any[]>([])
const stackedData = ref<any[]>([])
const stackedDates = ref<string[]>([])
const weeklyStats = ref<any>({})
const currentTime = ref('')
const chartDays = ref(3)
const downloadLoading = ref(false)
const crawlLoading = ref(false)
const schedulerStatus = ref<{running: boolean, has_aiotieba: boolean}>({running: false, has_aiotieba: false})

const stackedChartRef = ref<HTMLElement>()
const barChartRef = ref<HTMLElement>()
let stackedChart: echarts.ECharts | null = null
let barChart: echarts.ECharts | null = null

const appRankingData = ref<any[]>([])
const appRankingRawData = ref<any[]>([])
const appRankingLastUpdated = ref('')
const sortCountry = ref('cn')

const rankingChartRef = ref<HTMLElement>()
let rankingChart: echarts.ECharts | null = null

const chartTimeRange = ref('24h')
const selectedGames = ref<string[]>([])
const selectedCountries = ref<string[]>(['cn'])
const rankingHistoryData = ref<any[]>([])
const countries = ref([
  { label: '🇨🇳 中国', value: 'cn' },
  { label: '🇯🇵 日本', value: 'jp' },
  { label: '🇺🇸 美国', value: 'us' },
  { label: '🇰🇷 韩国', value: 'kr' }
])

const showAddGameDialog = ref(false)
const searchGameQuery = ref('')
const searchGameResults = ref<any[]>([])

const showSettingsDialog = ref(false)
const showGlobalSettingsDialog = ref(false)
const defaultGlobalSettings = {
  leftColumnWidth: 1.02,
  rightColumnWidth: 1.1,
  barChartHeight: 240,
  hotListHeight: 400,
  statsDays: 3,
  hotPostsLimit: 10,
  dailyHotPostsLimit: 3,
  fontSizeScale: 1,
  chartHeightScale: 1,
  panelOpacity: 0.92,
  borderRadius: 8,
  tableWidth: 100,
  tableHeight: 400,
  tableFontSize: 14,
  dailyPanelHeight: 200,
  weeklyHotListHeight: 400
}
const globalSettings = ref({ ...defaultGlobalSettings })
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
  currentTime.value = now.toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function getAppRankClass(rank: number) {
  if (!rank || rank > 100) return 'rank-gray'
  if (rank === 1) return 'rank-red'
  if (rank <= 3) return 'rank-rose'
  if (rank <= 10) return 'rank-gold'
  if (rank <= 20) return 'rank-purple'
  if (rank <= 40) return 'rank-blue'
  return 'rank-green'
}

function getRankClass(rank: number) {
  if (rank === 1) return 'rank-red'
  if (rank === 2) return 'rank-rose'
  if (rank === 3) return 'rank-gold'
  if (rank <= 10) return 'rank-purple'
  return 'rank-blue'
}

function handleSettingsCommand(command: string) {
  if (command === 'personal') {
    showSettingsDialog.value = true
  } else if (command === 'global') {
    if (!isAdmin.value) {
      ElMessage.warning('只有管理员可以调整全局设置')
      return
    }
    showGlobalSettingsDialog.value = true
  }
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
    stackedDates.value = data.dates || []
  } catch (error) { console.error('加载堆叠数据失败:', error) }
}

const sortedStats = computed(() => {
  if (!stackedData.value.length || !stackedDates.value.length) return []
  
  const statsMap: Record<string, any> = {}
  
  // 初始化每个贴吧的统计数据
  for (const tieba of monitoredForums.value) {
    statsMap[tieba] = {
      tieba_name: tieba,
      color: forumColors.value[tieba] || '#6366f1',
      daily: {} as Record<string, number>,
      total: 0
    }
  }
  
  // 填充数据
  for (const dayData of stackedData.value) {
    const date = dayData.date
    for (const tieba of monitoredForums.value) {
      const count = dayData[tieba] || 0
      statsMap[tieba].daily[date] = count
      statsMap[tieba].total += count
    }
  }
  
  // 按总发帖量递减排序
  return Object.values(statsMap).sort((a, b) => b.total - a.total)
})

async function loadWeeklyHotPosts() {
  try {
    const data = await api.get(`/tieba/hot/weekly?limit=${globalSettings.value.hotPostsLimit}`)
    const posts = data.posts || []
    // 计算热度并排序：热度 = 3 * 评论数 + 点赞数
    const withHotness = posts.map(post => {
      const comments = post.comments || post.comment_count || 0
      const likes = post.likes || post.like_count || 0
      const hotness = 3 * comments + likes
      return { ...post, hotness }
    })
    // 按热度降序排序
    weeklyHotPosts.value = withHotness.sort((a, b) => b.hotness - a.hotness)
  } catch (error) { console.error('加载周热帖失败:', error) }
}

async function loadDailyHotPosts() {
  try {
    const data = await api.get(`/tieba/hot/daily?limit=${globalSettings.value.dailyHotPostsLimit}`)
    const posts = data.posts || []
    // 计算热度并排序：热度 = 3 * 评论数 + 点赞数
    const withHotness = posts.map(post => {
      const comments = post.comments || post.comment_count || 0
      const likes = post.likes || post.like_count || 0
      const hotness = 3 * comments + likes
      return { ...post, hotness }
    })
    // 按热度降序排序
    dailyHotPosts.value = withHotness.sort((a, b) => b.hotness - a.hotness)
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

function sortAppRanking() {
  appRankingData.value = [...appRankingRawData.value].sort((a, b) => {
    const rankA = a.rankings[sortCountry.value]?.rank || 101
    const rankB = b.rankings[sortCountry.value]?.rank || 101
    return rankA - rankB
  })
}

function sortAppRankingByCountry(country: string, order: string = 'ascending') {
  appRankingData.value = [...appRankingRawData.value].sort((a, b) => {
    const rankA = a.rankings[country]?.rank || 101
    const rankB = b.rankings[country]?.rank || 101
    return order === 'ascending' ? rankA - rankB : rankB - rankA
  })
}

async function loadAppRanking() {
  try {
    const data = await api.get('/ranking/current')
    appRankingRawData.value = data.apps || []
    appRankingLastUpdated.value = data.last_updated || ''
    sortAppRanking()
    if (appRankingData.value.length > 0 && selectedGames.value.length === 0) {
      selectedGames.value = appRankingData.value.map(app => app.id)
    }
  } catch (error) { console.error('加载畅销榜失败:', error) }
}

// 优化数据加载，确保爬取后能及时更新数据
async function loadAllData() {
  try {
    // 并行加载所有数据
    await Promise.all([
      loadForums(),
      loadWeeklyStats(),
      loadStackedData(),
      loadWeeklyHotPosts(),
      loadDailyHotPosts(),
      loadLeaderboard(),
      loadSchedulerStatus(),
      loadAppRanking()
    ])
    // 加载排名历史
    await loadRankingHistory()
    // 强制更新图表
    nextTick(() => {
      updateBarChart()
      updateRankingChart()
    })
  } catch (error) {
    console.error('加载数据失败:', error)
  }
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
  const top5 = [...leaderboard.value]
    .sort((a, b) => b.total_posts - a.total_posts)
    .slice(0, 5)
    .reverse()
  
  // 检测是否为移动端
  const isMobile = window.innerWidth <= 768
  
  barChart.setOption({
    tooltip: { 
      trigger: 'axis', 
      backgroundColor: 'rgba(15, 23, 42, 0.98)', 
      borderColor: 'rgba(99, 102, 241, 0.35)', 
      borderWidth: 1,
      textStyle: { color: '#e2e8f0', fontSize: isMobile ? 12 : 11 },
      padding: isMobile ? [10, 14] : [8, 12],
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const item = top5[params[0].dataIndex]
        return `${item.tieba_name}<br/>
               发帖数：${item.total_posts}`
      }
    },
    grid: { 
      left: isMobile ? '2%' : '3%', 
      right: isMobile ? '2%' : '4%', 
      top: isMobile ? '2%' : '4%', 
      bottom: isMobile ? '2%' : '4%', 
      containLabel: true 
    },
    xAxis: { 
      type: 'value', 
      axisLine: { show: false }, 
      axisLabel: { 
        color: '#94a3b8', 
        fontSize: isMobile ? 11 : 10,
        interval: 0
      }, 
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      name: '发帖数',
      nameTextStyle: { color: '#94a3b8', fontSize: isMobile ? 11 : 10 }
    },
    yAxis: { 
      type: 'category', 
      data: top5.map((d: any) => isMobile && d.tieba_name.length > 6 ? d.tieba_name.slice(0, 6) + '...' : d.tieba_name), 
      axisLine: { show: false }, 
      axisLabel: { 
        color: '#e2e8f0', 
        fontSize: isMobile ? 12 : 10, 
        interval: 0 
      },
      axisTick: { show: false }
    },
    series: [{ 
      type: 'bar', 
      data: top5.map((item: any) => ({ 
        value: item.total_posts, 
        itemStyle: { 
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: item.color }, { offset: 1, color: item.color + '99' }]), 
          borderRadius: [0, 3, 3, 0] 
        } 
      })), 
      barWidth: isMobile ? '50%' : '40%'
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
  if (!rankingChart) {
    initRankingChart()
    setTimeout(() => updateRankingChart(), 100)
    return
  }
  
  if (rankingHistoryData.value.length === 0) {
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
  
  if (gamesToShow.length === 0) {
    rankingChart.setOption({
      title: {
        text: '请选择游戏',
        left: 'center',
        top: 'center',
        textStyle: { color: '#94a3b8', fontSize: 14 }
      }
    })
    return
  }
  
  const countriesToShow = selectedCountries.value.length > 0 
    ? selectedCountries.value 
    : ['cn']
  
  if (countriesToShow.length === 0) {
    rankingChart.setOption({
      title: {
        text: '请选择国家',
        left: 'center',
        top: 'center',
        textStyle: { color: '#94a3b8', fontSize: 14 }
      }
    })
    return
  }
  
  // 根据时间范围确定日期格式化方式
  const getDateKey = (date: Date) => {
    if (chartTimeRange.value === '24h') {
      return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit' })
    } else {
      return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit' })
    }
  }
  
  const dateMap = new Map<string, number>()
  rankingHistoryData.value.forEach((r: any) => {
    const d = new Date(r.recorded_at)
    const dateKey = getDateKey(d)
    if (!dateMap.has(dateKey)) {
      dateMap.set(dateKey, dateMap.size)
    }
  })
  const dates = Array.from(dateMap.keys()).sort()
  
  const recordMap = new Map<string, any>()
  rankingHistoryData.value.forEach((r: any) => {
    const d = new Date(r.recorded_at)
    const dateKey = getDateKey(d)
    const key = `${r.app_id}_${r.country}_${dateKey}`
    recordMap.set(key, r)
  })
  
  const series: any[] = []
  const colors = ['#6366f1', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#14b8a6', '#f97316']
  
  gamesToShow.forEach((app, appIndex) => {
    countriesToShow.forEach((country, countryIndex) => {
      const colorIndex = (appIndex * countriesToShow.length + countryIndex) % colors.length
      const data = dates.map(date => {
        const key = `${app.id}_${country}_${date}`
        const record = recordMap.get(key)
        return record ? record.rank : null
      })
      
      if (data.some((d: any) => d !== null)) {
        series.push({
          name: `${app.name_cn} (${country.toUpperCase()})`,
          type: 'line',
          data,
          smooth: true,
          symbol: chartTimeRange.value === '24h' ? 'circle' : 'emptyCircle',
          symbolSize: chartTimeRange.value === '24h' ? 6 : 4,
          lineStyle: { 
            width: chartTimeRange.value === '180d' ? 1.5 : 2, 
            color: colors[colorIndex] 
          },
          itemStyle: { color: colors[colorIndex] },
          emphasis: { focus: 'series' },
          connectNulls: chartTimeRange.value === '180d' // 180天模式下连接空值
        })
      }
    })
  })
  
  if (series.length === 0) {
    rankingChart.setOption({
      title: {
        text: '暂无匹配的历史数据',
        left: 'center',
        top: 'center',
        textStyle: { color: '#94a3b8', fontSize: 14 }
      }
    })
    return
  }
  
  // 先清除之前的 series，确保不显示已取消选择的游戏/国家
  rankingChart.setOption({ series: [] }, true)
  
  // 检测是否为移动端
  const isMobile = window.innerWidth <= 768
  
  rankingChart.setOption({
    title: { show: false },
    tooltip: { 
      trigger: 'axis', 
      backgroundColor: 'rgba(15, 23, 42, 0.98)', 
      borderColor: 'rgba(99, 102, 241, 0.35)', 
      borderWidth: 1,
      textStyle: { color: '#e2e8f0', fontSize: isMobile ? 12 : 13 },
      padding: isMobile ? [8, 12] : [10, 16],
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
      top: isMobile ? 0 : 2, 
      textStyle: { color: '#94a3b8', fontSize: isMobile ? 10 : 12 }, 
      pageIconColor: '#6366f1', 
      itemWidth: isMobile ? 10 : 12, 
      itemHeight: isMobile ? 8 : 10,
      pageIconSize: isMobile ? 10 : 12,
      pageTextStyle: { color: '#94a3b8' }
    },
    grid: { 
      left: isMobile ? '2%' : '3%', 
      right: isMobile ? '2%' : '3%', 
      top: isMobile ? '20%' : '15%', 
      bottom: isMobile ? '10%' : '8%', 
      containLabel: true 
    },
    xAxis: { 
      type: 'category', 
      data: dates, 
      axisLine: { lineStyle: { color: '#334155' } }, 
      axisLabel: { 
        color: '#94a3b8', 
        fontSize: isMobile ? 9 : 11, 
        rotate: dates.length > 10 || isMobile ? 45 : 0,
        interval: chartTimeRange.value === '180d' ? Math.floor(dates.length / (isMobile ? 20 : 30)) : (isMobile ? 2 : 0)
      },
      axisTick: { show: false }
    },
    yAxis: { 
      type: 'value', 
      axisLine: { show: false }, 
      axisLabel: { 
        color: '#94a3b8', 
        fontSize: isMobile ? 10 : 12 
      }, 
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      min: 1,
      max: 100,
      inverse: true
    },
    series: series.map(s => ({
      ...s,
      lineStyle: {
        ...s.lineStyle,
        width: isMobile ? 1.5 : s.lineStyle.width
      },
      symbolSize: isMobile ? 3 : s.symbolSize
    }))
  }, true)
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
    const artworkUrl = game.artworkUrl100 || game.artworkUrl60 || ''
    await api.post('/ranking/apps', {
      itunes_id: String(game.trackId),
      name_cn: game.trackName,
      name_en: game.trackName,
      icon_url: artworkUrl,
      developer: game.artistName || ''
    })
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
  
  root.style.setProperty('--bg-opacity', String(localSettings.value.bgOpacity))
  root.style.setProperty('--panel-opacity', String(localSettings.value.panelOpacity))
  root.style.setProperty('--blur-amount', `${localSettings.value.blurAmount}px`)
  root.style.setProperty('--border-radius', `${localSettings.value.borderRadius}px`)
  root.style.setProperty('--shadow-intensity', String(localSettings.value.shadowIntensity))
  root.style.setProperty('--font-size-scale', String(localSettings.value.fontSizeScale))
  root.style.setProperty('--chart-height-scale', String(localSettings.value.chartHeightScale))
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

async function loadGlobalSettings() {
  try {
    const response = await api.get('/admin/settings/data-observer')
    if (response.settings) {
      // 强制使用新的默认宽度值，忽略服务器保存的旧值
      const serverSettings = { ...response.settings }
      delete serverSettings.leftColumnWidth
      delete serverSettings.rightColumnWidth
      globalSettings.value = { ...defaultGlobalSettings, ...serverSettings }
      applyGlobalSettings()
    }
  } catch (error) {
    console.error('加载全局设置失败:', error)
  }
}

async function saveGlobalSettings() {
  try {
    await api.post('/admin/settings/data-observer', globalSettings.value)
    ElMessage.success('全局设置已保存')
    applyGlobalSettings()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

function resetGlobalSettings() {
  globalSettings.value = { ...defaultGlobalSettings }
  saveGlobalSettings()
}

function applyGlobalSettings() {
  const root = document.documentElement
  
  // 应用布局设置 - 不再动态设置宽度，使用CSS默认值
  // const contentGrid = document.querySelector('.content-grid') as HTMLElement
  // if (contentGrid) {
  //   contentGrid.style.gridTemplateColumns = `${globalSettings.value.leftColumnWidth}fr ${globalSettings.value.rightColumnWidth}fr`
  // }
  
  // 应用高度设置
  const barChart = document.querySelector('.bar-chart') as HTMLElement
  if (barChart) {
    barChart.style.height = `${globalSettings.value.barChartHeight}px`
  }
  
  const hotList = document.querySelector('.hot-list') as HTMLElement
  if (hotList) {
    hotList.style.maxHeight = `${globalSettings.value.weeklyHotListHeight}px`
  }
  
  // 应用表格设置
  const tableArea = document.querySelector('.table-area') as HTMLElement
  if (tableArea) {
    tableArea.style.height = `${globalSettings.value.tableHeight}px`
  }
  
  const statsTable = document.querySelector('.stats-table') as HTMLElement
  if (statsTable) {
    statsTable.style.fontSize = `${globalSettings.value.tableFontSize}px`
  }
  
  // 应用热帖设置
  const dailyGrid = document.querySelector('.daily-grid') as HTMLElement
  if (dailyGrid) {
    dailyGrid.style.height = `${globalSettings.value.dailyPanelHeight}px`
  }
  
  // 应用视觉设置
  root.style.setProperty('--font-size-scale', String(globalSettings.value.fontSizeScale))
  root.style.setProperty('--chart-height-scale', String(globalSettings.value.chartHeightScale))
  root.style.setProperty('--panel-opacity', String(globalSettings.value.panelOpacity))
  root.style.setProperty('--border-radius', `${globalSettings.value.borderRadius}px`)
  
  // 应用数据设置
  chartDays.value = globalSettings.value.statsDays
  loadStackedData()
  loadWeeklyHotPosts()
  loadDailyHotPosts()
  loadLeaderboard()
  
  // 触发图表重绘
  nextTick(() => {
    updateBarChart()
  })
}

function handleResize() { 
  stackedChart?.resize(); 
  barChart?.resize();
  rankingChart?.resize();
}



onMounted(() => { 
  updateTime(); 
  setInterval(updateTime, 1000); 
  initCharts(); 
  initRankingChart();
  loadSettings();
  loadGlobalSettings();
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
  --bg-opacity: 0.8;
  --panel-opacity: 0.7;
  --blur-amount: 12px;
  --border-radius: 12px;
  --shadow-intensity: 0.3;
  --font-size-scale: 0.75;
  --chart-height-scale: 1.2;
  --primary-color: #6366f1;
  --accent-color-1: #6366f1;
  --accent-color-2: #ec4899;
  --accent-color-3: #10b981;
  --accent-color-4: #f59e0b;
  --accent-color-5: #8b5cf6;
  --accent-color-6: #06b6d4;
  --text-primary: #ffffff;
  --text-secondary: #e2e8f0;
  --text-muted: #94a3b8;
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --border-color: rgba(99, 102, 241, 0.3);
}

.data-observer {
  min-height: 100vh;
  padding: 12px;
  background: linear-gradient(135deg, var(--bg-primary) 0%, #131c31 50%, #1e293b 100%);
  position: relative;
  overflow: hidden;
}

.data-observer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
              radial-gradient(circle at 80% 20%, rgba(236, 72, 153, 0.1) 0%, transparent 50%),
              radial-gradient(circle at 40% 80%, rgba(16, 185, 129, 0.1) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.data-observer > * {
  position: relative;
  z-index: 1;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 12px 16px;
  background: rgba(30, 41, 59, var(--panel-opacity));
  backdrop-filter: blur(var(--blur-amount));
  -webkit-backdrop-filter: blur(var(--blur-amount));
  border-radius: var(--border-radius);
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, calc(0.3 * var(--shadow-intensity))),
              0 1px 3px rgba(99, 102, 241, 0.1);
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.header-left h1 {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: calc(16px * var(--font-size-scale));
  font-weight: 500;
  color: var(--text-primary);
  margin: 0;
}

.header-left h1 .el-icon {
  color: var(--primary-color);
  font-size: calc(18px * var(--font-size-scale));
}

.update-time {
  font-size: calc(14px * var(--font-size-scale));
  color: var(--text-muted);
  font-family: 'SF Mono', 'Monaco', monospace;
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.header-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.stats-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  background: rgba(30, 41, 59, var(--panel-opacity));
  backdrop-filter: blur(var(--blur-amount));
  -webkit-backdrop-filter: blur(var(--blur-amount));
  border-radius: var(--border-radius);
  border: 1px solid rgba(99, 102, 241, 0.2);
  flex: 1;
  min-width: 180px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, calc(0.2 * var(--shadow-intensity))),
              0 1px 3px rgba(99, 102, 241, 0.1);
  position: relative;
  overflow: hidden;
}

.stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
}

.stat-item:hover {
  border-color: var(--primary-color);
  transform: translateY(-3px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, calc(0.3 * var(--shadow-intensity))),
              0 2px 8px rgba(99, 102, 241, 0.2);
}

.stat-item:hover .el-icon {
  transform: scale(1.1);
  color: var(--primary-color);
}

.stat-item .el-icon {
  font-size: calc(23px * var(--font-size-scale));
  color: var(--primary-color);
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  display: block;
  font-size: calc(16px * var(--font-size-scale));
  font-weight: 500;
  color: var(--text-primary);
  font-family: 'SF Mono', 'Monaco', monospace;
  line-height: 1.2;
}

.stat-label {
  display: block;
  font-size: calc(14px * var(--font-size-scale));
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  margin-top: 2px;
}

.stat-item.running .el-icon {
  color: #22c55e;
}

.stat-item.stopped .el-icon {
  color: #ef4444;
}

.content-grid {
  display: grid;
  grid-template-columns: 600px 0.9fr;
  gap: 12px;
  margin-bottom: 12px;
}

.left-column, .right-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel {
  background: rgba(30, 41, 59, var(--panel-opacity));
  border-radius: var(--border-radius);
  border: 1px solid rgba(99, 102, 241, 0.2);
  backdrop-filter: blur(var(--blur-amount));
  -webkit-backdrop-filter: blur(var(--blur-amount));
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, calc(0.3 * var(--shadow-intensity))),
              0 1px 3px rgba(99, 102, 241, 0.1);
  transition: all 0.3s ease;
  position: relative;
}

.panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
}

.panel:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, calc(0.4 * var(--shadow-intensity))),
              0 2px 8px rgba(99, 102, 241, 0.2);
  transform: translateY(-2px);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(99, 102, 241, 0.2);
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.1) 0%, transparent 100%);
}

.panel-header h3 {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 500;
  color: var(--text-primary);
  margin: 0;
}

.panel-header h3 .el-icon {
  color: var(--primary-color);
  font-size: calc(14px * var(--font-size-scale));
}

.chart-days-label {
  font-size: calc(14px * var(--font-size-scale));
  color: var(--text-muted);
  padding: 2px 8px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 4px;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.time-range-select {
  min-width: 90px;
}

.chart-area {
  padding: 16px;
}

.bar-chart {
  height: calc(280px * var(--chart-height-scale));
}

.stats-table-container {
  padding: 0;
  overflow-x: auto;
}

.stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: calc(14px * var(--font-size-scale));
}

.stats-table thead {
  background: rgba(99, 102, 241, 0.1);
  position: sticky;
  top: 0;
  z-index: 10;
}

.stats-table th {
  padding: 6px 3px;
  text-align: center;
  color: var(--text-primary);
  font-weight: 600;
  border-bottom: 2px solid rgba(99, 102, 241, 0.3);
  white-space: nowrap;
  font-size: calc(14px * var(--font-size-scale));
}

.stats-table tbody tr {
  border-bottom: 1px solid rgba(99, 102, 241, 0.1);
  transition: background 0.2s ease;
}

.stats-table tbody tr:hover {
  background: rgba(99, 102, 241, 0.05);
}

.stats-table td {
  padding: 5px 3px;
  text-align: center;
  color: var(--text-secondary);
  font-size: calc(14px * var(--font-size-scale));
}

.rank-col {
  width: 32px;
}

.tieba-col {
  text-align: center !important;
}

.date-col {
  min-width: 44px;
}

.total-col {
  min-width: 48px;
  font-weight: 700;
  color: var(--primary-color);
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  font-weight: 700;
  font-size: calc(14px * var(--font-size-scale));
  font-family: 'SF Mono', 'Monaco', monospace;
}

.rank-cell, .total-cell {
  font-family: 'SF Mono', 'Monaco', monospace;
  font-weight: 700;
  font-size: calc(15px * var(--font-size-scale));
}

.stats-cards-grid::-webkit-scrollbar {
  width: 6px;
}

.stats-cards-grid::-webkit-scrollbar-track {
  background: rgba(51, 65, 85, 0.5);
  border-radius: 3px;
}

.stats-cards-grid::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.5);
  border-radius: 3px;
}

.stats-cards-grid::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.7);
}

.stat-card {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: var(--border-radius);
  border: 1px solid rgba(99, 102, 241, 0.2);
  padding: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
  border-color: var(--primary-color);
}

.stat-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.rank-badge.small {
  width: 28px;
  height: 28px;
  font-size: calc(14px * var(--font-size-scale));
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-weight: 700;
  font-family: 'SF Mono', 'Monaco', monospace;
  flex-shrink: 0;
}

.stat-card-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.daily-stats {
  display: flex;
  gap: 8px;
  flex: 1;
  justify-content: flex-end;
}

.daily-stat {
  text-align: center;
  padding: 6px 10px;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
  border: 1px solid rgba(99, 102, 241, 0.1);
  flex-shrink: 0;
  min-width: 70px;
}

.daily-stat .date {
  font-size: calc(14px * var(--font-size-scale));
  color: var(--text-muted);
  margin-bottom: 4px;
  font-weight: 500;
}

.daily-stat .count {
  font-size: calc(15px * var(--font-size-scale));
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'SF Mono', 'Monaco', monospace;
}

.total-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(99, 102, 241, 0.05));
  border-radius: 8px;
  border: 1px solid rgba(99, 102, 241, 0.2);
  flex-shrink: 0;
  margin-left: 8px;
}

.total-stat .label {
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.total-stat .count {
  font-size: calc(18px * var(--font-size-scale));
  font-weight: 700;
  color: var(--primary-color);
  font-family: 'SF Mono', 'Monaco', monospace;
}

.el-table {
  --el-table-bg-color: transparent !important;
  --el-table-border-color: rgba(99, 102, 241, 0.2) !important;
  --el-table-header-bg-color: rgba(99, 102, 241, 0.1) !important;
  --el-table-header-text-color: var(--text-primary) !important;
  --el-table-text-color: var(--text-secondary) !important;
  --el-table-row-hover-bg-color: rgba(99, 102, 241, 0.1) !important;
  font-size: calc(14px * var(--font-size-scale)) !important;
}

.el-table th {
  font-weight: 600 !important;
  padding: 12px 8px !important;
  border-bottom: 1px solid rgba(99, 102, 241, 0.3) !important;
}

.el-table td {
  padding: 10px 8px !important;
  border-bottom: 1px solid rgba(99, 102, 241, 0.1) !important;
}

.el-table__row {
  transition: all 0.2s ease !important;
}

.el-table__row:hover {
  transform: translateX(2px) !important;
}

.hot-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 500px;
  overflow-y: auto;
}

.hot-list::-webkit-scrollbar {
  width: 6px;
}

.hot-list::-webkit-scrollbar-track {
  background: rgba(51, 65, 85, 0.5);
  border-radius: 3px;
}

.hot-list::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.5);
  border-radius: 3px;
}

.hot-list::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.7);
}

.hot-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: var(--border-radius);
  font-size: calc(14px * var(--font-size-scale));
  transition: all 0.3s ease;
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
}

.hot-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, var(--primary-color), rgba(99, 102, 241, 0.5));
  border-radius: var(--border-radius) 0 0 var(--border-radius);
}

.hot-item:hover {
  background: rgba(99, 102, 241, 0.1);
  transform: translateX(6px);
  border-color: var(--primary-color);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.15);
}

.hot-item .rank {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 700;
  color: var(--text-primary);
  background: var(--bg-tertiary);
  flex-shrink: 0;
  font-family: 'SF Mono', 'Monaco', monospace;
}

.hot-item .rank.r1 {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  box-shadow: 0 0 12px rgba(251, 191, 36, 0.4);
}

.hot-item .rank.r2 {
  background: linear-gradient(135deg, #cbd5e1, #94a3b8);
  box-shadow: 0 0 12px rgba(148, 163, 184, 0.35);
}

.hot-item .rank.r3 {
  background: linear-gradient(135deg, #fb923c, #ea580c);
  box-shadow: 0 0 12px rgba(251, 146, 60, 0.35);
}

.hot-item .title {
  flex: 1;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  font-weight: 500;
  font-size: calc(14px * var(--font-size-scale));
}

.hot-item .meta {
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  font-family: 'SF Mono', 'Monaco', monospace;
  font-size: calc(14px * var(--font-size-scale));
}

.hot-item .meta.hot {
  color: #f97316;
  font-weight: 600;
}

.hot-item .link {
  color: var(--primary-color);
  text-decoration: none;
  flex-shrink: 0;
  font-weight: 600;
  font-size: calc(14px * var(--font-size-scale));
  transition: color 0.2s ease;
}

.hot-item .link:hover {
  color: #60a5fa;
  text-decoration: underline;
}

.daily-grid {
  padding: 12px;
  display: flex;
  gap: 12px;
  overflow-x: auto;
}

.daily-grid::-webkit-scrollbar {
  height: 6px;
}

.daily-grid::-webkit-scrollbar-track {
  background: rgba(51, 65, 85, 0.5);
  border-radius: 3px;
}

.daily-grid::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.5);
  border-radius: 3px;
}

.daily-grid::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.7);
}

.daily-card {
  position: relative;
  padding: 14px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  flex: 0 0 auto;
  width: 160px;
}

.daily-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
  border-color: var(--primary-color);
}

.daily-card.c1 {
  border-color: rgba(251, 191, 36, 0.4);
  background: linear-gradient(180deg, rgba(251, 191, 36, 0.1) 0%, rgba(15, 23, 42, 0.8) 100%);
}

.daily-card.c2 {
  border-color: rgba(148, 163, 184, 0.4);
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.08) 0%, rgba(15, 23, 42, 0.8) 100%);
}

.daily-card.c3 {
  border-color: rgba(251, 146, 60, 0.4);
  background: linear-gradient(180deg, rgba(251, 146, 60, 0.08) 0%, rgba(15, 23, 42, 0.8) 100%);
}

.daily-card .badge {
  position: absolute;
  top: -10px;
  left: 16px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 700;
  color: var(--bg-primary);
  letter-spacing: 0.5px;
  font-family: 'SF Mono', 'Monaco', monospace;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.daily-card.c1 .badge {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
}

.daily-card.c2 .badge {
  background: linear-gradient(135deg, #cbd5e1, #94a3b8);
}

.daily-card.c3 .badge {
  background: linear-gradient(135deg, #fb923c, #ea580c);
}

.daily-card h4 {
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 600;
  color: var(--text-primary);
  margin: 12px 0 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.daily-card .meta {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.daily-card .meta span {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: calc(14px * var(--font-size-scale));
  color: var(--text-muted);
  font-family: 'SF Mono', 'Monaco', monospace;
}

.daily-card .meta span.hot {
  color: #f97316;
  font-weight: 600;
}

.daily-card .link {
  font-size: calc(14px * var(--font-size-scale));
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s ease;
}

.daily-card .link:hover {
  color: #60a5fa;
  text-decoration: underline;
}

.section-divider {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 24px 0 20px;
  padding: 16px 20px;
  background: rgba(30, 41, 59, var(--panel-opacity));
  backdrop-filter: blur(var(--blur-amount));
  -webkit-backdrop-filter: blur(var(--blur-amount));
  border-radius: var(--border-radius);
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, calc(0.3 * var(--shadow-intensity)));
  position: relative;
}

.section-divider::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
}

.section-divider h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: calc(20px * var(--font-size-scale));
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: 0.5px;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-ranking-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.app-ranking-compact {
  background: rgba(30, 41, 59, var(--panel-opacity));
  backdrop-filter: blur(var(--blur-amount));
  -webkit-backdrop-filter: blur(var(--blur-amount));
  border-radius: var(--border-radius);
  border: 1px solid rgba(99, 102, 241, 0.2);
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, calc(0.3 * var(--shadow-intensity)));
  position: relative;
}

.app-ranking-compact::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
}

.app-ranking-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  max-height: 500px;
  overflow-y: auto;
}

.app-ranking-list::-webkit-scrollbar {
  width: 6px;
}

.app-ranking-list::-webkit-scrollbar-track {
  background: rgba(51, 65, 85, 0.5);
  border-radius: 3px;
}

.app-ranking-list::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.5);
  border-radius: 3px;
}

.app-ranking-list::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.7);
}

.app-ranking-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: var(--border-radius);
  border: 1px solid rgba(99, 102, 241, 0.15);
  transition: all 0.2s ease;
}

.app-ranking-row:hover {
  background: rgba(99, 102, 241, 0.08);
  border-color: rgba(99, 102, 241, 0.3);
}

.app-index {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'SF Mono', 'Monaco', monospace;
  flex-shrink: 0;
}

.app-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid rgba(99, 102, 241, 0.3);
  flex-shrink: 0;
}

.app-name {
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
  min-width: 100px;
}

.app-ranks-inline {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 6px;
  border: 1px solid rgba(99, 102, 241, 0.1);
  cursor: pointer;
  transition: all 0.2s ease;
}

.rank-item:hover {
  background: rgba(99, 102, 241, 0.15);
}

.rank-item.active {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.4);
}

.rank-item .flag {
  font-size: calc(16px * var(--font-size-scale));
  flex-shrink: 0;
}

.rank-item .rank-num {
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 600;
  font-family: 'SF Mono', 'Monaco', monospace;
  min-width: 36px;
  text-align: center;
}

.delete-btn {
  padding: 4px;
  margin: 0;
}

.rank-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 700;
  font-family: 'SF Mono', 'Monaco', monospace;
  min-width: 60px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.rank-badge:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.rank-red {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.rank-rose {
  background: linear-gradient(135deg, #ec4899, #db2777);
  color: white;
  box-shadow: 0 2px 8px rgba(236, 72, 153, 0.3);
}

.rank-gold {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.rank-purple {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.rank-blue {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.rank-green {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.rank-gray {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  color: white;
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.3);
}



.app-ranking-chart {
  background: rgba(30, 41, 59, var(--panel-opacity));
  backdrop-filter: blur(var(--blur-amount));
  -webkit-backdrop-filter: blur(var(--blur-amount));
  border-radius: var(--border-radius);
  border: 1px solid rgba(99, 102, 241, 0.2);
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, calc(0.3 * var(--shadow-intensity)));
  position: relative;
}

.app-ranking-chart::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chart-selection-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin: 16px 0;
}

.selection-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selection-panel h4 {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.selection-select {
  width: 100%;
}

.ranking-chart-area {
  height: 400px;
  margin-top: 16px;
}

/* Element Plus 自定义样式 */
:deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-header-bg-color: rgba(59, 130, 246, 0.1);
  --el-table-header-text-color: #93c5fd;
  --el-table-row-hover-bg-color: rgba(59, 130, 246, 0.1);
  --el-table-border-color: var(--border-color);
}

:deep(.el-table th) {
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 600;
  padding: 14px;
  border-bottom: 2px solid var(--primary-color);
}

:deep(.el-table td) {
  font-size: calc(14px * var(--font-size-scale));
  color: var(--text-primary);
  padding: 14px;
  border-bottom: 1px solid var(--border-color);
}

:deep(.el-select .el-input__wrapper) {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

:deep(.el-select .el-input__inner) {
  color: var(--text-primary);
  font-size: calc(14px * var(--font-size-scale));
}

:deep(.el-select .el-select__caret) {
  color: var(--text-muted);
}

:deep(.el-option) {
  color: var(--text-primary);
  font-size: calc(14px * var(--font-size-scale));
}

:deep(.el-option:hover) {
  background: rgba(59, 130, 246, 0.1);
}

:deep(.el-option.is-selected) {
  background: rgba(59, 130, 246, 0.2);
  color: var(--text-primary);
}

:deep(.el-button) {
  font-size: calc(14px * var(--font-size-scale));
  padding: 8px 16px;
  border-radius: 8px;
}

:deep(.el-dropdown-menu) {
  background: rgba(30, 41, 59, 0.95);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

:deep(.el-dropdown-item) {
  color: var(--text-primary);
  font-size: calc(14px * var(--font-size-scale));
  padding: 8px 16px;
}

:deep(.el-dropdown-item:hover) {
  background: rgba(59, 130, 246, 0.1);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-selection-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .data-observer {
    padding: 12px;
  }
  
  .stats-row {
    flex-direction: column;
  }
  
  .stat-item {
    min-width: auto;
  }
  
  .daily-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .header-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .section-divider {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .header-controls {
    width: 100%;
    justify-content: space-between;
  }
  
  .ranking-chart-area {
    height: 300px;
  }
}
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
.table-header .col-country { width: 75px; text-align: center; font-size: 14px; font-weight: 600; color: #cbd5e1; cursor: pointer; transition: all 0.2s ease; border-radius: 4px; }
.table-header .col-country:hover { background: rgba(99, 102, 241, 0.15); color: #e0e7ff; }
.table-header .col-country.sort-active { background: rgba(99, 102, 241, 0.25); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.4); }
.table-header .col-actions { width: 50px; text-align: center; font-size: 14px; font-weight: 600; color: #cbd5e1; }
.table-row { display: flex; padding: 9px 14px; border-bottom: 1px solid rgba(99, 102, 241, 0.08); align-items: center; transition: background 0.15s ease; }
.table-row:last-child { border-bottom: none; }
.table-row:hover { background: rgba(99, 102, 241, 0.08); }
.table-row .col-game { flex: 1; }
.table-row .game-info { display: flex; align-items: center; gap: 10px; }
.table-row .game-icon { width: 40px; height: 40px; border-radius: 8px; object-fit: cover; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2); }
.table-row .game-icon-placeholder { width: 40px; height: 40px; border-radius: 8px; background: rgba(99, 102, 241, 0.15); display: flex; align-items: center; justify-content: center; color: #6366f1; }
.table-row .game-name { font-size: 14px; font-weight: 500; color: #e2e8f0; }
.table-row .col-country { width: 75px; text-align: center; }
.table-row .col-actions { width: 50px; text-align: center; }
.rank-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 14px; font-weight: 700; min-width: 40px; text-align: center; font-family: 'SF Mono', 'Monaco', monospace; }
.rank-badge.rank-red { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.35); font-weight: 900; }
.rank-badge.rank-rose { background: rgba(244, 63, 94, 0.2); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.35); }
.rank-badge.rank-gold { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.35); }
.rank-badge.rank-purple { background: rgba(139, 92, 246, 0.2); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.35); }
.rank-badge.rank-blue { background: rgba(59, 130, 246, 0.2); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.35); }
.rank-badge.rank-green { background: rgba(34, 197, 94, 0.18); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.25); }
.rank-badge.rank-gray { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.2); }

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

/* 手机端适配 */
@media (max-width: 640px) {
  .data-observer {
    padding: 8px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 8px;
    padding: 10px 12px;
  }
  
  .header-left h1 {
    font-size: calc(16px * var(--font-size-scale));
  }
  
  .header-right {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .stats-row {
    flex-direction: column;
    gap: 8px;
  }
  
  .stat-item {
    min-width: auto;
    padding: 10px 12px;
  }
  
  .content-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .panel-header {
    padding: 8px 12px;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .panel-header h3 {
    font-size: calc(13px * var(--font-size-scale));
  }
  
  .stats-table-container {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  
  .stats-table {
    min-width: 100%;
    font-size: calc(12px * var(--font-size-scale));
  }
  
  .stats-table th,
  .stats-table td {
    padding: 6px 4px;
  }
  
  .hot-list {
    padding: 8px;
    gap: 6px;
  }
  
  .hot-item {
    padding: 8px 10px;
    gap: 8px;
  }
  
  .hot-item .title {
    font-size: calc(12px * var(--font-size-scale));
  }
  
  .daily-grid {
    gap: 8px;
    padding: 8px;
  }
  
  .daily-card {
    width: 140px;
    padding: 10px;
  }
  
  .section-divider {
    padding: 10px 12px;
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .section-divider h2 {
    font-size: calc(14px * var(--font-size-scale));
  }
  
  .header-controls {
    flex-wrap: wrap;
    gap: 8px;
    width: 100%;
  }
  
  .app-ranking-list {
    padding: 8px;
    gap: 6px;
  }
  
  .app-ranking-row {
    padding: 8px 10px;
    gap: 8px;
  }
  
  .app-icon {
    width: 32px;
    height: 32px;
  }
  
  .app-name {
    font-size: calc(12px * var(--font-size-scale));
    min-width: 80px;
  }
  
  .app-ranks-inline {
    gap: 8px;
  }
  
  .rank-item {
    padding: 3px 6px;
    gap: 3px;
  }
  
  .rank-item .flag {
    font-size: calc(14px * var(--font-size-scale));
  }
  
  .rank-item .rank-num {
    font-size: calc(12px * var(--font-size-scale));
    min-width: 28px;
  }
  
  .bar-chart {
    height: 200px;
  }
  
  .ranking-chart-area {
    height: 250px;
  }
  
  .chart-selectors {
    flex-direction: column;
    gap: 8px;
  }
  
  .app-ranking-section {
    grid-template-columns: 1fr;
  }
  
  .table-header .col-country,
  .table-row .col-country {
    width: 50px;
    font-size: calc(11px * var(--font-size-scale));
  }
  
  .table-row .game-icon {
    width: 32px;
    height: 32px;
  }
  
  .table-row .game-name {
    font-size: calc(12px * var(--font-size-scale));
  }
  
  .rank-badge {
    font-size: calc(11px * var(--font-size-scale));
    padding: 2px 8px;
    min-width: 32px;
  }
}

/* 超小屏幕适配 */
@media (max-width: 380px) {
  .daily-card {
    width: 120px;
  }
  
  .app-ranks-inline {
    flex-wrap: wrap;
    gap: 4px;
  }
  
  .rank-item {
    padding: 2px 4px;
  }
  
  .rank-item .rank-num {
    min-width: 24px;
    font-size: calc(11px * var(--font-size-scale));
  }
}

/* 移动端优化 - 基于开源最佳实践 */
@media (max-width: 768px) {
  /* 基础布局优化 */
  .data-observer {
    padding: 4px;
    font-size: 14px;
  }
  
  /* 头部简化 */
  .page-header {
    padding: 8px;
    margin-bottom: 8px;
  }
  
  .header-left h1 {
    font-size: 16px;
  }
  
  .header-right {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .header-right .el-button {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  /* 统计卡片横向滚动 */
  .stats-row {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    gap: 8px;
    padding: 4px;
    -webkit-overflow-scrolling: touch;
  }
  
  .stats-row::-webkit-scrollbar {
    display: none;
  }
  
  .stat-item {
    flex: 0 0 auto;
    min-width: 140px;
    padding: 12px;
  }
  
  /* 内容区域单列 */
  .content-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  /* 面板简化 */
  .panel {
    border-radius: 8px;
  }
  
  .panel-header {
    padding: 10px 12px;
  }
  
  .panel-header h3 {
    font-size: 14px;
  }
  
  /* 表格横向滚动 */
  .stats-table-container {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    margin: 0 -4px;
    padding: 0 4px;
  }
  
  .stats-table {
    min-width: 500px;
    font-size: 12px;
  }
  
  .stats-table th,
  .stats-table td {
    padding: 8px 6px;
  }
  
  /* 热帖列表紧凑 */
  .hot-list {
    padding: 8px;
    gap: 6px;
    max-height: 400px;
  }
  
  .hot-item {
    padding: 10px 12px;
    gap: 8px;
  }
  
  .hot-item .title {
    font-size: 13px;
    line-height: 1.4;
  }
  
  .hot-item .meta {
    font-size: 11px;
  }
  
  /* 每日热帖横向滚动 */
  .daily-grid {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    gap: 10px;
    padding: 8px;
    -webkit-overflow-scrolling: touch;
  }
  
  .daily-grid::-webkit-scrollbar {
    display: none;
  }
  
  .daily-card {
    flex: 0 0 auto;
    width: 260px;
    padding: 12px;
  }
  
  /* iOS 排行榜优化 */
  .section-divider {
    padding: 10px 12px;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .section-divider h2 {
    font-size: 15px;
  }
  
  .header-controls {
    width: 100%;
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .app-ranking-list {
    padding: 8px;
    gap: 6px;
  }
  
  .app-ranking-row {
    padding: 10px 12px;
    gap: 10px;
    flex-wrap: wrap;
  }
  
  .app-icon {
    width: 36px;
    height: 36px;
  }
  
  .app-name {
    font-size: 14px;
    flex: 1 1 100%;
    order: 3;
    margin-top: 4px;
  }
  
  .app-ranks-inline {
    order: 2;
    flex: 1;
    justify-content: space-between;
    gap: 6px;
  }
  
  .rank-item {
    flex: 1;
    justify-content: center;
    padding: 6px 4px;
    gap: 4px;
  }
  
  .rank-item .flag {
    font-size: 14px;
  }
  
  .rank-item .rank-num {
    font-size: 13px;
    min-width: auto;
  }
  
  /* 图表高度调整 */
  .bar-chart {
    height: 220px;
  }
  
  .ranking-chart-area {
    height: 280px;
  }
  
  /* 游戏表格优化 */
  .app-ranking-section {
    grid-template-columns: 1fr;
  }
  
  .table-header .col-country,
  .table-row .col-country {
    width: 60px;
    font-size: 12px;
  }
  
  .table-row .game-icon {
    width: 36px;
    height: 36px;
  }
  
  .table-row .game-name {
    font-size: 13px;
  }
  
  .rank-badge {
    font-size: 12px;
    padding: 3px 8px;
    min-width: 36px;
  }
  
  /* 选择器优化 */
  .chart-selectors {
    flex-direction: column;
    gap: 8px;
  }
  
  .chart-selectors .el-select {
    width: 100%;
  }
}

/* 小屏幕手机优化 */
@media (max-width: 480px) {
  .data-observer {
    padding: 2px;
  }
  
  .page-header {
    padding: 6px 8px;
  }
  
  .header-left h1 {
    font-size: 15px;
  }
  
  .stat-item {
    min-width: 120px;
    padding: 10px;
  }
  
  .stat-value {
    font-size: 18px;
  }
  
  .stat-label {
    font-size: 11px;
  }
  
  .daily-card {
    width: 240px;
    padding: 10px;
  }
  
  .daily-card .title {
    font-size: 13px;
  }
  
  .app-ranking-row {
    padding: 8px;
  }
  
  .app-icon {
    width: 32px;
    height: 32px;
  }
  
  .rank-item {
    padding: 4px 2px;
  }
  
  .rank-item .flag {
    font-size: 12px;
  }
  
  .rank-item .rank-num {
    font-size: 11px;
  }
  
  .bar-chart {
    height: 180px;
  }
  
  .ranking-chart-area {
    height: 240px;
  }
  
  .stats-table {
    min-width: 450px;
  }
}

/* 触摸优化 */
@media (hover: none) and (pointer: coarse) {
  .hot-item:hover,
  .daily-card:hover,
  .app-ranking-row:hover {
    transform: none;
  }
  
  .hot-item:active,
  .daily-card:active,
  .app-ranking-row:active {
    background: rgba(99, 102, 241, 0.15);
  }
  
  .rank-item:active {
    background: rgba(99, 102, 241, 0.25);
  }
}
</style>
