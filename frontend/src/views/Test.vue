<template>
  <div style="padding: 20px;">
    <h1>测试页面</h1>
    <p> Luckysheet 测试</p>
    <div id="luckysheet" style="width: 100%; height: 400px; border: 2px solid red;"></div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  console.log('Test page mounted')
  
  setTimeout(() => {
    const luckysheet = window.luckysheet
    console.log('luckysheet:', typeof luckysheet)
    console.log('create:', typeof luckysheet?.create)
    
    if (luckysheet?.create) {
      luckysheet.create({
        container: 'luckysheet',
        title: 'Test',
        data: [{
          name: 'Sheet1',
          status: 1,
          celldata: [{r: 0, c: 0, v: {v: 'Hello'}}]
        }]
      })
      console.log('Created!')
    }
  }, 500)
})
</script>
