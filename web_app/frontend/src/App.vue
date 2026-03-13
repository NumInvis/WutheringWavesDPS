<template>
  <div id="app">
    <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside width="220px" class="sidebar">
        <div class="logo">
          <el-icon size="28"><DataAnalysis /></el-icon>
          <span>鸣潮动作数据</span>
        </div>
        <el-menu
          :default-active="$route.path"
          router
          class="nav-menu"
          background-color="#1a1a2e"
          text-color="#b8b9c0"
          active-text-color="#409eff"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/characters">
            <el-icon><UserFilled /></el-icon>
            <span>角色数据库</span>
          </el-menu-item>
          <el-menu-item index="/actions">
            <el-icon><Collection /></el-icon>
            <span>动作查询</span>
          </el-menu-item>
          <el-menu-item index="/echoes">
            <el-icon><MagicStick /></el-icon>
            <span>声骸数据库</span>
          </el-menu-item>
          <el-menu-item index="/calculator">
            <el-icon><Calculator /></el-icon>
            <span>伤害计算器</span>
          </el-menu-item>
        </el-menu>
        
        <div class="sidebar-footer">
          <p>数据版本: v1.0</p>
          <p>动作数据汇总</p>
        </div>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <h2>{{ $route.meta.title || '鸣潮动作数据汇总' }}</h2>
          </div>
          <div class="header-right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索角色或动作..."
              class="search-input"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </el-header>
        
        <el-main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      searchQuery: ''
    }
  },
  methods: {
    handleSearch() {
      if (this.searchQuery.trim()) {
        this.$router.push({
          path: '/actions',
          query: { search: this.searchQuery.trim() }
        })
      }
    }
  }
}
</script>

<style>
#app {
  height: 100vh;
}

.layout-container {
  height: 100%;
}

.sidebar {
  background: #1a1a2e;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #2a2a3e;
}

.logo .el-icon {
  color: #409eff;
}

.nav-menu {
  flex: 1;
  border-right: none;
}

.nav-menu .el-menu-item {
  font-size: 14px;
}

.nav-menu .el-menu-item .el-icon {
  font-size: 18px;
  margin-right: 8px;
}

.sidebar-footer {
  padding: 15px;
  text-align: center;
  color: #666;
  font-size: 12px;
  border-top: 1px solid #2a2a3e;
}

.sidebar-footer p {
  margin: 5px 0;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.search-input {
  width: 300px;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 全局样式 */
.page-container {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  min-height: calc(100vh - 140px);
}

.page-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.page-header h3 {
  margin: 0 0 10px 0;
  font-size: 18px;
  color: #303133;
}

.filter-bar {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.stat-card h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  opacity: 0.9;
}

.stat-card .number {
  font-size: 32px;
  font-weight: bold;
}
</style>
