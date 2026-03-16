<template>
  <div class="security-config">
    <div class="config-section">
      <h3><el-icon><Lock /></el-icon> IP白名单</h3>
      <p class="desc">白名单IP不受任何限制，优先级最高</p>
      <div class="ip-list">
        <el-tag v-for="ip in whitelist" :key="ip" closable @close="removeWhitelist(ip)" type="success">{{ ip }}</el-tag>
      </div>
      <div class="add-form">
        <el-input v-model="newWhitelistIp" placeholder="输入IP地址" size="small" style="width: 150px;" />
        <el-button type="success" size="small" @click="addWhitelist">添加</el-button>
      </div>
    </div>

    <div class="config-section">
      <h3><el-icon><Lock /></el-icon> IP黑名单</h3>
      <p class="desc">黑名单IP将被完全阻止访问</p>
      <div class="ip-list">
        <el-tag v-for="ip in blacklist" :key="ip" closable @close="removeBlacklist(ip)" type="danger">{{ ip }}</el-tag>
        <span v-if="blacklist.length === 0" class="empty">暂无黑名单</span>
      </div>
      <div class="add-form">
        <el-input v-model="newBlacklistIp" placeholder="输入IP地址" size="small" style="width: 150px;" />
        <el-button type="danger" size="small" @click="addBlacklist">添加</el-button>
      </div>
    </div>

    <div class="config-section">
      <h3><el-icon><Setting /></el-icon> 速率限制</h3>
      <div class="config-item">
        <span class="label">API请求限制 (次/分钟)</span>
        <el-input-number v-model="rateLimit.apiLimit" :min="10" :max="500" size="small" />
      </div>
      <div class="config-item">
        <span class="label">页面请求限制 (次/分钟)</span>
        <el-input-number v-model="rateLimit.pageLimit" :min="50" :max="1000" size="small" />
      </div>
    </div>

    <div class="config-section">
      <h3><el-icon><Monitor /></el-icon> 爬虫检测</h3>
      <div class="config-item">
        <span class="label">启用User-Agent检测</span>
        <el-switch v-model="crawlerDetection.enabled" />
      </div>
      <div class="blocked-agents">
        <span class="label">拦截的User-Agent关键词:</span>
        <el-tag v-for="agent in crawlerDetection.blockedAgents" :key="agent" size="small" style="margin: 2px;">{{ agent }}</el-tag>
      </div>
    </div>

    <div class="config-section">
      <h3><el-icon><DataLine /></el-icon> 实时监控</h3>
      <div class="monitor-stats">
        <div class="stat">
          <span class="v">{{ stats.totalRequests }}</span>
          <span class="l">今日请求</span>
        </div>
        <div class="stat">
          <span class="v">{{ stats.blockedRequests }}</span>
          <span class="l">已拦截</span>
        </div>
        <div class="stat">
          <span class="v">{{ stats.activeIps }}</span>
          <span class="l">活跃IP</span>
        </div>
      </div>
    </div>

    <div class="actions">
      <el-button type="primary" @click="saveConfig">保存配置</el-button>
      <el-button @click="loadConfig">重置</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock, Setting, Monitor, DataLine } from '@element-plus/icons-vue'
import api from '../api'

const whitelist = ref<string[]>(['111.18.157.89', '127.0.0.1', '::1'])
const blacklist = ref<string[]>([])
const newWhitelistIp = ref('')
const newBlacklistIp = ref('')

const rateLimit = ref({
  apiLimit: 60,
  pageLimit: 200
})

const crawlerDetection = ref({
  enabled: true,
  blockedAgents: ['bot', 'crawler', 'spider', 'scraper', 'python-requests', 'selenium', 'phantomjs']
})

const stats = ref({
  totalRequests: 0,
  blockedRequests: 0,
  activeIps: 0
})

function addWhitelist() {
  if (newWhitelistIp.value && !whitelist.value.includes(newWhitelistIp.value)) {
    whitelist.value.push(newWhitelistIp.value)
    newWhitelistIp.value = ''
  }
}

function removeWhitelist(ip: string) {
  whitelist.value = whitelist.value.filter(i => i !== ip)
}

function addBlacklist() {
  if (newBlacklistIp.value && !blacklist.value.includes(newBlacklistIp.value)) {
    blacklist.value.push(newBlacklistIp.value)
    newBlacklistIp.value = ''
  }
}

function removeBlacklist(ip: string) {
  blacklist.value = blacklist.value.filter(i => i !== ip)
}

async function loadConfig() {
  try {
    const data = await api.get('/admin/security-config')
    if (data.whitelist) whitelist.value = data.whitelist
    if (data.blacklist) blacklist.value = data.blacklist
    if (data.rateLimit) rateLimit.value = data.rateLimit
    if (data.crawlerDetection) crawlerDetection.value = data.crawlerDetection
    if (data.stats) stats.value = data.stats
  } catch (error) {
    console.error('加载安全配置失败:', error)
  }
}

async function saveConfig() {
  try {
    await api.post('/admin/security-config', {
      whitelist: whitelist.value,
      blacklist: blacklist.value,
      rateLimit: rateLimit.value,
      crawlerDetection: crawlerDetection.value
    })
    ElMessage.success({ message: '配置已保存', duration: 500 })
  } catch (error) {
    ElMessage.error({ message: '保存失败', duration: 500 })
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.security-config { padding: 16px; }

.config-section { background: rgba(26, 26, 40, 0.6); border-radius: 8px; padding: 14px; margin-bottom: 14px; border: 1px solid rgba(102, 126, 234, 0.12); }
.config-section h3 { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #fff; margin: 0 0 6px 0; }
.config-section h3 .el-icon { color: #667eea; }
.config-section .desc { font-size: 12px; color: #808090; margin: 0 0 10px 0; }

.ip-list { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; min-height: 28px; }
.ip-list .empty { font-size: 12px; color: #808090; }

.add-form { display: flex; gap: 8px; }

.config-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(102, 126, 234, 0.06); }
.config-item:last-child { border-bottom: none; }
.config-item .label { font-size: 13px; color: #a0a0b0; }

.blocked-agents { margin-top: 10px; }
.blocked-agents .label { display: block; font-size: 12px; color: #808090; margin-bottom: 6px; }

.monitor-stats { display: flex; gap: 16px; }
.monitor-stats .stat { display: flex; flex-direction: column; align-items: center; padding: 10px 20px; background: rgba(102, 126, 234, 0.1); border-radius: 8px; }
.monitor-stats .stat .v { font-size: 20px; font-weight: 600; color: #667eea; }
.monitor-stats .stat .l { font-size: 11px; color: #808090; }

.actions { display: flex; gap: 10px; justify-content: flex-end; }
</style>
