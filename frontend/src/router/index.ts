import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { guest: true }
  },
  {
    path: '/calculator',
    name: 'Calculator',
    component: () => import('@/views/Calculator.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/community',
    name: 'Community',
    component: () => import('@/views/Community.vue')
  },
  {
    path: '/tier-list',
    name: 'TierList',
    component: () => import('@/views/TierList.vue')
  },
  {
    path: '/admin/logs',
    name: 'AdminLogs',
    component: () => import('@/views/AdminLogs.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/test-sheet',
    name: 'TestSheet',
    component: () => import('@/views/Calculator-simple.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/test',
    name: 'Test',
    component: () => import('@/views/Test.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory('/WutheringWavesDPS/'),
  routes
})

// 白名单路由（不需要登录）
const whiteList = ['/', '/login', '/register', '/community', '/test']

router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()
  
  // 初始化用户状态
  if (!userStore.user && userStore.token) {
    try {
      await userStore.fetchCurrentUser()
    } catch (error) {
      console.error('Failed to fetch user:', error)
      userStore.logout()
    }
  }
  
  // 1. 管理员权限检查（最高优先级）
  if (to.meta.requiresAdmin) {
    if (!userStore.isAuthenticated) {
      ElMessage.warning({ message: '请先登录', duration: 2000 })
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
    if (!userStore.user?.is_admin) {
      ElMessage.error({ message: '需要管理员权限', duration: 2000 })
      next('/')
      return
    }
  }
  
  // 2. 需要登录的路由
  if (to.meta.requiresAuth) {
    if (!userStore.isAuthenticated) {
      ElMessage.warning({ message: '请先登录后访问', duration: 2000 })
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
  }
  
  // 3. 游客专属路由（登录后不能访问）
  if (to.meta.guest && userStore.isAuthenticated) {
    ElMessage.info({ message: '您已登录，无需再次访问', duration: 2000 })
    next('/')
    return
  }
  
  // 4. 默认放行
  next()
})

// 路由错误处理
router.onError((error) => {
  console.error('Router error:', error)
  ElMessage.error({ message: '页面加载失败，请刷新重试', duration: 2000 })
})

export default router
