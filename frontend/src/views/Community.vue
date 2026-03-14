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
                预览
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
  return sheet.owner_username === userStore.user.username
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
    await api.post(`/spreadsheets/${sheet.id}/toggle-feature`)
    sheet.is_featured = !sheet.is_featured
    ElMessage.success('操作成功')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

function openEditDialog(sheet: any) {
  if (!canEdit(sheet)) {
    ElMessage.warning('无权限编辑')
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
    ElMessage.error('文件大小不能超过 5MB')
    return false
  }
  return true
}

async function submitEdit() {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    if (!currentEditingSheet.value) {
      ElMessage.error('编辑信息无效')
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
      
      ElMessage.success('编辑成功')
      editDialogVisible.value = false
      await fetchSpreadsheets()
    } catch (error: any) {
      console.error('[Community] 编辑失败:', error)
      ElMessage.error(error.response?.data?.detail || '编辑失败')
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
    ElMessage.success('删除成功')
    await fetchSpreadsheets()
  } catch (error: any) {
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
  font-size: 16px;
  font-weight: 600;
  color: #888;
  transition: color 0.3s;
}

.star-number-active {
  color: #f7ba2a;
  text-shadow: 0 0 8px rgba(247, 186, 42, 0.5);
}

.star-button {
  transform: scale(1.17);
}

.description {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 10px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  max-height: 60px;
  overflow: hidden;
}

.description .el-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.description span {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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
