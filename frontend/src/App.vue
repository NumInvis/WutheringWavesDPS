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
              <router-link to="/tier-list" class="nav-link">排行</router-link>
              <el-dropdown trigger="hover" class="nav-link more-dropdown">
                <span class="more-label">
                  更多
                  <el-icon><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu class="more-dropdown-menu">
                    <div class="dropdown-header">友情链接</div>
                    <el-dropdown-item>
                      <a href="https://github.com/NumInvis" target="_blank" rel="noopener noreferrer" class="dropdown-item-link">
                        <el-icon><User /></el-icon>
                        <span>GitHub 主页</span>
                      </a>
                    </el-dropdown-item>
                    <el-dropdown-item>
                      <a href="https://www.kdocs.cn/l/chWXEqFmFGvu" target="_blank" rel="noopener noreferrer" class="dropdown-item-link">
                        <el-icon><Document /></el-icon>
                        <span>鸣潮动作数据汇总</span>
                      </a>
                    </el-dropdown-item>
                    <el-dropdown-item>
                      <a href="https://encore.moe/" target="_blank" rel="noopener noreferrer" class="dropdown-item-link">
                        <el-icon><Link /></el-icon>
                        <span>安可网</span>
                      </a>
                    </el-dropdown-item>
                    <el-dropdown-item>
                      <a href="https://ww.nanoka.cc/" target="_blank" rel="noopener noreferrer" class="dropdown-item-link">
                        <el-icon><Platform /></el-icon>
                        <span>鸣潮数据库</span>
                      </a>
                    </el-dropdown-item>
                    <el-dropdown-item>
                      <a href="https://space.bilibili.com/274736623?spm_id_from=333.788.0.0" target="_blank" rel="noopener noreferrer" class="dropdown-item-link">
                        <el-icon><VideoPlay /></el-icon>
                        <span>鬼神莫能窥的B站</span>
                      </a>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <router-link v-if="isAdmin" to="/admin/dashboard" class="nav-link">监控中心</router-link>
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
import { SwitchButton, ArrowDown, Edit, Lock, User, Document, Link, Platform, VideoPlay } from '@element-plus/icons-vue'
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
  
  // 预加载壁纸 - 使用 requestIdleCallback 和 link preload 确保快速加载
  if ('requestIdleCallback' in window) {
    (window as any).requestIdleCallback(() => {
      preloadBackgroundImage()
    })
  } else {
    setTimeout(preloadBackgroundImage, 100)
  }
})

// 预加载背景图片
function preloadBackgroundImage() {
  const img = new Image()
  img.src = '/picture.webp'
  img.crossOrigin = 'anonymous'
  
  // 添加 link preload 到 head
  const link = document.createElement('link')
  link.rel = 'preload'
  link.as = 'image'
  link.href = '/picture.webp'
  document.head.appendChild(link)
  
  console.log('[App] Background image preloaded')
}

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
    ElMessage.success({
      message: '昵称已更新',
      duration: 2000
    })
    editDialogVisible.value = false
  } catch (error) {
    ElMessage.error({ message: '更新失败', duration: 2000 })
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
      ElMessage.success({ message: '密码已修改，请重新登录', duration: 2000 })
      passwordDialogVisible.value = false
      userStore.logout()
      setTimeout(() => {
        router.push('/login')
      }, 1000)
    } catch (error: any) {
      console.error('修改密码失败:', error)
      ElMessage.error({ message: error.response?.data?.detail || '修改密码失败', duration: 2000 })
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
      ElMessage.success({ message: '已退出登录', duration: 2000 })
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
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.app-container {
  height: 100%;
  width: 100%;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
  background-attachment: fixed;
  position: relative;
}

.app-container::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/picture.webp');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.15;
  z-index: 0;
  pointer-events: none;
}

.main-layout {
  height: 100%;
}

.app-header {
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0 20px;
  height: 64px !important;
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
  transition: transform 0.2s ease;
}

.logo:hover {
  transform: scale(1.02);
}

.logo-text {
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.3px;
}

.nav-menu {
  display: flex;
  gap: 8px;
}

.nav-link {
  color: #cbd5e1;
  text-decoration: none;
  padding: 10px 18px;
  border-radius: 8px;
  transition: all 0.25s ease;
  font-weight: 500;
  font-size: 14px;
  position: relative;
}

.nav-link:hover {
  color: #fff;
  background: rgba(102, 126, 234, 0.2);
}

.nav-link.router-link-active {
  color: #fff;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.more-dropdown {
  display: flex;
  align-items: center;
}

.more-label {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.more-label .el-icon {
  font-size: 12px;
  transition: transform 0.2s ease;
}

.more-dropdown:hover .more-label .el-icon {
  transform: rotate(180deg);
}

.dropdown-section {
  padding: 8px 0;
}

.dropdown-section-title {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dropdown-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  color: #e2e8f0;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.dropdown-link:hover {
  background: rgba(102, 126, 234, 0.2);
  color: #fff;
}

.dropdown-link .el-icon {
  font-size: 16px;
  color: #a5b4fc;
}

.user-area {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: #e2e8f0;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.25s ease;
  background: rgba(255, 255, 255, 0.1);
}

.user-dropdown:hover {
  background: rgba(255, 255, 255, 0.15);
}

.username {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.app-main {
  padding: 24px;
  overflow: auto;
}

.app-footer {
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  height: auto !important;
  padding: 20px;
  text-align: center;
}

.app-footer p {
  margin: 0;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
}
</style>

<style>
.more-dropdown-menu {
  background: #1a1a2e !important;
  border: 1px solid rgba(167, 139, 250, 0.3) !important;
  border-radius: 12px !important;
  box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.7) !important;
  padding: 8px !important;
}

.more-dropdown-menu .dropdown-header {
  padding: 8px 12px 4px 12px;
  font-size: 12px;
  font-weight: 700;
  color: #a78bfa;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.more-dropdown-menu .el-dropdown-menu__item {
  padding: 0 !important;
  margin: 4px !important;
  border-radius: 8px !important;
  background: transparent !important;
}

.more-dropdown-menu .el-dropdown-menu__item:hover {
  background: rgba(167, 139, 250, 0.2) !important;
}

.dropdown-item-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: #ffffff;
  text-decoration: none;
  font-weight: 700;
  font-size: 15px;
  width: 100%;
}

.dropdown-item-link:hover {
  color: #ffffff;
}

.dropdown-item-link .el-icon {
  font-size: 18px;
  color: #a78bfa;
}
</style>
