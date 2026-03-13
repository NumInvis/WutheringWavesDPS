<template>
  <div class="page-container">
    <div class="page-header">
      <h3>伤害计算器</h3>
      <p>配置角色面板，计算DPS</p>
    </div>
    
    <el-row :gutter="20">
      <!-- 左侧面板配置 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>角色面板</span>
            </div>
          </template>
          
          <el-form :model="panel" label-position="top" size="small">
            <el-divider>基础属性</el-divider>
            <el-form-item label="角色">
              <el-select v-model="panel.character_id" placeholder="选择角色" style="width: 100%">
                <el-option
                  v-for="char in characters"
                  :key="char.id"
                  :label="char.name"
                  :value="char.id"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="等级">
              <el-slider v-model="panel.level" :max="90" show-input />
            </el-form-item>
            
            <el-form-item label="共鸣链">
              <el-rate v-model="panel.chain_level" :max="6" />
            </el-form-item>
            
            <el-divider>武器配置</el-divider>
            <el-form-item label="武器">
              <el-input v-model="panel.weapon_name" placeholder="武器名称" />
            </el-form-item>
            <el-form-item label="武器等级">
              <el-slider v-model="panel.weapon_level" :max="90" show-input />
            </el-form-item>
            
            <el-divider>面板数值</el-divider>
            <el-form-item label="基础白值">
              <el-input-number v-model="panel.base_atk" :min="0" style="width: 100%" />
            </el-form-item>
            <el-form-item label="攻击百分比%">
              <el-input-number v-model="panel.atk_pct" :min="0" style="width: 100%" />
            </el-form-item>
            <el-form-item label="暴击率%">
              <el-input-number v-model="panel.crit_rate" :min="0" :max="100" style="width: 100%" />
            </el-form-item>
            <el-form-item label="暴击伤害%">
              <el-input-number v-model="panel.crit_dmg" :min="0" style="width: 100%" />
            </el-form-item>
            <el-form-item label="属伤加成%">
              <el-input-number v-model="panel.element_bonus" :min="0" style="width: 100%" />
            </el-form-item>
            
            <el-divider>技能加成</el-divider>
            <el-form-item label="普攻加成%">
              <el-input-number v-model="panel.normal_bonus" :min="0" style="width: 100%" />
            </el-form-item>
            <el-form-item label="重击加成%">
              <el-input-number v-model="panel.heavy_bonus" :min="0" style="width: 100%" />
            </el-form-item>
            <el-form-item label="技能加成%">
              <el-input-number v-model="panel.skill_bonus" :min="0" style="width: 100%" />
            </el-form-item>
            <el-form-item label="解放加成%">
              <el-input-number v-model="panel.ult_bonus" :min="0" style="width: 100%" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 右侧动作队列 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>动作队列</span>
              <div>
                <el-button type="primary" size="small" @click="addAction">
                  <el-icon><Plus /></el-icon> 添加动作
                </el-button>
                <el-button size="small" @click="clearActions">清空</el-button>
              </div>
            </div>
          </template>
          
          <!-- 动作列表 -->
          <el-table :data="actionQueue" stripe>
            <el-table-column type="index" width="50" />
            <el-table-column label="动作" min-width="150">
              <template #default="{ row, $index }">
                <el-select v-model="row.action_id" placeholder="选择动作" @change="updateAction($index)">
                  <el-option-group
                    v-for="group in actionGroups"
                    :key="group.label"
                    :label="group.label"
                  >
                    <el-option
                      v-for="action in group.actions"
                      :key="action.id"
                      :label="action.action_name"
                      :value="action.id"
                    />
                  </el-option-group>
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="倍率%" width="100">
              <template #default="{ row }">
                <el-input-number v-model="row.multiplier" :min="0" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="次数" width="80">
              <template #default="{ row }">
                <el-input-number v-model="row.count" :min="1" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="伤害" width="120">
              <template #default="{ row }">
                <span class="damage-value">{{ formatNumber(row.damage) }}</span>
              </template>
            </el-table-column>
            <el-table-column width="80">
              <template #default="{ $index }">
                <el-button type="danger" link @click="removeAction($index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 统计结果 -->
          <el-divider />
          <div class="calc-result">
            <el-row :gutter="20">
              <el-col :span="8">
                <div class="result-item">
                  <span class="result-label">总伤害</span>
                  <span class="result-value">{{ formatNumber(totalDamage) }}</span>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="result-item">
                  <span class="result-label">战斗时长</span>
                  <el-input-number v-model="battleTime" :min="1" :max="300" size="small" />
                  <span>秒</span>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="result-item">
                  <span class="result-label">DPS</span>
                  <span class="result-value highlight">{{ formatNumber(dps) }}</span>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

export default {
  name: 'Calculator',
  setup() {
    const characters = ref([])
    const actions = ref([])
    const actionQueue = ref([])
    const battleTime = ref(25)
    
    const panel = ref({
      character_id: null,
      level: 90,
      chain_level: 0,
      weapon_name: '',
      weapon_level: 90,
      base_atk: 1000,
      atk_pct: 50,
      crit_rate: 50,
      crit_dmg: 150,
      element_bonus: 60,
      normal_bonus: 0,
      heavy_bonus: 0,
      skill_bonus: 0,
      ult_bonus: 0
    })
    
    // 按类型分组的动作
    const actionGroups = computed(() => {
      const groups = {}
      actions.value.forEach(action => {
        const type = action.action_type || '其他'
        if (!groups[type]) {
          groups[type] = []
        }
        groups[type].push(action)
      })
      return Object.entries(groups).map(([label, actions]) => ({ label, actions }))
    })
    
    // 计算面板攻击
    const panelAtk = computed(() => {
      return panel.value.base_atk * (1 + panel.value.atk_pct / 100)
    })
    
    // 计算双爆区
    const critZone = computed(() => {
      const rate = Math.min(panel.value.crit_rate / 100, 1)
      const dmg = panel.value.crit_dmg / 100
      return 1 + rate * dmg
    })
    
    // 计算总伤害
    const totalDamage = computed(() => {
      return actionQueue.value.reduce((sum, item) => sum + (item.damage * item.count), 0)
    })
    
    // 计算DPS
    const dps = computed(() => {
      return battleTime.value > 0 ? totalDamage.value / battleTime.value : 0
    })
    
    onMounted(() => {
      fetchCharacters()
    })
    
    // 监听角色选择变化
    watch(() => panel.value.character_id, (newId) => {
      if (newId) {
        fetchCharacterActions(newId)
      }
    })
    
    const fetchCharacters = async () => {
      try {
        const response = await axios.get('/api/characters')
        if (response.data.success) {
          characters.value = response.data.data
        }
      } catch (error) {
        console.error('获取角色列表失败:', error)
      }
    }
    
    const fetchCharacterActions = async (charId) => {
      try {
        const response = await axios.get(`/api/characters/${charId}/actions`, {
          params: { per_page: 1000 }
        })
        if (response.data.success) {
          actions.value = response.data.data
        }
      } catch (error) {
        console.error('获取动作列表失败:', error)
      }
    }
    
    const addAction = () => {
      actionQueue.value.push({
        action_id: null,
        action_name: '',
        multiplier: 100,
        count: 1,
        damage: 0
      })
    }
    
    const removeAction = (index) => {
      actionQueue.value.splice(index, 1)
    }
    
    const clearActions = () => {
      actionQueue.value = []
    }
    
    const updateAction = (index) => {
      const item = actionQueue.value[index]
      const action = actions.value.find(a => a.id === item.action_id)
      if (action) {
        item.action_name = action.action_name
        item.action_type = action.action_type
        calculateDamage(item)
      }
    }
    
    const calculateDamage = (item) => {
      // 基础伤害公式：面板攻击 × 倍率 × 攻击区 × 加成区 × 双爆区 × 防御区 × 抗性区
      const baseDmg = panelAtk.value * (item.multiplier / 100)
      
      // 加成区
      let bonusZone = 1 + panel.value.element_bonus / 100
      if (item.action_type === '常态攻击') {
        bonusZone += panel.value.normal_bonus / 100
      } else if (item.action_type === '共鸣技能') {
        bonusZone += panel.value.skill_bonus / 100
      } else if (item.action_type === '共鸣解放') {
        bonusZone += panel.value.ult_bonus / 100
      }
      
      // 防御区（假设怪物等级90，无减防）
      const defenseZone = 1520 / (1520 + (792 + 8 * 90))
      
      // 抗性区（假设20%抗性）
      const resistanceZone = 0.8
      
      item.damage = baseDmg * bonusZone * critZone.value * defenseZone * resistanceZone
    }
    
    // 监听队列变化，重新计算
    watch(actionQueue, () => {
      actionQueue.value.forEach(item => {
        if (item.action_id) {
          calculateDamage(item)
        }
      })
    }, { deep: true })
    
    const formatNumber = (num) => {
      if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万'
      }
      return Math.round(num).toLocaleString()
    }
    
    return {
      characters,
      actions,
      actionQueue,
      actionGroups,
      panel,
      battleTime,
      totalDamage,
      dps,
      addAction,
      removeAction,
      clearActions,
      updateAction,
      formatNumber
    }
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.damage-value {
  color: #f56c6c;
  font-weight: bold;
}

.calc-result {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.result-item {
  text-align: center;
}

.result-label {
  display: block;
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.result-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.result-value.highlight {
  color: #67c23a;
}
</style>
