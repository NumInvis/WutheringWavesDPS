<template>
  <div class="calculator">
    <h1>测试页面</h1>
    <div id="luckysheet" style="width: 100%; height: 600px; border: 2px solid red;"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  console.log('onMounted')
  
  // 直接初始化，不等待
  setTimeout(() => {
    const luckysheet = (window as any).luckysheet
    console.log('luckysheet:', typeof luckysheet)
    console.log('luckysheet.create:', typeof luckysheet?.create)
    
    if (luckysheet?.create) {
      const container = document.getElementById('luckysheet')
      console.log('container:', container)
      console.log('container size:', container?.getBoundingClientRect())
      
      try {
        luckysheet.create({
          container: 'luckysheet',
          title: '测试',
          lang: 'zh',
          data: [{
            name: 'Sheet1',
            status: 1,
            order: 0,
            celldata: [
              { r: 0, c: 0, v: { v: 'Hello' } },
              { r: 0, c: 1, v: { v: 'World' } }
            ],
            row: 10,
            column: 10
          }]
        })
        console.log('Success!')
      } catch (e) {
        console.error('Error:', e)
      }
    }
  }, 500)
})
</script>

<style scoped>
.calculator {
  padding: 20px;
}
</style>
