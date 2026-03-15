<template>
  <div class="home">
    <div class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">Beta 1.0</div>
        <h1 class="hero-title">莫宁宁的WutheringWavesDPS</h1>
        <div class="hero-features">
          <div class="feature-item">
            <div class="feature-icon">📊</div>
            <div class="feature-text">在线表格</div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">✅</div>
            <div class="feature-text">完全兼容</div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">👥</div>
            <div class="feature-text">社区分享</div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">❤️</div>
            <div class="feature-text">完全公益</div>
          </div>
        </div>
        <div class="hero-actions">
          <el-button type="primary" size="large" class="primary-btn" @click="startCalculate">
            开始计算
          </el-button>
          <el-button size="large" class="secondary-btn" @click="$router.push('/community')">
            浏览社区
          </el-button>
        </div>
        
        <div class="support-section">
          <div class="support-title">支持我们</div>
          <div class="support-links">
            <a href="https://afdian.com/a/r0xy0" target="_blank" rel="noopener noreferrer" class="support-link afdian-link">
              <span class="link-icon">💖</span>
              <span class="link-text">爱发电赞助</span>
            </a>
            <a href="https://github.com/NumInvis/WutheringWavesDPS" target="_blank" rel="noopener noreferrer" class="support-link github-link">
              <span class="link-icon">⭐</span>
              <span class="link-text">GitHub 项目</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function startCalculate() {
  router.push('/calculator?loadTemplate=true')
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.hero-section {
  text-align: center;
  padding: 80px 20px;
  position: relative;
}

.hero-content {
  position: relative;
  z-index: 1;
  background: rgba(15, 15, 26, 0.7);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 60px 40px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.hero-badge {
  display: inline-block;
  padding: 6px 16px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
  border: 1px solid rgba(102, 126, 234, 0.4);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  color: #c7d2fe;
  margin-bottom: 24px;
  letter-spacing: 0.5px;
}

.hero-title {
  font-size: 56px;
  font-weight: 800;
  margin: 0 0 20px 0;
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.1;
  letter-spacing: -1px;
}

.hero-subtitle {
  font-size: 18px;
  color: #cbd5e1;
  margin: 0 0 48px 0;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
}

.hero-features {
  display: flex;
  gap: 24px;
  justify-content: center;
  margin-bottom: 48px;
  flex-wrap: wrap;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 32px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  transition: all 0.3s ease;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(102, 126, 234, 0.4);
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}

.feature-icon {
  font-size: 36px;
}

.feature-text {
  font-size: 15px;
  font-weight: 600;
  color: #e2e8f0;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.primary-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  padding: 16px 36px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
}

.secondary-btn {
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #e2e8f0;
  padding: 16px 36px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.secondary-btn:hover {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.support-section {
  margin-top: 48px;
  padding-top: 32px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.support-title {
  font-size: 14px;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 20px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.support-links {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.support-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 12px;
  text-decoration: none;
  transition: all 0.3s ease;
  font-weight: 500;
}

.afdian-link {
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%);
  border: 1px solid rgba(236, 72, 153, 0.4);
  color: #f9a8d4;
}

.afdian-link:hover {
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%);
  border-color: rgba(236, 72, 153, 0.6);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(236, 72, 153, 0.3);
}

.github-link {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #e2e8f0;
}

.github-link:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.link-icon {
  font-size: 18px;
}

.link-text {
  font-size: 14px;
}
</style>
