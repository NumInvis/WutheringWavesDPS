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
            <el-button v-else type="primary" @click="importExcel" :loading="importing" :disabled="!isReady">
              导入Excel
            </el-button>
          </div>
        </div>
      </template>
      
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
      
      <div class="sheet-wrapper" v-loading="!isReady" element-loading-text="正在加载表格组件...">
        <div id="luckysheet" class="sheet-container"></div>
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
import * as XLSX from 'xlsx'

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
const uploadedFiles = ref<UploadedFile[]>([])
const currentFileIndex = ref<number>(-1)
const importing = ref(false)
const isReady = ref(false)
const publishing = ref(false)

const isPreviewMode = ref(false)
const isEditable = ref(true)
const previewSheetId = ref<string | null>(null)
const previewFile = ref<UploadedFile | null>(null)

const publishDialogVisible = ref(false)
const publishFormRef = ref<FormInstance>()
const publishForm = reactive({
  title: '',
  area: 'pull_table' as 'pull_table' | 'other',
  description: ''
})

const publishRules: FormRules = {
  title: [
    { required: true, message: '请输入表格标题', trigger: 'blur' },
    { min: 2, max: 200, message: '标题长度在 2 到 200 个字符', trigger: 'blur' }
  ],
  area: [
    { required: true, message: '请选择上传区域', trigger: 'change' }
  ]
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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

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

onMounted(() => {
  const originalAlert = window.alert
  window.alert = function(msg) {
    if (typeof msg === 'string' && (msg.includes('公式') || msg.includes('error') || msg.includes('错误'))) {
      console.log('Suppressed formula error:', msg)
      return
    }
    return originalAlert.apply(window, arguments)
  }
  
  checkPreviewMode()
  checkTemplateLoad()
  loadAllScripts()
})

onUnmounted(() => {
  destroySheet()
})

watch(() => route.query, () => {
  if (isReady.value) {
    checkPreviewMode()
    checkTemplateLoad()
    if (isPreviewMode.value) {
      loadPreviewSheet()
    }
  }
}, { deep: true })

function checkTemplateLoad() {
  const loadTemplate = route.query.loadTemplate as string
  if (loadTemplate === 'true' && !isPreviewMode.value && uploadedFiles.value.length === 0) {
    loadDefaultTemplate()
  }
}

async function loadDefaultTemplate() {
  try {
    const response = await fetch('/api/spreadsheets/template')
    if (response.ok) {
      const data = await response.json()
      if (data.file_url) {
        const fileResponse = await fetch(data.file_url)
        const blob = await fileResponse.blob()
        const arrayBuffer = await blob.arrayBuffer()
        const file = new File([blob], '拉表模板.xlsx', { type: blob.type })
        
        const newFile: UploadedFile = {
          id: 'template',
          name: '拉表模板.xlsx',
          size: blob.size,
          content: arrayBuffer,
          file: file
        }
        
        uploadedFiles.value.push(newFile)
        currentFileIndex.value = 0
        
        await loadExcelParser()
        await parseAndShowExcel(file, false)
        
        router.replace({ path: '/calculator' })
      }
    }
  } catch (error) {
    console.log('加载模板失败', error)
  }
}

function checkPreviewMode() {
  const preview = route.query.preview as string
  const editable = route.query.editable as string
  
  if (preview) {
    isPreviewMode.value = true
    isEditable.value = editable === 'true'
    previewSheetId.value = preview
  } else {
    isPreviewMode.value = false
    isEditable.value = true
    previewSheetId.value = null
  }
}

async function loadAllScripts() {
  console.log('[Script Load] Starting...')
  
  if ((window as any).luckysheet && typeof (window as any).luckysheet.create === 'function') {
    console.log('[Script Load] Luckysheet already loaded')
    isReady.value = true
    await nextTick()
    initEmptySheet()
    if (isPreviewMode.value) {
      loadPreviewSheet()
    }
    return
  }

  const loadCSS = (href: string): Promise<void> => {
    return new Promise((resolve) => {
      if (document.querySelector(`link[href="${href}"]`)) {
        console.log('[Script Load] CSS already exists:', href)
        resolve()
        return
      }
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = href
      link.onload = () => {
        console.log('[Script Load] CSS loaded:', href)
        resolve()
      }
      link.onerror = () => {
        console.error('[Script Load] CSS failed:', href)
        resolve()
      }
      document.head.appendChild(link)
    })
  }

  const loadScript = (src: string): Promise<void> => {
    return new Promise((resolve) => {
      if (document.querySelector(`script[src="${src}"]`)) {
        console.log('[Script Load] Script already exists:', src)
        resolve()
        return
      }
      const script = document.createElement('script')
      script.src = src
      script.onload = () => {
        console.log('[Script Load] Script loaded:', src)
        resolve()
      }
      script.onerror = () => {
        console.error('[Script Load] Script failed:', src)
        resolve()
      }
      document.head.appendChild(script)
    })
  }

  try {
    console.log('[Script Load] Loading CSS files...')
    await loadCSS('https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/css/pluginsCss.css')
    await loadCSS('https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/plugins.css')
    await loadCSS('https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/css/luckysheet.css')
    await loadCSS('https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/assets/iconfont/iconfont.css')
    
    console.log('[Script Load] Loading JS files...')
    await loadScript('https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/js/plugin.js')
    await loadScript('https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/luckysheet.umd.js')
    
    console.log('[Script Load] Waiting for luckysheet to initialize...')
    await waitForLuckysheet()
    
    console.log('[Script Load] Luckysheet ready, checking...')
    const luckysheet = (window as any).luckysheet
    console.log('[Script Load] luckysheet object:', typeof luckysheet)
    console.log('[Script Load] luckysheet.create:', typeof luckysheet?.create)
    
    isReady.value = true
    await nextTick()
    
    // 初始化空表格
    console.log('[Script Load] Initializing empty sheet...')
    initEmptySheet()
    
    if (isPreviewMode.value) {
      loadPreviewSheet()
    }
    
    console.log('[Script Load] Complete!')
  } catch (error) {
    console.error('[Script Load] Failed:', error)
    ElMessage.error('表格组件加载失败，请刷新页面重试')
  }
}

function destroySheet() {
  try {
    const luckysheet = (window as any).luckysheet
    if (luckysheet && typeof luckysheet.destroy === 'function') {
      luckysheet.destroy()
    }
  } catch (e) {
    console.log('destroy warning', e)
  }
}

function initEmptySheet() {
  console.log('[initEmptySheet] Starting...')
  
  const luckysheet = (window as any).luckysheet
  if (!luckysheet || typeof luckysheet.create !== 'function') {
    console.error('[initEmptySheet] luckysheet not loaded or create is not a function')
    return
  }
  
  // 先销毁旧实例
  destroySheet()
  
  // 等待DOM更新
  setTimeout(() => {
    try {
      console.log('[initEmptySheet] Creating new sheet...')
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
  }, 100)
}

function importExcel() {
  if (!isReady.value) {
    ElMessage.warning('表格组件正在加载，请稍候')
    return
  }
  fileInput.value?.click()
}

async function handleFile(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  importing.value = true
  
  try {
    const content = await file.arrayBuffer()
    
    const newFile: UploadedFile = {
      id: Date.now().toString(),
      name: file.name,
      size: file.size,
      content: content,
      file: file
    }
    
    uploadedFiles.value.push(newFile)
    currentFileIndex.value = uploadedFiles.value.length - 1
    
    await loadExcelParser()
    await parseAndShowExcel(file, false)
    
    ElMessage.success('Excel已导入')
  } catch (error) {
    console.error('导入失败', error)
    ElMessage.error('导入失败: ' + ((error as Error).message || '未知错误'))
  } finally {
    importing.value = false
    if (target) {
      target.value = ''
    }
  }
}

async function loadExcelParser() {
  if ((window as any).LuckyExcel) return
  
  return new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/luckyexcel@1.0.1/dist/luckyexcel.umd.js'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('加载Excel解析器失败'))
    document.head.appendChild(script)
  })
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
        
        previewFile.value = {
          id: previewSheetId.value,
          name: data.filename || 'preview.xlsx',
          size: blob.size,
          content: arrayBuffer,
          file: file
        }
        
        await loadExcelParser()
        await parseAndShowExcel(file, !isEditable.value)
      }
    }
  } catch (error) {
    ElMessage.error('加载预览失败')
  }
}

async function parseAndShowExcel(file: File, readOnly: boolean = false): Promise<void> {
  const LuckyExcel = (window as any).LuckyExcel
  
  if (!LuckyExcel) {
    console.error('[Excel Load] LuckyExcel not loaded')
    throw new Error('Excel解析器未加载')
  }

  console.log('[Excel Load] Starting transformExcelToLucky for file:', file.name, 'size:', file.size)

  // 使用 Promise 包装回调
  const exportJson = await new Promise<any>((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('Excel解析超时（10秒）'))
    }, 10000)

    try {
      LuckyExcel.transformExcelToLucky(file, (data: any) => {
        clearTimeout(timeout)
        console.log('[Excel Load] Callback received data:', data)
        resolve(data)
      })
    } catch (err) {
      clearTimeout(timeout)
      reject(err)
    }
  })

  console.log('[Excel Load] ExportJson received:', exportJson)
  
  if (!exportJson) {
    console.error('[Excel Load] exportJson is null/undefined')
    throw new Error('Excel解析失败：返回数据为空')
  }
  
  if (!exportJson.sheets) {
    console.error('[Excel Load] exportJson.sheets is missing:', exportJson)
    throw new Error('Excel文件格式错误：缺少sheets数据')
  }
  
  if (exportJson.sheets.length === 0) {
    console.error('[Excel Load] exportJson.sheets is empty')
    throw new Error('Excel文件为空或无法解析')
  }

  console.log('[Excel Load] Sheets count:', exportJson.sheets.length)

  destroySheet()

  const luckysheet = (window as any).luckysheet
  if (!luckysheet || typeof luckysheet.create !== 'function') {
    console.error('[Excel Load] luckysheet not available:', luckysheet)
    throw new Error('表格组件未正确加载')
  }

  console.log('[Excel Load] Creating luckysheet with data')

  // 确保数据格式正确，只加载前100行和前100列
  const MAX_ROWS = 100
  const MAX_COLS = 100
  
  const sheetsData = exportJson.sheets.map((sheet: any, index: number) => {
    // 过滤celldata，只保留前100行和前100列的数据
    let filteredCelldata = sheet.celldata || []
    if (filteredCelldata.length > 0) {
      filteredCelldata = filteredCelldata.filter((cell: any) => {
        const row = cell?.r || 0
        const col = cell?.c || 0
        return row < MAX_ROWS && col < MAX_COLS
      })
    }
    
    console.log(`[Excel Load] Sheet ${index}: original cells=${sheet.celldata?.length || 0}, filtered cells=${filteredCelldata.length}`)
    
    return {
      name: sheet.name || `Sheet${index + 1}`,
      color: sheet.color || '',
      status: index === 0 ? 1 : 0,
      order: index,
      celldata: filteredCelldata,
      row: Math.min(sheet.row || 84, MAX_ROWS),
      column: Math.min(sheet.column || 60, MAX_COLS),
      config: sheet.config || {},
      pivotTable: sheet.pivotTable || null,
      isPivotTable: sheet.isPivotTable || false
    }
  })

  try {
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
  } catch (e) {
    console.error('[Excel Load] Error creating luckysheet:', e)
    throw e
  }
}

async function switchSheet(index: number) {
  if (index >= 0 && index < uploadedFiles.value.length) {
    currentFileIndex.value = index
    const file = uploadedFiles.value[index]
    await parseAndShowExcel(file.file, false)
  }
}

async function downloadFile(file: UploadedFile) {
  try {
    const blob = new Blob([file.content], { 
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = file.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载完成')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

function exitCurrentSheet() {
  if (isPreviewMode.value) {
    router.push('/community')
  } else {
    if (uploadedFiles.value.length > 0) {
      uploadedFiles.value = []
      currentFileIndex.value = -1
    }
    initEmptySheet()
  }
}

function openPublishDialog() {
  if (!userStore.isAuthenticated) {
    ElMessage.warning('请先登录后发布')
    return
  }
  
  const fileName = currentFileName.value.replace(/\.(xlsx|xls|xlsm)$/i, '')
  publishForm.title = fileName
  publishForm.area = 'pull_table'
  publishForm.description = ''
  publishDialogVisible.value = true
}

async function publishCurrentSheet() {
  if (!publishFormRef.value) return
  
  await publishFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    publishing.value = true
    try {
      let fileContent: ArrayBuffer | null = null
      let fileName = publishForm.title + '.xlsx'
      
      if (isPreviewMode.value && previewFile.value) {
        fileContent = previewFile.value.content
        fileName = previewFile.value.name
      } else if (currentFileIndex.value >= 0 && uploadedFiles.value[currentFileIndex.value]) {
        fileContent = uploadedFiles.value[currentFileIndex.value].content
        fileName = uploadedFiles.value[currentFileIndex.value].name
      }
      
      if (!fileContent) {
        ElMessage.error('没有可发布的表格')
        return
      }
      
      const blob = new Blob([fileContent], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const file = new File([blob], fileName, { type: blob.type })
      
      const formData = new FormData()
      formData.append('file', file)
      
      const uploadResponse = await fetch('/api/uploads', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      })
      
      if (!uploadResponse.ok) {
        throw new Error('文件上传失败')
      }
      
      const uploadResult = await uploadResponse.json()
      
      const spreadsheetData = {
        title: publishForm.title,
        description: publishForm.description || null,
        area: publishForm.area,
        character_tags: [],
        tags: [],
        is_public: true,
        is_draft: false,
        file_url: uploadResult.file_url,
        file_size: uploadResult.file_size
      }
      
      const createResponse = await fetch('/api/spreadsheets', {
        method: 'POST',
        body: JSON.stringify(spreadsheetData),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userStore.token}`
        }
      })
      
      if (!createResponse.ok) {
        throw new Error('创建表格失败')
      }
      
      ElMessage.success('表格已发布！')
      publishDialogVisible.value = false
      router.push('/community')
      
    } catch (error) {
      ElMessage.error('发布失败: ' + ((error as Error).message || '未知错误'))
    } finally {
      publishing.value = false
    }
  })
}

function removeFile(index: number) {
  if (index >= 0 && index < uploadedFiles.value.length) {
    uploadedFiles.value.splice(index, 1)
    if (currentFileIndex.value >= uploadedFiles.value.length) {
      currentFileIndex.value = uploadedFiles.value.length - 1
    }
    if (uploadedFiles.value.length === 0) {
      initEmptySheet()
    } else if (currentFileIndex.value >= 0) {
      switchSheet(currentFileIndex.value)
    }
    ElMessage.success('已删除')
  }
}

async function downloadCurrentSheet() {
  try {
    const luckysheet = (window as any).luckysheet
    if (!luckysheet || typeof luckysheet.getluckysheetfile !== 'function') {
      ElMessage.error('表格组件未正确加载')
      return
    }

    const fileName = currentFileName.value || 'export.xlsx'
    
    if (isPreviewMode.value && previewFile.value) {
      await downloadFileFromLuckysheet(fileName)
    } else if (currentFileIndex.value >= 0 && uploadedFiles.value[currentFileIndex.value]) {
      await downloadFileFromLuckysheet(fileName)
    } else {
      ElMessage.error('没有可下载的表格')
    }
  } catch (error) {
    console.error('下载失败', error)
    ElMessage.error('下载失败')
  }
}

async function downloadFileFromLuckysheet(fileName: string) {
  try {
    const luckysheet = (window as any).luckysheet
    const LuckyExcel = (window as any).LuckyExcel
    
    if (luckysheet && LuckyExcel && typeof LuckyExcel.transformLuckyToExcel === 'function') {
      const luckyFile = luckysheet.getluckysheetfile()
      if (!luckyFile) {
        ElMessage.error('无法获取表格数据')
        return
      }
      
      LuckyExcel.transformLuckyToExcel(luckyFile, (blob: Blob) => {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = fileName
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
        ElMessage.success('下载完成')
      })
    } else {
      ElMessage.warning('暂不支持直接导出修改内容，请使用原始文件')
      if (isPreviewMode.value && previewFile.value) {
        await downloadFile(previewFile.value)
      } else if (currentFileIndex.value >= 0 && uploadedFiles.value[currentFileIndex.value]) {
        await downloadFile(uploadedFiles.value[currentFileIndex.value])
      }
    }
  } catch (error) {
    console.error('导出失败', error)
    ElMessage.warning('导出修改内容失败，正在下载原始文件')
    if (isPreviewMode.value && previewFile.value) {
      await downloadFile(previewFile.value)
    } else if (currentFileIndex.value >= 0 && uploadedFiles.value[currentFileIndex.value]) {
      await downloadFile(uploadedFiles.value[currentFileIndex.value])
    }
  }
}
</script>

<style scoped>
.calculator {
  height: 100%;
}

.calculator-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.calculator-card :deep(.el-card__body) {
  flex: 1;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  padding: 12px 16px;
  background: #1a1a2e;
  border-bottom: 1px solid #2a2a3e;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.sheet-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #16213e;
  border: 1px solid #2a2a3e;
  border-radius: 4px;
}

.sheet-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sheet-name {
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sheet-size {
  font-size: 12px;
  color: #888;
}

.sheet-actions {
  display: flex;
  gap: 4px;
}

.sheet-wrapper {
  flex: 1;
  position: relative;
  min-height: 0;
}

.sheet-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
}
</style>
