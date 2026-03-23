<template>
  <div class="survey-manage-page">
    <div class="page-header">
      <h2>📋 问卷管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        创建问卷
      </el-button>
    </div>

    <!-- 问卷列表 -->
    <el-table :data="surveys" v-loading="loading" style="width: 100%">
      <el-table-column prop="title" label="问卷标题" min-width="200">
        <template #default="{ row }">
          <div class="survey-title-cell">
            <span class="title">{{ row.title }}</span>
            <el-tag
              :type="getStatusType(row.status)"
              size="small"
              class="status-tag"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="时间设置" min-width="200">
        <template #default="{ row }">
          <div class="time-info">
            <div v-if="row.start_time">
              开始: {{ formatDateTime(row.start_time) }}
            </div>
            <div v-else>开始: 立即</div>
            <div v-if="row.end_time">
              结束: {{ formatDateTime(row.end_time) }}
            </div>
            <div v-else>结束: 无限期</div>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="total_responses" label="填写次数" width="100" align="center" />

      <el-table-column label="设置" width="150">
        <template #default="{ row }">
          <div class="settings-info">
            <el-tag v-if="row.allow_anonymous" size="small" type="info">匿名</el-tag>
            <el-tag v-if="row.allow_multiple" size="small" type="info">多次</el-tag>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="380" fixed="right">
        <template #default="{ row }">
          <el-button-group>
            <el-button size="small" @click="viewSurvey(row)">查看</el-button>
            <el-button size="small" type="primary" @click="editSurvey(row)">编辑</el-button>
            <el-button size="small" type="success" @click="viewStatistics(row)">统计</el-button>
            <el-button size="small" type="warning" @click="viewResponses(row)">填写记录</el-button>
            <el-button size="small" type="danger" @click="deleteSurvey(row)">删除</el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchSurveys"
        @current-change="fetchSurveys"
      />
    </div>

    <!-- 创建/编辑问卷对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑问卷' : '创建问卷'"
      width="900px"
      :close-on-click-modal="false"
    >
      <el-form :model="surveyForm" label-position="top">
        <!-- 基本信息 -->
        <el-divider content-position="left">基本信息</el-divider>

        <el-form-item label="问卷标题" required>
          <el-input v-model="surveyForm.title" placeholder="请输入问卷标题" />
        </el-form-item>

        <el-form-item label="问卷描述">
          <el-input
            v-model="surveyForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入问卷描述"
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-date-picker
                v-model="surveyForm.start_time"
                type="datetime"
                placeholder="立即开始"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间">
              <el-date-picker
                v-model="surveyForm.end_time"
                type="datetime"
                placeholder="无限期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="状态">
              <el-select v-model="surveyForm.status" style="width: 100%">
                <el-option label="草稿" value="draft" />
                <el-option label="已发布" value="published" />
                <el-option label="暂停" value="paused" />
                <el-option label="已关闭" value="closed" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="允许匿名">
              <el-switch v-model="surveyForm.allow_anonymous" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="允许多次填写">
              <el-switch v-model="surveyForm.allow_multiple" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 问题列表 -->
        <el-divider content-position="left">
          问题列表
          <el-button type="primary" size="small" @click="addQuestion" style="margin-left: 10px">
            <el-icon><Plus /></el-icon>
            添加问题
          </el-button>
        </el-divider>

        <div v-for="(question, index) in surveyForm.questions" :key="index" class="question-editor">
          <el-card>
            <template #header>
              <div class="question-header">
                <span>问题 {{ index + 1 }}</span>
                <el-button type="danger" size="small" @click="removeQuestion(index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </template>

            <el-form-item label="问题标题" required>
              <el-input v-model="question.title" placeholder="请输入问题" />
            </el-form-item>

            <el-form-item label="问题描述">
              <el-input
                v-model="question.description"
                type="textarea"
                :rows="2"
                placeholder="问题说明（可选）"
              />
            </el-form-item>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="问题类型" required>
                  <el-select v-model="question.question_type" style="width: 100%">
                    <el-option label="单选题" value="single_choice" />
                    <el-option label="多选题" value="multiple_choice" />
                    <el-option label="填空题" value="fill_in_blank" />
                    <el-option label="评分题" value="rating" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="是否必填">
                  <el-switch v-model="question.is_required" />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 选项设置（单选/多选） -->
            <template v-if="['single_choice', 'multiple_choice'].includes(question.question_type)">
              <el-form-item label="选项">
                <div
                  v-for="(option, optIndex) in question.options"
                  :key="optIndex"
                  class="option-item"
                >
                  <el-input v-model="option.content" placeholder="选项内容">
                    <template #append>
                      <el-button @click="removeOption(question, optIndex)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </template>
                  </el-input>
                </div>
                <el-button type="primary" size="small" @click="addOption(question)">
                  <el-icon><Plus /></el-icon>
                  添加选项
                </el-button>
              </el-form-item>
            </template>

            <!-- 评分设置 -->
            <template v-if="question.question_type === 'rating'">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="最大评分">
                    <el-input-number v-model="question.config.max_rating" :min="3" :max="10" />
                  </el-form-item>
                </el-col>
              </el-row>
            </template>

            <!-- 填空设置 -->
            <template v-if="question.question_type === 'fill_in_blank'">
              <el-form-item label="提示文字">
                <el-input v-model="question.config.placeholder" placeholder="请输入提示文字" />
              </el-form-item>
              <el-form-item label="最大长度">
                <el-input-number v-model="question.config.max_length" :min="10" :max="2000" />
              </el-form-item>
            </template>
          </el-card>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveSurvey">保存</el-button>
      </template>
    </el-dialog>

    <!-- 统计对话框 -->
    <el-dialog
      v-model="statisticsVisible"
      title="问卷统计"
      width="800px"
    >
      <div v-if="statistics" class="statistics-content">
        <div class="stat-header">
          <h3>{{ statistics.title }}</h3>
          <p>总填写次数: {{ statistics.total_responses }}</p>
        </div>

        <div
          v-for="(question, index) in statistics.questions"
          :key="question.id"
          class="stat-question"
        >
          <h4>{{ index + 1 }}. {{ question.title }}</h4>
          <p class="question-type">类型: {{ getQuestionTypeText(question.question_type) }}</p>

          <!-- 单选/多选统计 -->
          <template v-if="question.option_statistics">
            <el-table :data="formatOptionStats(question.option_statistics)" size="small">
              <el-table-column prop="option" label="选项" />
              <el-table-column prop="count" label="选择次数" width="100" />
              <el-table-column prop="percentage" label="占比" width="100">
                <template #default="{ row }">
                  {{ row.percentage }}%
                </template>
              </el-table-column>
            </el-table>
          </template>

          <!-- 评分统计 -->
          <template v-if="question.average_rating !== undefined">
            <div class="rating-stat">
              <el-rate
                :model-value="question.average_rating"
                disabled
                show-score
                :max="5"
              />
              <span class="rating-count">{{ question.rating_count }} 人评分</span>
            </div>
          </template>
        </div>
      </div>
    </el-dialog>

    <!-- 填写记录对话框 -->
    <el-dialog
      v-model="responsesVisible"
      title="填写记录"
      width="900px"
    >
      <div v-if="currentSurvey" class="responses-header">
        <h3>{{ currentSurvey.title }}</h3>
        <p>共 {{ responsesTotal }} 人填写</p>
      </div>
      
      <el-table :data="responses" v-loading="responsesLoading" style="width: 100%">
        <el-table-column label="用户" min-width="150">
          <template #default="{ row }">
            <template v-if="row.is_anonymous">
              <el-tag size="small" type="info">匿名用户</el-tag>
            </template>
            <template v-else>
              <div v-if="row.user">
                <div class="username">{{ row.user.username }}</div>
                <div class="email">{{ row.user.email }}</div>
              </div>
              <el-tag v-else size="small" type="danger">用户已删除</el-tag>
            </template>
          </template>
        </el-table-column>
        <el-table-column prop="submitted_at" label="提交时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.submitted_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewResponseDetail(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-wrapper" style="margin-top: 20px;">
        <el-pagination
          v-model:current-page="responsesPage"
          v-model:page-size="responsesPageSize"
          :total="responsesTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchResponses"
          @current-change="fetchResponses"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import api from '@/api'

const loading = ref(false)
const saving = ref(false)
const surveys = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref('')

const surveyForm = ref<any>({
  title: '',
  description: '',
  status: 'draft',
  start_time: null,
  end_time: null,
  allow_anonymous: false,
  allow_multiple: false,
  max_responses: null,
  questions: []
})

const statisticsVisible = ref(false)
const statistics = ref<any>(null)

const responsesVisible = ref(false)
const responsesLoading = ref(false)
const responses = ref<any[]>([])
const responsesPage = ref(1)
const responsesPageSize = ref(20)
const responsesTotal = ref(0)
const currentSurvey = ref<any>(null)

const fetchSurveys = async () => {
  loading.value = true
  try {
    const response = await api.get('/surveys/admin/list', {
      params: { page: page.value, page_size: pageSize.value }
    })
    surveys.value = response.surveys || []
    total.value = response.total || 0
  } catch (error) {
    ElMessage.error('获取问卷列表失败')
  } finally {
    loading.value = false
  }
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    published: 'success',
    paused: 'warning',
    closed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    paused: '暂停',
    closed: '已关闭'
  }
  return map[status] || status
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

const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const showCreateDialog = () => {
  isEditing.value = false
  editingId.value = ''
  surveyForm.value = {
    title: '',
    description: '',
    status: 'draft',
    start_time: null,
    end_time: null,
    allow_anonymous: false,
    allow_multiple: false,
    questions: []
  }
  dialogVisible.value = true
}

const addQuestion = () => {
  surveyForm.value.questions.push({
    title: '',
    description: '',
    question_type: 'single_choice',
    is_required: true,
    order: surveyForm.value.questions.length,
    config: {},
    options: [{ content: '', order: 0 }]
  })
}

const removeQuestion = (index: number) => {
  surveyForm.value.questions.splice(index, 1)
  // 重新排序
  surveyForm.value.questions.forEach((q: any, i: number) => {
    q.order = i
  })
}

const addOption = (question: any) => {
  question.options.push({
    content: '',
    order: question.options.length
  })
}

const removeOption = (question: any, index: number) => {
  question.options.splice(index, 1)
}

const saveSurvey = async () => {
  if (!surveyForm.value.title) {
    ElMessage.warning('请输入问卷标题')
    return
  }

  if (surveyForm.value.questions.length === 0) {
    ElMessage.warning('请至少添加一个问题')
    return
  }

  // 验证问题
  for (const q of surveyForm.value.questions) {
    if (!q.title) {
      ElMessage.warning('请填写所有问题的标题')
      return
    }
    if (['single_choice', 'multiple_choice'].includes(q.question_type)) {
      if (q.options.length < 2) {
        ElMessage.warning('单选题和多选题至少需要2个选项')
        return
      }
      for (const opt of q.options) {
        if (!opt.content) {
          ElMessage.warning('请填写所有选项的内容')
          return
        }
      }
    }
  }

  saving.value = true
  try {
    // 构建符合后端API格式的数据
    const formData = {
      title: surveyForm.value.title,
      description: surveyForm.value.description,
      start_time: surveyForm.value.start_time,
      end_time: surveyForm.value.end_time,
      allow_anonymous: surveyForm.value.allow_anonymous,
      allow_multiple: surveyForm.value.allow_multiple,
      max_responses: surveyForm.value.max_responses,
      questions: surveyForm.value.questions
    }

    if (isEditing.value) {
      // 更新时包含status
      await api.put(`/surveys/admin/${editingId.value}`, surveyForm.value)
      ElMessage.success('问卷更新成功')
    } else {
      // 创建时不包含status（后端会默认设置为draft）
      await api.post('/surveys/admin/create', formData)
      ElMessage.success('问卷创建成功')
    }
    dialogVisible.value = false
    fetchSurveys()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const editSurvey = async (row: any) => {
  try {
    const response = await api.get(`/surveys/admin/${row.id}`)
    const data = response

    isEditing.value = true
    editingId.value = row.id
    surveyForm.value = {
      title: data.title,
      description: data.description,
      status: data.status,
      start_time: data.start_time ? new Date(data.start_time) : null,
      end_time: data.end_time ? new Date(data.end_time) : null,
      allow_anonymous: data.allow_anonymous,
      allow_multiple: data.allow_multiple,
      max_responses: data.max_responses,
      questions: data.questions.map((q: any) => ({
        ...q,
        config: q.config || {},
        options: q.options || []
      }))
    }
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取问卷详情失败')
  }
}

const viewSurvey = (row: any) => {
  window.open(`/survey/${row.id}`, '_blank')
}

const viewStatistics = async (row: any) => {
  try {
    const response = await api.get(`/surveys/admin/${row.id}/statistics`)
    statistics.value = response
    statisticsVisible.value = true
  } catch (error) {
    ElMessage.error('获取统计失败')
  }
}

const formatOptionStats = (stats: Record<string, number>) => {
  const total = Object.values(stats).reduce((a, b) => a + b, 0)
  return Object.entries(stats).map(([option, count]) => ({
    option,
    count,
    percentage: total > 0 ? Math.round((count / total) * 100) : 0
  }))
}

const deleteSurvey = async (row: any) => {
  const confirm = await ElMessageBox.confirm(
    `确定要删除问卷"${row.title}"吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'danger'
    }
  ).catch(() => false)

  if (!confirm) return

  try {
    await api.delete(`/surveys/admin/${row.id}`)
    ElMessage.success('删除成功')
    fetchSurveys()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const viewResponses = async (row: any) => {
  currentSurvey.value = row
  responsesPage.value = 1
  responsesVisible.value = true
  await fetchResponses()
}

const fetchResponses = async () => {
  if (!currentSurvey.value) return

  responsesLoading.value = true
  try {
    const response = await api.get(`/surveys/admin/${currentSurvey.value.id}/responses`, {
      params: { page: responsesPage.value, page_size: responsesPageSize.value }
    })
    responses.value = response.responses || []
    responsesTotal.value = response.total || 0
  } catch (error) {
    ElMessage.error('获取填写记录失败')
  } finally {
    responsesLoading.value = false
  }
}

const viewResponseDetail = (row: any) => {
  window.open(`/admin/survey-response/${row.id}`, '_blank')
}

onMounted(() => {
  fetchSurveys()
})
</script>

<style scoped>
.survey-manage-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
}

.page-header .el-button {
  font-size: 16px;
  padding: 8px 16px;
}

.survey-title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.survey-title-cell .title {
  flex: 1;
  font-size: 16px;
}

.survey-title-cell .status-tag {
  font-size: 14px;
  padding: 2px 8px;
}

.time-info {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.settings-info {
  display: flex;
  gap: 4px;
}

.settings-info .el-tag {
  font-size: 14px;
  padding: 2px 8px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.pagination-wrapper .el-pagination {
  font-size: 16px;
}

.question-editor {
  margin-bottom: 16px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
}

.question-header .el-button {
  font-size: 14px;
}

.option-item {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.option-item .el-input {
  font-size: 16px;
}

.option-item .el-input :deep(.el-input__inner) {
  font-size: 16px;
}

.option-item .el-button {
  font-size: 14px;
}

.statistics-content .stat-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.statistics-content .stat-header h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
}

.statistics-content .stat-header p {
  font-size: 16px;
}

.statistics-content .stat-question {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.statistics-content .stat-question:last-child {
  border-bottom: none;
}

.statistics-content .stat-question h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.statistics-content .stat-question .question-type {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.rating-stat {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rating-stat .rating-count {
  color: var(--text-secondary);
  font-size: 16px;
}

.rating-stat .el-rate {
  font-size: 16px;
}

.responses-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.responses-header h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
}

.responses-header p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 16px;
}

.username {
  font-weight: 500;
  font-size: 16px;
}

.email {
  font-size: 14px;
  color: var(--text-secondary);
}

.el-table {
  font-size: 16px;
}

.el-table :deep(.el-table__cell) {
  font-size: 16px;
}

.el-dialog {
  font-size: 16px;
}

.el-dialog__title {
  font-size: 20px;
}

.el-form {
  font-size: 16px;
}

.el-form-item__label {
  font-size: 16px;
}

.el-input {
  font-size: 16px;
}

.el-input :deep(.el-input__inner) {
  font-size: 16px;
}

.el-select {
  font-size: 16px;
}

.el-select :deep(.el-select__input) {
  font-size: 16px;
}

.el-select :deep(.el-select__placeholder) {
  font-size: 16px;
}

.el-date-picker {
  font-size: 16px;
}

.el-date-picker :deep(.el-input__inner) {
  font-size: 16px;
}

.el-switch {
  font-size: 16px;
}

.el-switch :deep(.el-switch__label) {
  font-size: 16px;
}

.el-input-number {
  font-size: 16px;
}

.el-input-number :deep(.el-input__inner) {
  font-size: 16px;
}

.el-button {
  font-size: 16px;
  padding: 8px 16px;
}

.el-button--small {
  font-size: 14px;
  padding: 6px 12px;
}

.el-tag {
  font-size: 14px;
}

.el-divider__text {
  font-size: 18px;
}
</style>
