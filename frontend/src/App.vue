<template>
  <div class="app-container">
    <el-config-provider :locale="zhCn">
      <el-container class="main-layout">
        <el-header class="app-header">
          <div class="header-content">
            <div class="logo" @click="router.push('/')">
              <span class="logo-text">WutheringWavesDPS</span>
            </div>
            <nav class="nav-menu">
              <router-link to="/" class="nav-link">首页</router-link>
              <router-link to="/calculator" class="nav-link">工作区</router-link>
              <router-link to="/community" class="nav-link">社区</router-link>
            </nav>
            <div class="user-area">
              <template v-if="userStore.isAuthenticated">
                <el-dropdown @command="handleCommand">
                  <span class="user-dropdown">
                    <el-avatar :size="32" @click.stop="openEditDialog">
                      {{ userStore.user?.display_name?.[0] || userStore.user?.username?.[0] || 'U' }}
                    </el-avatar>
                    <span class="username">{{ userStore.user?.display_name || userStore.user?.username }}</span>
                    <el-icon><ArrowDown /></el-icon>
                  </span>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit">
                        <el-icon><Edit /></el-icon>
                        修改昵称
                      </el-dropdown-item>
                      <el-dropdown-item command="logout">
                        <el-icon><SwitchButton /></el-icon>
                        退出登录
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
              <template v-else>
                <el-button type="primary" @click="router.push('/login')">
                  登录
                </el-button>
              </template>
            </div>
          </div>
        </el-header>
        <el-main class="app-main">
          <router-view />
        </el-main>
        <el-footer class="app-footer">
          <p>WutheringWavesDPS Beta1.0</p>
        </el-footer>
      </el-container>
    </el-config-provider>

    <el-dialog v-model="editDialogVisible" title="修改昵称" width="400px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="昵称">
          <el-input v-model="editForm.display_name" placeholder="请输入昵称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleUpdateProfile">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { onMounted, ref, reactive } from 'vue'
import { ElConfigProvider, ElMessage } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { SwitchButton, ArrowDown, Edit } from '@element-plus/icons-vue'
import { useUserStore } from './stores/user'
import api from './api'

const router = useRouter()
const userStore = useUserStore()

const editDialogVisible = ref(false)
const editLoading = ref(false)
const editForm = reactive({
  display_name: ''
})

onMounted(() => {
  userStore.initialize()
})

function openEditDialog() {
  editForm.display_name = userStore.user?.display_name || userStore.user?.username || ''
  editDialogVisible.value = true
}

async function handleUpdateProfile() {
  editLoading.value = true
  try {
    await api.put('/auth/me', {
      display_name: editForm.display_name
    })
    await userStore.fetchCurrentUser()
    ElMessage.success('昵称已更新')
    editDialogVisible.value = false
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    editLoading.value = false
  }
}

const handleCommand = (command: string) => {
  switch (command) {
    case 'edit':
      openEditDialog()
      break
    case 'logout':
      userStore.logout()
      ElMessage.success('已退出登录')
      window.location.href = '/'
      break
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
}

.app-container {
  height: 100%;
  width: 100%;
}

.main-layout {
  height: 100%;
}

.app-header {
  background: #1a1a2e;
  border-bottom: 1px solid #2a2a3e;
  padding: 0 20px;
  height: 60px !important;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 1600px;
  margin: 0 auto;
}

.logo {
  cursor: pointer;
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.nav-menu {
  display: flex;
  gap: 20px;
}

.nav-link {
  color: #a0a0a0;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: all 0.3s;
}

.nav-link:hover {
  color: #409eff;
}

.nav-link.router-link-active {
  color: #409eff;
}

.user-area {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #fff;
}

.username {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-main {
  background: #0a0a0f;
  padding: 20px;
  overflow: auto;
}

.app-footer {
  background: #1a1a2e;
  border-top: 1px solid #2a2a3e;
  height: auto !important;
  padding: 16px;
  text-align: center;
}

.app-footer p {
  margin: 0;
  color: #666;
  font-size: 13px;
}
</style>
