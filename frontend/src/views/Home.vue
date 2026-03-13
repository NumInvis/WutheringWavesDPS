<template>
  <div class="home">
    <div class="hero-section">
      <h1 class="hero-title">鸣潮拉表开源社区</h1>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="startCalculate">
          开始计算
        </el-button>
        <el-button size="large" @click="$router.push('/community')">
          浏览社区
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function startCalculate() {
  router.push('/calculator?loadTemplate=true')
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.hero-section {
  text-align: center;
  padding: 120px 20px;
}

.hero-title {
  font-size: 48px;
  font-weight: 600;
  margin: 0 0 40px 0;
  color: #fff;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}
</style>
