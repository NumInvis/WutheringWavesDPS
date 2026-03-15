<template>
  <div class="tier-list-container">
    <div class="tier-list-content">
      <div class="tier-list-left">
        <h2 class="section-title">自定义排行</h2>
        
        <div class="tier-rows" ref="tierListRef">
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
              @dragover.prevent
              @drop="(e) => handleDrop(e, index)"
            >
              <div
                v-for="character in tier.characters"
                :key="character.id"
                class="character-item"
                draggable="true"
                @dragstart="(e) => handleDragStart(e, tier.id, character)"
                @dragend="handleDragEnd"
              >
                <img 
                  v-if="character.image" 
                  :src="character.image" 
                  :alt="character.name"
                  class="character-image"
                />
                <div v-else class="character-placeholder">
                  {{ character.name?.charAt(0) || '?' }}
                </div>
                <span class="character-name">{{ character.name }}</span>
              </div>
            </div>
            <button 
              class="remove-tier-btn"
              @click="removeTier(index)"
              v-if="tiers.length > 1"
            >
              <el-icon><Close /></el-icon>
            </button>
          </div>
        </div>
        
        <div class="tier-actions">
          <el-button type="primary" @click="addTier">
            <el-icon><Plus /></el-icon>
            添加层级
          </el-button>
          <el-button type="success" @click="exportImage">
            <el-icon><Download /></el-icon>
            导出图片
          </el-button>
        </div>
      </div>
      
      <div class="tier-list-right">
        <h2 class="section-title">角色池</h2>
        <div class="character-pool">
          <div
            v-for="character in characterPool"
            :key="character.id"
            class="pool-character"
            draggable="true"
            @dragstart="(e) => handleDragStart(e, null, character)"
            @dragend="handleDragEnd"
          >
            <img 
              v-if="character.image" 
              :src="character.image" 
              :alt="character.name"
              class="character-image"
            />
            <div v-else class="character-placeholder">
              {{ character.name?.charAt(0) || '?' }}
            </div>
            <span class="character-name">{{ character.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Download, Close } from '@element-plus/icons-vue'
import html2canvas from 'html2canvas'

interface Character {
  id: string
  name: string
  image?: string
}

interface Tier {
  id: string
  label: string
  color: string
  characters: Character[]
}

const tierListRef = ref<HTMLElement>()

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

const characterPool = ref<Character[]>([
  { id: '1', name: '今汐' },
  { id: '2', name: '折枝' },
  { id: '3', name: '散华' },
  { id: '4', name: '春庭' },
  { id: '5', name: '釉瑚' },
  { id: '6', name: '卡卡罗' },
  { id: '7', name: '安可' },
  { id: '8', name: '维里奈' },
  { id: '9', name: '莫特斐' },
  { id: '10', name: '炽霞' },
  { id: '11', name: '白芷' },
  { id: '12', name: '凌阳' },
  { id: '13', name: '守岸人' },
  { id: '14', name: '渊武' },
  { id: '15', name: '散华' },
  { id: '16', name: '桃祈' },
  { id: '17', name: '丹瑾' },
  { id: '18', name: '鉴心' },
  { id: '19', name: '长离' },
  { id: '20', name: '夜岚' }
])

const tiers = ref<Tier[]>([
  {
    id: 'tier-1',
    label: 'SS',
    color: '#ff4444',
    characters: []
  },
  {
    id: 'tier-2',
    label: 'S',
    color: '#ff9800',
    characters: []
  },
  {
    id: 'tier-3',
    label: 'A',
    color: '#ffeb3b',
    characters: []
  },
  {
    id: 'tier-4',
    label: 'B',
    color: '#4caf50',
    characters: []
  }
])

let dragData: { tierId: string | null; character: Character } | null = null

function handleDragStart(e: DragEvent, tierId: string | null, character: Character) {
  dragData = { tierId, character }
  e.dataTransfer?.effectAllowed = 'move'
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

function addTier() {
  const nextIndex = tiers.value.length
  const newTier: Tier = {
    id: `tier-${Date.now()}`,
    label: tierLabels[nextIndex % tierLabels.length] || '?',
    color: tierColors[nextIndex % tierColors.length],
    characters: []
  }
  tiers.value.push(newTier)
}

function removeTier(index: number) {
  const removedTier = tiers.value[index]
  characterPool.value.push(...removedTier.characters)
  tiers.value.splice(index, 1)
}

async function exportImage() {
  if (!tierListRef.value) return
  
  try {
    ElMessage.info('正在生成图片...')
    
    const canvas = await html2canvas(tierListRef.value, {
      backgroundColor: '#1a1a2e',
      scale: 2,
      useCORS: true
    })
    
    const link = document.createElement('a')
    link.download = 'tier-list.png'
    link.href = canvas.toDataURL('image/png')
    link.click()
    
    ElMessage.success('图片导出成功！')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('图片导出失败，请重试')
  }
}
</script>

<style scoped>
.tier-list-container {
  min-height: calc(100vh - 128px);
  padding: 24px;
  color: #e2e8f0;
}

.tier-list-content {
  display: flex;
  gap: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.tier-list-left {
  flex: 1;
  min-width: 0;
}

.tier-list-right {
  width: 320px;
  flex-shrink: 0;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
  color: #fff;
}

.tier-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tier-row {
  display: flex;
  align-items: stretch;
  background: rgba(20, 20, 35, 0.9);
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

.tier-label {
  width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 800;
  color: #000;
  flex-shrink: 0;
}

.tier-items {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  min-height: 80px;
  align-content: flex-start;
}

.tier-items.drag-over {
  background: rgba(102, 126, 234, 0.2);
}

.character-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s ease;
  min-width: 70px;
}

.character-item:hover {
  background: rgba(102, 126, 234, 0.3);
  transform: translateY(-2px);
}

.character-item:active {
  cursor: grabbing;
}

.character-image {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.character-placeholder {
  width: 50px;
  height: 50px;
  border-radius: 50%;
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

.remove-tier-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.8);
  border: none;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.tier-row:hover .remove-tier-btn {
  opacity: 1;
}

.remove-tier-btn:hover {
  background: rgba(239, 68, 68, 1);
}

.tier-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.character-pool {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  max-height: calc(100vh - 250px);
  overflow-y: auto;
  padding: 4px;
}

.pool-character {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  cursor: grab;
  transition: all 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.pool-character:hover {
  background: rgba(102, 126, 234, 0.3);
  transform: translateY(-4px);
  border-color: rgba(102, 126, 234, 0.5);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.pool-character:active {
  cursor: grabbing;
}

.pool-character .character-image,
.pool-character .character-placeholder {
  width: 60px;
  height: 60px;
}

.pool-character .character-name {
  font-size: 12px;
  max-width: 80px;
}

.character-pool::-webkit-scrollbar {
  width: 6px;
}

.character-pool::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.character-pool::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.5);
  border-radius: 3px;
}

.character-pool::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.7);
}
</style>
