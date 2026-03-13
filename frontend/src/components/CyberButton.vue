<template>
  <el-button 
    :type="btnType" 
    :size="size"
    :loading="loading"
    :disabled="disabled"
    :class="['cyber-button', `cyber-button-${variant}`]"
    @click="$emit('click', $event)"
  >
    <slot></slot>
  </el-button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'outline' | 'ghost' | 'danger'
  size?: 'large' | 'default' | 'small'
  loading?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'default',
  loading: false,
  disabled: false
})

const emit = defineEmits<{
  (e: 'click', event: Event): void
}>()

const btnType = computed(() => {
  if (props.variant === 'danger') return 'danger'
  if (props.variant === 'primary') return 'primary'
  return 'default'
})
</script>

<style scoped>
.cyber-button {
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.cyber-button-primary {
  background: linear-gradient(
    135deg,
    var(--primary-color) 0%,
    var(--secondary-color) 100%
  );
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
}

.cyber-button-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 212, 255, 0.4);
}

.cyber-button-outline {
  background: transparent;
  border: 2px solid rgba(255, 255, 255, 0.2);
  color: var(--text-primary);
}

.cyber-button-outline:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: rgba(0, 212, 255, 0.05);
}

.cyber-button-ghost {
  background: transparent;
  border: none;
  color: var(--text-secondary);
}

.cyber-button-ghost:hover {
  color: var(--primary-color);
  background: rgba(0, 212, 255, 0.05);
}

.cyber-button-danger {
  background: linear-gradient(
    135deg,
    var(--danger-color) 0%,
    #ff6b6b 100%
  );
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(255, 68, 68, 0.3);
}

.cyber-button-danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(255, 68, 68, 0.4);
}
</style>
