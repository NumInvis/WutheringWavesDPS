<template>
  <el-dialog
    v-model="visible"
    title="上传表格"
    width="600px"
    :close-on-click-modal="false"
    class="upload-dialog"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="选择文件" prop="file">
        <el-upload
          class="file-uploader"
          drag
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileChange"
          accept=".xlsx,.xls"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              仅支持 .xlsx 和 .xls 格式
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
        <el-input v-model="form.title" placeholder="请输入表格标题" maxlength="200" show-word-limit />
      </el-form-item>
      
      <el-form-item label="上传区域" prop="area">
        <el-radio-group v-model="form.area">
          <el-radio value="pull_table">拉表区</el-radio>
          <el-radio value="other">其他区</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item 
        v-if="form.area === 'pull_table'" 
        label="角色标签" 
        prop="characterTags"
      >
        <el-select
          v-model="form.characterTags"
          multiple
          filterable
          placeholder="选择相关角色"
          style="width: 100%"
        >
          <el-option
            v-for="char in characters"
            :key="char.id"
            :label="char.name"
            :value="char.id"
          >
            <span class="char-option">
              <span class="char-name">{{ char.name }}</span>
              <el-tag :type="getElementTagType(char.element)" size="small">
                {{ char.element }}
              </el-tag>
              <el-tag v-if="char.rarity === 5" type="warning" size="small">★5</el-tag>
              <el-tag v-else type="info" size="small">★4</el-tag>
            </span>
          </el-option>
        </el-select>
      </el-form-item>
      
      <el-form-item label="表格介绍" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="简单介绍一下这个表格的用途..."
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="发布状态">
        <el-radio-group v-model="form.isDraft">
          <el-radio :value="false">发布公开</el-radio>
          <el-radio :value="true">保存草稿</el-radio>
        </el-radio-group>
        <div class="form-hint">
          <el-icon v-if="form.isDraft"><Edit /></el-icon>
          <el-icon v-else><Share /></el-icon>
          {{ form.isDraft ? '仅自己可见，可以继续编辑' : '所有人可见，可以搜索和下载' }}
        </div>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="uploading" @click="handleSubmit">
        {{ uploading ? '上传中...' : (form.isDraft ? '保存草稿' : '发布') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { UploadFilled, Document, Edit, Share } from '@element-plus/icons-vue'
import { WUWA_CHARACTERS } from '../data/characters'

const props = defineProps<{
  modelValue: boolean
  initialFile?: File | null
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
const characters = WUWA_CHARACTERS

const form = reactive({
  file: null as File | null,
  title: '',
  area: 'pull_table' as 'pull_table' | 'other',
  characterTags: [] as string[],
  description: '',
  isDraft: false
})

const rules: FormRules = {
  file: [
    { required: true, message: '请选择要上传的文件', trigger: 'change' }
  ],
  title: [
    { required: true, message: '请输入表格标题', trigger: 'blur' },
    { min: 2, max: 200, message: '标题长度在 2 到 200 个字符', trigger: 'blur' }
  ],
  area: [
    { required: true, message: '请选择上传区域', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入表格介绍', trigger: 'blur' },
    { min: 10, max: 500, message: '介绍长度在 10 到 500 个字符', trigger: 'blur' }
  ]
}

function getElementTagType(element: string) {
  const typeMap: Record<string, any> = {
    '光': 'success',
    '暗': 'danger',
    '火': 'warning',
    '水': 'primary',
    '风': 'info',
    '土': ''
  }
  return typeMap[element] || ''
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
      const formData = new FormData()
      if (form.file) {
        formData.append('file', form.file)
      }
      
      const token = localStorage.getItem('token')
      const uploadResponse = await fetch('/api/uploads', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!uploadResponse.ok) {
        throw new Error('文件上传失败')
      }
      
      const uploadResult = await uploadResponse.json()
      
      const spreadsheetData = {
        title: form.title,
        description: form.description,
        area: form.area,
        character_tags: form.area === 'pull_table' ? form.characterTags : [],
        tags: form.characterTags,
        is_public: !form.isDraft,
        is_draft: form.isDraft,
        file_url: uploadResult.file_url,
        file_size: uploadResult.file_size
      }
      
      const createResponse = await fetch('/api/spreadsheets', {
        method: 'POST',
        body: JSON.stringify(spreadsheetData),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!createResponse.ok) {
        throw new Error('创建表格失败')
      }
      
      ElMessage.success(form.isDraft ? '草稿已保存' : '表格已发布！')
      emit('success')
      handleCancel()
      
    } catch (error) {
      ElMessage.error('上传失败，请重试')
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
  form.characterTags = []
  form.description = ''
  form.isDraft = false
  formRef.value?.resetFields()
}

watch(() => props.initialFile, (newFile) => {
  if (newFile) {
    form.file = newFile
    form.title = newFile.name.replace('.xlsx', '').replace('.xls', '')
  }
})

watch(visible, (val) => {
  if (!val) {
    resetForm()
  }
})
</script>

<style scoped>
.upload-dialog {
}

.file-uploader {
  width: 100%;
}

.selected-file {
  margin-top: 10px;
}

.char-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.char-name {
  flex: 1;
}

.form-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
