<template>
  <div class="home">
    <div class="announcement-section" v-if="activeAnnouncement">
      <div class="announcement-content">
        <div class="announcement-icon">📢</div>
        <div class="announcement-text">
          <span class="announcement-tag">公告</span>
          <span class="announcement-title">{{ activeAnnouncement.title }}</span>
          <span class="announcement-message">{{ activeAnnouncement.content }}</span>
        </div>
        <el-button text class="close-btn" @click="dismissAnnouncement">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </div>

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

    <div class="history-announcements-section" v-if="historyAnnouncements.length > 0">
      <div class="section-header">
        <h2 class="section-title">历史公告</h2>
        <el-button text @click="showAllAnnouncements = !showAllAnnouncements">
          {{ showAllAnnouncements ? '收起' : '查看全部' }}
        </el-button>
      </div>
      <div class="announcements-list">
        <div 
          v-for="announcement in displayAnnouncements" 
          :key="announcement.id"
          class="announcement-item"
        >
          <div class="announcement-date">
            {{ formatDate(announcement.created_at) }}
          </div>
          <div class="announcement-info">
            <h3 class="announcement-item-title">{{ announcement.title }}</h3>
            <p class="announcement-item-content">{{ announcement.content }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Close } from '@element-plus/icons-vue'
import axios from 'axios'

interface Announcement {
  id: string
  title: string
  content: string
  is_active: boolean
  is_pinned: boolean
  created_at: string
}

const router = useRouter()
const activeAnnouncement = ref<Announcement | null>(null)
const historyAnnouncements = ref<Announcement[]>([])
const showAllAnnouncements = ref(false)
const dismissedAnnouncements = ref<Set<string>>(new Set())

const displayAnnouncements = computed(() => {
  return showAllAnnouncements.value 
    ? historyAnnouncements.value 
    : historyAnnouncements.value.slice(0, 3)
})

async function loadAnnouncements() {
  try {
    const response = await axios.get(import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/announcements/active')
    if (response.data.length > 0) {
      const announcement = response.data[0]
      if (!dismissedAnnouncements.value.has(announcement.id)) {
        activeAnnouncement.value = announcement
      }
    }
    
    const historyResponse = await axios.get(import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/announcements')
    historyAnnouncements.value = historyResponse.data.filter((a: Announcement) => !a.is_active)
  } catch (error) {
    console.error('加载公告失败:', error)
  }
}

function dismissAnnouncement() {
  if (activeAnnouncement.value) {
    dismissedAnnouncements.value.add(activeAnnouncement.value.id)
    activeAnnouncement.value = null
  }
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

function startCalculate() {
  router.push('/calculator?loadTemplate=true')
}

onMounted(() => {
  loadAnnouncements()
})
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.announcement-section {
  margin-bottom: 24px;
}

.announcement-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(102, 126, 234, 0.4);
  border-radius: 16px;
}

.announcement-icon {
  font-size: 28px;
}

.announcement-text {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.announcement-tag {
  display: inline-block;
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
}

.announcement-title {
  font-size: 16px;
  color: #fff;
  font-weight: 700;
}

.announcement-message {
  font-size: 14px;
  color: #cbd5e1;
  font-weight: 500;
}

.close-btn {
  color: #94a3b8;
  padding: 4px;
}

.close-btn:hover {
  color: #e2e8f0;
}

.history-announcements-section {
  max-width: 1000px;
  margin: 48px auto 0;
  padding: 0 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0;
}

.announcements-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.announcement-item {
  display: flex;
  gap: 20px;
  padding: 20px 24px;
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  transition: all 0.3s ease;
}

.announcement-item:hover {
  border-color: rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.announcement-date {
  flex-shrink: 0;
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
  border: 1px solid rgba(102, 126, 234, 0.4);
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #a5b4fc;
  height: fit-content;
}

.announcement-info {
  flex: 1;
  min-width: 0;
}

.announcement-item-title {
  font-size: 16px;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0 0 8px 0;
}

.announcement-item-content {
  font-size: 14px;
  color: #94a3b8;
  margin: 0;
  line-height: 1.6;
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
