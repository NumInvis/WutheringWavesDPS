<template>
  <div class="tier-list-container">
    <div class="tier-list-header">
      <h1 class="page-title">自定义角色排行</h1>
      <div class="header-actions">
        <el-button 
          v-if="userStore.user?.is_admin"
          type="primary"
          @click="showAddCharacter = true"
        >
          <el-icon><Plus /></el-icon>
          添加角色
        </el-button>
        <el-button 
          v-if="userStore.isAuthenticated"
          type="success"
          @click="exportImage"
        >
          <el-icon><Download /></el-icon>
          导出图片
        </el-button>
      </div>
    </div>

    <div class="tier-list-content">
      <div class="tier-list-main" ref="tierListRef">
        <div class="tier-rows">
          <div 
            v-for="(tier, index) in tiers" 
            :key="tier.id"
            class="tier-row"
          >
            <div 
              class="tier-label"
              :style="{ backgroundColor: tier.color }"
            >
              {{ tier.label }}
            </div>
            <div 
              class="tier-items"
              :class="{ 'disabled': !userStore.isAuthenticated }"
              @dragover.prevent="userStore.isAuthenticated"
              @drop="userStore.isAuthenticated ? handleDrop($event, index) : null"
            >
              <div
                v-for="character in tier.characters"
                :key="character.id"
                class="character-item"
                :class="{ 
                  'disabled': !userStore.isAuthenticated,
                  'star-5': character.rarity === 5,
                  'star-4': character.rarity === 4
                }"
                :draggable="userStore.isAuthenticated"
                @dragstart="userStore.isAuthenticated ? handleDragStart($event, tier.id, character) : null"
                @dragend="userStore.isAuthenticated ? handleDragEnd() : null"
              >
                <img 
                  v-if="character.image" 
                  :src="character.image" 
                  :alt="character.name"
                  class="character-image"
                />
                <div v-else class="character-placeholder">
                  {{ character.name ? character.name.charAt(0) : '?' }}
                </div>
                <span class="character-name">{{ character.name }}</span>
                <div class="rarity-badge" :class="'rarity-' + character.rarity">
                  {{ character.rarity }}★
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="character-pool-section">
        <h2 class="section-title">角色池</h2>
        <div class="character-pool">
          <div
            v-for="character in characterPool"
            :key="character.id"
            class="pool-character"
            :class="{ 
              'disabled': !userStore.isAuthenticated,
              'star-5': character.rarity === 5,
              'star-4': character.rarity === 4
            }"
            :draggable="userStore.isAuthenticated"
            @dragstart="userStore.isAuthenticated ? handleDragStart($event, null, character) : null"
            @dragend="userStore.isAuthenticated ? handleDragEnd() : null"
          >
            <img 
              v-if="character.image" 
              :src="character.image" 
              :alt="character.name"
              class="character-image"
            />
            <div v-else class="character-placeholder">
              {{ character.name ? character.name.charAt(0) : '?' }}
            </div>
            <span class="character-name">{{ character.name }}</span>
            <div class="rarity-badge" :class="'rarity-' + character.rarity">
              {{ character.rarity }}★
            </div>
            <el-button 
              v-if="userStore.user?.is_admin"
              type="danger"
              size="small"
              circle
              class="delete-btn"
              @click.stop="deleteCharacter(character.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog 
      v-model="showAddCharacter" 
      title="添加新角色" 
      width="450px"
    >
      <el-form :model="newCharacterForm" label-width="80px">
        <el-form-item label="角色名称">
          <el-input v-model="newCharacterForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色星级">
          <el-radio-group v-model="newCharacterForm.rarity">
            <el-radio-button :value="4">四星</el-radio-button>
            <el-radio-button :value="5">五星</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="角色头像">
          <el-upload
            class="avatar-uploader"
            :action="uploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="handleAvatarSuccess"
            :before-upload="beforeAvatarUpload"
          >
            <img v-if="newCharacterForm.image" :src="newCharacterForm.image" class="avatar" />
            <div v-else class="upload-placeholder">
              <el-icon class="upload-icon"><Plus /></el-icon>
              <span>点击上传</span>
            </div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddCharacter = false">取消</el-button>
        <el-button type="primary" @click="addCharacter" :loading="addCharacterLoading">
          添加
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Download, Delete } from '@element-plus/icons-vue'
import html2canvas from 'html2canvas'
import { useUserStore } from '../stores/user'
import axios from 'axios'

interface Character {
  id: string
  name: string
  image?: string
  rarity: 4 | 5
}

interface Tier {
  id: string
  label: string
  color: string
  characters: Character[]
}

const userStore = useUserStore()

const tierListRef = ref<HTMLElement>()
const showAddCharacter = ref(false)
const addCharacterLoading = ref(false)
const newCharacterForm = ref({
  name: '',
  image: '',
  rarity: 5 as 4 | 5
})

const tierColors = [
  '#ff4444',
  '#ff9800',
  '#ffeb3b',
  '#4caf50',
  '#2196f3',
  '#9c27b0',
  '#607d8b'
]

const tierLabels = ['SS', 'S', 'A', 'B', 'C', 'D', 'F']

const characterPool = ref<Character[]>([])

const tiers = ref<Tier[]>([
  { id: 'tier-1', label: 'SS', color: '#ff4444', characters: [] },
  { id: 'tier-2', label: 'S', color: '#ff9800', characters: [] },
  { id: 'tier-3', label: 'A', color: '#ffeb3b', characters: [] },
  { id: 'tier-4', label: 'B', color: '#4caf50', characters: [] },
  { id: 'tier-5', label: 'C', color: '#2196f3', characters: [] }
])

const uploadUrl = import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/upload'
const uploadHeaders = {
  'Authorization': userStore.token ? 'Bearer ' + userStore.token : ''
}

let dragData: { tierId: string | null; character: Character } | null = null

function handleDragStart(e: DragEvent, tierId: string | null, character: Character) {
  dragData = { tierId, character }
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
  }
}

function handleDragEnd() {
  dragData = null
}

function handleDrop(e: DragEvent, targetTierIndex: number) {
  e.preventDefault()
  if (!dragData) return

  const { tierId, character } = dragData
  
  if (tierId) {
    const sourceTier = tiers.value.find(t => t.id === tierId)
    if (sourceTier) {
      sourceTier.characters = sourceTier.characters.filter(c => c.id !== character.id)
    }
  } else {
    characterPool.value = characterPool.value.filter(c => c.id !== character.id)
  }

  tiers.value[targetTierIndex].characters.push({ ...character })
}

async function exportImage() {
  if (!tierListRef.value) return
  
  try {
    ElMessage.info('正在生成图片...')
    
    const canvas = await html2canvas(tierListRef.value, {
      backgroundColor: '#0f0f1a',
      scale: 2,
      useCORS: true
    })
    
    const link = document.createElement('a')
    link.download = 'wuthering-waves-tier-list.png'
    link.href = canvas.toDataURL('image/png')
    link.click()
    
    ElMessage.success('图片导出成功！')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('图片导出失败，请重试')
  }
}

function handleAvatarSuccess(response: any) {
  newCharacterForm.value.image = response.file_url
  ElMessage.success('头像上传成功！')
}

function beforeAvatarUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB!')
    return false
  }
  return true
}

async function addCharacter() {
  if (!newCharacterForm.value.name) {
    ElMessage.error('请输入角色名称')
    return
  }
  
  addCharacterLoading.value = true
  try {
    const response = await axios.post(
      import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/characters/admin/characters',
      {
        name: newCharacterForm.value.name,
        image: newCharacterForm.value.image,
        rarity: newCharacterForm.value.rarity
      },
      {
        headers: {
          'Authorization': 'Bearer ' + userStore.token
        }
      }
    )
    
    characterPool.value.push(response.data)
    ElMessage.success('角色添加成功！')
    showAddCharacter.value = false
    newCharacterForm.value = { name: '', image: '', rarity: 5 }
  } catch (error) {
    ElMessage.error('添加角色失败')
  } finally {
    addCharacterLoading.value = false
  }
}

async function deleteCharacter(id: string) {
  try {
    await axios.delete(
      import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/characters/admin/characters/' + id,
      {
        headers: {
          'Authorization': 'Bearer ' + userStore.token
        }
      }
    )
    
    characterPool.value = characterPool.value.filter(c => c.id !== id)
    ElMessage.success('角色删除成功！')
  } catch (error) {
    ElMessage.error('删除角色失败')
  }
}

async function loadCharacters() {
  try {
    const response = await axios.get(import.meta.env.VITE_API_URL + '/WutheringWavesDPS/api/characters')
    characterPool.value = response.data
  } catch (error) {
    console.error('加载角色失败:', error)
  }
}

onMounted(() => {
  loadCharacters()
})
</script>

<style scoped>
.tier-list-container {
  min-height: calc(100vh - 128px);
  padding: 24px;
  color: #e2e8f0;
  position: relative;
  z-index: 1;
}

.tier-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.tier-list-content {
  display: flex;
  gap: 24px;
  max-width: 1800px;
  margin: 0 auto;
}

.tier-list-main {
  flex: 1;
  min-width: 0;
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
}

.tier-rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tier-row {
  display: flex;
  align-items: stretch;
  background: rgba(20, 20, 35, 0.9);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(167, 139, 250, 0.15);
}

.tier-label {
  width: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 800;
  color: #000;
  flex-shrink: 0;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.3);
}

.tier-items {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px;
  min-height: 80px;
  align-content: flex-start;
}

.tier-items.disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.character-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 8px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  cursor: grab;
  transition: all 0.3s ease;
  min-width: 70px;
  position: relative;
  border: 2px solid transparent;
}

.character-item.star-5 {
  border-color: #ffd700;
  box-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
}

.character-item.star-4 {
  border-color: #a855f7;
  box-shadow: 0 0 10px rgba(168, 85, 247, 0.3);
}

.character-item.disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.character-item:hover:not(.disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.character-item:active {
  cursor: grabbing;
}

.character-image {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.character-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.character-name {
  font-size: 11px;
  font-weight: 600;
  color: #e2e8f0;
  text-align: center;
  max-width: 70px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rarity-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 10px;
  z-index: 10;
}

.rarity-badge.rarity-5 {
  background: linear-gradient(135deg, #ffd700, #ffb700);
  color: #000;
  box-shadow: 0 2px 6px rgba(255, 215, 0, 0.5);
}

.rarity-badge.rarity-4 {
  background: linear-gradient(135deg, #a855f7, #7c3aed);
  color: #fff;
  box-shadow: 0 2px 6px rgba(168, 85, 247, 0.5);
}

.character-pool-section {
  width: 320px;
  flex-shrink: 0;
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 16px 0;
  color: #fff;
}

.character-pool {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
  padding: 4px;
}

.pool-character {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  cursor: grab;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  position: relative;
}

.pool-character.star-5 {
  border-color: #ffd700;
  box-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
}

.pool-character.star-4 {
  border-color: #a855f7;
  box-shadow: 0 0 10px rgba(168, 85, 247, 0.3);
}

.pool-character.disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.pool-character:hover:not(.disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.pool-character:active {
  cursor: grabbing;
}

.pool-character .character-image,
.pool-character .character-placeholder {
  width: 44px;
  height: 44px;
}

.pool-character .character-name {
  font-size: 10px;
  max-width: 60px;
}

.delete-btn {
  position: absolute;
  top: -8px;
  left: -8px;
  width: 24px;
  height: 24px;
  z-index: 20;
}

.character-pool::-webkit-scrollbar {
  width: 6px;
}

.character-pool::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.character-pool::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 3px;
}

.avatar-uploader .avatar {
  width: 100px;
  height: 100px;
  border-radius: 12px;
  object-fit: cover;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.upload-placeholder {
  width: 100px;
  height: 100px;
  border: 2px dashed rgba(167, 139, 250, 0.5);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(167, 139, 250, 0.05);
}

.upload-placeholder:hover {
  border-color: rgba(167, 139, 250, 0.8);
  background: rgba(167, 139, 250, 0.1);
}

.upload-icon {
  font-size: 28px;
  color: #a78bfa;
}

.upload-placeholder span {
  font-size: 12px;
  color: #94a3b8;
}
</style>
