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
      
      <div class="sheet-wrapper">
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
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

interface UploadedFile {
  id: string
  name: string
  size: number
  content: ArrayBuffer
  file: File
}

const route = useRoute()
const router = useRouter()

const fileInput = ref<HTMLInputElement>()
const loadError = ref('')
const importing = ref(false)
const publishing = ref(false)
const uploadedFiles = ref<UploadedFile[]>([])
const currentFileIndex = ref(-1)
const previewFile = ref<UploadedFile | null>(null)
const isPreviewMode = ref(false)
const previewSheetId = ref('')
const isEditable = ref(true)
const shouldLoadTemplate = ref(false)

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

function retryLoad() {
  loadError.value = ''
  init()
}

function destroySheet() {
  try {
    const luckysheet = (window as any).luckysheet
    if (luckysheet && typeof luckysheet.destroy === 'function') {
      luckysheet.destroy()
    }
  } catch (e) {
  }
}

function convertPercentFormula(formula: string): string {
  if (!formula) return formula
  return formula.replace(/(\d+\.?\d*)%/g, '($1/100)')
}

function setupPercentFormulaHandler() {
  const luckysheet = (window as any).luckysheet
  if (!luckysheet) return
  
  setTimeout(() => {
    try {
      const fileData = luckysheet.getLuckysheetfile && luckysheet.getLuckysheetfile()
      if (fileData && fileData.length > 0) {
        fileData.forEach((sheet: any) => {
          if (sheet.celldata) {
            sheet.celldata.forEach((cell: any) => {
              if (cell.v && typeof cell.v === 'object' && cell.v.f) {
                cell.v.f = convertPercentFormula(cell.v.f)
              }
            })
          }
        })
        if (typeof luckysheet.refresh === 'function') {
          luckysheet.refresh()
        }
      }
    } catch (e) {
    }
  }, 800)
}

function initEmptySheet() {
  console.log('[Calculator] 初始化空表格...')
  
  const luckysheet = (window as any).luckysheet
  if (!luckysheet || typeof luckysheet.create !== 'function') {
    console.error('[Calculator] Luckysheet不可用')
    loadError.value = '表格组件未加载，请刷新页面'
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
      forceCalculation: true,
      sheetFormulaBar: true,
      cellRightClickConfig: {
        copy: true,
        copyAs: true,
        paste: true,
        insertRow: true,
        insertColumn: true,
        deleteRow: true,
        deleteColumn: true,
        deleteCell: true,
        hideRow: true,
        hideColumn: true,
        clear: true,
        matrix: true,
        sort: true,
        filter: true,
        cellFormat: true
      },
      data: [{
        name: 'Sheet1',
        color: '#409eff',
        status: 1,
        order: 0,
        celldata: [],
        row: 84,
        column: 60
      }],
      hook: {
        cellUpdateBefore: function(rc: any, change: any, workbook: any) {
          try {
            if (change && change.v && typeof change.v === 'object' && change.v.f) {
              change.v.f = convertPercentFormula(change.v.f)
            }
          } catch (e) {
          }
          return true
        },
        cellUpdated: function(rc: any, oldValue: any, newValue: any, isRefresh: any) {
          try {
            const luckysheet = (window as any).luckysheet
            if (luckysheet && luckysheet.refresh) {
              setTimeout(() => {
                try {
                  const fileData = luckysheet.getLuckysheetfile && luckysheet.getLuckysheetfile()
                  if (fileData && fileData.length > 0) {
                    fileData.forEach((sheet: any) => {
                      if (sheet.celldata) {
                        sheet.celldata.forEach((cell: any) => {
                          if (cell.v && typeof cell.v === 'object' && cell.v.f) {
                            cell.v.f = convertPercentFormula(cell.v.f)
                          }
                        })
                      }
                    })
                    luckysheet.refresh()
                  }
                } catch (e) {
                }
              }, 100)
            }
          } catch (e) {
          }
        }
      }
    })
    console.log('[Calculator] 空表格初始化成功')
    setupPercentFormulaHandler()
  } catch (e) {
    console.error('[Calculator] 初始化失败:', e)
    loadError.value = '表格初始化失败'
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
  console.log('[Calculator] 开始加载Excel:', file.name)
  
  const LuckyExcel = (window as any).LuckyExcel
  const luckysheet = (window as any).luckysheet
  
  if (!LuckyExcel) {
    throw new Error('Excel解析器未加载')
  }
  
  if (!luckysheet?.create) {
    throw new Error('表格组件未正确加载')
  }

  const exportJson = await new Promise<any>((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Excel解析超时')), 10000)
    
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

  console.log('[Calculator] 解析到', exportJson.sheets.length, '个工作表')
  console.log('[Calculator] 原始数据:', exportJson)

  destroySheet()

  const sheetsData = exportJson.sheets.map((sheet: any, index: number) => {
    const sheetData = {
      ...sheet,
      name: sheet.name || `Sheet${index + 1}`,
      status: index === 0 ? 1 : 0,
      order: index
    }
    
    if (sheetData.celldata && sheetData.celldata.length > 0) {
      sheetData.celldata.forEach((cell: any) => {
        if (cell.v && typeof cell.v === 'object' && cell.v.f) {
          cell.v.f = convertPercentFormula(cell.v.f)
        }
      })
    }
    
    return sheetData
  })

  luckysheet.create({
    container: 'luckysheet',
    data: sheetsData,
    title: exportJson.info?.name || file.name.replace(/\.(xlsx|xls|xlsm)$/i, ''),
    lang: 'zh',
    showinfobar: false,
    showsheetbar: true,
    showstatisticBar: true,
    enableAddRow: !readOnly,
    enableAddCol: !readOnly,
    allowEdit: !readOnly,
    forceCalculation: true,
    sheetFormulaBar: true,
    cellRightClickConfig: {
      copy: true,
      copyAs: true,
      paste: true,
      insertRow: true,
      insertColumn: true,
      deleteRow: true,
      deleteColumn: true,
      deleteCell: true,
      hideRow: true,
      hideColumn: true,
      clear: true,
      matrix: true,
      sort: true,
      filter: true,
      cellFormat: true
    },
    hook: {
      cellUpdateBefore: function(rc: any, change: any, workbook: any) {
        try {
          if (change && change.v && typeof change.v === 'object' && change.v.f) {
            change.v.f = convertPercentFormula(change.v.f)
          }
        } catch (e) {
        }
        return true
      },
      cellUpdated: function(rc: any, oldValue: any, newValue: any, isRefresh: any) {
        try {
          const luckysheet = (window as any).luckysheet
          if (luckysheet && luckysheet.refresh) {
            setTimeout(() => {
              try {
                const fileData = luckysheet.getLuckysheetfile && luckysheet.getLuckysheetfile()
                if (fileData && fileData.length > 0) {
                  fileData.forEach((sheet: any) => {
                    if (sheet.celldata) {
                      sheet.celldata.forEach((cell: any) => {
                        if (cell.v && typeof cell.v === 'object' && cell.v.f) {
                          cell.v.f = convertPercentFormula(cell.v.f)
                        }
                      })
                    }
                  })
                  luckysheet.refresh()
                }
              } catch (e) {
              }
            }, 100)
          }
        } catch (e) {
        }
      }
    }
  })

  setTimeout(() => {
    try {
      const luckysheetInstance = (window as any).luckysheet
      if (luckysheetInstance && typeof luckysheetInstance.refresh === 'function') {
        luckysheetInstance.refresh()
      }
    } catch (e) {
    }
  }, 500)
  
  setupPercentFormulaHandler()
}

function checkPreviewMode() {
  const sheetId = route.query.preview as string
  if (sheetId) {
    isPreviewMode.value = true
    previewSheetId.value = sheetId
    isEditable.value = route.query.editable === 'true'
  }
  
  const loadTemplate = route.query.loadTemplate as string
  if (loadTemplate === 'true') {
    shouldLoadTemplate.value = true
  }
}

async function loadTemplateSheet() {
  console.log('[Calculator] 加载模板表格 #00000000')
  
  try {
    const templateResponse = await fetch('/WutheringWavesDPS/api/spreadsheets/template')
    if (templateResponse.ok) {
      const templateData = await templateResponse.json()
      if (templateData.id && templateData.file_url) {
        let fileUrl = templateData.file_url
        if (!fileUrl.startsWith('/WutheringWavesDPS')) {
          fileUrl = '/WutheringWavesDPS' + fileUrl
        }
        const fileResponse = await fetch(fileUrl)
        const blob = await fileResponse.blob()
        const arrayBuffer = await blob.arrayBuffer()
        const file = new File([blob], templateData.title + '.xlsx', { type: blob.type })
        
        uploadedFiles.value.push({
          id: 'template-' + Date.now(),
          name: file.name,
          size: blob.size,
          content: arrayBuffer,
          file: file
        })
        currentFileIndex.value = uploadedFiles.value.length - 1
        
        await loadExcelParser()
        await parseAndShowExcel(file, false)
        console.log('[Calculator] 模板加载成功')
      }
    }
  } catch (error) {
    console.error('[Calculator] 加载模板失败:', error)
    ElMessage.error('加载模板失败')
  }
}

async function loadPreviewSheet() {
  if (!previewSheetId.value) return
  
  console.log('[Calculator] 加载预览表格:', previewSheetId.value)
  
  try {
    const response = await api.get(`/spreadsheets/${previewSheetId.value}/download`)
    console.log('[Calculator] 下载接口响应:', response)
    
    if (response.file_url) {
      let fileUrl = response.file_url
      if (!fileUrl.startsWith('/WutheringWavesDPS')) {
        fileUrl = '/WutheringWavesDPS' + fileUrl
      }
      console.log('[Calculator] 下载文件:', fileUrl)
      
      const fileResponse = await fetch(fileUrl)
      const blob = await fileResponse.blob()
      const arrayBuffer = await blob.arrayBuffer()
      const file = new File([blob], response.filename || 'preview.xlsx', { type: blob.type })
      
      console.log('[Calculator] 文件信息:', file.name, file.size)
      
      uploadedFiles.value.push({
        id: 'preview-' + Date.now(),
        name: file.name,
        size: blob.size,
        content: arrayBuffer,
        file: file
      })
      currentFileIndex.value = uploadedFiles.value.length - 1
      isPreviewMode.value = false
      
      console.log('[Calculator] 开始解析Excel')
      await loadExcelParser()
      await parseAndShowExcel(file, false)
      console.log('[Calculator] Excel解析完成')
    }
  } catch (error) {
    console.error('[Calculator] 加载预览失败:', error)
    ElMessage.error('加载预览失败: ' + (error as Error).message)
  }
}

async function init() {
  console.log('[Calculator] 开始初始化...')
  loadError.value = ''
  
  try {
    await new Promise<void>((resolve) => {
      let attempts = 0
      const check = () => {
        attempts++
        if ((window as any).luckysheet && typeof (window as any).luckysheet.create === 'function') {
          resolve()
        } else if (attempts < 50) {
          setTimeout(check, 100)
        } else {
          resolve()
        }
      }
      check()
    })
    
    if (shouldLoadTemplate.value) {
      await loadTemplateSheet()
    } else if (isPreviewMode.value) {
      await loadPreviewSheet()
    } else {
      initEmptySheet()
    }
    
    console.log('[Calculator] 初始化完成')
  } catch (error) {
    console.error('[Calculator] 初始化失败:', error)
    loadError.value = '初始化失败: ' + (error as Error).message
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
    console.error('[Calculator] 导入失败:', error)
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
  if (isPreviewMode.value && previewFile.value) {
    downloadFile(previewFile.value)
  } else if (currentFileIndex.value >= 0) {
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
      formData.append('description', publishForm.description || '')
      formData.append('area', publishForm.area)

      await api.post('/spreadsheets/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      ElMessage.success('发布成功')
      publishDialogVisible.value = false
      router.push('/community')
    } catch (error: any) {
      console.error('[Calculator] 发布失败:', error)
      ElMessage.error(error.response?.data?.detail || '发布失败')
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
  window.alert = function() {}
  window.confirm = function() { return false }
  window.prompt = function() { return null }
  checkPreviewMode()
  init()
})

onUnmounted(() => {
  destroySheet()
})
</script>

<style scoped>
.calculator {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.calculator-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(15, 15, 26, 0.75);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.calculator-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  min-height: 0;
  overflow: auto;
}

.calculator-card :deep(.el-card__header) {
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 16px 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  font-size: 18px;
  font-weight: 600;
  color: #e2e8f0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.sheet-list {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.sheet-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  margin-bottom: 10px;
  transition: all 0.25s ease;
}

.sheet-item:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(102, 126, 234, 0.3);
  transform: translateY(-2px);
}

.sheet-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sheet-name {
  font-weight: 600;
  color: #e2e8f0;
  font-size: 15px;
}

.sheet-size {
  font-size: 13px;
  color: #94a3b8;
}

.sheet-actions {
  display: flex;
  gap: 8px;
}

.sheet-wrapper {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

#luckysheet {
  width: 100% !important;
  height: 100% !important;
  min-height: 500px;
}
</style>
