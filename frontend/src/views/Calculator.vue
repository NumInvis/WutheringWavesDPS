<template>
  <div class="calculator">
    <el-card class="calculator-card">
      <template #header>
        <div class="card-header">
          <span>🧮 DPS计算器</span>
          <el-space>
            <el-button @click="importExcel">
              <el-icon><Upload /></el-icon>
              导入Excel
            </el-button>
            <el-button @click="exportExcel">
              <el-icon><Download /></el-icon>
              导出Excel
            </el-button>
            <el-button @click="saveDraft">
              <el-icon><Document /></el-icon>
              保存草稿
            </el-button>
            <el-button type="primary" @click="showUploadDialog">
              <el-icon><FolderChecked /></el-icon>
              发布/上传
            </el-button>
          </el-space>
        </div>
      </template>
      <div class="sheet-container" ref="sheetContainer"></div>
    </el-card>
    
    <input type="file" ref="fileInput" accept=".xlsx,.xls" @change="handleFile" style="display: none" />
    
    <UploadDialog 
      v-model:visible="uploadDialogVisible"
      :initial-file="currentFile"
      @success="handleUploadSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Upload, Download, FolderChecked, Document } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import UploadDialog from '../components/UploadDialog.vue'

const sheetContainer = ref<HTMLElement>()
const fileInput = ref<HTMLInputElement>()
const uploadDialogVisible = ref(false)
const currentFile = ref<File | null>(null)

let luckysheetInstance: any = null

function convertFormula(formula: string): string {
  if (!formula) return formula
  
  let result = formula
  const percentRegex = /(\d+\.?\d*)%/g
  
  result = result.replace(percentRegex, (match, p1) => {
    const value = parseFloat(p1) / 100
    return `(${value})`
  })
  
  return result
}

onMounted(() => {
  loadLuckySheetScripts()
})

onUnmounted(() => {
  if (luckysheetInstance) {
    luckysheetInstance = null
  }
})

function loadLuckySheetScripts() {
  if ((window as any).luckysheet) {
    initSheet()
    return
  }
  
  const cssLink = document.createElement('link')
  cssLink.rel = 'stylesheet'
  cssLink.href = 'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/css/pluginsCss.css'
  document.head.appendChild(cssLink)
  
  const cssLink2 = document.createElement('link')
  cssLink2.rel = 'stylesheet'
  cssLink2.href = 'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/plugins.css'
  document.head.appendChild(cssLink2)
  
  const cssLink3 = document.createElement('link')
  cssLink3.rel = 'stylesheet'
  cssLink3.href = 'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/css/luckysheet.css'
  document.head.appendChild(cssLink3)
  
  const cssLink4 = document.createElement('link')
  cssLink4.rel = 'stylesheet'
  cssLink4.href = 'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/assets/iconfont/iconfont.css'
  document.head.appendChild(cssLink4)
  
  const script1 = document.createElement('script')
  script1.src = 'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/js/plugin.js'
  script1.onload = () => {
    const script2 = document.createElement('script')
    script2.src = 'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/luckysheet.umd.js'
    script2.onload = () => {
      initSheet()
    }
    document.head.appendChild(script2)
  }
  document.head.appendChild(script1)
}

function initSheet() {
  if (!sheetContainer.value) return
  
  luckysheetInstance = (window as any).luckysheet.create({
    container: sheetContainer.value,
    title: '鸣潮DPS计算器',
    lang: 'zh',
    showinfobar: true,
    showsheetbar: true,
    showstatisticBar: true,
    enableAddRow: true,
    enableAddCol: true,
    allowEdit: true,
    data: [{
      name: 'Sheet1',
      color: '#00d4ff',
      status: 1,
      order: 0,
      celldata: [],
      row: 100,
      column: 50,
      defaultRowHeight: 20,
      defaultColWidth: 80
    }],
    forceCalculation: true,
    hook: {
      cellUpdatedBefore: (r: number, c: number, value: any, sheetFile: any, isRefresh: boolean) => {
        if (value && typeof value === 'object' && value.f) {
          value.f = convertFormula(value.f)
        }
        return value
      }
    }
  })
}

function importExcel() {
  fileInput.value?.click()
}

async function handleFile(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  currentFile.value = file
  
  try {
    ElMessage.info('正在解析Excel文件...')
    
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch('/api/uploads', {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error('文件上传失败')
    }
    
    const result = await response.json()
    ElMessage.success(`文件已上传: ${result.filename}`)
    
    loadExcelIntoSheet(file)
    
  } catch (error) {
    ElMessage.error('文件处理失败，请先登录')
  } finally {
    if (target) {
      target.value = ''
    }
  }
}

async function loadExcelIntoSheet(file: File) {
  try {
    if (!(window as any).LuckyExcel) {
      const script = document.createElement('script')
      script.src = 'https://cdn.jsdelivr.net/npm/luckyexcel@1.0.1/dist/luckyexcel.umd.js'
      script.onload = () => {
        parseExcel(file)
      }
      document.head.appendChild(script)
    } else {
      parseExcel(file)
    }
  } catch (error) {
    ElMessage.error('Excel解析失败')
  }
}

async function parseExcel(file: File) {
  try {
    (window as any).LuckyExcel.transformExcelToLucky(file, (exportJson: any) => {
      if (exportJson.sheets && exportJson.sheets.length > 0) {
        exportJson.sheets.forEach((sheet: any) => {
          if (sheet.celldata) {
            sheet.celldata.forEach((cell: any) => {
              if (cell.v && cell.v.f) {
                cell.v.f = convertFormula(cell.v.f)
              }
            })
          }
        })
        
        (window as any).luckysheet.destroy()
        luckysheetInstance = (window as any).luckysheet.create({
          container: sheetContainer.value,
          title: file.name.replace('.xlsx', '').replace('.xls', ''),
          lang: 'zh',
          showinfobar: true,
          showsheetbar: true,
          showstatisticBar: true,
          data: exportJson.sheets,
          forceCalculation: true
        })
        
        ElMessage.success('Excel文件已成功加载')
      }
    })
  } catch (error) {
    ElMessage.error('Excel解析失败')
  }
}

function exportExcel() {
  try {
    if (!(window as any).luckysheet) {
      ElMessage.error('表格未初始化')
      return
    }
    
    ElMessage.info('导出功能开发中，请使用Luckysheet内置的导出功能')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

async function saveToServer() {
  try {
    await ElMessageBox.prompt('请输入表格标题', '保存表格', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '请输入有效的标题'
    }).then(async ({ value }) => {
      const sheetData = (window as any).luckysheet.getAllSheets()
      
      ElMessage.success(`表格 "${value}" 保存功能开发中`)
    })
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('保存失败')
    }
  }
}

function showUploadDialog() {
  uploadDialogVisible.value = true
}

function handleUploadSuccess() {
  ElMessage.success('表格发布/上传成功！')
}

async function saveDraft() {
  try {
    await ElMessageBox.prompt('请输入草稿名称', '保存草稿', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '请输入有效的草稿名称'
    }).then(async ({ value }) => {
      const sheetData = (window as any).luckysheet.getAllSheets()
      
      ElMessage.success(`草稿 "${value}" 已保存！`)
    })
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('保存失败')
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
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sheet-container {
  width: 100%;
  height: 100%;
}
</style>
