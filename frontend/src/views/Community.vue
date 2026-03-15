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
              <div class="description" v-if="sheet.description">
                <el-icon><Document /></el-icon>
                <span>{{ sheet.description }}</span>
              </div>
            </div>
            
            <div class="star-section">
              <span class="star-number" :class="{ 'star-number-active': sheet.has_starred }">
                {{ sheet.has_starred ? '★' : '☆' }} {{ sheet.star_count || 0 }}
              </span>
              <el-button 
                class="star-button"
                size="small"
                :type="sheet.has_starred ? 'warning' : 'default'"
                @click="toggleStar(sheet)"
              >
                <el-icon v-if="sheet.has_starred"><StarFilled /></el-icon>
                <el-icon v-else><Star /></el-icon>
              </el-button>
            </div>
            
            <div class="card-actions">
              <el-button size="small" @click="previewSheet(sheet)">
                载入
              </el-button>
              <el-button size="small" type="primary" @click="downloadSheet(sheet)">
                下载
              </el-button>
              <template v-if="canEdit(sheet)">
                <el-button size="small" type="primary" @click="openEditDialog(sheet)">
                  编辑
                </el-button>
                <el-button size="small" type="danger" @click="confirmDelete(sheet)">
                  删除
                </el-button>
              </template>
              <template v-else-if="isAdmin">
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
    
    <el-dialog v-model="editDialogVisible" title="编辑表格信息" width="500px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="表格标题" prop="title">
          <el-input v-model="editForm.title" placeholder="请输入表格标题（不超过 15 字）" maxlength="15" show-word-limit />
        </el-form-item>
        <el-form-item label="表格介绍" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="4"
            placeholder="简单介绍一下这个表格（不超过 100 字）"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="更换文件">
          <el-upload
            class="file-uploader"
            drag
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleEditFileChange"
            :before-upload="beforeUpload"
            accept=".xlsx,.xls,.xlsm"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .xlsx, .xls, .xlsm 格式，文件不超过 5MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editing" @click="submitEdit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Star, StarFilled, View, User, Upload, Document, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import UploadDialog from '../components/UploadDialog.vue'
import { useUserStore } from '../stores/user'
import api from '../api'
import type { FormInstance, FormRules } from 'element-plus'

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

// 编辑相关
const editDialogVisible = ref(false)
const editFormRef = ref<FormInstance>()
const editing = ref(false)
const currentEditingSheet = ref<any>(null)
const editFile = ref<File | null>(null)

const editForm = ref({
  title: '',
  description: ''
})

const editRules: FormRules = {
  title: [
    { required: true, message: '请输入表格标题', trigger: 'blur' },
    { min: 2, max: 15, message: '标题长度在 2 到 15 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 100, message: '介绍不能超过 100 字', trigger: 'blur' }
  ]
}

function canEdit(sheet: any): boolean {
  if (!userStore.user) return false
  return sheet.user_id === userStore.user.id
}

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
    ElMessage.error({ message: '加载失败', duration: 3000 })
  } finally {
    loading.value = false
  }
}

function openUploadDialog() {
  if (!userStore.isAuthenticated) {
    ElMessage.warning({ message: '请先登录后上传', duration: 3000 })
    return
  }
  uploadDialogVisible.value = true
}

function handleUploadSuccess() {
  fetchSpreadsheets()
}

function previewSheet(sheet: any) {
  const isOwner = userStore.user && sheet.user_id === userStore.user.id
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
    ElMessage.error({ message: '下载失败', duration: 3000 })
  }
}

async function toggleStar(sheet: any) {
  if (!userStore.isAuthenticated) {
    ElMessage.warning({ message: '请先登录', duration: 3000 })
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
    ElMessage.error({ message: '操作失败', duration: 3000 })
  }
}

async function toggleFeature(sheet: any) {
  if (!isAdmin.value) {
    ElMessage.warning({ message: '需要管理员权限', duration: 3000 })
    return
  }

  try {
    await api.post(`/spreadsheets/${sheet.id}/toggle-feature`)
    sheet.is_featured = !sheet.is_featured
    ElMessage.success({ message: '操作成功', duration: 3000 })
  } catch (error) {
    ElMessage.error({ message: '操作失败', duration: 3000 })
  }
}

function openEditDialog(sheet: any) {
  if (!canEdit(sheet)) {
    ElMessage.warning({ message: '无权限编辑', duration: 3000 })
    return
  }
  currentEditingSheet.value = sheet
  editForm.value = {
    title: sheet.title,
    description: sheet.description || ''
  }
  editFile.value = null
  editDialogVisible.value = true
}

function handleEditFileChange(file: any) {
  editFile.value = file.raw
}

function beforeUpload(file: File) {
  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error({ message: '文件大小不能超过 5MB', duration: 3000 })
    return false
  }
  return true
}

async function submitEdit() {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    if (!currentEditingSheet.value) {
      ElMessage.error({ message: '编辑信息无效', duration: 3000 })
      return
    }
    
    editing.value = true
    try {
      const formData = new FormData()
      formData.append('title', editForm.value.title)
      if (editForm.value.description) {
        formData.append('description', editForm.value.description)
      }
      if (editFile.value) {
        formData.append('file', editFile.value)
      }
      
      await api.put(`/spreadsheets/${currentEditingSheet.value.id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      ElMessage.success({ message: '编辑成功', duration: 3000 })
      editDialogVisible.value = false
      await fetchSpreadsheets()
    } catch (error: any) {
      console.error('[Community] 编辑失败:', error)
      ElMessage.error({ message: error.response?.data?.detail || '编辑失败', duration: 3000 })
    } finally {
      editing.value = false
    }
  })
}

async function confirmDelete(sheet: any) {
  const isOwner = canEdit(sheet)
  const confirmText = isOwner 
    ? `确定要删除表格"${sheet.title}"吗？此操作不可恢复`
    : `确定要删除表格"${sheet.title}"吗？（管理员操作）`
  
  try {
    await ElMessageBox.confirm(confirmText, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/spreadsheets/${sheet.id}`)
    ElMessage.success({ message: '删除成功', duration: 3000 })
    await fetchSpreadsheets()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error({ message: '删除失败', duration: 3000 })
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
  padding: 20px;
}

.search-card {
  margin-bottom: 24px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(15, 15, 26, 0.75);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.search-card :deep(.el-card__body) {
  padding: 24px;
}

.spreadsheet-list {
  min-height: 400px;
}

.spreadsheet-card {
  margin-bottom: 20px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(15, 15, 26, 0.75);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.spreadsheet-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  border-color: rgba(102, 126, 234, 0.3);
}

.spreadsheet-card :deep(.el-card__body) {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 12px;
}

.card-header .title {
  font-size: 18px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #e2e8f0;
}

.sheet-number {
  font-size: 13px;
  color: #909399;
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 600;
}

.card-body {
  margin-bottom: 16px;
}

.meta {
  display: flex;
  gap: 20px;
  color: #94a3b8;
  font-size: 14px;
  margin-bottom: 12px;
}

.meta span {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.meta span:hover {
  background: rgba(255, 255, 255, 0.08);
}

.meta .view-count:hover {
  color: #409eff;
}

.star-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  margin-bottom: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.1) 100%);
  border: 1px solid rgba(251, 191, 36, 0.3);
  margin: 16px 0;
  padding: 14px 18px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.star-section:hover {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2) 0%, rgba(245, 158, 11, 0.15) 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(251, 191, 36, 0.2);
}

.star-number {
  font-size: 17px;
  font-weight: 700;
  color: #fbbf24;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.star-number-active {
  color: #f59e0b;
  text-shadow: 0 0 12px rgba(245, 158, 11, 0.5);
  transform: scale(1.03);
}

.star-button {
  transform: scale(1);
  border-radius: 10px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2) 0%, rgba(245, 158, 11, 0.15) 100%);
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.star-button:hover {
  transform: scale(1.08) rotate(10deg);
  box-shadow: 0 4px 16px rgba(251, 191, 36, 0.4);
}

.description {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 10px;
  font-size: 14px;
  color: #1e3a5f;
  line-height: 1.6;
  max-height: 72px;
  overflow: hidden;
  border-left: 4px solid #3b82f6;
}

.description .el-icon {
  flex-shrink: 0;
  margin-top: 2px;
  color: #3b82f6;
}

.description span {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.card-actions .el-button {
  border-radius: 8px;
  font-weight: 500;
  padding: 8px 16px;
  transition: all 0.2s;
}

.card-actions .el-button:hover {
  transform: translateY(-1px);
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 40px;
  padding: 20px;
}

.pagination-container :deep(.el-pagination) {
  background: white;
  padding: 12px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}
</style>
