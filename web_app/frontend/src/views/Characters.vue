<template>
  <div class="page-container">
    <div class="page-header">
      <h3>角色数据库</h3>
      <p>共 {{ total }} 个角色</p>
    </div>
    
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filters.gender" placeholder="性别" clearable @change="handleFilter">
        <el-option label="女" value="女" />
        <el-option label="男" value="男" />
      </el-select>
      
      <el-select v-model="filters.body_type" placeholder="体型" clearable @change="handleFilter">
        <el-option label="大" value="大" />
        <el-option label="中" value="中" />
        <el-option label="中小" value="中小" />
        <el-option label="小" value="小" />
      </el-select>
      
      <el-select v-model="filters.element" placeholder="属性" clearable @change="handleFilter">
        <el-option label="衍射" value="衍射" />
        <el-option label="湮灭" value="湮灭" />
        <el-option label="热熔" value="热熔" />
        <el-option label="导电" value="导电" />
        <el-option label="气动" value="气动" />
        <el-option label="冷凝" value="冷凝" />
      </el-select>
      
      <el-input
        v-model="filters.search"
        placeholder="搜索角色名"
        clearable
        @keyup.enter="handleFilter"
        style="width: 200px"
      />
      
      <el-button type="primary" @click="handleFilter">
        <el-icon><Search /></el-icon> 筛选
      </el-button>
      
      <el-button @click="resetFilter">重置</el-button>
    </div>
    
    <!-- 角色卡片网格 -->
    <el-row :gutter="20">
      <el-col
        v-for="char in characters"
        :key="char.id"
        :xs="12"
        :sm="8"
        :md="6"
        :lg="4"
        class="char-col"
      >
        <el-card class="char-card" @click="goToDetail(char.id)">
          <div class="char-avatar">
            <div class="avatar-placeholder">
              {{ char.name.charAt(0) }}
            </div>
          </div>
          <div class="char-info">
            <h4 class="char-name">{{ char.name }}</h4>
            <div class="char-tags">
              <el-tag size="small" :type="char.gender === '女' ? 'danger' : 'primary'">
                {{ char.gender }}
              </el-tag>
              <el-tag size="small" type="info">{{ char.body_type }}</el-tag>
              <el-tag v-if="char.element" size="small" type="warning">{{ char.element }}</el-tag>
            </div>
            <p class="action-count">{{ char.action_count }} 个动作</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 空状态 -->
    <el-empty v-if="characters.length === 0 && !loading" description="暂无数据" />
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="5" animated />
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'Characters',
  setup() {
    const store = useStore()
    const router = useRouter()
    
    const filters = ref({
      gender: '',
      body_type: '',
      element: '',
      search: ''
    })
    
    const characters = computed(() => store.state.characters)
    const loading = computed(() => store.state.loading)
    const total = computed(() => characters.value.length)
    
    onMounted(() => {
      store.dispatch('fetchCharacters')
    })
    
    const handleFilter = () => {
      const params = {}
      if (filters.value.gender) params.gender = filters.value.gender
      if (filters.value.body_type) params.body_type = filters.value.body_type
      if (filters.value.element) params.element = filters.value.element
      if (filters.value.search) params.search = filters.value.search
      
      store.dispatch('fetchCharacters', params)
    }
    
    const resetFilter = () => {
      filters.value = {
        gender: '',
        body_type: '',
        element: '',
        search: ''
      }
      store.dispatch('fetchCharacters')
    }
    
    const goToDetail = (id) => {
      router.push(`/characters/${id}`)
    }
    
    return {
      filters,
      characters,
      loading,
      total,
      handleFilter,
      resetFilter,
      goToDetail
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

.char-col {
  margin-bottom: 20px;
}

.char-card {
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.char-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.char-avatar {
  margin-bottom: 15px;
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  margin: 0 auto;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32px;
  font-weight: bold;
}

.char-name {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #303133;
}

.char-tags {
  display: flex;
  gap: 5px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.action-count {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.loading-wrapper {
  padding: 20px;
}
</style>
