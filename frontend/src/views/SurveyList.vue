<template>
  <div class="survey-list-page">
    <div class="page-header">
      <h1>📋 问卷调查</h1>
      <p class="subtitle">参与问卷，分享您的想法</p>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="surveys.length === 0" class="empty-state">
      <el-empty description="暂无可填写的问卷" />
    </div>

    <div v-else class="survey-grid">
      <el-card
        v-for="survey in surveys"
        :key="survey.id"
        class="survey-card"
        :class="{ 'submitted': survey.has_submitted }"
      >
        <div class="survey-header">
          <h3 class="survey-title">{{ survey.title }}</h3>
          <el-tag
            v-if="survey.has_submitted"
            type="success"
            size="small"
          >
            已填写
          </el-tag>
          <el-tag
            v-else
            type="primary"
            size="small"
          >
            可填写
          </el-tag>
        </div>

        <p class="survey-description">{{ survey.description || '暂无描述' }}</p>

        <div class="survey-meta">
          <span class="meta-item">
            <el-icon><Document /></el-icon>
            {{ survey.question_count }} 个问题
          </span>
          <span v-if="survey.end_time" class="meta-item">
            <el-icon><Timer /></el-icon>
            截止: {{ formatDate(survey.end_time) }}
          </span>
          <span v-if="survey.allow_anonymous" class="meta-item">
            <el-icon><User /></el-icon>
            支持匿名
          </span>
        </div>

        <div class="survey-actions">
          <el-button
            v-if="!survey.has_submitted"
            type="primary"
            @click="goToSurvey(survey.id)"
          >
            立即填写
          </el-button>
          <el-button
            v-else
            type="info"
            @click="viewStatistics(survey.id)"
          >
            查看统计
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Timer, User } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()
const loading = ref(false)
const surveys = ref<any[]>([])

const fetchSurveys = async () => {
  loading.value = true
  try {
    const response = await api.get('/surveys/list')
    surveys.value = response.surveys || []
  } catch (error) {
    ElMessage.error('获取问卷列表失败')
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const goToSurvey = (id: string) => {
  router.push(`/survey/${id}`)
}

const viewStatistics = (id: string) => {
  router.push(`/survey/${id}?view=statistics`)
}

onMounted(() => {
  fetchSurveys()
})
</script>

<style scoped>
.survey-list-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  color: #000000 !important;
  position: relative;
  z-index: 1;
}

.survey-list-page * {
  color: #000000 !important;
  opacity: 1 !important;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 30px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.page-header h1 {
    font-size: 32px;
    margin-bottom: 8px;
    color: #000000 !important;
    font-weight: 700;
  }

  .page-header .subtitle {
    color: #333333 !important;
    font-size: 18px;
  }

  .loading-state {
    padding: 40px;
  }

  .empty-state {
    padding: 60px 0;
  }

  .survey-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 20px;
  }

  .survey-card {
    transition: all 0.3s ease;
    background: rgba(255, 255, 255, 0.98) !important;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 2px solid rgba(255, 255, 255, 0.9) !important;
  }

  .survey-card :deep(.el-card__body) {
    color: #303133 !important;
  }

  .survey-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    background: rgba(255, 255, 255, 1) !important;
  }

  .survey-card.submitted {
    opacity: 1;
    background-color: rgba(245, 247, 250, 0.95) !important;
  }

  .survey-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .survey-title {
    font-size: 20px;
    margin: 0;
    flex: 1;
    color: #000000 !important;
    font-weight: 700;
    text-shadow: 0 0 1px rgba(0, 0, 0, 0.1);
  }

  .survey-description {
    color: #222222 !important;
    font-size: 16px;
    margin-bottom: 16px;
    min-height: 48px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    font-weight: 500;
  }

  .survey-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 16px;
  }

  .meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 15px;
    color: #333333 !important;
    font-weight: 500;
  }

  .survey-actions {
    display: flex;
    justify-content: flex-end;
  }

  .survey-actions .el-button {
    font-size: 16px;
    padding: 8px 16px;
  }
</style>
