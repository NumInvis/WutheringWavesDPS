<template>
  <div class="page-container" v-if="character">
    <!-- 角色信息头部 -->
    <div class="char-header">
      <div class="char-avatar-large">
        {{ character.name.charAt(0) }}
      </div>
      <div class="char-header-info">
        <h2>{{ character.name }}</h2>
        <div class="char-meta">
          <el-tag :type="character.gender === '女' ? 'danger' : 'primary'" size="large">
            {{ character.gender }}
          </el-tag>
          <el-tag type="info" size="large">{{ character.body_type }}</el-tag>
          <el-tag v-if="character.element" type="warning" size="large">{{ character.element }}</el-tag>
          <el-tag v-if="character.weapon_type" type="success" size="large">{{ character.weapon_type }}</el-tag>
        </div>
        <p class="action-total">共 {{ actions.length }} 个动作</p>
      </div>
    </div>
    
    <!-- 动作类型分布 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <span>动作类型分布</span>
        </div>
      </template>
      <div class="action-type-tags">
        <div
          v-for="(count, type) in character.action_stats"
          :key="type"
          class="type-tag-item"
          :class="{ active: selectedType === type }"
          @click="selectType(type)"
        >
          <span class="type-name">{{ type }}</span>
          <span class="type-count">{{ count }}</span>
        </div>
      </div>
    </el-card>
    
    <!-- 动作列表 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <span>动作列表</span>
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button label="table">表格</el-radio-button>
            <el-radio-button label="card">卡片</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      
      <!-- 表格视图 -->
      <el-table
        v-if="viewMode === 'table'"
        :data="filteredActions"
        stripe
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="action_name" label="动作名称" min-width="150" />
        <el-table-column prop="action_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.action_type || '未知' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_frame" label="发生帧" width="80" sortable />
        <el-table-column prop="duration_frame" label="持续帧" width="80" sortable />
        <el-table-column prop="self_hitstop" label="顿帧-自" width="80" />
        <el-table-column prop="enemy_hitstop" label="顿帧-敌" width="80" />
        <el-table-column prop="poise_damage" label="削韧" width="80" sortable />
        <el-table-column prop="concerto_recovery" label="协奏" width="80" sortable />
        <el-table-column label="特性" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.can_parry" size="small" type="success">弹</el-tag>
            <el-tag v-if="row.can_detach" size="small" type="warning">脱</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 卡片视图 -->
      <el-row v-else :gutter="15">
        <el-col
          v-for="action in filteredActions"
          :key="action.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
        >
          <el-card class="action-card" @click="showDetail(action)">
            <div class="action-card-header">
              <h4>{{ action.action_name }}</h4>
              <el-tag size="small">{{ action.action_type || '未知' }}</el-tag>
            </div>
            <div class="action-card-body">
              <div class="stat-row">
                <span>发生帧:</span>
                <strong>{{ action.start_frame || '-' }}</strong>
              </div>
              <div class="stat-row">
                <span>持续帧:</span>
                <strong>{{ action.duration_frame || '-' }}</strong>
              </div>
              <div class="stat-row">
                <span>削韧:</span>
                <strong>{{ action.poise_damage || '-' }}</strong>
              </div>
              <div class="stat-row">
                <span>协奏:</span>
                <strong>{{ action.concerto_recovery || '-' }}</strong>
              </div>
            </div>
            <div class="action-card-footer">
              <el-tag v-if="action.can_parry" size="small" type="success">可弹刀</el-tag>
              <el-tag v-if="action.can_detach" size="small" type="warning">可脱手</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-empty v-if="filteredActions.length === 0" description="暂无动作数据" />
    </el-card>
    
    <!-- 动作详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="动作详情"
      width="600px"
    >
      <div v-if="selectedAction" class="action-detail">
        <h3>{{ selectedAction.action_name }}</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类型">{{ selectedAction.action_type || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="位置状态">{{ selectedAction.position_state || '-' }}</el-descriptions-item>
          <el-descriptions-item label="发生帧">{{ selectedAction.start_frame || '-' }}</el-descriptions-item>
          <el-descriptions-item label="持续帧">{{ selectedAction.duration_frame || '-' }}</el-descriptions-item>
          <el-descriptions-item label="动作结束帧">{{ selectedAction.end_frame || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态转换时间">{{ selectedAction.state_transition_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="顿帧-自">{{ selectedAction.self_hitstop || '-' }}</el-descriptions-item>
          <el-descriptions-item label="顿帧-敌">{{ selectedAction.enemy_hitstop || '-' }}</el-descriptions-item>
          <el-descriptions-item label="无敌启动帧">{{ selectedAction.invincible_start || '-' }}</el-descriptions-item>
          <el-descriptions-item label="无敌持续帧">{{ selectedAction.invincible_duration || '-' }}</el-descriptions-item>
          <el-descriptions-item label="削韧值">{{ selectedAction.poise_damage || '-' }}</el-descriptions-item>
          <el-descriptions-item label="协奏回收">{{ selectedAction.concerto_recovery || '-' }}</el-descriptions-item>
          <el-descriptions-item label="核心回收">{{ selectedAction.core_recovery || '-' }}</el-descriptions-item>
          <el-descriptions-item label="受击韧性系数">{{ selectedAction.hit_resistance_factor || '-' }}</el-descriptions-item>
          <el-descriptions-item label="中断优先级">{{ selectedAction.interrupt_priority || '-' }}</el-descriptions-item>
          <el-descriptions-item label="优先级改变">{{ selectedAction.priority_change || '-' }}</el-descriptions-item>
          <el-descriptions-item label="派生帧">{{ selectedAction.derive_frame || '-' }}</el-descriptions-item>
          <el-descriptions-item label="派生持续帧">{{ selectedAction.derive_duration || '-' }}</el-descriptions-item>
          <el-descriptions-item label="可弹刀">{{ selectedAction.can_parry ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="可脱手">{{ selectedAction.can_detach ? '是' : '否' }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="selectedAction.notes" class="action-notes">
          <h4>备注</h4>
          <p>{{ selectedAction.notes }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
  
  <el-empty v-else-if="!loading" description="角色不存在" />
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useStore } from 'vuex'
import { useRoute } from 'vue-router'
import axios from 'axios'

export default {
  name: 'CharacterDetail',
  setup() {
    const store = useStore()
    const route = useRoute()
    
    const character = ref(null)
    const actions = ref([])
    const loading = ref(false)
    const selectedType = ref('')
    const viewMode = ref('table')
    const detailVisible = ref(false)
    const selectedAction = ref(null)
    
    const charId = computed(() => route.params.id)
    
    const filteredActions = computed(() => {
      if (!selectedType.value) return actions.value
      return actions.value.filter(a => a.action_type === selectedType.value)
    })
    
    onMounted(() => {
      fetchCharacterDetail()
      fetchActions()
    })
    
    const fetchCharacterDetail = async () => {
      try {
        const response = await axios.get(`/api/characters/${charId.value}`)
        if (response.data.success) {
          character.value = response.data.data
        }
      } catch (error) {
        console.error('获取角色详情失败:', error)
      }
    }
    
    const fetchActions = async () => {
      loading.value = true
      try {
        const response = await axios.get(`/api/characters/${charId.value}/actions`, {
          params: { per_page: 1000 }
        })
        if (response.data.success) {
          actions.value = response.data.data
        }
      } catch (error) {
        console.error('获取动作列表失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    const selectType = (type) => {
      selectedType.value = selectedType.value === type ? '' : type
    }
    
    const showDetail = (action) => {
      selectedAction.value = action
      detailVisible.value = true
    }
    
    return {
      character,
      actions,
      loading,
      selectedType,
      viewMode,
      detailVisible,
      selectedAction,
      filteredActions,
      selectType,
      showDetail
    }
  }
}
</script>

<style scoped>
.char-header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: #fff;
}

.char-avatar-large {
  width: 100px;
  height: 100px;
  background: rgba(255,255,255,0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  font-weight: bold;
  margin-right: 20px;
}

.char-header-info h2 {
  margin: 0 0 10px 0;
  font-size: 28px;
}

.char-meta {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.action-total {
  margin: 0;
  opacity: 0.9;
}

.section-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.action-type-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.type-tag-item {
  display: flex;
  align-items: center;
  padding: 8px 15px;
  background: #f5f7fa;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.type-tag-item:hover,
.type-tag-item.active {
  background: #409eff;
  color: #fff;
}

.type-name {
  margin-right: 8px;
}

.type-count {
  background: rgba(0,0,0,0.1);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.action-card {
  margin-bottom: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.action-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.action-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.action-card-header h4 {
  margin: 0;
  font-size: 14px;
}

.action-card-body {
  margin-bottom: 10px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px solid #eee;
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row span {
  color: #909399;
  font-size: 13px;
}

.action-card-footer {
  display: flex;
  gap: 5px;
}

.action-detail h3 {
  margin: 0 0 20px 0;
  text-align: center;
}

.action-notes {
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.action-notes h4 {
  margin: 0 0 10px 0;
}

.action-notes p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}
</style>
