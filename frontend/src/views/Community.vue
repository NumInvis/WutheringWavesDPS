<template>
  <div class="community">
    <el-card class="search-card">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索表格..."
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
          <el-button type="primary" @click="openUploadDialog">
            <el-icon><Upload /></el-icon>
            上传表格
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <div v-loading="loading" class="spreadsheet-list">
      <el-empty v-if="!loading && spreadsheets.length === 0" description="暂无表格" />

      <el-row :gutter="20">
        <el-col :span="8" v-for="sheet in spreadsheets" :key="sheet.id">
          <el-card class="spreadsheet-card" shadow="hover">
            <div class="card-header">
              <span class="title">
                <span v-if="sheet.sheet_number !== undefined && sheet.sheet_number !== null" class="sheet-number">#{{ String(sheet.sheet_number).padStart(8, '0') }}</span>
                {{ sheet.title }}
                <el-tag v-if="sheet.is_featured" size="small" type="warning">置顶</el-tag>
              </span>
              <el-tag v-if="sheet.area" size="small" :type="sheet.area === 'pull_table' ? 'primary' : 'success'">
                {{ sheet.area === 'pull_table' ? '拉表区' : '其他区' }}
              </el-tag>
            </div>
            
            <div class="card-body">
              <div class="meta">
                <span><el-icon><User /></el-icon> {{ sheet.owner_display_name || sheet.owner_username }}</span>
                <span class="view-count"><el-icon><View /></el-icon> {{ sheet.view_count || 0 }}</span>
              </div>
            </div>
            
            <div class="star-section">
              <span class="star-number">{{ sheet.star_count || 0 }} 赞</span>
              <el-button 
                size="large" 
                :type="sheet.has_starred ? 'warning' : 'default'"
                @click="toggleStar(sheet)"
                class="star-button"
              >
                <el-icon><Star /></el-icon>
                {{ sheet.has_starred ? '已赞' : '点赞' }}
              </el-button>
            </div>
            
            <div class="card-actions">
              <el-button size="small" @click="previewSheet(sheet)">
                预览
              </el-button>
              <el-button size="small" type="primary" @click="downloadSheet(sheet)">
                下载
              </el-button>
              <template v-if="isAdmin">
                <el-button size="small" :type="sheet.is_featured ? 'warning' : 'default'" @click="toggleFeature(sheet)">
                  {{ sheet.is_featured ? '取消置顶' : '置顶' }}
                </el-button>
                <el-button size="small" type="danger" @click="confirmDelete(sheet)">
                  删除
                </el-button>
              </template>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <div class="pagination-container" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[12, 24, 48]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchSpreadsheets"
          @current-change="fetchSpreadsheets"
        />
      </div>
    </div>

    <UploadDialog v-model="uploadDialogVisible" @success="handleUploadSuccess" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Star, View, User, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import UploadDialog from '../components/UploadDialog.vue'
import { useUserStore } from '../stores/user'
import api from '../api'

const router = useRouter()
const userStore = useUserStore()

// 计算属性：是否为管理员
const isAdmin = computed(() => {
  console.log('[Community] Checking admin, user:', userStore.user)
  return userStore.user?.is_admin === true
})

const searchKeyword = ref('')
const selectedArea = ref('')
const loading = ref(false)
const spreadsheets = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)

const uploadDialogVisible = ref(false)

async function fetchSpreadsheets() {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    if (selectedArea.value) {
      params.area = selectedArea.value
    }

    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }

    const data = await api.get('/spreadsheets', { params })
    spreadsheets.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function openUploadDialog() {
  if (!userStore.isAuthenticated) {
    ElMessage.warning('请先登录后上传')
    return
  }
  uploadDialogVisible.value = true
}

function handleUploadSuccess() {
  fetchSpreadsheets()
}

function previewSheet(sheet: any) {
  const isOwner = userStore.user && sheet.owner_id === userStore.user.id
  const isAdmin = userStore.user?.is_admin
  
  router.push({
    path: '/calculator',
    query: {
      preview: sheet.id,
      editable: (isOwner || isAdmin) ? 'true' : 'false'
    }
  })
}

async function downloadSheet(sheet: any) {
  try {
    const data = await api.get(`/spreadsheets/${sheet.id}/download`)
    if (data.file_url) {
      const fileResponse = await fetch(data.file_url)
      const blob = await fileResponse.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = sheet.title + '.xlsx'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    }
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

async function toggleStar(sheet: any) {
  if (!userStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    return
  }
  
  try {
    if (sheet.has_starred) {
      await api.delete(`/stars/spreadsheet/${sheet.id}`)
      sheet.star_count = (sheet.star_count || 0) - 1
      sheet.has_starred = false
    } else {
      await api.post('/stars', {
        spreadsheet_id: sheet.id
      })
      sheet.star_count = (sheet.star_count || 0) + 1
      sheet.has_starred = true
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function toggleFeature(sheet: any) {
  if (!isAdmin.value) {
    ElMessage.warning('需要管理员权限')
    return
  }
  
  try {
    await api.put(`/spreadsheets/${sheet.id}/admin`, { 
      is_featured: !sheet.is_featured 
    })
    ElMessage.success(sheet.is_featured ? '已取消置顶' : '已置顶')
    fetchSpreadsheets()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function confirmDelete(sheet: any) {
  if (!isAdmin.value) {
    ElMessage.warning('需要管理员权限')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除表格"${sheet.title}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/spreadsheets/${sheet.id}`)
    ElMessage.success('已删除')
    fetchSpreadsheets()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
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

.spreadsheet-list {
  min-height: 400px;
}

.spreadsheet-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-header .title {
  font-size: 16px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sheet-number {
  font-size: 12px;
  color: #888;
  font-family: monospace;
}

.card-body {
  margin-bottom: 12px;
}

.meta {
  display: flex;
  gap: 16px;
  color: #888;
  font-size: 13px;
}

.meta span {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.meta .view-count:hover {
  color: #409eff;
}

.star-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  margin-bottom: 12px;
  border-top: 1px solid #2a2a3e;
  border-bottom: 1px solid #2a2a3e;
}

.star-number {
  font-size: 18px;
  font-weight: 600;
  color: #f7ba2a;
}

.star-button {
  min-width: 100px;
}

.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}
</style>
