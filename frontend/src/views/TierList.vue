<template>
  <div class="tier-maker">
    <!-- 顶部工具栏 -->
    <header class="toolbar">
      <div class="toolbar-brand">
        <h1>角色排行制作器</h1>
      </div>
      <div class="toolbar-actions">
        <label class="toggle-label">
          <input type="checkbox" v-model="showNames" @change="saveUserData" />
          <span>显示名称</span>
        </label>
        <button v-if="userStore.isAuthenticated" class="btn btn-secondary" @click="editSettings">
          设置
        </button>
        <button v-if="userStore.isAuthenticated" class="btn btn-secondary" @click="resetTierList">
          重置
        </button>
      </div>
    </header>

    <!-- 游客提示 -->
    <div v-if="!userStore.isAuthenticated" class="guest-notice">
      <span>登录后可以创建和保存自己的排行榜</span>
    </div>

    <div class="workspace">
      <!-- 左侧：角色素材库 -->
      <aside class="material-panel">
        <div class="panel-header">
          <h2>角色素材库</h2>
          <span class="badge">{{ allCharacters.length }}</span>
        </div>
        <div class="material-grid">
          <div
            v-for="character in allCharacters"
            :key="character.id"
            class="material-card"
            :class="{ 'star-5': character.rarity === 5, 'star-4': character.rarity === 4 }"
            draggable="true"
            @dragstart="handleDragStart($event, character)"
          >
            <div class="card-image">
              <img :src="character.image" :alt="character.name" loading="lazy" />
            </div>
            <span v-if="showNames" class="card-name" :style="{ fontSize: cardNameSize + 'px' }">{{ character.name }}</span>
          </div>
        </div>
      </aside>

      <!-- 右侧：排行榜 -->
      <main class="ranking-panel" :style="{ backgroundColor: `rgba(22, 22, 32, ${bgOpacity / 100})` }">
        <div class="ranking-header">
          <h2 :style="{ fontSize: titleSize + 'px' }">{{ tierTitle }}</h2>
        </div>
        <div class="tier-list">
          <div
            v-for="(tier, index) in tiers"
            :key="tier.id"
            class="tier-row"
            :class="{ 'drop-active': dragOverTier === index }"
            @dragover.prevent="handleDragOver($event, index)"
            @dragleave="handleDragLeave"
            @drop="handleDrop($event, index)"
          >
            <div class="tier-label" :style="{ backgroundColor: tier.color, fontSize: tierLabelSize + 'px', opacity: tierOpacity / 100 }">
              {{ tier.label }}
            </div>
            <div class="tier-slots">
              <div
                v-for="(char, charIndex) in tier.characters"
                :key="char.instanceId"
                class="slot-card"
                :class="{ 'star-5': char.rarity === 5, 'star-4': char.rarity === 4 }"
                draggable="true"
                @dragstart="handleTierDragStart($event, tier.id, char, charIndex)"
              >
                <div class="slot-image">
                  <img :src="char.image" :alt="char.name" />
                </div>
                <span v-if="showNames" class="slot-name" :style="{ fontSize: cardNameSize + 'px' }">{{ char.name }}</span>
                <button class="slot-remove" @click="removeFromTier(tier.id, charIndex)">×</button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- 设置弹窗 -->
    <div v-if="showSettings" class="modal" @click.self="showSettings = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>排行榜设置</h3>
          <button class="close-btn" @click="showSettings = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>排行榜标题</label>
            <input v-model="editTitleText" type="text" maxlength="30" />
          </div>
          <div class="form-group">
            <label>标题字号 ({{ editTitleSize }}px)</label>
            <input v-model.number="editTitleSize" type="range" min="16" max="48" />
          </div>
          <div class="form-group">
            <label>层级标签字号 ({{ editTierLabelSize }}px)</label>
            <input v-model.number="editTierLabelSize" type="range" min="16" max="40" />
          </div>
          <div class="form-group">
            <label>角色名字号 ({{ editCardNameSize }}px)</label>
            <input v-model.number="editCardNameSize" type="range" min="8" max="16" />
          </div>
          <div class="form-group">
            <label>层级颜色不透明度 ({{ editTierOpacity }}%)</label>
            <input v-model.number="editTierOpacity" type="range" min="20" max="100" />
          </div>
          <div class="form-group">
            <label>排行榜背景透明度 ({{ editBgOpacity }}%)</label>
            <input v-model.number="editBgOpacity" type="range" min="0" max="100" />
          </div>
          <div class="form-group">
            <label>层级设置</label>
            <div class="tier-settings">
              <div v-for="(tier, index) in editTiers" :key="tier.id" class="tier-setting-row">
                <input v-model="tier.label" type="text" maxlength="3" class="tier-label-input" />
                <input v-model="tier.color" type="color" class="tier-color-input" />
                <button v-if="editTiers.length > 2" class="btn-icon" @click="removeTier(index)">−</button>
              </div>
              <button v-if="editTiers.length < 8" class="btn btn-secondary btn-full" @click="addTier">
                + 添加层级
              </button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showSettings = false">取消</button>
          <button class="btn btn-primary" @click="saveSettings">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { characterImages } from '../characterImages.js'

interface Character {
  id: string
  name: string
  image: string
  rarity: 4 | 5
}

interface TierCharacter extends Character {
  instanceId: string
}

interface Tier {
  id: string
  label: string
  color: string
  characters: TierCharacter[]
}

const userStore = useUserStore()
const showSettings = ref(false)
const showNames = ref(true)
const dragOverTier = ref<number | null>(null)

const tierTitle = ref('我的排行榜')
const titleSize = ref(24)
const tierLabelSize = ref(28)
const cardNameSize = ref(11)
const tierOpacity = ref(100)
const bgOpacity = ref(100)

const editTitleText = ref('')
const editTitleSize = ref(24)
const editTierLabelSize = ref(28)
const editCardNameSize = ref(11)
const editTierOpacity = ref(100)
const editBgOpacity = ref(100)

const defaultTiers: Tier[] = [
  { id: 'S', label: 'S', color: '#ff6b6b', characters: [] },
  { id: 'A', label: 'A', color: '#ffa94d', characters: [] },
  { id: 'B', label: 'B', color: '#ffd43b', characters: [] },
  { id: 'C', label: 'C', color: '#69db7c', characters: [] },
  { id: 'D', label: 'D', color: '#4dabf7', characters: [] }
]

const tiers = ref<Tier[]>(JSON.parse(JSON.stringify(defaultTiers)))
const editTiers = ref<Tier[]>([])

const allCharacters = ref<Character[]>([])

// 加载角色数据
const loadCharacters = async () => {
  try {
    const response = await fetch('/WutheringWavesDPS/characters.json')
    const data = await response.json()
    if (data.characters && Array.isArray(data.characters)) {
      // 使用Base64图片
      allCharacters.value = data.characters.map(char => ({
        ...char,
        image: characterImages[char.name] || ''
      }))
    }
  } catch (e) {
    console.error('加载角色失败:', e)
  }
}

// 加载用户数据
const loadUserData = () => {
  if (!userStore.user?.id) return
  try {
    const stored = localStorage.getItem(`wwdps_user_${userStore.user.id}`)
    if (stored) {
      const data = JSON.parse(stored)
      if (data.title) tierTitle.value = data.title
      if (data.titleSize) titleSize.value = data.titleSize
      if (data.tierLabelSize) tierLabelSize.value = data.tierLabelSize
      if (data.cardNameSize) cardNameSize.value = data.cardNameSize
      if (data.tierOpacity) tierOpacity.value = data.tierOpacity
      if (data.bgOpacity) bgOpacity.value = data.bgOpacity
      if (data.tiers) tiers.value = data.tiers
      if (data.showNames !== undefined) showNames.value = data.showNames
    }
  } catch (e) {
    console.error('加载用户数据失败:', e)
  }
}

// 保存用户数据
const saveUserData = () => {
  if (!userStore.user?.id) return
  const data = {
    title: tierTitle.value,
    titleSize: titleSize.value,
    tierLabelSize: tierLabelSize.value,
    cardNameSize: cardNameSize.value,
    tierOpacity: tierOpacity.value,
    bgOpacity: bgOpacity.value,
    tiers: tiers.value,
    showNames: showNames.value
  }
  localStorage.setItem(`wwdps_user_${userStore.user.id}`, JSON.stringify(data))
}

// 拖拽从素材库
function handleDragStart(e: DragEvent, character: Character) {
  if (e.dataTransfer) {
    e.dataTransfer.setData('application/json', JSON.stringify({ character, fromPool: true }))
    e.dataTransfer.effectAllowed = 'copy'
  }
}

// 拖拽从tier
function handleTierDragStart(e: DragEvent, tierId: string, character: TierCharacter, index: number) {
  if (e.dataTransfer) {
    e.dataTransfer.setData('application/json', JSON.stringify({ character, tierId, index, fromTier: true }))
    e.dataTransfer.effectAllowed = 'move'
  }
}

function handleDragOver(e: DragEvent, tierIndex: number) {
  e.preventDefault()
  dragOverTier.value = tierIndex
}

function handleDragLeave() {
  dragOverTier.value = null
}

function handleDrop(e: DragEvent, tierIndex: number) {
  e.preventDefault()
  dragOverTier.value = null
  
  const data = e.dataTransfer?.getData('application/json')
  if (!data) return
  
  try {
    const { character, tierId, index, fromTier } = JSON.parse(data)
    
    // 从原tier移除
    if (fromTier && tierId) {
      const sourceTier = tiers.value.find(t => t.id === tierId)
      if (sourceTier) {
        sourceTier.characters.splice(index, 1)
      }
    }
    
    // 添加到目标tier
    const newChar: TierCharacter = {
      ...character,
      instanceId: `${character.id}_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`
    }
    tiers.value[tierIndex].characters.push(newChar)
    
    saveUserData()
  } catch (e) {
    console.error('拖放失败:', e)
  }
}

function removeFromTier(tierId: string, charIndex: number) {
  const tier = tiers.value.find(t => t.id === tierId)
  if (tier) {
    tier.characters.splice(charIndex, 1)
    saveUserData()
  }
}

function resetTierList() {
  tiers.value.forEach(tier => tier.characters = [])
  saveUserData()
}

// 编辑设置
function editSettings() {
  editTitleText.value = tierTitle.value
  editTitleSize.value = titleSize.value
  editTierLabelSize.value = tierLabelSize.value
  editCardNameSize.value = cardNameSize.value
  editTierOpacity.value = tierOpacity.value
  editBgOpacity.value = bgOpacity.value
  editTiers.value = JSON.parse(JSON.stringify(tiers.value))
  showSettings.value = true
}

function saveSettings() {
  tierTitle.value = editTitleText.value || '我的排行榜'
  titleSize.value = editTitleSize.value
  tierLabelSize.value = editTierLabelSize.value
  cardNameSize.value = editCardNameSize.value
  tierOpacity.value = editTierOpacity.value
  bgOpacity.value = editBgOpacity.value
  tiers.value = editTiers.value.map(t => ({
    ...t,
    characters: tiers.value.find(ot => ot.id === t.id)?.characters || []
  }))
  showSettings.value = false
  saveUserData()
}

function addTier() {
  const colors = ['#ff6b6b', '#ffa94d', '#ffd43b', '#69db7c', '#4dabf7', '#da77f2', '#adb5bd', '#495057']
  const labels = ['S', 'A', 'B', 'C', 'D', 'E', 'F', 'G']
  const index = editTiers.value.length
  editTiers.value.push({
    id: `tier_${Date.now()}`,
    label: labels[index] || `T${index + 1}`,
    color: colors[index] || '#666',
    characters: []
  })
}

function removeTier(index: number) {
  editTiers.value.splice(index, 1)
}

onMounted(() => {
  loadCharacters()
  loadUserData()
})
</script>

<style scoped>
.tier-maker {
  min-height: 100vh;
  background: #0d0d15;
  color: #e8e8f0;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #161620;
  border-bottom: 1px solid #2a2a3a;
}

.toolbar-brand h1 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #fff;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #a0a0b0;
}

.toggle-label input {
  accent-color: #4dabf7;
}

.btn {
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4dabf7;
  color: #fff;
}

.btn-primary:hover {
  background: #339af0;
}

.btn-secondary {
  background: #3a3a5a;
  color: #fff;
  border: 1px solid #4a4a6a;
  font-weight: 500;
}

.btn-secondary:hover {
  background: #4a4a7a;
  border-color: #5a5a8a;
}

.btn-full {
  width: 100%;
}

.btn-text {
  background: transparent;
  color: #a0a0b0;
}

.btn-text:hover {
  color: #fff;
}

.btn-icon {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: none;
  background: #ff6b6b;
  color: #fff;
  cursor: pointer;
  font-size: 16px;
}

/* 游客提示 */
.guest-notice {
  background: #1a1a28;
  padding: 10px 24px;
  text-align: center;
  color: #808090;
  font-size: 13px;
  border-bottom: 1px solid #2a2a3a;
}

/* 工作区 */
.workspace {
  display: flex;
  height: calc(100vh - 57px);
}

/* 左侧素材面板 */
.material-panel {
  width: 380px;
  flex-shrink: 0;
  background: #161620;
  border-right: 1px solid #2a2a3a;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #2a2a3a;
}

.panel-header h2 {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  color: #fff;
}

.badge {
  background: #2a2a3a;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  color: #808090;
}

.material-grid {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  align-content: start;
}

.material-card {
  background: #1e1e2e;
  border-radius: 8px;
  padding: 8px;
  text-align: center;
  cursor: grab;
  border: 2px solid transparent;
  transition: transform 0.15s;
}

.material-card:hover {
  transform: translateY(-2px);
}

.material-card.star-5 {
  border-color: #ffd700;
}

.material-card.star-4 {
  border-color: #a855f7;
}

.card-image {
  width: 64px;
  height: 64px;
  margin: 0 auto 8px;
  border-radius: 6px;
  overflow: hidden;
  background: #2a2a3a;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-name {
  color: #b0b0c0;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 右侧排行面板 */
.ranking-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ranking-header {
  padding: 24px;
  border-bottom: 1px solid #2a2a3a;
  text-align: center;
}

.ranking-header h2 {
  font-weight: 700;
  margin: 0;
  color: #fff;
}

.tier-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tier-row {
  display: flex;
  background: #161620;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #2a2a3a;
  min-height: 100px;
}

.tier-row.drop-active {
  border-color: #4dabf7;
  box-shadow: 0 0 0 2px rgba(77, 171, 247, 0.2);
}

.tier-label {
  width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #000;
  flex-shrink: 0;
  user-select: none;
}

.tier-slots {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 14px;
  align-content: flex-start;
}

.slot-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #1e1e2e;
  border-radius: 8px;
  padding: 4px;
  border: 2px solid transparent;
  cursor: grab;
}

.slot-card.star-5 {
  border-color: #ffd700;
}

.slot-card.star-4 {
  border-color: #a855f7;
}

.slot-image {
  width: 64px;
  height: 64px;
  border-radius: 6px;
  overflow: hidden;
  background: #2a2a3a;
}

.slot-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.slot-name {
  color: #b0b0c0;
  margin-top: 4px;
  max-width: 64px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.slot-remove {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ff6b6b;
  border: 2px solid #0d0d15;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.slot-card:hover .slot-remove {
  opacity: 1;
}

/* 弹窗 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #161620;
  border-radius: 12px;
  width: 420px;
  max-height: 80vh;
  overflow-y: auto;
  border: 1px solid #2a2a3a;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #2a2a3a;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: #606070;
  font-size: 24px;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #2a2a3a;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #a0a0b0;
}

.form-group input[type="text"] {
  width: 100%;
  padding: 10px 12px;
  background: #1e1e2e;
  border: 1px solid #2a2a3a;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input[type="range"] {
  width: 100%;
  cursor: pointer;
}

.tier-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tier-setting-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tier-label-input {
  width: 60px !important;
  text-align: center;
}

.tier-color-input {
  width: 40px;
  height: 36px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 滚动条 */
.material-grid::-webkit-scrollbar,
.tier-list::-webkit-scrollbar,
.modal-content::-webkit-scrollbar {
  width: 6px;
}

.material-grid::-webkit-scrollbar-track,
.tier-list::-webkit-scrollbar-track,
.modal-content::-webkit-scrollbar-track {
  background: transparent;
}

.material-grid::-webkit-scrollbar-thumb,
.tier-list::-webkit-scrollbar-thumb,
.modal-content::-webkit-scrollbar-thumb {
  background: #3a3a4a;
  border-radius: 3px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .material-panel {
    width: 300px;
  }
  
  .material-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .workspace {
    flex-direction: column;
  }
  
  .material-panel {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid #2a2a3a;
  }
  
  .material-grid {
    grid-template-columns: repeat(6, 1fr);
  }
}
</style>
