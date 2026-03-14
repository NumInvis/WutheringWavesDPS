<template>
  <div class="calculator">
    <el-card class="calculator-card">
      <template #header>
        <div class="card-header">
          <span>工作区</span>
          <div class="header-actions">
            <template v-if="currentFileName">
              <el-button @click="downloadCurrentSheet">
                下载
              </el-button>
              <el-button @click="exitCurrentSheet">
                退出本表
              </el-button>
              <template v-if="!isPreviewMode">
                <el-button type="primary" @click="openPublishDialog" :loading="publishing">
                  发布本表
                </el-button>
              </template>
            </template>
            <el-button v-else type="primary" @click="importExcel" :loading="importing">
              导入Excel
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 加载错误提示 -->
      <el-alert
        v-if="loadError"
        :title="loadError"
        type="error"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #default>
          <el-button type="primary" size="small" @click="retryLoad" style="margin-top: 8px">
            重新加载
          </el-button>
        </template>
      </el-alert>
      
      <div class="sheet-list" v-if="!isPreviewMode && uploadedFiles.length > 0">
        <div class="sheet-item" v-for="(file, index) in uploadedFiles" :key="file.id">
          <div class="sheet-info">
            <span class="sheet-name">{{ file.name }}</span>
            <span class="sheet-size">{{ formatFileSize(file.size) }}</span>
          </div>
          <div class="sheet-actions">
            <el-button size="small" @click="switchSheet(index)">
              切换
            </el-button>
            <el-button size="small" type="primary" @click="downloadFile(file)">
              下载
            </el-button>
            <el-button size="small" type="danger" @click="removeFile(index)">
              删除
            </el-button>
          </div>
        </div>
      </div>
      
      <div class="sheet-wrapper" style="height: 600px;">
        <div v-if="!isReady && !loadError" class="loading-text">正在加载表格组件...</div>
        <div id="luckysheet" style="width: 100%; height: 100%;"></div>
      </div>
    </el-card>

    <input type="file" ref="fileInput" accept=".xlsx,.xls,.xlsm" @change="handleFile" style="display: none" />

    <el-dialog v-model="publishDialogVisible" title="发布表格" width="500px">
      <el-form :model="publishForm" :rules="publishRules" ref="publishFormRef" label-width="100px">
        <el-form-item label="表格标题" prop="title">
          <el-input v-model="publishForm.title" placeholder="请输入表格标题" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="上传区域" prop="area">
          <el-radio-group v-model="publishForm.area">
            <el-radio value="pull_table">拉表区</el-radio>
            <el-radio value="other">其他区</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="表格介绍">
          <el-input
            v-model="publishForm.description"
            type="textarea"
            :rows="3"
            placeholder="简单介绍一下这个表格（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="publishDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="publishing" @click="publishCurrentSheet">
          发布
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

interface UploadedFile {
  id: string
  name: string
  size: number
  content: ArrayBuffer
  file: File
}

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const fileInput = ref<HTMLInputElement>()
const isReady = ref(false)
const loadError = ref('')
const importing = ref(false)
const publishing = ref(false)
const uploadedFiles = ref<UploadedFile[]>([])
const currentFileIndex = ref(-1)
const previewFile = ref<UploadedFile | null>(null)
const isPreviewMode = ref(false)
const previewSheetId = ref('')
const isEditable = ref(true)

const publishDialogVisible = ref(false)
const publishFormRef = ref()
const publishForm = reactive({
  title: '',
  area: 'pull_table',
  description: ''
})
const publishRules = {
  title: [{ required: true, message: '请输入表格标题', trigger: 'blur' }],
  area: [{ required: true, message: '请选择上传区域', trigger: 'change' }]
}

const currentFileName = computed(() => {
  if (isPreviewMode.value && previewFile.value) {
    return previewFile.value.name
  }
  if (currentFileIndex.value >= 0 && uploadedFiles.value[currentFileIndex.value]) {
    return uploadedFiles.value[currentFileIndex.value].name
  }
  return ''
})

// 等待Luckysheet加载
function waitForLuckysheet(): Promise<void> {
  return new Promise((resolve, reject) => {
    let attempts = 0
    const maxAttempts = 50
    
    const check = () => {
      attempts++
      const luckysheet = (window as any).luckysheet
      
      if (luckysheet && typeof luckysheet.create === 'function') {
        resolve()
      } else if (attempts >= maxAttempts) {
        reject(new Error('Luckysheet加载超时'))
      } else {
        setTimeout(check, 100)
      }
    }
    check()
  })
}

async function loadAllScripts() {
  console.log('[loadAllScripts] Starting...')
  loadError.value = ''
  
  try {
    // 等待Luckysheet可用
    await waitForLuckysheet()
    
    isReady.value = true
    await nextTick()
    initEmptySheet()
    
    if (isPreviewMode.value) {
      loadPreviewSheet()
    }
    
    console.log('[loadAllScripts] Complete!')
  } catch (error) {
    console.error('[loadAllScripts] Failed:', error)
    loadError.value = '表格组件加载失败，请刷新页面重试'
  }
}

function retryLoad() {
  loadError.value = ''
  loadAllScripts()
}

function destroySheet() {
  try {
    const luckysheet = (window as any).luckysheet
    if (luckysheet && typeof luckysheet.destroy === 'function') {
      luckysheet.destroy()
    }
  } catch (e) {
    // 忽略
  }
}

function initEmptySheet() {
  console.log('[initEmptySheet] Starting...')
  
  const luckysheet = (window as any).luckysheet
  if (!luckysheet || typeof luckysheet.create !== 'function') {
    console.error('[initEmptySheet] luckysheet not available')
    return
  }
  
  destroySheet()
  
  try {
    luckysheet.create({
      container: 'luckysheet',
      title: '工作区',
      lang: 'zh',
      showinfobar: false,
      showsheetbar: true,
      showstatisticBar: true,
      enableAddRow: true,
      enableAddCol: true,
      allowEdit: true,
      showtoolbarConfig: {
        check: false,
        print: false
      },
      data: [{
        name: 'Sheet1',
        color: '#409eff',
        status: 1,
        order: 0,
        celldata: [],
        row: 84,
        column: 60,
        defaultRowHeight: 19,
        defaultColWidth: 73
      }]
    })
    console.log('[initEmptySheet] Success!')
  } catch (e) {
    console.error('[initEmptySheet] Error:', e)
  }
}

async function loadExcelParser() {
  if ((window as any).LuckyExcel) return
  
  return new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/luckyexcel@1.0.1/dist/luckyexcel.umd.js'
    script.onload = () => {
      setTimeout(() => {
        if ((window as any).LuckyExcel) {
          resolve()
        } else {
          reject(new Error('LuckyExcel初始化失败'))
        }
      }, 100)
    }
    script.onerror = () => reject(new Error('加载Excel解析器失败'))
    document.head.appendChild(script)
  })
}

async function parseAndShowExcel(file: File, readOnly: boolean = false): Promise<void> {
  const LuckyExcel = (window as any).LuckyExcel
  
  if (!LuckyExcel) {
    throw new Error('Excel解析器未加载')
  }

  console.log('[Excel Load] Starting:', file.name)

  const exportJson = await new Promise<any>((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('Excel解析超时（10秒）'))
    }, 10000)

    try {
      LuckyExcel.transformExcelToLucky(file, (data: any) => {
        clearTimeout(timeout)
        resolve(data)
      })
    } catch (err) {
      clearTimeout(timeout)
      reject(err)
    }
  })

  if (!exportJson?.sheets?.length) {
    throw new Error('Excel文件为空或无法解析')
  }

  console.log('[Excel Load] Sheets:', exportJson.sheets.length)

  destroySheet()

  const luckysheet = (window as any).luckysheet
  if (!luckysheet?.create) {
    throw new Error('表格组件未正确加载')
  }

  // 限制数据量
  const MAX_ROWS = 100
  const MAX_COLS = 100
  
  const sheetsData = exportJson.sheets.map((sheet: any, index: number) => {
    let celldata = sheet.celldata || []
    if (celldata.length > 0) {
      celldata = celldata.filter((cell: any) => {
        const row = cell?.r || 0
        const col = cell?.c || 0
        return row < MAX_ROWS && col < MAX_COLS
      })
    }
    
    return {
      name: sheet.name || `Sheet${index + 1}`,
      color: sheet.color || '',
      status: index === 0 ? 1 : 0,
      order: index,
      celldata,
      row: Math.min(sheet.row || 84, MAX_ROWS),
      column: Math.min(sheet.column || 60, MAX_COLS),
      config: sheet.config || {},
      pivotTable: sheet.pivotTable || null,
      isPivotTable: sheet.isPivotTable || false
    }
  })

  luckysheet.create({
    container: 'luckysheet',
    title: file.name.replace(/\.(xlsx|xls|xlsm)$/i, ''),
    lang: 'zh',
    showinfobar: false,
    showsheetbar: true,
    showstatisticBar: true,
    enableAddRow: !readOnly,
    enableAddCol: !readOnly,
    allowEdit: !readOnly,
    showtoolbarConfig: {
      check: false,
      print: false
    },
    data: sheetsData
  })

  console.log('[Excel Load] Success!')
}

function checkPreviewMode() {
  const sheetId = route.query.sheet as string
  if (sheetId) {
    isPreviewMode.value = true
    previewSheetId.value = sheetId
    isEditable.value = route.query.edit !== 'false'
  }
}

function checkTemplateLoad() {
  const template = route.query.template as string
  if (template === '1') {
    loadTemplate()
  }
}

async function loadTemplate() {
  try {
    const response = await fetch('/api/spreadsheets/template')
    if (response.ok) {
      const data = await response.json()
      if (data.file_url) {
        const fileResponse = await fetch(data.file_url)
        const blob = await fileResponse.blob()
        const arrayBuffer = await blob.arrayBuffer()
        const file = new File([blob], '拉表模板.xlsx', { type: blob.type })
        
        await loadExcelParser()
        await parseAndShowExcel(file, false)
        
        uploadedFiles.value.push({
          id: 'template-' + Date.now(),
          name: '拉表模板.xlsx',
          size: blob.size,
          content: arrayBuffer,
          file: file
        })
        currentFileIndex.value = uploadedFiles.value.length - 1
      }
    }
  } catch (error) {
    console.error('加载模板失败:', error)
  }
}

async function loadPreviewSheet() {
  if (!previewSheetId.value) return
  
  try {
    const response = await fetch(`/api/spreadsheets/${previewSheetId.value}/download`, {
      headers: {
        'Authorization': userStore.token ? `Bearer ${userStore.token}` : ''
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.file_url) {
        const fileResponse = await fetch(data.file_url)
        const blob = await fileResponse.blob()
        const arrayBuffer = await blob.arrayBuffer()
        const file = new File([blob], data.filename || 'preview.xlsx', { type: blob.type })
        
        await loadExcelParser()
        await parseAndShowExcel(file, !isEditable.value)
      }
    }
  } catch (error) {
    console.error('加载预览失败:', error)
    ElMessage.error('加载预览失败')
  }
}

function importExcel() {
  fileInput.value?.click()
}

async function handleFile(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  importing.value = true
  try {
    await loadExcelParser()
    await parseAndShowExcel(file, false)
    
    const arrayBuffer = await file.arrayBuffer()
    uploadedFiles.value.push({
      id: 'local-' + Date.now(),
      name: file.name,
      size: file.size,
      content: arrayBuffer,
      file: file
    })
    currentFileIndex.value = uploadedFiles.value.length - 1
    
    ElMessage.success('导入成功')
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败: ' + (error as Error).message)
  } finally {
    importing.value = false
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  }
}

function switchSheet(index: number) {
  currentFileIndex.value = index
  const file = uploadedFiles.value[index]
  if (file) {
    parseAndShowExcel(file.file, false)
  }
}

function downloadFile(file: UploadedFile) {
  const blob = new Blob([file.content], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = file.name
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function downloadCurrentSheet() {
  if (currentFileIndex.value >= 0) {
    downloadFile(uploadedFiles.value[currentFileIndex.value])
  }
}

function removeFile(index: number) {
  uploadedFiles.value.splice(index, 1)
  if (currentFileIndex.value === index) {
    currentFileIndex.value = -1
    initEmptySheet()
  } else if (currentFileIndex.value > index) {
    currentFileIndex.value--
  }
}

function exitCurrentSheet() {
  if (isPreviewMode.value) {
    router.push('/community')
  } else {
    currentFileIndex.value = -1
    initEmptySheet()
  }
}

function openPublishDialog() {
  if (currentFileIndex.value < 0) {
    ElMessage.warning('请先导入表格')
    return
  }
  publishForm.title = uploadedFiles.value[currentFileIndex.value].name.replace(/\.xlsx?$/i, '')
  publishDialogVisible.value = true
}

async function publishCurrentSheet() {
  if (!publishFormRef.value) return
  
  await publishFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    
    const currentFile = uploadedFiles.value[currentFileIndex.value]
    if (!currentFile) {
      ElMessage.error('没有找到要发布的文件')
      return
    }

    publishing.value = true
    try {
      const formData = new FormData()
      formData.append('file', currentFile.file)
      formData.append('title', publishForm.title)
      formData.append('description', publishForm.description)
      formData.append('area', publishForm.area)

      const response = await fetch('/api/spreadsheets', {
        method: 'POST',
        headers: {
          'Authorization': userStore.token ? `Bearer ${userStore.token}` : ''
        },
        body: formData
      })

      if (response.ok) {
        ElMessage.success('发布成功')
        publishDialogVisible.value = false
        router.push('/community')
      } else {
        const error = await response.json()
        ElMessage.error(error.detail || '发布失败')
      }
    } catch (error) {
      console.error('发布失败:', error)
      ElMessage.error('发布失败')
    } finally {
      publishing.value = false
    }
  })
}

function formatFileSize(size: number): string {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / 1024 / 1024).toFixed(1) + ' MB'
}

onMounted(() => {
  checkPreviewMode()
  checkTemplateLoad()
  loadAllScripts()
})

onUnmounted(() => {
  destroySheet()
})

watch(() => route.query.sheet, (newSheet) => {
  if (newSheet) {
    isPreviewMode.value = true
    previewSheetId.value = newSheet as string
    if (isReady.value) {
      loadPreviewSheet()
    }
  }
})
</script>

<style scoped>
.calculator {
  max-width: 1400px;
  margin: 0 auto;
}

.calculator-card {
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.sheet-list {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #2a2a3e;
}

.sheet-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #1a1a2e;
  border-radius: 4px;
  margin-bottom: 8px;
}

.sheet-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sheet-name {
  font-weight: 500;
  color: #fff;
}

.sheet-size {
  font-size: 12px;
  color: #888;
}

.sheet-actions {
  display: flex;
  gap: 8px;
}

.sheet-wrapper {
  min-height: 500px;
  background: #fff;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.loading-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #909399;
  font-size: 14px;
}

.sheet-container {
  width: 100%;
  height: 600px;
}
</style>
