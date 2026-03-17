<template>
  <div class="app-ranking">
    <header class="page-header">
      <div class="header-left">
        <h1><el-icon><Iphone /></el-icon> iOS畅销榜排行</h1>
        <span class="update-time">更新时间: {{ lastUpdated || '-' }}</span>
      </div>
      <div class="header-right">
        <el-button v-if="userStore.user?.is_admin" type="success" @click="crawlData" :loading="crawlLoading">
          <el-icon><Refresh /></el-icon> 爬取数据
        </el-button>
      </div>
    </header>

    <div class="stats-row">
      <div class="stat-item">
        <el-icon><Monitor /></el-icon>
        <div class="stat-content">
          <span class="stat-value">{{ apps.length }}</span>
          <span class="stat-label">监控游戏</span>
        </div>
      </div>
      <div class="stat-item">
        <el-icon><Location /></el-icon>
        <div class="stat-content">
          <span class="stat-value">4</span>
          <span class="stat-label">地区</span>
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

    <div class="ranking-cards">
      <div v-for="app in appsWithRankings" :key="app.id" class="ranking-card">
        <div class="card-header">
          <h3>{{ app.name_cn }}</h3>
          <div class="card-actions">
            <span class="en-name">{{ app.name_en }}</span>
            <el-button v-if="userStore.user?.is_admin" type="danger" size="small" link @click="deleteApp(app.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
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
          <el-select v-model="timeRange" size="small" @change="loadAndUpdateChart" class="time-range-select">
            <el-option label="24小时" value="24h" />
            <el-option label="30天" value="30d" />
            <el-option label="180天" value="180d" />
          </el-select>
        </div>
        
        <div class="filter-section">
          <div class="filter-row">
            <div class="filter-item">
              <label class="filter-label">游戏选择</label>
              <el-select
                v-model="selectedGameIds"
                multiple
                filterable
                collapse-tags
                collapse-tags-tooltip
                placeholder="请选择游戏"
                class="filter-select game-select"
                :loading="gamesLoading"
                @change="handleGameSelectChange"
              >
                <template #header>
                  <div class="select-header">
                    <el-checkbox
                      v-model="selectAllGames"
                      @change="handleSelectAllGames"
                    >全选</el-checkbox>
                  </div>
                </template>
                <el-option
                  v-for="app in apps"
                  :key="app.id"
                  :label="app.name_cn"
                  :value="app.id"
                >
                  <div class="select-option">
                    <span class="option-name">{{ app.name_cn }}</span>
                    <span class="option-sub">{{ app.name_en }}</span>
                  </div>
                </el-option>
                <template #empty>
                  <div class="select-empty">
                    <el-icon><DocumentDelete /></el-icon>
                    <span>暂无游戏数据</span>
                  </div>
                </template>
              </el-select>
            </div>
            
            <div class="filter-item">
              <label class="filter-label">地区选择</label>
              <el-select
                v-model="selectedCountryCodes"
                multiple
                filterable
                collapse-tags
                collapse-tags-tooltip
                placeholder="请选择地区"
                class="filter-select country-select"
                @change="handleCountrySelectChange"
              >
                <template #header>
                  <div class="select-header">
                    <el-checkbox
                      v-model="selectAllCountries"
                      @change="handleSelectAllCountries"
                    >全选</el-checkbox>
                  </div>
                </template>
                <el-option
                  v-for="(name, code) in countries"
                  :key="code"
                  :label="`${flags[code]} ${name}`"
                  :value="code"
                >
                  <div class="select-option country-option">
                    <span class="option-flag">{{ flags[code] }}</span>
                    <span class="option-name">{{ name }}</span>
                  </div>
                </el-option>
              </el-select>
            </div>
          </div>
        </div>
        
        <div class="chart-info" v-if="selectedGames.length > 0 || selectedCountries.length > 0">
          <span class="info-tag" v-for="game in selectedGames" :key="game">{{ game }}</span>
          <span class="info-tag country" v-for="country in selectedCountries" :key="country">{{ flags[country] }} {{ countries[country] }}</span>
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
              <el-empty v-if="!topApps[code]?.apps?.length" description="暂无数据" :image-size="60" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <div class="panel overtake-panel">
        <div class="panel-header">
          <h3><el-icon><Timer /></el-icon> 游戏超越应用累计时间</h3>
          <el-select v-model="overtakeTimeRange" size="small" @change="loadOvertakeData" class="time-range-select">
            <el-option label="7天" value="7d" />
            <el-option label="30天" value="30d" />
            <el-option label="90天" value="90d" />
          </el-select>
        </div>
        <div class="overtake-list">
          <div v-for="game in overtakeData" :key="game.game_id" class="overtake-item">
            <h4>{{ game.game_name }}</h4>
            <div class="overtake-details">
              <div v-for="(hours, appId) in game.overtake_times" :key="appId" class="overtake-detail">
                <span class="app-name">{{ referenceAppIds.find(app => app.id === appId)?.name || appId }}</span>
                <span class="hours">{{ hours.toFixed(1) }} 小时</span>
              </div>
            </div>
          </div>
          <el-empty v-if="!overtakeData.length" description="暂无数据" :image-size="60" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Iphone, Refresh, Monitor, Location, Timer, TrendCharts, Trophy, Delete, DocumentDelete } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../api'
import { useUserStore } from '../stores/user'

export default {
  name: 'AppRanking',
  setup() {
    const referenceAppIds = [
      { id: 'douyin', name: '抖音' },
      { id: 'tencent_video', name: '腾讯视频' },
      { id: 'qq_music', name: 'QQ音乐' },
      { id: 'netease_music', name: '网易云音乐' },
      { id: 'baidupan', name: '百度网盘' },
      { id: 'wechat', name: '微信' }
    ]

    const userStore = useUserStore()
    const apps = ref([])
    const appsWithRankings = ref([])
    const referenceApps = ref([])
    const topApps = ref({})
    const lastUpdated = ref('')
    const crawlLoading = ref(false)
    const schedulerStatus = ref({ running: false })
    const timeRange = ref('30d')
    const activeCountry = ref('cn')
    const chartRef = ref(null)
    let chart = null

    const selectAllGames = ref(false)
    const selectAllCountries = ref(false)
    const selectedGameIds = ref([])
    const selectedCountryCodes = ref([])
    const gamesLoading = ref(false)

    const selectedGames = computed(() => {
      return selectedGameIds.value.map(appId => {
        const app = apps.value.find(a => a.id === appId)
        return app?.name_cn || appId
      })
    })

    const selectedCountries = computed(() => {
      return selectedCountryCodes.value
    })

    const countries = {
      cn: '中国',
      jp: '日本',
      us: '美国',
      kr: '韩国'
    }

    const flags = {
      cn: '🇨🇳',
      jp: '🇯🇵',
      us: '🇺🇸',
      kr: '🇰🇷'
    }

    function getRankClass(rank) {
      if (!rank || rank > 100) return 'rank-low'
      if (rank <= 10) return 'rank-high'
      if (rank <= 50) return 'rank-mid'
      return 'rank-low'
    }

    async function loadCurrentRanking() {
      gamesLoading.value = true
      try {
        const data = await api.get('/ranking/current')
        apps.value = data.apps || []
        appsWithRankings.value = data.apps || []
        lastUpdated.value = data.last_updated || ''
        
        if (apps.value.length && selectedGameIds.value.length === 0) {
          if (apps.value[0]) {
            selectedGameIds.value = [apps.value[0].id]
          }
        }
        if (selectedCountryCodes.value.length === 0) {
          selectedCountryCodes.value = ['cn']
        }
        
        updateSelectAllStates()
      } catch (error) {
        console.error('加载排名数据失败:', error)
      } finally {
        gamesLoading.value = false
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

    async function loadReferenceApps() {
      try {
        const data = await api.get('/ranking/reference-apps')
        referenceApps.value = data.apps || []
      } catch (error) {
        console.error('加载参考应用数据失败:', error)
      }
    }

    const overtakeData = ref([])
    const overtakeTimeRange = ref('7d')

    async function loadOvertakeData() {
      try {
        const data = await api.get('/ranking/overtake-time', { params: { time_range: overtakeTimeRange.value } })
        overtakeData.value = data || []
      } catch (error) {
        console.error('加载超越时间数据失败:', error)
      }
    }

    function handleSelectAllGames(checked) {
      if (checked) {
        selectedGameIds.value = apps.value.map(app => app.id)
      } else {
        selectedGameIds.value = []
      }
      updateSelectAllStates()
      loadAndUpdateChart()
    }

    function handleSelectAllCountries(checked) {
      if (checked) {
        selectedCountryCodes.value = Object.keys(countries)
      } else {
        selectedCountryCodes.value = []
      }
      updateSelectAllStates()
      loadAndUpdateChart()
    }

    function handleGameSelectChange() {
      updateSelectAllStates()
      loadAndUpdateChart()
    }

    function handleCountrySelectChange() {
      updateSelectAllStates()
      loadAndUpdateChart()
    }

    function updateSelectAllStates() {
      if (apps.value.length === 0) {
        selectAllGames.value = false
      } else {
        selectAllGames.value = selectedGameIds.value.length === apps.value.length
      }
      
      const countryCodes = Object.keys(countries)
      if (countryCodes.length === 0) {
        selectAllCountries.value = false
      } else {
        selectAllCountries.value = selectedCountryCodes.value.length === countryCodes.length
      }
    }

    async function loadAndUpdateChart() {
      if (!selectedGameIds.value.length || selectedCountryCodes.value.length === 0 || !chartRef.value) return
      
      try {
        const days = timeRange.value === '24h' ? 1 : timeRange.value === '30d' ? 30 : 180
        
        const promises = selectedGameIds.value.map(appId => {
          return api.get(`/ranking/history/${appId}`, { params: { days } })
        })
        
        const historyDataList = await Promise.all(promises)
        updateChart(historyDataList)
      } catch (error) {
        console.error('加载历史数据失败:', error)
      }
    }

    function updateChart(dataList) {
      if (!chart) return
      
      const series = []
      const legendData = []
      const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#fee140']
      let colorIndex = 0
      
      dataList.forEach((data) => {
        const appName = data.app.name_cn
        
        selectedCountryCodes.value.forEach(country => {
          const records = data.history[country]
          if (records && records.length > 0) {
            const seriesName = `${appName} - ${countries[country]}`
            legendData.push(seriesName)
            
            const sampledData = sampleData(records, timeRange.value)
            const chartData = sampledData.map(r => [r.recorded_at, r.rank])
            
            series.push({
              name: seriesName,
              type: 'line',
              data: chartData,
              smooth: true,
              symbol: 'none',
              lineStyle: {
                width: 2,
                color: colors[colorIndex % colors.length]
              }
            })
            
            colorIndex++
          }
        })
      })
      
      const referenceColors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dfe6e9']
      let refColorIndex = 0
      
      selectedCountryCodes.value.forEach(country => {
        referenceApps.value.forEach(app => {
          const rank = app.rankings[country]?.rank
          if (rank && rank <= 100) {
            const seriesName = `${app.name} - ${countries[country]}`
            legendData.push(seriesName)
            
            series.push({
              name: seriesName,
              type: 'line',
              data: [[dataList[0]?.history[country]?.[0]?.recorded_at || new Date().toISOString(), rank], [dataList[0]?.history[country]?.[dataList[0].history[country].length - 1]?.recorded_at || new Date().toISOString(), rank]],
              lineStyle: {
                width: 2,
                color: referenceColors[refColorIndex % referenceColors.length],
                type: 'dashed'
              },
              symbol: 'none',
              tooltip: {
                formatter: `${app.name}: ${rank}`
              }
            })
            
            refColorIndex++
          }
        })
      })
      
      const option = {
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 15, 26, 0.95)',
          borderColor: 'rgba(102, 126, 234, 0.3)',
          textStyle: { color: '#fff' },
          formatter: function(params) {
            let result = params[0].axisValue + '<br/>'
            params.forEach(function(item) {
              result += item.marker + ' ' + item.seriesName + ': ' + (item.value[1] > 100 ? '>100' : item.value[1]) + '<br/>'
            })
            return result
          }
        },
        legend: {
          data: legendData,
          bottom: 0,
          textStyle: { color: '#a0a0b0', fontSize: 11 },
          type: 'scroll'
        },
        grid: {
          left: '3%',
          right: '4%',
          top: '3%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'time',
          axisLine: { lineStyle: { color: '#3a3a4a' } },
          axisLabel: {
            color: '#a0a0b0',
            fontSize: 11,
            formatter: function(value) {
              const date = new Date(value)
              if (timeRange.value === '24h') {
                return date.getHours() + ':' + date.getMinutes().toString().padStart(2, '0')
              }
              return (date.getMonth() + 1) + '-' + date.getDate()
            }
          }
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
        series: series,
        animation: false
      }
      
      chart.setOption(option, true)
    }

    function sampleData(records, range) {
      if (!records || records.length === 0) return []
      
      let maxPoints = 0
      switch (range) {
        case '24h':
          maxPoints = 100
          break
        case '30d':
          maxPoints = 200
          break
        case '180d':
          maxPoints = 300
          break
        default:
          maxPoints = 200
      }
      
      if (records.length <= maxPoints) return records
      
      const step = Math.ceil(records.length / maxPoints)
      const sampled = []
      for (let i = 0; i < records.length; i += step) {
        sampled.push(records[i])
      }
      
      if (sampled[sampled.length - 1] !== records[records.length - 1]) {
        sampled[sampled.length - 1] = records[records.length - 1]
      }
      
      return sampled
    }

    function initChart() {
      nextTick(() => {
        if (chartRef.value) {
          chart = echarts.init(chartRef.value)
          loadAndUpdateChart()
        }
      })
    }

    function handleResize() {
      if (chart) {
        chart.resize()
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
          loadAndUpdateChart()
        }, 2000)
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '爬取失败')
      } finally {
        crawlLoading.value = false
      }
    }

    async function deleteApp(appId) {
      try {
        await ElMessageBox.confirm('确定要删除这个游戏吗？', '确认删除', {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await api.delete(`/ranking/apps/${appId}`)
        ElMessage.success('删除成功')
        loadCurrentRanking()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error(error.response?.data?.detail || '删除失败')
        }
      }
    }

    async function loadAllData() {
      await Promise.all([loadCurrentRanking(), loadTopApps(), loadSchedulerStatus(), loadReferenceApps(), loadOvertakeData()])
      loadAndUpdateChart()
    }

    let refreshInterval = null

    function startAutoRefresh() {
      refreshInterval = window.setInterval(() => {
        loadAllData()
      }, 5 * 60 * 1000)
    }

    function stopAutoRefresh() {
      if (refreshInterval) {
        clearInterval(refreshInterval)
        refreshInterval = null
      }
    }

    onMounted(() => {
      initChart()
      loadAllData()
      startAutoRefresh()
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      if (chart) {
        chart.dispose()
      }
      stopAutoRefresh()
      window.removeEventListener('resize', handleResize)
    })

    return {
      referenceAppIds,
      userStore,
      apps,
      appsWithRankings,
      referenceApps,
      topApps,
      lastUpdated,
      crawlLoading,
      schedulerStatus,
      timeRange,
      activeCountry,
      chartRef,
      selectAllGames,
      selectAllCountries,
      selectedGameIds,
      selectedCountryCodes,
      gamesLoading,
      selectedGames,
      selectedCountries,
      countries,
      flags,
      getRankClass,
      loadCurrentRanking,
      loadTopApps,
      loadSchedulerStatus,
      loadReferenceApps,
      overtakeData,
      overtakeTimeRange,
      loadOvertakeData,
      handleSelectAllGames,
      handleSelectAllCountries,
      handleGameSelectChange,
      handleCountrySelectChange,
      updateSelectAllStates,
      loadAndUpdateChart,
      updateChart,
      sampleData,
      initChart,
      handleResize,
      crawlData,
      deleteApp,
      loadAllData,
      startAutoRefresh,
      stopAutoRefresh
    }
  }
}
</script>

<style scoped>
:root {
  --bg-opacity: 1;
  --panel-opacity: 0.95;
  --blur-amount: 0px;
  --border-radius: 12px;
  --shadow-intensity: 0.2;
  --font-size-scale: 1.1;
  --chart-height-scale: 1.2;
  --primary-color: #3b82f6;
  --accent-color-1: #3b82f6;
  --accent-color-2: #ec4899;
  --accent-color-3: #10b981;
  --accent-color-4: #f59e0b;
  --accent-color-5: #8b5cf6;
  --accent-color-6: #06b6d4;
  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --border-color: rgba(59, 130, 246, 0.2);
}

.app-ranking {
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, var(--bg-primary) 0%, #131c31 100%);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: rgba(30, 41, 59, var(--panel-opacity));
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, calc(0.3 * var(--shadow-intensity)));
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: calc(22px * var(--font-size-scale));
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: 0.5px;
}

.header-left h1 .el-icon {
  color: var(--primary-color);
  font-size: calc(24px * var(--font-size-scale));
}

.update-time {
  font-size: calc(14px * var(--font-size-scale));
  color: var(--text-muted);
  font-family: 'SF Mono', 'Monaco', monospace;
  background: rgba(59, 130, 246, 0.1);
  padding: 4px 10px;
  border-radius: 12px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.header-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.stats-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(30, 41, 59, var(--panel-opacity));
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
  flex: 1;
  min-width: 200px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, calc(0.15 * var(--shadow-intensity)));
}

.stat-item:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
}

.stat-item .el-icon {
  font-size: calc(24px * var(--font-size-scale));
  color: var(--primary-color);
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  display: block;
  font-size: calc(24px * var(--font-size-scale));
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'SF Mono', 'Monaco', monospace;
  line-height: 1.2;
}

.stat-label {
  display: block;
  font-size: calc(14px * var(--font-size-scale));
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-top: 4px;
}

.stat-item.running .el-icon {
  color: #22c55e;
}

.stat-item.stopped .el-icon {
  color: #ef4444;
}

.ranking-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.ranking-card {
  background: rgba(30, 41, 59, var(--panel-opacity));
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, calc(0.2 * var(--shadow-intensity)));
}

.ranking-card:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, calc(0.3 * var(--shadow-intensity)));
  border-color: var(--primary-color);
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(180deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
}

.card-header h3 {
  font-size: calc(16px * var(--font-size-scale));
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-header .en-name {
  font-size: calc(12px * var(--font-size-scale));
  color: var(--text-muted);
}

.card-body {
  padding: 16px 20px;
}

.country-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.country-row .flag {
  font-size: calc(20px * var(--font-size-scale));
  flex-shrink: 0;
}

.country-row .country-name {
  flex: 1;
  font-size: calc(14px * var(--font-size-scale));
  color: var(--text-secondary);
}

.country-row .rank {
  font-size: calc(18px * var(--font-size-scale));
  font-weight: 700;
  min-width: 60px;
  text-align: right;
  font-family: 'SF Mono', 'Monaco', monospace;
  padding: 4px 12px;
  border-radius: 16px;
}

.rank-high {
  background: rgba(34, 197, 94, 0.2);
  color: #86efac;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.rank-mid {
  background: rgba(245, 158, 11, 0.2);
  color: #fcd34d;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.rank-low {
  background: rgba(148, 163, 184, 0.2);
  color: #cbd5e1;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.panel {
  background: rgba(30, 41, 59, var(--panel-opacity));
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, calc(0.2 * var(--shadow-intensity)));
}

.panel:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, calc(0.3 * var(--shadow-intensity)));
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(180deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
}

.panel-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: calc(16px * var(--font-size-scale));
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: 0.3px;
}

.panel-header h3 .el-icon {
  color: var(--primary-color);
  font-size: calc(18px * var(--font-size-scale));
}

.time-range-select {
  min-width: 120px;
}

.filter-section {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-item {
  flex: 1;
  min-width: 250px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  display: block;
  font-size: calc(14px * var(--font-size-scale));
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-select {
  width: 100%;
}

.chart-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.info-tag {
  font-size: calc(13px * var(--font-size-scale));
  padding: 4px 12px;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 16px;
  color: var(--text-secondary);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.info-tag.country {
  background: rgba(34, 197, 94, 0.2);
  border-color: rgba(34, 197, 94, 0.3);
}

.chart-area {
  height: 400px;
  padding: 20px;
}

.country-tabs {
  padding: 0 20px;
}

.country-tabs :deep(.el-tabs__item) {
  color: var(--text-muted);
  font-size: calc(14px * var(--font-size-scale));
  padding: 12px 16px;
}

.country-tabs :deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
  font-weight: 600;
}

.country-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--primary-color);
  height: 3px;
}

.top-list {
  padding: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.top-list::-webkit-scrollbar {
  width: 6px;
}

.top-list::-webkit-scrollbar-track {
  background: rgba(51, 65, 85, 0.5);
  border-radius: 3px;
}

.top-list::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.5);
  border-radius: 3px;
}

.top-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--border-radius);
  margin-bottom: 10px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid var(--border-color);
  transition: all 0.2s ease;
}

.top-item:hover {
  background: rgba(59, 130, 246, 0.1);
  transform: translateX(4px);
  border-color: var(--primary-color);
}

.top-item .rank {
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

.top-item .rank.r1 {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  box-shadow: 0 0 12px rgba(251, 191, 36, 0.4);
}

.top-item .rank.r2 {
  background: linear-gradient(135deg, #cbd5e1, #94a3b8);
  box-shadow: 0 0 12px rgba(148, 163, 184, 0.35);
}

.top-item .rank.r3 {
  background: linear-gradient(135deg, #fb923c, #ea580c);
  box-shadow: 0 0 12px rgba(251, 146, 60, 0.35);
}

.top-item .app-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid var(--border-color);
  flex-shrink: 0;
}

.top-item .app-info {
  flex: 1;
  min-width: 0;
}

.top-item .app-name {
  display: block;
  font-size: calc(14px * var(--font-size-scale));
  color: var(--text-primary);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-item .developer {
  display: block;
  font-size: calc(12px * var(--font-size-scale));
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.overtake-list {
  padding: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.overtake-list::-webkit-scrollbar {
  width: 6px;
}

.overtake-list::-webkit-scrollbar-track {
  background: rgba(51, 65, 85, 0.5);
  border-radius: 3px;
}

.overtake-list::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.5);
  border-radius: 3px;
}

.overtake-item {
  padding: 16px;
  border-radius: var(--border-radius);
  margin-bottom: 12px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid var(--border-color);
  transition: all 0.2s ease;
}

.overtake-item:hover {
  border-color: var(--primary-color);
  background: rgba(59, 130, 246, 0.1);
}

.overtake-item h4 {
  font-size: calc(16px * var(--font-size-scale));
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.overtake-details {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.overtake-detail {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(59, 130, 246, 0.15);
  border-radius: 16px;
  font-size: calc(13px * var(--font-size-scale));
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.overtake-detail .app-name {
  color: var(--text-secondary);
  font-weight: 500;
}

.overtake-detail .hours {
  font-weight: 700;
  color: #22c55e;
  font-family: 'SF Mono', 'Monaco', monospace;
}

/* Element Plus 自定义样式 */
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

:deep(.el-checkbox__label) {
  color: var(--text-secondary);
  font-size: calc(14px * var(--font-size-scale));
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

:deep(.el-checkbox__inner) {
  border-color: var(--border-color);
}

:deep(.el-checkbox__inner:hover) {
  border-color: var(--primary-color);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .ranking-cards {
    grid-template-columns: 1fr;
  }
  
  .filter-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .filter-item {
    min-width: auto;
  }
}

@media (max-width: 768px) {
  .app-ranking {
    padding: 12px;
  }
  
  .stats-row {
    flex-direction: column;
  }
  
  .stat-item {
    min-width: auto;
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
  
  .chart-area {
    height: 300px;
  }
  
  .filter-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .filter-item {
    min-width: auto;
  }
}
</style>