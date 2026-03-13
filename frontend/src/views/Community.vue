<template>
  <div class="community">
    <el-card class="search-card">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-input 
            v-model="searchKeyword" 
            placeholder="搜索表格模板..." 
            clearable
            @keyup.enter="fetchSpreadsheets"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select v-model="selectedArea" placeholder="选择区域" style="width: 100%" @change="fetchSpreadsheets" clearable>
            <el-option label="全部区域" value="" />
            <el-option label="拉表区" value="pull_table" />
            <el-option label="其他区" value="other" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="selectedCharacter" placeholder="选择角色" style="width: 100%" @change="fetchSpreadsheets" clearable filterable>
            <el-option label="全部角色" value="" />
            <el-option 
              v-for="char in characters" 
              :key="char.id" 
              :label="char.name" 
              :value="char.id" 
            />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <el-row :gutter="20" class="content-row">
      <el-col :span="6">
        <el-card class="sidebar-card">
          <template #header>
            <span>🏷️ 区域</span>
          </template>
          <el-menu 
            :default-active="selectedArea" 
            @select="handleAreaSelect"
          >
            <el-menu-item index="">全部</el-menu-item>
            <el-menu-item index="pull_table">📊 拉表区</el-menu-item>
            <el-menu-item index="other">📁 其他区</el-menu-item>
          </el-menu>
        </el-card>
        
        <el-card class="sidebar-card" style="margin-top: 20px;">
          <template #header>
            <span>🎮 角色标签</span>
          </template>
          <div class="tags-cloud">
            <el-tag 
              v-for="char in characters" 
              :key="char.id" 
              class="hot-tag" 
              :type="getElementTagType(char.element)"
              @click="handleCharacterClick(char.id)"
            >
              {{ char.name }}
            </el-tag>
          </div>
        </el-card>
        
        <el-card class="sidebar-card" style="margin-top: 20px;">
          <template #header>
            <span>⭐ 筛选</span>
          </template>
          <div class="filter-options">
            <el-checkbox v-model="showFeaturedOnly" @change="fetchSpreadsheets">只看精华</el-checkbox>
            <el-checkbox v-model="showMySpreadsheets" @change="fetchSpreadsheets">只看我的</el-checkbox>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="18">
        <el-card class="list-card">
          <template #header>
            <div class="list-header">
              <span>📋 表格列表</span>
              <el-radio-group v-model="sortBy" size="small" @change="fetchSpreadsheets">
                <el-radio-button value="created_at">最新</el-radio-button>
                <el-radio-button value="view_count">浏览</el-radio-button>
                <el-radio-button value="star_count">评分</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          
          <div v-loading="loading" class="spreadsheet-list">
            <el-empty v-if="!loading && spreadsheets.length === 0" description="暂无表格" />
            
            <el-row :gutter="20">
              <el-col :span="12" v-for="sheet in spreadsheets" :key="sheet.id">
                <el-card 
                  class="spreadsheet-card" 
                  :class="{ 'is-banned': sheet.is_banned, 'is-featured': sheet.is_featured, 'is-draft': sheet.is_draft }"
                  shadow="hover" 
                  @click="viewSpreadsheet(sheet)"
                >
                  <div class="card-content">
                    <div class="card-title">
                      <el-tag v-if="sheet.is_featured" size="small" type="warning" effect="dark">
                        <el-icon><StarFilled /></el-icon>
                        精华
                      </el-tag>
                      <el-tag v-if="sheet.is_banned" size="small" type="danger" effect="dark">
                        <el-icon><Close /></el-icon>
                        已下架
                      </el-tag>
                      <el-tag v-if="sheet.is_draft" size="small" type="info" effect="dark">
                        <el-icon><Document /></el-icon>
                        草稿
                      </el-tag>
                      <el-tag v-if="sheet.area" size="small" :type="sheet.area === 'pull_table' ? 'primary' : 'success'">
                        {{ sheet.area === 'pull_table' ? '拉表区' : '其他区' }}
                      </el-tag>
                      <span class="title-text">{{ sheet.title }}</span>
                    </div>
                    <p class="card-description">{{ sheet.description || '暂无描述' }}</p>
                    <div class="character-tags" v-if="sheet.character_tags && sheet.character_tags.length > 0">
                      <el-tag 
                        v-for="tag in sheet.character_tags.slice(0, 4)" 
                        :key="tag" 
                        size="small" 
                        class="character-tag"
                      >
                        {{ getCharacterName(tag) }}
                      </el-tag>
                      <el-tag v-if="sheet.character_tags.length > 4" size="small" type="info">
                        +{{ sheet.character_tags.length - 4 }}
                      </el-tag>
                    </div>
                    <div class="card-meta">
                      <span class="meta-item">
                        <el-icon><User /></el-icon>
                        {{ sheet.owner_display_name || sheet.owner_username }}
                      </span>
                      <span class="meta-item">
                        <el-icon><Star /></el-icon>
                        {{ sheet.star_count || 0 }}
                      </span>
                      <span class="meta-item">
                        <el-icon><View /></el-icon>
                        {{ sheet.view_count || 0 }}
                      </span>
                      <span class="meta-item">
                        <el-icon><Download /></el-icon>
                        {{ sheet.download_count || 0 }}
                      </span>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            
            <div class="pagination-container" v-if="total > pageSize">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :total="total"
                :page-sizes="[10, 20, 50, 100]"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="fetchSpreadsheets"
                @current-change="fetchSpreadsheets"
              />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Star, View, Download, User, StarFilled, Close, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { WUWA_CHARACTERS } from '../data/characters'
import api from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const searchKeyword = ref('')
const selectedArea = ref('')
const selectedCharacter = ref('')
const sortBy = ref('created_at')
const sortOrder = ref('desc')
const showFeaturedOnly = ref(false)
const showMySpreadsheets = ref(false)

const loading = ref(false)
const spreadsheets = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const characters = WUWA_CHARACTERS

const characterMap = computed(() => {
  const map: Record<string, string> = {}
  characters.forEach(char => {
    map[char.id] = char.name
  })
  return map
})

function getCharacterName(id: string): string {
  return characterMap.value[id] || id
}

function getElementTagType(element: string): any {
  const typeMap: Record<string, any> = {
    '光': 'warning',
    '暗': 'info',
    '火': 'danger',
    '水': 'primary',
    '风': 'success',
    '土': ''
  }
  return typeMap[element] || ''
}

async function fetchSpreadsheets() {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      page_size: pageSize.value.toString(),
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    })
    
    if (selectedArea.value) {
      params.append('area', selectedArea.value)
    }
    
    if (selectedCharacter.value) {
      params.append('character_tag', selectedCharacter.value)
    }
    
    if (searchKeyword.value) {
      params.append('search', searchKeyword.value)
    }
    
    if (showFeaturedOnly.value) {
      params.append('featured', 'true')
    }
    
    if (showMySpreadsheets.value && userStore.user) {
      params.append('owner_id', userStore.user.id.toString())
    }
    
    const response = await fetch(`/api/spreadsheets?${params}`, {
      headers: {
        'Authorization': userStore.token ? `Bearer ${userStore.token}` : ''
      }
    })
    if (response.ok) {
      const data = await response.json()
      spreadsheets.value = data.items || []
      total.value = data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载表格列表失败')
    console.error('Failed to fetch spreadsheets:', error)
  } finally {
    loading.value = false
  }
}

function handleAreaSelect(area: string) {
  selectedArea.value = area
  currentPage.value = 1
  fetchSpreadsheets()
}

function handleCharacterClick(charId: string) {
  selectedCharacter.value = selectedCharacter.value === charId ? '' : charId
  currentPage.value = 1
  fetchSpreadsheets()
}

function viewSpreadsheet(sheet: any) {
  ElMessage.info(`查看表格: ${sheet.title}`)
}

onMounted(() => {
  fetchSpreadsheets()
})
</script>

<style scoped>
.community {
  max-width: 1400px;
  margin: 0 auto;
}

.search-card {
  margin-bottom: 20px;
}

.content-row {
  margin-top: 20px;
}

.sidebar-card {
  margin-bottom: 20px;
}

.tags-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hot-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.hot-tag:hover {
  transform: scale(1.05);
}

.filter-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.spreadsheet-list {
  min-height: 400px;
}

.spreadsheet-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.spreadsheet-card:hover {
  transform: translateY(-2px);
}

.spreadsheet-card.is-featured {
  border-left: 4px solid #e6a23c;
}

.spreadsheet-card.is-banned {
  opacity: 0.6;
  border-left: 4px solid #f56c6c;
}

.spreadsheet-card.is-draft {
  border-left: 4px solid #909399;
}

.card-content {
  padding: 5px 0;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.card-description {
  color: #666;
  font-size: 14px;
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  min-height: 40px;
}

.character-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.character-tag {
  cursor: default;
}

.card-meta {
  display: flex;
  gap: 16px;
  color: #999;
  font-size: 13px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}
</style>
