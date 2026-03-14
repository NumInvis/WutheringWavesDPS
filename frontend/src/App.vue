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
              <router-link v-if="isAdmin" to="/admin/logs" class="nav-link">日志</router-link>
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
                      <el-dropdown-item command="change_password">
                        <el-icon><Lock /></el-icon>
                        修改密码
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
          <router-view v-slot="{ Component, route }">
            <keep-alive :include="['Calculator']">
              <component :is="Component" :key="route.fullPath" v-if="route.meta.keepAlive !== false" />
            </keep-alive>
            <component :is="Component" v-if="route.meta.keepAlive === false" :key="route.fullPath" />
          </router-view>
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

    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="400px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" placeholder="请输入原密码" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" placeholder="请输入新密码" show-password />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="password" placeholder="请再次输入新密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { onMounted, ref, reactive, computed } from 'vue'
import { ElConfigProvider, ElMessage } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { SwitchButton, ArrowDown, Edit, Lock } from '@element-plus/icons-vue'
import { useUserStore } from './stores/user'
import api from './api'

const router = useRouter()
const userStore = useUserStore()

// 计算属性：是否为管理员
const isAdmin = computed(() => {
  return userStore.user?.is_admin === true
})

const editDialogVisible = ref(false)
const editLoading = ref(false)
const editForm = reactive({
  display_name: ''
})

const passwordDialogVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref()
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validatePasswordFormat = (rule: any, value: string, callback: any) => {
  if (!/^[a-zA-Z0-9]+$/.test(value)) {
    callback(new Error('密码只能是字母和数字，不能包含其他字符'))
  } else {
    callback()
  }
}

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9]+$/, message: '密码只能是字母和数字', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9]+$/, message: '密码只能是字母和数字，不能包含其他字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

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

function openPasswordDialog() {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  passwordDialogVisible.value = true
}

async function handleChangePassword() {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    
    passwordLoading.value = true
    try {
      const response = await api.post('/auth/change-password', {
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      console.log('密码修改成功:', response)
      ElMessage.success('密码已修改，请重新登录')
      passwordDialogVisible.value = false
      userStore.logout()
      setTimeout(() => {
        router.push('/login')
      }, 1000)
    } catch (error: any) {
      console.error('修改密码失败:', error)
      ElMessage.error(error.response?.data?.detail || '修改密码失败')
    } finally {
      passwordLoading.value = false
    }
  })
}

const handleCommand = (command: string) => {
  switch (command) {
    case 'edit':
      openEditDialog()
      break
    case 'change_password':
      openPasswordDialog()
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
