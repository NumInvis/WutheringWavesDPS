<template>
  <div class="survey-response-detail-page">
    <div class="page-header">
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="15" animated />
    </div>

    <template v-else-if="responseDetail">
      <div class="response-header">
        <h1>{{ responseDetail.survey_title }}</h1>
        <div class="response-meta">
          <el-tag :type="responseDetail.is_anonymous ? 'info' : 'primary'" size="large">
            {{ responseDetail.is_anonymous ? '匿名用户' : '实名用户' }}
          </el-tag>
          <template v-if="!responseDetail.is_anonymous && responseDetail.user">
            <div class="user-info">
              <span class="username">{{ responseDetail.user.username }}</span>
              <span class="email">{{ responseDetail.user.email }}</span>
            </div>
          </template>
          <span class="submit-time">
            提交时间: {{ formatDateTime(responseDetail.submitted_at) }}
          </span>
        </div>
      </div>

      <div class="questions-list">
        <div
          v-for="(question, index) in responseDetail.questions"
          :key="question.id"
          class="question-item"
        >
          <div class="question-header">
            <span class="question-number">{{ index + 1 }}</span>
            <span class="question-title">{{ question.title }}</span>
            <el-tag size="small" :type="getQuestionTypeTag(question.question_type)">
              {{ getQuestionTypeText(question.question_type) }}
            </el-tag>
          </div>
          
          <div class="answer-display">
            <div class="answer-label">回答：</div>
            <div class="answer-content">
              <template v-if="question.answer">
                <template v-if="question.question_type === 'single_choice'">
                  <el-tag type="success">{{ question.answer }}</el-tag>
                </template>
                <template v-else-if="question.question_type === 'multiple_choice'">
                  <el-tag v-for="option in question.answer.split('、')" :key="option" type="success" style="margin-right: 8px;">
                    {{ option }}
                  </el-tag>
                </template>
                <template v-else-if="question.question_type === 'fill_in_blank'">
                  <div class="fill-answer">{{ question.answer }}</div>
                </template>
                <template v-else-if="question.question_type === 'rating'">
                  <el-rate
                    :model-value="parseRatingValue(question.answer)"
                    disabled
                    show-score
                    :max="5"
                  />
                </template>
              </template>
              <template v-else>
                <span class="no-answer">未回答</span>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>

    <el-empty v-else description="回答记录不存在" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const responseDetail = ref<any>(null)

const fetchResponseDetail = async () => {
  const responseId = route.params.id as string
  if (!responseId) return

  loading.value = true
  try {
    const response = await api.get(`/surveys/admin/response/${responseId}`)
    responseDetail.value = response
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取回答详情失败')
    router.push('/admin/surveys')
  } finally {
    loading.value = false
  }
}

const getQuestionTypeText = (type: string) => {
  const map: Record<string, string> = {
    single_choice: '单选题',
    multiple_choice: '多选题',
    fill_in_blank: '填空题',
    rating: '评分题'
  }
  return map[type] || type
}

const getQuestionTypeTag = (type: string) => {
  const map: Record<string, string> = {
    single_choice: 'primary',
    multiple_choice: 'success',
    fill_in_blank: 'info',
    rating: 'warning'
  }
  return map[type] || 'info'
}

const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const parseRatingValue = (value: string) => {
  const match = value.match(/(\d+)\s*分/)
  return match ? parseInt(match[1]) : 0
}

const goBack = () => {
  router.push('/admin/surveys')
}

onMounted(() => {
  fetchResponseDetail()
})
</script>

<style scoped>
.survey-response-detail-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.loading-state {
  padding: 40px;
}

.response-header {
  background: white;
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.response-header h1 {
  font-size: 24px;
  margin: 0 0 20px 0;
}

.response-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 15px;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-info .username {
  font-weight: 500;
  font-size: 14px;
}

.user-info .email {
  font-size: 12px;
  color: #888;
}

.submit-time {
  color: #888;
  font-size: 14px;
}

.questions-list {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.question-item {
  margin-bottom: 35px;
  padding-bottom: 35px;
  border-bottom: 1px solid #e4e7ed;
}

.question-item:last-of-type {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.question-number {
  width: 32px;
  height: 32px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.question-title {
  font-size: 16px;
  font-weight: 500;
  flex: 1;
}

.answer-display {
  display: flex;
  gap: 15px;
  padding-left: 42px;
}

.answer-label {
  font-weight: 500;
  color: #666;
  white-space: nowrap;
}

.answer-content {
  flex: 1;
}

.fill-answer {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.no-answer {
  color: #888;
  font-style: italic;
}
</style>
