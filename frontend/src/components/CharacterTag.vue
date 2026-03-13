<template>
  <el-tag 
    :type="tagType" 
    :size="size"
    :effect="effect"
    class="character-tag"
  >
    <slot></slot>
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { WUWA_CHARACTERS } from '../data/characters'

interface Props {
  characterId?: string
  element?: string
  size?: 'large' | 'default' | 'small'
  effect?: 'dark' | 'light' | 'plain'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'small',
  effect: 'dark'
})

const tagType = computed(() => {
  if (props.characterId) {
    const char = WUWA_CHARACTERS.find(c => c.id === props.characterId)
    if (char) {
      return getElementTagType(char.element)
    }
  }
  if (props.element) {
    return getElementTagType(props.element)
  }
  return 'info'
})

function getElementTagType(element: string): any {
  const typeMap: Record<string, any> = {
    '光': 'warning',
    '暗': 'info',
    '火': 'danger',
    '水': 'primary',
    '风': 'success',
    '土': ''
  }
  return typeMap[element] || 'info'
}
</script>

<style scoped>
.character-tag {
  font-weight: 500;
}
</style>
