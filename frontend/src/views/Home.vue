<template>
  <div class="home">
    <div class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <el-icon><Lightning /></el-icon>
          <span>v3.0 全新升级</span>
        </div>
        
        <h1 class="hero-title">
          <span class="title-line-1">鸣潮排轴</span>
          <span class="title-line-2">
            <span class="glitch">DPS</span>
            <span class="glow">计算器</span>
          </span>
        </h1>
        
        <p class="hero-description">
          面向多用户的开源协作平台<br>
          提供完整的Excel级表格功能，助力你的排轴之路
        </p>
        
        <div class="hero-actions">
          <el-button size="large" class="cyber-btn-primary" @click="$router.push('/calculator')">
            <el-icon><Cpu /></el-icon>
            立即开始
          </el-button>
          <el-button size="large" class="cyber-btn-outline" @click="$router.push('/community')">
            <el-icon><ChatDotRound /></el-icon>
            浏览社区
          </el-button>
        </div>
        
        <div class="hero-stats">
          <div class="stat-item">
            <div class="stat-number">20+</div>
            <div class="stat-label">鸣潮角色</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-number">Excel</div>
            <div class="stat-label">完全兼容</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-number">开源</div>
            <div class="stat-label">免费使用</div>
          </div>
        </div>
      </div>
      
      <div class="hero-visual">
        <div class="grid-lines"></div>
        <div class="floating-cards">
          <div class="floating-card card-1" style="--delay: 0s;">
            <el-icon><Document /></el-icon>
            <span>拉表模板</span>
          </div>
          <div class="floating-card card-2" style="--delay: 0.5s;">
            <el-icon><Star /></el-icon>
            <span>社区评分</span>
          </div>
          <div class="floating-card card-3" style="--delay: 1s;">
            <el-icon><Download /></el-icon>
            <span>一键下载</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="feature-section">
      <div class="section-header">
        <h2 class="section-title">
          <span class="title-prefix">⚡</span>
          核心功能
        </h2>
        <p class="section-subtitle">强大而优雅的工具，助你一臂之力</p>
      </div>
      
      <el-row :gutter="24">
        <el-col :xs="24" :sm="12" :md="8" v-for="(feature, index) in features" :key="index">
          <div class="feature-card" :style="{ '--delay': `${index * 0.1}s` }">
            <div class="feature-icon" :style="{ '--color': feature.color }">
              <el-icon :size="28">
                <component :is="feature.icon" />
              </el-icon>
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-desc">{{ feature.description }}</p>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <div class="cta-section">
      <div class="cta-content">
        <h2 class="cta-title">
          准备好了吗？
          <span class="cta-emoji">🚀</span>
        </h2>
        <p class="cta-desc">
          立即开始你的排轴之旅，与万千玩家一起进步！
        </p>
        <el-button size="large" class="cyber-btn-primary" @click="$router.push('/calculator')">
          <el-icon><MagicStick /></el-icon>
          开始使用
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Lightning, 
  Cpu, 
  ChatDotRound, 
  Document, 
  Star, 
  Download,
  MagicStick,
  Edit,
  Share,
  Trophy
} from '@element-plus/icons-vue'

const features = [
  {
    icon: Edit,
    title: 'Excel级表格',
    description: '完整的Excel功能，支持公式计算、格式保留、导入导出，让你无缝切换。',
    color: '#00d4ff'
  },
  {
    icon: Share,
    title: '社区分享',
    description: '分享你的拉表模板，与其他玩家交流学习，共同提升游戏水平。',
    color: '#7928ca'
  },
  {
    icon: Trophy,
    title: '评分系统',
    description: '为优质模板点赞，发现最实用的拉表方案，让优秀作品脱颖而出。',
    color: '#ffaa00'
  }
]
</script>

<style scoped>
.home {
  max-width: 1400px;
  margin: 0 auto;
}

.hero-section {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 60px;
  align-items: center;
  padding: 60px 0;
  min-height: 70vh;
}

.hero-content {
  z-index: 1;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: linear-gradient(
    135deg,
    rgba(0, 212, 255, 0.15) 0%,
    rgba(121, 40, 202, 0.15) 100%
  );
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 50px;
  color: var(--primary-color);
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 24px;
  animation: float 3s ease-in-out infinite;
}

.hero-title {
  font-size: 64px;
  font-weight: 800;
  line-height: 1.1;
  margin: 0 0 20px 0;
  display: flex;
  flex-direction: column;
}

.title-line-1 {
  background: linear-gradient(
    135deg,
    var(--text-primary) 0%,
    var(--text-secondary) 100%
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-line-2 {
  display: flex;
  gap: 12px;
}

.glitch {
  color: var(--accent-color);
  position: relative;
  animation: glitch 3s infinite;
}

.glow {
  color: var(--primary-color);
  text-shadow: 0 0 20px var(--primary-color),
               0 0 40px var(--primary-color),
               0 0 60px var(--primary-color);
}

.hero-description {
  font-size: 18px;
  color: var(--text-secondary);
  line-height: 1.8;
  margin-bottom: 36px;
}

.hero-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 48px;
}

.cyber-btn-primary {
  background: linear-gradient(
    135deg,
    var(--primary-color) 0%,
    var(--secondary-color) 100%
  );
  border: none;
  color: white;
  font-weight: 600;
  padding: 12px 32px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4);
  transition: all 0.3s ease;
}

.cyber-btn-primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(0, 212, 255, 0.5);
}

.cyber-btn-outline {
  background: transparent;
  border: 2px solid rgba(255, 255, 255, 0.2);
  color: var(--text-primary);
  font-weight: 600;
  padding: 12px 32px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.cyber-btn-outline:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: rgba(0, 212, 255, 0.05);
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 32px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(
    135deg,
    var(--primary-color) 0%,
    var(--secondary-color) 100%
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: linear-gradient(
    180deg,
    transparent 0%,
    var(--border-color) 50%,
    transparent 100%
  );
}

.hero-visual {
  position: relative;
  height: 500px;
}

.grid-lines {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  border-radius: 16px;
  border: 1px solid rgba(0, 212, 255, 0.1);
}

.floating-cards {
  position: absolute;
  inset: 0;
}

.floating-card {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 24px;
  background: rgba(18, 18, 26, 0.9);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  animation: float-card 3s ease-in-out infinite;
  animation-delay: var(--delay);
}

.card-1 {
  top: 50px;
  left: 30px;
}

.card-2 {
  top: 180px;
  right: 50px;
}

.card-3 {
  bottom: 80px;
  left: 80px;
}

.floating-card .el-icon {
  font-size: 28px;
  color: var(--primary-color);
}

.floating-card span {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

@keyframes float-card {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-15px);
  }
}

.feature-section {
  padding: 80px 0;
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-title {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-prefix {
  font-size: 32px;
}

.section-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}

.feature-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 32px;
  text-align: center;
  transition: all 0.4s ease;
  animation: slide-up 0.6s ease forwards;
  opacity: 0;
  animation-delay: var(--delay);
}

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.feature-card:hover {
  transform: translateY(-8px);
  border-color: var(--border-glow);
  box-shadow: 0 12px 40px rgba(0, 212, 255, 0.15);
}

.feature-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(
    135deg,
    rgba(0, 212, 255, 0.1) 0%,
    rgba(121, 40, 202, 0.1) 100%
  );
  border-radius: 20px;
  border: 1px solid var(--border-glow);
}

.feature-icon .el-icon {
  color: var(--primary-color);
}

.feature-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--text-primary);
}

.feature-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0;
}

.cta-section {
  margin: 80px 0 40px;
  padding: 60px;
  background: linear-gradient(
    135deg,
    rgba(0, 212, 255, 0.1) 0%,
    rgba(121, 40, 202, 0.1) 100%
  );
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 24px;
  text-align: center;
}

.cta-content {
  max-width: 600px;
  margin: 0 auto;
}

.cta-title {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 16px 0;
}

.cta-emoji {
  display: inline-block;
  animation: float 2s ease-in-out infinite;
}

.cta-desc {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0 0 32px 0;
}

@media (max-width: 1024px) {
  .hero-section {
    grid-template-columns: 1fr;
    gap: 40px;
    padding: 40px 0;
  }
  
  .hero-visual {
    display: none;
  }
  
  .hero-title {
    font-size: 48px;
  }
}

@media (max-width: 640px) {
  .hero-title {
    font-size: 36px;
  }
  
  .hero-actions {
    flex-direction: column;
  }
  
  .hero-stats {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .stat-divider {
    display: none;
  }
}
</style>
