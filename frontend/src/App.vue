<template>
  <el-config-provider :locale="zhCn">
    <div id="app" class="cyber-bg grid-bg">
      <div class="particles-container">
        <div 
          v-for="i in 20" 
          :key="i" 
          class="particle"
          :style="particleStyle(i)"
        ></div>
      </div>
      
      <el-container class="app-container">
        <el-header class="app-header">
          <div class="header-left">
            <router-link to="/" class="logo-link">
              <div class="logo-container">
                <span class="logo-icon">⚡</span>
                <h1 class="app-title">
                  <span class="glitch-text">鸣潮</span>
                  <span class="glow-text">排轴DPS计算器</span>
                </h1>
              </div>
            </router-link>
          </div>
          
          <div class="header-nav">
            <router-link 
              v-slot="{ isActive }" 
              to="/" 
              custom
            >
              <el-button 
                link 
                :class="['nav-link', { active: isActive }]"
                @click="$router.push('/')"
              >
                <el-icon><HomeFilled /></el-icon>
                首页
              </el-button>
            </router-link>
            <router-link 
              v-slot="{ isActive }" 
              to="/calculator" 
              custom
            >
              <el-button 
                link 
                :class="['nav-link', { active: isActive }]"
                @click="$router.push('/calculator')"
              >
                <el-icon><Cpu /></el-icon>
                计算器
              </el-button>
            </router-link>
            <router-link 
              v-slot="{ isActive }" 
              to="/community" 
              custom
            >
              <el-button 
                link 
                :class="['nav-link', { active: isActive }]"
                @click="$router.push('/community')"
              >
                <el-icon><ChatDotRound /></el-icon>
                社区
              </el-button>
            </router-link>
          </div>
          
          <div class="header-right">
            <template v-if="userStore.isAuthenticated">
              <el-dropdown @command="handleCommand">
                <span class="user-dropdown">
                  <el-avatar :size="36" :src="userStore.user?.avatar_url" class="user-avatar">
                    {{ userStore.displayName?.charAt(0)?.toUpperCase() || 'U' }}
                  </el-avatar>
                  <div class="user-info">
                    <span class="username">{{ userStore.displayName || userStore.username }}</span>
                    <el-tag v-if="userStore.user?.is_admin" size="small" type="danger" effect="dark" class="admin-tag">
                      管理员
                    </el-tag>
                  </div>
                  <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu class="cyber-dropdown">
                    <el-dropdown-item command="profile" class="cyber-dropdown-item">
                      <el-icon><User /></el-icon>
                      个人中心
                    </el-dropdown-item>
                    <el-dropdown-item command="my-spreadsheets" class="cyber-dropdown-item">
                      <el-icon><Document /></el-icon>
                      我的表格
                    </el-dropdown-item>
                    <el-dropdown-item divided command="logout" class="cyber-dropdown-item danger">
                      <el-icon><SwitchButton /></el-icon>
                      退出登录
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
            <template v-else>
              <el-button class="cyber-btn" @click="$router.push('/login')">
                登录
              </el-button>
              <el-button type="primary" class="cyber-btn-primary" @click="$router.push('/register')">
                注册
              </el-button>
            </template>
          </div>
        </el-header>
        
        <el-main class="app-main">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
        
        <el-footer class="app-footer">
          <div class="footer-content">
            <div class="footer-left">
              <span class="footer-icon">⚡</span>
              <p>© 2026 鸣潮排轴DPS计算器 - 开源项目</p>
            </div>
            <div class="footer-right">
              <span class="status-dot online"></span>
              <span class="status-text">系统运行中</span>
            </div>
          </div>
        </el-footer>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowDown, 
  HomeFilled, 
  Cpu, 
  ChatDotRound,
  User,
  Document,
  SwitchButton
} from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { useUserStore } from './stores/user'

const router = useRouter()
const userStore = useUserStore()

const particleStyle = (i: number) => {
  const left = Math.random() * 100
  const delay = Math.random() * 5
  const duration = 3 + Math.random() * 2
  const size = 2 + Math.random() * 4
  return {
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
    width: `${size}px`,
    height: `${size}px`
  }
}

onMounted(() => {
  userStore.initialize()
})

async function handleCommand(command: string) {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'my-spreadsheets':
      router.push('/my-spreadsheets')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '安全提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
          customClass: 'cyber-message-box'
        })
        userStore.logout()
        ElMessage.success('已安全退出登录')
        router.push('/')
      } catch {
      }
      break
  }
}
</script>

<style scoped>
.particles-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.particle {
  position: absolute;
  bottom: -10px;
  background: radial-gradient(circle, var(--primary-color) 0%, transparent 70%);
  border-radius: 50%;
  animation: particle-float linear infinite;
}

@keyframes particle-float {
  0% {
    transform: translateY(0) scale(1);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100vh) scale(0);
    opacity: 0;
  }
}

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

.app-header {
  background: linear-gradient(
    180deg,
    rgba(18, 18, 26, 0.95) 0%,
    rgba(18, 18, 26, 0.85) 100%
  );
  backdrop-filter: blur(10px);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo-link {
  text-decoration: none;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 28px;
  animation: float 3s ease-in-out infinite;
}

.app-title {
  font-size: 18px;
  margin: 0;
  display: flex;
  gap: 6px;
  font-weight: 600;
}

.glitch-text {
  color: var(--accent-color);
  position: relative;
  animation: glitch 4s infinite;
}

.glow-text {
  color: var(--primary-color);
  text-shadow: 0 0 10px var(--primary-color),
               0 0 20px var(--primary-color);
}

.header-nav {
  display: flex;
  gap: 5px;
}

.nav-link {
  color: var(--text-secondary) !important;
  font-size: 15px;
  padding: 8px 20px;
  border-radius: 6px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-link:hover {
  color: var(--primary-color) !important;
  background: rgba(0, 212, 255, 0.1);
}

.nav-link.active {
  color: var(--primary-color) !important;
  background: linear-gradient(
    135deg,
    rgba(0, 212, 255, 0.15) 0%,
    rgba(0, 212, 255, 0.05) 100%
  );
  border: 1px solid rgba(0, 212, 255, 0.3);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cyber-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.cyber-btn:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: rgba(0, 212, 255, 0.3);
  color: var(--primary-color);
}

.cyber-btn-primary {
  background: linear-gradient(
    135deg,
    var(--primary-color) 0%,
    var(--secondary-color) 100%
  );
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
  transition: all 0.3s ease;
}

.cyber-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 212, 255, 0.4);
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  color: white;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.user-dropdown:hover {
  background: rgba(0, 212, 255, 0.1);
}

.user-avatar {
  border: 2px solid var(--primary-color);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.username {
  font-size: 14px;
  font-weight: 500;
}

.admin-tag {
  font-size: 10px;
  padding: 0 4px;
  height: 16px;
  line-height: 14px;
}

.dropdown-icon {
  font-size: 12px;
  color: var(--text-muted);
  transition: transform 0.3s ease;
}

.user-dropdown:hover .dropdown-icon {
  color: var(--primary-color);
  transform: translateY(2px);
}

.cyber-dropdown {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.cyber-dropdown-item {
  color: var(--text-secondary);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.cyber-dropdown-item:hover {
  background: rgba(0, 212, 255, 0.1);
  color: var(--primary-color);
}

.cyber-dropdown-item.danger:hover {
  background: rgba(255, 68, 68, 0.1);
  color: var(--danger-color);
}

.app-main {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: transparent;
}

.app-footer {
  padding: 16px 30px;
  background: linear-gradient(
    0deg,
    rgba(18, 18, 26, 0.95) 0%,
    rgba(18, 18, 26, 0.85) 100%
  );
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(0, 212, 255, 0.1);
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.footer-icon {
  font-size: 20px;
  animation: glow-pulse 2s ease-in-out infinite;
}

.footer-left p {
  margin: 0;
  color: var(--text-muted);
  font-size: 13px;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success-color);
  box-shadow: 0 0 10px var(--success-color);
  animation: glow-pulse 1.5s ease-in-out infinite;
}

.status-text {
  color: var(--success-color);
  font-size: 13px;
}
</style>
