<template>
  <el-dialog
    v-model="visible"
    title="上传表格"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="选择文件" prop="file">
        <el-upload
          class="file-uploader"
          drag
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileChange"
          :before-upload="beforeUpload"
          accept=".xlsx,.xls,.xlsm"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .xlsx, .xls, .xlsm 格式，文件不超过 5MB
            </div>
          </template>
        </el-upload>
        <div v-if="form.file" class="selected-file">
          <el-tag closable @close="clearFile" type="info">
            <el-icon><Document /></el-icon>
            {{ form.file.name }}
          </el-tag>
        </div>
      </el-form-item>

      <el-form-item label="表格标题" prop="title">
        <el-input v-model="form.title" placeholder="请输入表格标题（不超过15字）" maxlength="15" show-word-limit />
      </el-form-item>

      <el-form-item label="上传区域" prop="area">
        <el-radio-group v-model="form.area">
          <el-radio value="pull_table">拉表区</el-radio>
          <el-radio value="other">其他区</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="表格介绍" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="简单介绍一下这个表格（不超过100字）"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="uploading" @click="handleSubmit">
        {{ uploading ? '上传中...' : '发布' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { UploadFilled, Document } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: boolean
  initialFile?: File | null
  initialFileId?: string | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formRef = ref<FormInstance>()
const uploading = ref(false)

const form = reactive({
  file: null as File | null,
  title: '',
  area: 'pull_table' as 'pull_table' | 'other',
  description: ''
})

const rules: FormRules = {
  file: [
    { required: true, message: '请选择要上传的文件', trigger: 'change' }
  ],
  title: [
    { required: true, message: '请输入表格标题', trigger: 'blur' },
    { min: 2, max: 15, message: '标题长度在 2 到 15 个字符', trigger: 'blur' }
  ],
  area: [
    { required: true, message: '请选择上传区域', trigger: 'change' }
  ]
}

function beforeUpload(file: File) {
  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 5MB')
    return false
  }
  return true
}

function handleFileChange(file: any) {
  form.file = file.raw
}

function clearFile() {
  form.file = null
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    uploading.value = true
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        ElMessage.error('请先登录后再上传')
        uploading.value = false
        return
      }

      const formData = new FormData()
      if (form.file) {
        formData.append('file', form.file)
      }

      const uploadResponse = await fetch('/WutheringWavesDPS/api/uploads', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json().catch(() => ({}))
        throw new Error(errorData.detail || '文件上传失败')
      }

      const uploadResult = await uploadResponse.json()
      
      let fileUrl = uploadResult.file_url
      if (!fileUrl.startsWith('/WutheringWavesDPS')) {
        fileUrl = '/WutheringWavesDPS' + fileUrl
      }

      const spreadsheetData = {
        title: form.title,
        description: form.description || null,
        area: form.area,
        character_tags: [],
        tags: [],
        is_public: true,
        is_draft: false,
        file_url: fileUrl,
        file_size: uploadResult.file_size
      }

      const createResponse = await fetch('/WutheringWavesDPS/api/spreadsheets', {
        method: 'POST',
        body: JSON.stringify(spreadsheetData),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })

      if (!createResponse.ok) {
        const errorData = await createResponse.json().catch(() => ({}))
        throw new Error(errorData.detail || '创建表格失败')
      }

      ElMessage.success('表格已发布！')
      emit('success')
      handleCancel()

    } catch (error: any) {
      ElMessage.error(error.message || '上传失败，请重试')
      console.error(error)
    } finally {
      uploading.value = false
    }
  })
}

function handleCancel() {
  visible.value = false
  resetForm()
}

function resetForm() {
  form.file = null
  form.title = ''
  form.area = 'pull_table'
  form.description = ''
  formRef.value?.resetFields()
}

watch(() => props.initialFile, (newFile) => {
  if (newFile) {
    form.file = newFile
    form.title = newFile.name.replace(/\.(xlsx|xls|xlsm)$/i, '')
  }
})

watch(visible, (val) => {
  if (!val) {
    resetForm()
  }
})
</script>

<style scoped>
.file-uploader {
  width: 100%;
}

.selected-file {
  margin-top: 10px;
}
</style>
