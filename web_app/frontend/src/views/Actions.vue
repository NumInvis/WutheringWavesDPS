<template>
  <div class="page-container">
    <div class="page-header">
      <h3>动作查询</h3>
      <p>高级筛选和对比动作数据</p>
    </div>
    
    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :model="filters" label-position="top">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="角色">
              <el-select
                v-model="filters.character_id"
                placeholder="选择角色"
                clearable
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="char in characterOptions"
                  :key="char.id"
                  :label="char.name"
                  :value="char.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="动作类型">
              <el-select v-model="filters.type" placeholder="选择类型" clearable style="width: 100%">
                <el-option label="常态攻击" value="常态攻击" />
                <el-option label="共鸣技能" value="共鸣技能" />
                <el-option label="共鸣回路" value="共鸣回路" />
                <el-option label="共鸣解放" value="共鸣解放" />
                <el-option label="变奏技能" value="变奏技能" />
                <el-option label="延奏技能" value="延奏技能" />
                <el-option label="闪避" value="闪避" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="搜索">
              <el-input
                v-model="filters.search"
                placeholder="动作名称/备注"
                clearable
                @keyup.enter="handleSearch"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="位置状态">
              <el-select v-model="filters.position_state" placeholder="选择状态" clearable style="width: 100%">
                <el-option label="地面" value="地面" />
                <el-option label="空中" value="空中" />
                <el-option label="地转空" value="地转空" />
                <el-option label="空转地" value="空转地" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="发生帧范围">
              <el-input-number v-model="filters.min_start_frame" :min="0" placeholder="最小" style="width: 48%" />
              <span style="margin: 0 2%">-</span>
              <el-input-number v-model="filters.max_start_frame" :min="0" placeholder="最大" style="width: 48%" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="削韧值范围">
              <el-input-number v-model="filters.min_poise" :min="0" placeholder="最小" style="width: 48%" />
              <span style="margin: 0 2%">-</span>
              <el-input-number v-model="filters.max_poise" :min="0" placeholder="最大" style="width: 48%" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="特性">
              <el-checkbox v-model="filters.can_parry">可弹刀</el-checkbox>
              <el-checkbox v-model="filters.can_detach">可脱手</el-checkbox>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="操作">
              <el-button type="primary" @click="handleSearch">
                <el-icon><Search /></el-icon> 查询
              </el-button>
              <el-button @click="resetFilters">重置</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
    
    <!-- 批量操作 -->
    <div class="batch-actions">
      <el-button
        type="primary"
        :disabled="selectedActions.length < 2"
        @click="showCompare"
      >
        对比选中 ({{ selectedActions.length }})
      </el-button>
      <el-button @click="clearSelection">清空选择</el-button>
    </div>
    
    <!-- 动作表格 -->
    <el-card>
      <el-table
        :data="actions"
        stripe
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="character_name" label="角色" width="100" />
        <el-table-column prop="action_name" label="动作名称" min-width="150" />
        <el-table-column prop="action_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.action_type || '未知' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_frame" label="发生帧" width="80" sortable />
        <el-table-column prop="duration_frame" label="持续帧" width="80" />
        <el-table-column prop="self_hitstop" label="顿帧-自" width="80" />
        <el-table-column prop="enemy_hitstop" label="顿帧-敌" width="80" />
        <el-table-column prop="poise_damage" label="削韧" width="80" sortable />
        <el-table-column prop="concerto_recovery" label="协奏" width="80" sortable />
        <el-table-column label="特性" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.can_parry" size="small" type="success">弹</el-tag>
            <el-tag v-if="row.can_detach" size="small" type="warning">脱</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
    
    <!-- 对比弹窗 -->
    <el-dialog
      v-model="compareVisible"
      title="动作对比"
      width="900px"
    >
      <el-table :data="compareActions" border>
        <el-table-column prop="attr" label="属性" width="120" />
        <el-table-column
          v-for="action in selectedActions"
          :key="action.id"
          :label="action.action_name"
        >
          <template #default="{ row }">
            {{ row[action.id] || '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, reactive } from 'vue'
import axios from 'axios'

export default {
  name: 'Actions',
  setup() {
    const actions = ref([])
    const loading = ref(false)
    const characterOptions = ref([])
    const selectedActions = ref([])
    const compareVisible = ref(false)
    const compareActions = ref([])
    
    const filters = reactive({
      character_id: null,
      type: '',
      search: '',
      position_state: '',
      min_start_frame: null,
      max_start_frame: null,
      min_poise: null,
      max_poise: null,
      can_parry: false,
      can_detach: false
    })
    
    const pagination = reactive({
      page: 1,
      per_page: 50,
      total: 0
    })
    
    onMounted(() => {
      fetchCharacters()
      fetchActions()
    })
    
    const fetchCharacters = async () => {
      try {
        const response = await axios.get('/api/characters')
        if (response.data.success) {
          characterOptions.value = response.data.data
        }
      } catch (error) {
        console.error('获取角色列表失败:', error)
      }
    }
    
    const fetchActions = async () => {
      loading.value = true
      try {
        const params = {
          page: pagination.page,
          per_page: pagination.per_page
        }
        
        if (filters.character_id) params.character_id = filters.character_id
        if (filters.type) params.type = filters.type
        if (filters.search) params.search = filters.search
        if (filters.position_state) params.position_state = filters.position_state
        if (filters.min_start_frame !== null) params.min_start_frame = filters.min_start_frame
        if (filters.max_start_frame !== null) params.max_start_frame = filters.max_start_frame
        if (filters.min_poise !== null) params.min_poise = filters.min_poise
        if (filters.max_poise !== null) params.max_poise = filters.max_poise
        if (filters.can_parry) params.can_parry = 'true'
        if (filters.can_detach) params.can_detach = 'true'
        
        const response = await axios.get('/api/actions', { params })
        if (response.data.success) {
          actions.value = response.data.data
          pagination.total = response.data.total
        }
      } catch (error) {
        console.error('获取动作列表失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    const handleSearch = () => {
      pagination.page = 1
      fetchActions()
    }
    
    const resetFilters = () => {
      filters.character_id = null
      filters.type = ''
      filters.search = ''
      filters.position_state = ''
      filters.min_start_frame = null
      filters.max_start_frame = null
      filters.min_poise = null
      filters.max_poise = null
      filters.can_parry = false
      filters.can_detach = false
      handleSearch()
    }
    
    const handleSelectionChange = (selection) => {
      selectedActions.value = selection
    }
    
    const clearSelection = () => {
      selectedActions.value = []
    }
    
    const showCompare = () => {
      const attrs = [
        { key: 'character_name', label: '角色' },
        { key: 'action_type', label: '类型' },
        { key: 'start_frame', label: '发生帧' },
        { key: 'duration_frame', label: '持续帧' },
        { key: 'self_hitstop', label: '顿帧-自' },
        { key: 'enemy_hitstop', label: '顿帧-敌' },
        { key: 'poise_damage', label: '削韧值' },
        { key: 'concerto_recovery', label: '协奏回收' },
        { key: 'core_recovery', label: '核心回收' },
        { key: 'can_parry', label: '可弹刀' },
        { key: 'can_detach', label: '可脱手' }
      ]
      
      compareActions.value = attrs.map(attr => {
        const row = { attr: attr.label }
        selectedActions.value.forEach(action => {
          row[action.id] = action[attr.key]
        })
        return row
      })
      
      compareVisible.value = true
    }
    
    const viewDetail = (action) => {
      // 可以打开详情弹窗或跳转到角色详情页
      console.log('查看详情:', action)
    }
    
    const handleSizeChange = (size) => {
      pagination.per_page = size
      fetchActions()
    }
    
    const handlePageChange = (page) => {
      pagination.page = page
      fetchActions()
    }
    
    return {
      actions,
      loading,
      filters,
      pagination,
      characterOptions,
      selectedActions,
      compareVisible,
      compareActions,
      handleSearch,
      resetFilters,
      handleSelectionChange,
      clearSelection,
      showCompare,
      viewDetail,
      handleSizeChange,
      handlePageChange
    }
  }
}
</script>

<style scoped>
.filter-card {
  margin-bottom: 20px;
}

.batch-actions {
  margin-bottom: 15px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
