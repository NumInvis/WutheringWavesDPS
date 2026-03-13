<template>
  <div class="page-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card blue">
          <el-icon size="40"><UserFilled /></el-icon>
          <div class="stat-info">
            <h4>角色总数</h4>
            <p class="number">{{ stats?.total_characters || 0 }}</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card purple">
          <el-icon size="40"><Collection /></el-icon>
          <div class="stat-info">
            <h4>动作总数</h4>
            <p class="number">{{ stats?.total_actions || 0 }}</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card green">
          <el-icon size="40"><MagicStick /></el-icon>
          <div class="stat-info">
            <h4>声骸总数</h4>
            <p class="number">{{ stats?.total_echoes || 0 }}</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card orange">
          <el-icon size="40"><DataAnalysis /></el-icon>
          <div class="stat-info">
            <h4>数据版本</h4>
            <p class="number">v1.0</p>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 分布图表 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>性别分布</span>
            </div>
          </template>
          <div ref="genderChart" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>体型分布</span>
            </div>
          </template>
          <div ref="bodyChart" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 动作类型分布 -->
    <el-row class="charts-row">
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>动作类型分布</span>
            </div>
          </template>
          <div ref="actionTypeChart" class="chart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 快速入口 -->
    <el-row :gutter="20" class="quick-links">
      <el-col :span="8">
        <el-card class="link-card" @click="$router.push('/characters')">
          <el-icon size="48" color="#409eff"><UserFilled /></el-icon>
          <h3>角色数据库</h3>
          <p>查看所有角色的详细动作数据</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="link-card" @click="$router.push('/actions')">
          <el-icon size="48" color="#67c23a"><Collection /></el-icon>
          <h3>动作查询</h3>
          <p>高级筛选和对比动作数据</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="link-card" @click="$router.push('/echoes')">
          <el-icon size="48" color="#e6a23c"><MagicStick /></el-icon>
          <h3>声骸数据库</h3>
          <p>查看所有声骸的详细信息</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useStore } from 'vuex'
import * as echarts from 'echarts'

export default {
  name: 'Home',
  setup() {
    const store = useStore()
    const genderChart = ref(null)
    const bodyChart = ref(null)
    const actionTypeChart = ref(null)
    
    let genderChartInstance = null
    let bodyChartInstance = null
    let actionTypeChartInstance = null
    
    const stats = computed(() => store.state.stats)
    
    onMounted(async () => {
      await store.dispatch('fetchStats')
      await store.dispatch('fetchFilters')
      
      initCharts()
    })
    
    onUnmounted(() => {
      genderChartInstance?.dispose()
      bodyChartInstance?.dispose()
      actionTypeChartInstance?.dispose()
    })
    
    const initCharts = () => {
      if (!stats.value) return
      
      // 性别分布饼图
      if (genderChart.value) {
        genderChartInstance = echarts.init(genderChart.value)
        genderChartInstance.setOption({
          tooltip: { trigger: 'item' },
          legend: { bottom: '5%' },
          series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
            label: { show: false },
            emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
            data: Object.entries(stats.value.gender_distribution || {}).map(([name, value]) => ({
              name, value
            }))
          }]
        })
      }
      
      // 体型分布饼图
      if (bodyChart.value) {
        bodyChartInstance = echarts.init(bodyChart.value)
        bodyChartInstance.setOption({
          tooltip: { trigger: 'item' },
          legend: { bottom: '5%' },
          series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
            label: { show: false },
            emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
            data: Object.entries(stats.value.body_type_distribution || {}).map(([name, value]) => ({
              name, value
            }))
          }]
        })
      }
      
      // 动作类型柱状图
      if (actionTypeChart.value) {
        actionTypeChartInstance = echarts.init(actionTypeChart.value)
        const actionTypes = Object.entries(stats.value.action_type_distribution || {})
        actionTypeChartInstance.setOption({
          tooltip: { trigger: 'axis' },
          xAxis: {
            type: 'category',
            data: actionTypes.map(([name]) => name),
            axisLabel: { rotate: 30 }
          },
          yAxis: { type: 'value' },
          series: [{
            data: actionTypes.map(([, value]) => value),
            type: 'bar',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#83bff6' },
                { offset: 0.5, color: '#188df0' },
                { offset: 1, color: '#188df0' }
              ])
            }
          }]
        })
      }
    }
    
    return {
      stats,
      genderChart,
      bodyChart,
      actionTypeChart
    }
  }
}
</script>

<style scoped>
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 8px;
  color: #fff;
}

.stat-card.blue { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stat-card.purple { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.stat-card.green { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.stat-card.orange { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }

.stat-card .el-icon {
  margin-right: 15px;
}

.stat-info h4 {
  margin: 0 0 5px 0;
  font-size: 14px;
  opacity: 0.9;
}

.stat-info .number {
  margin: 0;
  font-size: 28px;
  font-weight: bold;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 350px;
}

.card-header {
  font-weight: bold;
}

.chart {
  height: 250px;
}

.quick-links {
  margin-top: 20px;
}

.link-card {
  text-align: center;
  padding: 30px;
  cursor: pointer;
  transition: all 0.3s;
}

.link-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.link-card h3 {
  margin: 15px 0 10px 0;
  color: #303133;
}

.link-card p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}
</style>
