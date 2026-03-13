<template>
  <div class="page-container">
    <div class="page-header">
      <h3>声骸数据库</h3>
      <p>共 {{ total }} 个声骸</p>
    </div>
    
    <!-- 搜索栏 -->
    <div class="filter-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索声骸名称或动作..."
        clearable
        @keyup.enter="handleSearch"
        style="width: 300px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <el-select v-model="skillType" placeholder="技能类型" clearable @change="handleSearch">
        <el-option label="召唤" value="召唤" />
        <el-option label="变身" value="变身" />
      </el-select>
      
      <el-button type="primary" @click="handleSearch">搜索</el-button>
      <el-button @click="resetSearch">重置</el-button>
    </div>
    
    <!-- 声骸列表 -->
    <el-row :gutter="20">
      <el-col
        v-for="echo in echoes"
        :key="echo.id"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
      >
        <el-card class="echo-card" @click="showDetail(echo)">
          <div class="echo-header">
            <h4 class="echo-name">{{ echo.name }}</h4>
            <el-tag v-if="echo.skill_type" size="small" type="primary">{{ echo.skill_type }}</el-tag>
          </div>
          <p class="echo-action">{{ echo.action_name }}</p>
          <div class="echo-stats">
            <div class="stat-item">
              <span class="stat-label">冷却</span>
              <span class="stat-value">{{ echo.cooldown || '-' }}s</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">削韧</span>
              <span class="stat-value">{{ echo.poise_damage || '-' }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">协奏</span>
              <span class="stat-value">{{ echo.concerto_recovery || '-' }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 空状态 -->
    <el-empty v-if="echoes.length === 0 && !loading" description="暂无数据" />
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="5" animated />
    </div>
    
    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="声骸详情"
      width="600px"
    >
      <div v-if="selectedEcho" class="echo-detail">
        <h3>{{ selectedEcho.name }}</h3>
        <p class="echo-action-name">{{ selectedEcho.action_name }}</p>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="技能类型">{{ selectedEcho.skill_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="冷却时间">{{ selectedEcho.cooldown ? selectedEcho.cooldown + 's' : '-' }}</el-descriptions-item>
          <el-descriptions-item label="发生帧">{{ selectedEcho.start_frame || '-' }}</el-descriptions-item>
          <el-descriptions-item label="持续帧">{{ selectedEcho.duration_frame || '-' }}</el-descriptions-item>
          <el-descriptions-item label="动作结束帧">{{ selectedEcho.end_frame || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态转换时间">{{ selectedEcho.state_transition_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="顿帧-自">{{ selectedEcho.self_hitstop || '-' }}</el-descriptions-item>
          <el-descriptions-item label="顿帧-敌">{{ selectedEcho.enemy_hitstop || '-' }}</el-descriptions-item>
          <el-descriptions-item label="削韧值">{{ selectedEcho.poise_damage || '-' }}</el-descriptions-item>
          <el-descriptions-item label="协奏回收">{{ selectedEcho.concerto_recovery || '-' }}</el-descriptions-item>
          <el-descriptions-item label="核心回收">{{ selectedEcho.core_recovery || '-' }}</el-descriptions-item>
          <el-descriptions-item label="可弹刀">{{ selectedEcho.can_parry ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="可脱手">{{ selectedEcho.can_detach ? '是' : '否' }}</el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedEcho.description" class="echo-description">
          <h4>技能说明</h4>
          <p>{{ selectedEcho.description }}</p>
        </div>
        
        <div v-if="selectedEcho.notes" class="echo-notes">
          <h4>备注</h4>
          <p>{{ selectedEcho.notes }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'Echoes',
  setup() {
    const store = useStore()
    
    const searchQuery = ref('')
    const skillType = ref('')
    const detailVisible = ref(false)
    const selectedEcho = ref(null)
    
    const echoes = computed(() => store.state.echoes)
    const loading = computed(() => store.state.loading)
    const total = computed(() => echoes.value.length)
    
    onMounted(() => {
      store.dispatch('fetchEchoes')
    })
    
    const handleSearch = () => {
      const params = {}
      if (searchQuery.value) params.search = searchQuery.value
      if (skillType.value) params.skill_type = skillType.value
      store.dispatch('fetchEchoes', params)
    }
    
    const resetSearch = () => {
      searchQuery.value = ''
      skillType.value = ''
      store.dispatch('fetchEchoes')
    }
    
    const showDetail = (echo) => {
      selectedEcho.value = echo
      detailVisible.value = true
    }
    
    return {
      searchQuery,
      skillType,
      detailVisible,
      selectedEcho,
      echoes,
      loading,
      total,
      handleSearch,
      resetSearch,
      showDetail
    }
  }
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
  flex-wrap: wrap;
}

.echo-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.echo-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.echo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.echo-name {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.echo-action {
  margin: 0 0 15px 0;
  color: #606266;
  font-size: 14px;
}

.echo-stats {
  display: flex;
  justify-content: space-around;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-value {
  display: block;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.loading-wrapper {
  padding: 20px;
}

.echo-detail h3 {
  margin: 0 0 5px 0;
  text-align: center;
}

.echo-action-name {
  text-align: center;
  color: #606266;
  margin-bottom: 20px;
}

.echo-description,
.echo-notes {
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.echo-description h4,
.echo-notes h4 {
  margin: 0 0 10px 0;
}

.echo-description p,
.echo-notes p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}
</style>
