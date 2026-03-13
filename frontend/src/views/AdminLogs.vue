<template>
  <div class="admin-logs">
    <el-card class="logs-card">
      <template #header>
        <div class="card-header">
          <span>系统日志</span>
          <div class="header-actions">
            <el-button @click="refreshLogs" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="danger" @click="clearLogs">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
          </div>
        </div>
      </template>

      <div class="logs-filter">
        <el-radio-group v-model="logLevel" @change="filterLogs">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="info">信息</el-radio-button>
          <el-radio-button label="warn">警告</el-radio-button>
          <el-radio-button label="error">错误</el-radio-button>
        </el-radio-group>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索日志..."
          clearable
          style="width: 300px"
          @input="filterLogs"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <div class="logs-container" v-loading="loading">
        <div v-if="filteredLogs.length === 0" class="empty-logs">
          <el-empty description="暂无日志" />
        </div>
        <div v-else class="logs-list">
          <div
            v-for="(log, index) in filteredLogs"
            :key="index"
            class="log-item"
            :class="log.level"
          >
            <div class="log-header">
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <el-tag :type="getLogType(log.level)" size="small">
                {{ log.level.toUpperCase() }}
              </el-tag>
            </div>
            <div class="log-message">{{ log.message }}</div>
            <div v-if="log.details" class="log-details">
              <pre>{{ JSON.stringify(log.details, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>

      <div class="logs-pagination" v-if="filteredLogs.length > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredLogs.length"
          :page-sizes="[50, 100, 200]"
          layout="total, sizes, prev, pager, next"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete, Search } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'

interface LogEntry {
  timestamp: number
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
  details?: any
}

const router = useRouter()
const userStore = useUserStore()

const logs = ref<LogEntry[]>([])
const loading = ref(false)
const logLevel = ref('all')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(100)
const refreshInterval = ref<number | null>(null)

// 检查是否为管理员
onMounted(() => {
  if (!userStore.user?.is_admin) {
    ElMessage.error('需要管理员权限')
    router.push('/')
    return
  }
  
  fetchLogs()
  
  // 每5秒刷新一次日志（不使用实时订阅避免递归更新）
  refreshInterval.value = window.setInterval(() => {
    loadLocalLogs()
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
})

async function fetchLogs() {
  loading.value = true
  try {
    // 从本地存储加载日志
    loadLocalLogs()
  } catch (error) {
    console.error('获取日志失败:', error)
  } finally {
    loading.value = false
  }
}

function loadLocalLogs() {
  // 从localStorage加载本地日志
  const localLogs = localStorage.getItem('app_logs')
  if (localLogs) {
    try {
      logs.value = JSON.parse(localLogs)
    } catch (e) {
      logs.value = []
    }
  }
}

const filteredLogs = computed(() => {
  let result = logs.value

  // 按级别筛选
  if (logLevel.value !== 'all') {
    result = result.filter(log => log.level === logLevel.value)
  }

  // 按关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(log => 
      log.message.toLowerCase().includes(keyword) ||
      JSON.stringify(log.details).toLowerCase().includes(keyword)
    )
  }

  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

function filterLogs() {
  currentPage.value = 1
}

function refreshLogs() {
  fetchLogs()
  ElMessage.success('日志已刷新')
}

async function clearLogs() {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有日志吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '清空',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    logs.value = []
    localStorage.removeItem('app_logs')
    ElMessage.success('日志已清空')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清空失败')
    }
  }
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function getLogType(level: string): string {
  // 确保level是字符串
  const safeLevel = String(level || '').toLowerCase()
  
  const typeMap: Record<string, string> = {
    'info': 'info',
    'warn': 'warning',
    'error': 'danger',
    'debug': 'info'
  }
  
  // 如果level不在map中，返回'info'作为默认值
  const result = typeMap[safeLevel]
  if (!result) {
    console.warn('[AdminLogs] Unknown log level:', level, 'using default')
    return 'info'
  }
  return result
}
</script>

<style scoped>
.admin-logs {
  max-width: 1400px;
  margin: 0 auto;
}

.logs-card {
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

.logs-filter {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #2a2a3e;
}

.logs-container {
  min-height: 400px;
}

.empty-logs {
  padding: 60px 0;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-item {
  padding: 12px 16px;
  background: #1a1a2e;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}

.log-item.info {
  border-left-color: #409eff;
}

.log-item.warn {
  border-left-color: #e6a23c;
}

.log-item.error {
  border-left-color: #f56c6c;
}

.log-item.debug {
  border-left-color: #909399;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.log-time {
  font-size: 12px;
  color: #888;
  font-family: monospace;
}

.log-message {
  font-size: 14px;
  color: #fff;
  word-break: break-all;
}

.log-details {
  margin-top: 8px;
  padding: 8px;
  background: #0a0a0f;
  border-radius: 4px;
}

.log-details pre {
  margin: 0;
  font-size: 12px;
  color: #888;
  overflow-x: auto;
}

.logs-pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
