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
              <span class="log-time">{{ log.datetime || formatTime(log.timestamp) }}</span>
              <el-tag :type="getLogType(log.level || 'info')" size="small">
                {{ (log.level || 'info').toUpperCase() }}
              </el-tag>
              <span v-if="log.user" class="log-user">用户：{{ log.user }}</span>
              <span v-if="log.ip" class="log-ip">IP: {{ log.ip }}</span>
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
import api from '../api'

interface LogEntry {
  timestamp: number
  datetime: string
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
  details?: any
  user?: string
  ip?: string
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
  
  // 每 3 秒刷新一次日志
  refreshInterval.value = window.setInterval(() => {
    fetchLogs()
  }, 3000)
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
})

async function fetchLogs() {
  loading.value = true
  try {
    const data = await api.get('/admin/logs', {
      params: {
        level: logLevel.value !== 'all' ? logLevel.value : undefined,
        limit: 200
      }
    })
    logs.value = data.logs || []
  } catch (error) {
    console.error('获取日志失败:', error)
  } finally {
    loading.value = false
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
      JSON.stringify(log.details || {}).toLowerCase().includes(keyword) ||
      (log.user || '').toLowerCase().includes(keyword) ||
      (log.ip || '').toLowerCase().includes(keyword)
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
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(15, 15, 26, 0.75);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.logs-card :deep(.el-card__header) {
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 16px 24px;
}

.logs-card :deep(.el-card__body) {
  padding: 24px;
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

.logs-filter {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-wrap: wrap;
  gap: 16px;
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
  gap: 12px;
}

.log-item {
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-left: 4px solid #409eff;
  transition: all 0.25s ease;
}

.log-item:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.log-item.info {
  border-left-color: #60a5fa;
  background: rgba(96, 165, 250, 0.08);
}

.log-item.warn {
  border-left-color: #fbbf24;
  background: rgba(251, 191, 36, 0.08);
}

.log-item.error {
  border-left-color: #f87171;
  background: rgba(248, 113, 113, 0.08);
}

.log-item.debug {
  border-left-color: #94a3b8;
  background: rgba(148, 163, 184, 0.08);
}

.log-header {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
  flex-wrap: wrap;
}

.log-time {
  font-size: 13px;
  color: #94a3b8;
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
  background: rgba(255, 255, 255, 0.05);
  padding: 4px 10px;
  border-radius: 6px;
}

.log-message {
  font-size: 15px;
  color: #e2e8f0;
  word-break: break-all;
  line-height: 1.6;
}

.log-details {
  margin-top: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.log-details pre {
  margin: 0;
  font-size: 12px;
  color: #94a3b8;
  overflow-x: auto;
  line-height: 1.5;
}

.logs-pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>
