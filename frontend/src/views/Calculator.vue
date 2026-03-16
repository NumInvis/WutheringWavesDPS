<template>
  <div class="calculator">
    <el-card class="calculator-card">
      <template #header>
        <div class="card-header">
          <span>工作区</span>
          <div class="header-actions">
            <el-button @click="toggleSkillSearch">
              {{ showSkillSearch ? '关闭技能搜索' : '开启技能搜索' }}
            </el-button>
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

    <div v-if="showSkillSearch" class="floating-skill-panel" :style="panelStyle" @mousedown="startDrag">
      <div class="panel-header" @mousedown="startDrag">
        <span class="panel-title">技能搜索</span>
        <div class="panel-controls">
          <el-button size="small" circle @click="toggleMinimize">
            <el-icon v-if="!isMinimized"><Minus /></el-icon>
            <el-icon v-else><Plus /></el-icon>
          </el-button>
          <el-button size="small" circle type="danger" @click="toggleSkillSearch">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
      <div v-if="!isMinimized" class="panel-content">
        <el-input
          v-model="skillSearchQuery"
          placeholder="搜角色..."
          size="small"
          clearable
          class="compact-search"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <div class="compact-content">
          <el-select
            v-model="skillSelectedCharacter"
            placeholder="选择角色"
            size="small"
            filterable
            clearable
            class="compact-select"
            style="width: 100%"
            @change="handleCharacterChange"
          >
            <el-option
              v-for="char in filteredSkillCharacters"
              :key="char"
              :label="char"
              :value="char"
            />
          </el-select>
          
          <el-select
            v-if="skillSelectedCharacter"
            v-model="selectedActionName"
            placeholder="选择动作"
            size="small"
            filterable
            clearable
            class="compact-select"
            style="width: 100%"
            @change="handleActionSelect"
          >
            <el-option
              v-for="action in skillCharacterActions"
              :key="action['角色/动作']"
              :label="action['角色/动作']"
              :value="action['角色/动作']"
            />
          </el-select>
        </div>
        
        <div v-if="skillSelectedAction" class="compact-params">
          <div
            v-for="param in tableData"
            :key="param.param"
            class="param-row"
            @click="copyParam(param.value)"
          >
            <span class="param-label">{{ param.param }}</span>
            <span class="param-value" :title="String(param.value)">{{ param.value }}</span>
            <el-icon class="copy-icon-small"><DocumentCopy /></el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, DocumentCopy, Minus, Plus, Close } from '@element-plus/icons-vue'
import api from '../api'

interface ActionData {
  [key: string]: any
  '角色/动作': string
}

const characterList = [
  '椿', '灯灯', '守岸人', '釉瑚', '折枝', '长离', '今汐', '吟霖', '鉴心', '丹瑾',
  '桃祈', '散华', '炽霞', '秧秧', '暗主', '光主', '白芷', '维里奈', '安可', '卡卡罗',
  '忌炎', '相里要', '凌阳', '珂莱塔', '洛可可', '莫特斐', '渊武', '秋水', '菲比', '布兰特',
  '风主', '坎特蕾拉', '赞妮', '夏空', '卡提希娅/芙露德莉斯', '露帕', '弗洛洛', '奥古斯塔', '尤诺',
  '嘉贝莉娜', '仇远', '千咲', '卜灵', '琳奈', '莫宁', '爱弥斯/机兵爱弥斯', '陆·赫斯', '西格莉卡'
]

const mergedCharacters: Record<string, string[]> = {
  '卡提希娅/芙露德莉斯': ['卡提希娅', '芙露德莉斯'],
  '爱弥斯/机兵爱弥斯': ['爱弥斯', '机兵爱弥斯']
}

const paramList = [
  { key: '结算类型', label: '结算类型' },
  { key: '技能类型', label: '技能类型' },
  { key: '伤害类型', label: '伤害类型' },
  { key: '伤害子类', label: '伤害子类' },
  { key: '倍率关联', label: '倍率关联' },
  { key: '倍率', label: '倍率' },
  { key: '大招能量', label: '大招能量' },
  { key: '协奏能量', label: '协奏能量' },
  { key: '偏谐值', label: '偏谐值' },
  { key: '核心能量1', label: '核心能量1' },
  { key: '核心能量2', label: '核心能量2' },
  { key: '核心能量3', label: '核心能量3' },
]

const showSkillSearch = ref(false)
const isMinimized = ref(false)
const skillSearchQuery = ref('')
const skillSelectedCharacter = ref<string | null>(null)
const selectedActionName = ref('')
const skillSelectedAction = ref<ActionData | null>(null)
const allSkillData = ref<ActionData[]>([])

const panelPosition = ref({ x: 20, y: 80 })
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

const panelStyle = computed(() => ({
  left: panelPosition.value.x + 'px',
  top: panelPosition.value.y + 'px'
}))

const skillCharacters = computed(() => characterList)

function normalizeText(text: string) {
  return text.toLowerCase().replace(/[·・]/g, '')
}

const filteredSkillCharacters = computed(() => {
  if (!skillSearchQuery.value) return skillCharacters.value
  const normalizedQuery = normalizeText(skillSearchQuery.value)
  return skillCharacters.value.filter(char =>
    normalizeText(char).includes(normalizedQuery)
  )
})

const skillCharacterActions = computed(() => {
  if (!skillSelectedCharacter.value) return []
  
  const actions: ActionData[] = []
  let inCharacter = false
  let targetNames: string[] = [skillSelectedCharacter.value]
  
  if (mergedCharacters[skillSelectedCharacter.value]) {
    targetNames = mergedCharacters[skillSelectedCharacter.value]
  }
  
  allSkillData.value.forEach(item => {
    const name = item['角色/动作']
    if (!name) return
    
    const isTargetCharacter = targetNames.some(target => name === target)
    
    if (isTargetCharacter) {
      inCharacter = true
    } else if (inCharacter && characterList.includes(name) && !targetNames.includes(name)) {
      inCharacter = false
    } else if (inCharacter && name) {
      actions.push(item)
    }
  })
  
  return actions
})

const tableData = computed(() => {
  if (!skillSelectedAction.value) return []
  return paramList.map(param => ({
    param: param.label,
    value: skillSelectedAction.value![param.key]
  }))
})

async function loadSkillData() {
  try {
    const response = await fetch('/WutheringWavesDPS/wwac_data.json')
    allSkillData.value = await response.json()
  } catch (error) {
    console.error('加载技能数据失败:', error)
  }
}

function toggleSkillSearch() {
  showSkillSearch.value = !showSkillSearch.value
  if (showSkillSearch.value && allSkillData.value.length === 0) {
    loadSkillData()
  }
}



function toggleMinimize() {
  isMinimized.value = !isMinimized.value
}

function startDrag(event: MouseEvent) {
  if ((event.target as HTMLElement).closest('.panel-controls')) return
  isDragging.value = true
  dragOffset.value = {
    x: event.clientX - panelPosition.value.x,
    y: event.clientY - panelPosition.value.y
  }
  
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

function onDrag(event: MouseEvent) {
  if (!isDragging.value) return
  panelPosition.value = {
    x: event.clientX - dragOffset.value.x,
    y: event.clientY - dragOffset.value.y
  }
}

function stopDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

function handleCharacterChange() {
  selectedActionName.value = ''
  skillSelectedAction.value = null
}

function handleActionSelect(actionName: string) {
  const action = skillCharacterActions.value.find(a => a['角色/动作'] === actionName)
  if (action) {
    skillSelectedAction.value = action
  }
}

function copyParam(value: any) {
  if (value === undefined || value === null || value === '') return
  navigator.clipboard.writeText(String(value)).then(() => {
    ElMessage.success({ message: '已复制: ' + value, duration: 500 })
  }).catch(() => {
    ElMessage.error({ message: '复制失败', duration: 500 })
  })
}

onUnmounted(() => {
  stopDrag()
})

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
    ElMessage.error({ message: '加载模板失败', duration: 500 })
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
    ElMessage.error({ message: '加载预览失败: ' + (error as Error).message, duration: 500 })
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
    
    ElMessage.success({ message: '导入成功', duration: 500 })
  } catch (error) {
    console.error('[Calculator] 导入失败:', error)
    ElMessage.error({ message: '导入失败: ' + (error as Error).message, duration: 500 })
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
    ElMessage.warning({ message: '请先导入表格', duration: 500 })
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
      ElMessage.error({ message: '没有找到要发布的文件', duration: 500 })
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
      
      ElMessage.success({ message: '发布成功', duration: 500 })
      publishDialogVisible.value = false
      router.push('/community')
    } catch (error: any) {
      console.error('[Calculator] 发布失败:', error)
      ElMessage.error({ message: error.response?.data?.detail || '发布失败', duration: 500 })
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

.floating-skill-panel {
  position: fixed;
  z-index: 1000;
  width: 280px;
  background: rgba(15, 15, 26, 0.95);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(102, 126, 234, 0.4);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  user-select: none;
}

.floating-skill-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  border-bottom: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 12px 12px 0 0;
  cursor: move;
}

.floating-skill-panel .panel-title {
  font-size: 14px;
  font-weight: 700;
  color: #e2e8f0;
}

.floating-skill-panel .panel-controls {
  display: flex;
  gap: 6px;
}

.floating-skill-panel .panel-content {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
}

.floating-skill-panel .compact-search {
  width: 100%;
}

.floating-skill-panel .compact-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.floating-skill-panel .compact-select {
  flex: 1;
}

.floating-skill-panel .compact-params {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
}

.floating-skill-panel .param-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.floating-skill-panel .param-row:hover {
  background: rgba(102, 126, 234, 0.15);
}

.floating-skill-panel .param-label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
  flex-shrink: 0;
  min-width: 70px;
}

.floating-skill-panel .param-value {
  font-size: 12px;
  color: #e2e8f0;
  font-weight: 600;
  flex: 1;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 0 8px;
}

.floating-skill-panel .copy-icon-small {
  font-size: 12px;
  color: #a5b4fc;
  opacity: 0;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
}

.floating-skill-panel .param-row:hover .copy-icon-small {
  opacity: 1;
}

.floating-skill-panel :deep(.el-select) {
  width: 100%;
}

.floating-skill-panel :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset;
}

.floating-skill-panel :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.5) inset;
}

.floating-skill-panel :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.8) inset;
}

.floating-skill-panel :deep(.el-input__inner) {
  color: #e2e8f0;
}

.floating-skill-panel :deep(.el-select-dropdown) {
  background: rgba(15, 15, 26, 0.98);
  border: 1px solid rgba(102, 126, 234, 0.4);
}

.floating-skill-panel :deep(.el-select-dropdown__item) {
  color: #cbd5e1;
}

.floating-skill-panel :deep(.el-select-dropdown__item:hover) {
  background: rgba(102, 126, 234, 0.15);
  color: #fff;
}

.floating-skill-panel :deep(.el-select-dropdown__item.selected) {
  background: rgba(102, 126, 234, 0.3);
  color: #fff;
}

.floating-skill-panel :deep(.el-button--small) {
  padding: 4px 8px;
  height: 24px;
}

.floating-skill-panel :deep(.el-button--circle) {
  padding: 0;
  width: 24px;
  height: 24px;
}
</style>
