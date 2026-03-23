<template>
  <div class="survey-detail-page">
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="10" animated />
    </div>

    <div v-else-if="showStatistics && statistics" class="statistics-page">
      <div class="statistics-header">
        <h1>{{ statistics.title }}</h1>
        <el-button type="primary" @click="goBack">返回列表</el-button>
      </div>
      <div class="statistics-meta">
        <el-tag type="info">总共 {{ statistics.total_responses }} 人填写</el-tag>
        <el-tag type="success">问题数量: {{ statistics.questions?.length || 0 }}</el-tag>
      </div>

      <div class="questions-statistics">
        <div
          v-for="(question, index) in statistics.questions"
          :key="question.id"
          class="question-stat-item"
        >
          <div class="question-title">
            <span class="question-number">{{ index + 1 }}</span>
            <span>{{ question.title }}</span>
          </div>

          <div v-if="question.question_type === 'single_choice' || question.question_type === 'multiple_choice'" class="options-stats">
            <div
              v-for="opt in question.options"
              :key="opt.id"
              class="option-stat"
            >
              <div class="option-info">
                <span class="option-content">{{ opt.content }}</span>
                <span class="option-count">{{ opt.count }} 票 ({{ opt.percentage }}%)</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: opt.percentage + '%' }"></div>
              </div>
            </div>
          </div>

          <div v-else-if="question.question_type === 'rating'" class="rating-stats">
            <div class="rating-display">
              <span class="rating-label">平均分：</span>
              <span class="rating-value">{{ question.average_rating }}</span>
              <span class="rating-suffix">/{{ question.max_rating }}分</span>
            </div>
            <div class="rating-count">共 {{ question.rating_count }} 人评分</div>
          </div>

          <div v-else-if="question.question_type === 'fill_in_blank'" class="fill-stats">
            <el-tag type="warning">共 {{ question.answer_count }} 人填写</el-tag>
            <el-button size="small" text type="primary">查看详情需管理员权限</el-button>
          </div>
        </div>
      </div>
    </div>

    <template v-else-if="survey">
      <div class="survey-header">
        <h1>{{ survey.title }}</h1>
        <p class="description">{{ survey.description }}</p>
      </div>

      <el-form
        ref="formRef"
        :model="answers"
        class="survey-form"
      >
        <div
          v-for="(question, index) in survey.questions"
          :key="question.id"
          class="question-item"
        >
          <div class="question-header">
            <span class="question-number">{{ index + 1 }}</span>
            <span class="question-title">{{ question.title }}</span>
            <el-tag v-if="question.is_required" type="danger" size="small">必填</el-tag>
          </div>

          <p v-if="question.description" class="question-description">
            {{ question.description }}
          </p>

          <!-- 单选题 -->
          <el-form-item
            v-if="question.question_type === 'single_choice'"
            :prop="question.id"
            :rules="question.is_required ? [{ required: true, message: '请选择一个选项', trigger: 'change' }] : []"
          >
            <el-radio-group v-model="answers[question.id]">
              <el-radio
                v-for="option in question.options"
                :key="option.id"
                :label="option.id"
              >
                {{ option.content }}
              </el-radio>
            </el-radio-group>
          </el-form-item>

          <!-- 多选题 -->
          <el-form-item
            v-else-if="question.question_type === 'multiple_choice'"
            :prop="question.id"
            :rules="question.is_required ? [{ required: true, message: '请至少选择一个选项', trigger: 'change', type: 'array' }] : []"
          >
            <el-checkbox-group v-model="answers[question.id]">
              <el-checkbox
                v-for="option in question.options"
                :key="option.id"
                :label="option.id"
              >
                {{ option.content }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <!-- 填空题 -->
          <el-form-item
            v-else-if="question.question_type === 'fill_in_blank'"
            :prop="question.id"
            :rules="question.is_required ? [{ required: true, message: '请填写答案', trigger: 'blur' }] : []"
          >
            <el-input
              v-model="answers[question.id]"
              type="textarea"
              :rows="3"
              :placeholder="question.config?.placeholder || '请输入您的答案'"
              :maxlength="question.config?.max_length || 500"
              show-word-limit
            />
          </el-form-item>

          <!-- 评分题 -->
          <el-form-item
            v-else-if="question.question_type === 'rating'"
            :prop="question.id"
            :rules="question.is_required ? [{ required: true, message: '请进行评分', trigger: 'change' }] : []"
          >
            <el-rate
              v-model="answers[question.id]"
              :max="question.config?.max_rating || 5"
              :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
              show-text
            />
          </el-form-item>
        </div>

        <div class="form-actions">
          <el-checkbox
            v-if="survey.allow_anonymous"
            v-model="isAnonymous"
            class="anonymous-checkbox"
          >
            匿名提交
          </el-checkbox>

          <el-button
            type="primary"
            size="large"
            :loading="submitting"
            @click="submitSurvey"
          >
            提交问卷
          </el-button>
        </div>
      </el-form>
    </template>

    <el-empty v-else description="问卷不存在或已结束" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const survey = ref<any>(null)
const statistics = ref<any>(null)
const showStatistics = ref(false)
const answers = reactive<Record<string, any>>({})
const isAnonymous = ref(false)
const formRef = ref()

const fetchSurvey = async () => {
  const surveyId = route.params.id as string
  if (!surveyId) return

  // 重置状态
  survey.value = null
  statistics.value = null
  showStatistics.value = false
  
  // 清空答案
  Object.keys(answers).forEach(key => delete answers[key])
  isAnonymous.value = false

  // 检查是否需要直接查看统计
  const viewMode = route.query.view as string
  if (viewMode === 'statistics') {
    await fetchStatistics(surveyId)
    return
  }

  loading.value = true
  try {
    const response = await api.get(`/surveys/${surveyId}`)
    survey.value = response

    // 初始化答案
    survey.value.questions.forEach((q: any) => {
      if (q.question_type === 'multiple_choice') {
        answers[q.id] = []
      } else {
        answers[q.id] = ''
      }
    })
  } catch (error: any) {
    // 如果用户已填写，直接显示统计
    if (error.response?.data?.detail === '您已填写过此问卷') {
      await fetchStatistics(surveyId)
    } else {
      ElMessage.error(error.response?.data?.detail || '获取问卷失败')
      router.push('/surveys')
    }
  } finally {
    loading.value = false
  }
}

const fetchStatistics = async (surveyId: string) => {
  try {
    const response = await api.get(`/surveys/${surveyId}/statistics`)
    console.log('Statistics response:', response)
    statistics.value = response
    showStatistics.value = true
    console.log('statistics.value:', statistics.value)
    console.log('statistics.questions:', statistics.value?.questions)
  } catch (error: any) {
    console.error('Statistics fetch error:', error)
    ElMessage.error(error.response?.data?.detail || '获取统计失败')
  }
}

const submitSurvey = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) {
      ElMessage.warning('请完成所有必填项')
      return
    }

    const confirm = await ElMessageBox.confirm(
      '确认提交问卷吗？提交后不可修改。',
      '确认提交',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).catch(() => false)

    if (!confirm) return

    submitting.value = true
    try {
      const surveyId = route.params.id as string

      // 构建答案数据
      const answersData = survey.value.questions.map((q: any) => {
        const answerValue = answers[q.id]
        let answerData: any = {}

        if (q.question_type === 'single_choice') {
          const option = q.options.find((o: any) => o.id === answerValue)
          answerData = {
            option_id: answerValue,
            text: option?.content || ''
          }
        } else if (q.question_type === 'multiple_choice') {
          const texts = answerValue.map((id: string) => {
            const option = q.options.find((o: any) => o.id === id)
            return option?.content || ''
          })
          answerData = {
            option_ids: answerValue,
            texts: texts
          }
        } else if (q.question_type === 'fill_in_blank') {
          answerData = { text: answerValue }
        } else if (q.question_type === 'rating') {
          answerData = { value: answerValue }
        }

        return {
          question_id: q.id,
          answer_data: answerData
        }
      })

      await api.post(`/surveys/${surveyId}/submit`, {
        answers: answersData,
        is_anonymous: isAnonymous.value
      })

      ElMessage.success('问卷提交成功！')
      
      // 提交后显示统计
      await fetchStatistics(surveyId)
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '提交失败')
    } finally {
      submitting.value = false
    }
  })
}

const goBack = () => {
  router.push('/surveys')
}

// 监听路由参数变化
watch(() => route.params.id, () => {
  fetchSurvey()
})

onMounted(() => {
  fetchSurvey()
})
</script>

<style scoped>
.survey-detail-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  position: relative;
  z-index: 1;
}

.survey-detail-page * {
  color: #000000 !important;
  opacity: 1 !important;
}

.loading-state {
  padding: 40px;
}

/* 统计页面样式 */
.statistics-page {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  color: #000000;
}

.statistics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.statistics-header h1 {
    font-size: 28px;
    margin: 0;
    color: #303133;
  }

  .statistics-meta {
    margin-bottom: 30px;
  }

  .statistics-meta .el-tag {
    font-size: 16px;
    padding: 4px 12px;
  }

  .questions-statistics {
    margin-top: 30px;
  }

  .question-stat-item {
    margin-bottom: 35px;
    padding-bottom: 35px;
    border-bottom: 1px solid #e4e7ed;
  }

  .question-stat-item:last-of-type {
    border-bottom: none;
  }

  .question-stat-item .question-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    font-size: 18px;
    font-weight: 500;
    color: #303133;
  }

  .question-stat-item .question-number {
    width: 32px;
    height: 32px;
    background: #67c23a;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 16px;
  }

  .options-stats {
    margin-top: 15px;
  }

  .option-stat {
    margin-bottom: 15px;
  }

  .option-info {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  .option-content {
    font-size: 16px;
    color: #303133;
  }

  .option-count {
    color: #606266;
    font-size: 15px;
  }

  .progress-bar {
    height: 10px;
    background: #f0f0f0;
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #409eff, #67c23a);
    border-radius: 4px;
    transition: width 0.5s ease;
  }

  .rating-stats,
  .fill-stats {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-top: 15px;
  }

  .rating-display {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .rating-label {
    font-size: 16px;
    color: #303133;
  }

  .rating-value {
    font-size: 32px;
    font-weight: bold;
    color: #f7ba2a;
  }

  .rating-suffix {
    font-size: 16px;
    color: #606266;
  }

  .rating-count {
    font-size: 16px;
    color: #606266;
  }

  .fill-stats .el-tag {
    font-size: 16px;
    padding: 4px 12px;
  }

  .fill-stats .el-button {
    font-size: 16px;
  }

  /* 原问卷页面样式 */
  .survey-header {
    text-align: center;
    margin-bottom: 40px;
  }

  .survey-header h1 {
    font-size: 28px;
    margin-bottom: 12px;
    color: #303133;
  }

  .survey-header .description {
    color: #606266;
    font-size: 16px;
  }

  .survey-form {
    background: rgba(245, 247, 250, 0.98);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 12px;
    padding: 30px;
    color: #000000;
  }

  .question-item {
    margin-bottom: 30px;
    padding-bottom: 30px;
    border-bottom: 1px solid #e4e7ed;
  }

  .question-item:last-of-type {
    border-bottom: none;
  }

  .question-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
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
    font-size: 16px;
  }

  .question-title {
    font-size: 18px;
    font-weight: 500;
    flex: 1;
    color: #303133;
  }

  .question-description {
    color: #606266;
    font-size: 15px;
    margin: 8px 0 16px 38px;
  }

  .form-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #e4e7ed;
  }

  .anonymous-checkbox :deep(.el-checkbox__label) {
    color: #606266;
    font-size: 16px;
  }

  .form-actions .el-button {
    font-size: 18px;
    padding: 10px 20px;
  }

  .el-radio :deep(.el-radio__label) {
    font-size: 16px;
    color: #303133;
  }

  .el-checkbox :deep(.el-checkbox__label) {
    font-size: 16px;
    color: #303133;
  }

  .el-input :deep(.el-input__inner) {
    font-size: 16px;
    color: #303133;
  }

  .el-rate :deep(.el-rate__text) {
    font-size: 16px;
    color: #303133;
  }
</style>
