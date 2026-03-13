<template>
  <div class="login-container">
    <div class="particles" id="particles"></div>
    <div class="scanlines"></div>
    
    <div class="login-wrapper">
      <div class="glitch-container">
        <h1 class="glitch" data-text="鸣潮计算器">鸣潮计算器</h1>
      </div>
      
      <div class="login-card">
        <div class="card-header">
          <div class="header-line"></div>
          <h2 class="card-title">
            <span class="title-prefix">⚡</span>
            用户登录
            <span class="title-suffix">⚡</span>
          </h2>
          <div class="header-line"></div>
        </div>
        
        <el-form :model="loginForm" :rules="rules" ref="loginFormRef" class="login-form">
          <div class="form-item-wrapper">
            <el-form-item prop="username">
              <div class="input-wrapper">
                <span class="input-prefix">USER:</span>
                <el-input 
                  v-model="loginForm.username" 
                  placeholder="输入用户名"
                  class="cyber-input"
                  @keyup.enter="handleLogin"
                />
                <span class="input-cursor"></span>
              </div>
            </el-form-item>
          </div>
          
          <div class="form-item-wrapper">
            <el-form-item prop="password">
              <div class="input-wrapper">
                <span class="input-prefix">PASS:</span>
                <el-input 
                  v-model="loginForm.password" 
                  type="password" 
                  placeholder="输入密码"
                  show-password
                  class="cyber-input"
                  @keyup.enter="handleLogin"
                />
                <span class="input-cursor"></span>
              </div>
            </el-form-item>
          </div>
          
          <el-form-item>
            <el-button 
              type="primary" 
              @click="handleLogin" 
              :loading="loading" 
              class="cyber-button"
            >
              <span class="button-text">
                <span v-if="!loading">连接服务器</span>
                <span v-else>正在连接...</span>
              </span>
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="card-footer">
          <div class="status-bar">
            <span class="status-dot"></span>
            <span class="status-text">系统状态: 正常运行</span>
          </div>
          <p class="hint-text">首次登录自动创建账号</p>
        </div>
      </div>
      
      <div class="deco-lines">
        <div class="deco-line line-1"></div>
        <div class="deco-line line-2"></div>
        <div class="deco-line line-3"></div>
        <div class="deco-line line-4"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)
let animationFrameId: number

const loginForm = reactive({
  username: '',
  password: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 1, max: 50, message: '用户名长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 1, message: '请输入密码', trigger: 'blur' }
  ]
}

function createParticles() {
  const container = document.getElementById('particles')
  if (!container) return
  
  for (let i = 0; i < 50; i++) {
    const particle = document.createElement('div')
    particle.className = 'particle'
    particle.style.left = Math.random() * 100 + '%'
    particle.style.top = Math.random() * 100 + '%'
    particle.style.animationDelay = Math.random() * 5 + 's'
    particle.style.animationDuration = (3 + Math.random() * 4) + 's'
    container.appendChild(particle)
  }
}

onMounted(() => {
  createParticles()
})

onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
})

async function handleLogin() {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const success = await userStore.login(loginForm.username, loginForm.password)
        if (success) {
          ElMessage.success('连接成功！')
          const redirect = (route.query.redirect as string) || '/'
          router.push(redirect)
        }
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  position: relative;
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f1a 100%);
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #00ffff;
  border-radius: 50%;
  box-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff;
  animation: float 5s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) translateX(0);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  50% {
    transform: translateY(-100px) translateX(50px);
  }
}

.scanlines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.15),
    rgba(0, 0, 0, 0.15) 1px,
    transparent 1px,
    transparent 2px
  );
  pointer-events: none;
  z-index: 2;
  animation: scan 0.1s linear infinite;
}

@keyframes scan {
  0% {
    transform: translateY(0);
  }
  100% {
    transform: translateY(4px);
  }
}

.login-wrapper {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.glitch-container {
  margin-bottom: 40px;
}

.glitch {
  position: relative;
  font-size: 48px;
  font-weight: bold;
  color: #00ffff;
  text-transform: uppercase;
  letter-spacing: 4px;
  text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 40px #00ffff;
  animation: glitch 2s infinite;
}

.glitch::before,
.glitch::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.glitch::before {
  color: #ff00ff;
  animation: glitch-1 0.5s infinite;
  clip-path: polygon(0 0, 100% 0, 100% 45%, 0 45%);
  transform: translate(-2px);
}

.glitch::after {
  color: #00ff00;
  animation: glitch-2 0.5s infinite;
  clip-path: polygon(0 55%, 100% 55%, 100% 100%, 0 100%);
  transform: translate(2px);
}

@keyframes glitch {
  0%, 100% {
    text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 40px #00ffff;
  }
  25% {
    text-shadow: 0 0 10px #ff00ff, 0 0 20px #ff00ff, 0 0 40px #ff00ff;
  }
  50% {
    text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00, 0 0 40px #00ff00;
  }
  75% {
    text-shadow: 0 0 10px #ffff00, 0 0 20px #ffff00, 0 0 40px #ffff00;
  }
}

@keyframes glitch-1 {
  0%, 100% {
    transform: translate(0);
  }
  20% {
    transform: translate(-3px, 3px);
  }
  40% {
    transform: translate(-3px, -3px);
  }
  60% {
    transform: translate(3px, 3px);
  }
  80% {
    transform: translate(3px, -3px);
  }
}

@keyframes glitch-2 {
  0%, 100% {
    transform: translate(0);
  }
  20% {
    transform: translate(3px, -3px);
  }
  40% {
    transform: translate(3px, 3px);
  }
  60% {
    transform: translate(-3px, -3px);
  }
  80% {
    transform: translate(-3px, 3px);
  }
}

.login-card {
  position: relative;
  width: 420px;
  padding: 40px;
  background: rgba(10, 10, 20, 0.9);
  border: 2px solid #00ffff;
  border-radius: 0;
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.3), inset 0 0 20px rgba(0, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.card-header {
  text-align: center;
  margin-bottom: 40px;
}

.header-line {
  height: 2px;
  background: linear-gradient(90deg, transparent, #00ffff, #ff00ff, #00ffff, transparent);
  margin: 15px 0;
}

.card-title {
  font-size: 24px;
  color: #00ffff;
  text-transform: uppercase;
  letter-spacing: 3px;
  margin: 0;
  text-shadow: 0 0 10px #00ffff;
}

.title-prefix,
.title-suffix {
  color: #ff00ff;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

.login-form {
  margin-bottom: 20px;
}

.form-item-wrapper {
  margin-bottom: 25px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid #00ffff;
  padding: 5px 15px;
  transition: all 0.3s;
}

.input-wrapper:hover,
.input-wrapper:focus-within {
  border-color: #ff00ff;
  box-shadow: 0 0 15px rgba(255, 0, 255, 0.3);
  background: rgba(255, 0, 255, 0.05);
}

.input-prefix {
  font-family: 'Courier New', monospace;
  color: #00ffff;
  font-size: 14px;
  margin-right: 10px;
  text-shadow: 0 0 5px #00ffff;
}

.cyber-input {
  flex: 1;
  background: transparent !important;
  border: none !important;
  color: #fff !important;
  font-family: 'Courier New', monospace;
  font-size: 16px;
}

.cyber-input :deep(.el-input__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  padding: 0;
}

.cyber-input :deep(.el-input__inner) {
  color: #fff !important;
}

.input-cursor {
  width: 10px;
  height: 20px;
  background: #00ffff;
  animation: cursor-blink 0.8s infinite;
  margin-left: 5px;
}

@keyframes cursor-blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

.cyber-button {
  width: 100%;
  height: 50px;
  background: linear-gradient(90deg, #00ffff, #ff00ff);
  border: none;
  font-size: 16px;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 2px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.cyber-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.cyber-button:hover::before {
  left: 100%;
}

.cyber-button:hover {
  transform: scale(1.02);
  box-shadow: 0 0 30px rgba(0, 255, 255, 0.5), 0 0 60px rgba(255, 0, 255, 0.3);
}

.button-text {
  position: relative;
  z-index: 1;
  color: #0a0a0f;
}

.card-footer {
  text-align: center;
}

.status-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 15px;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #00ff00;
  border-radius: 50%;
  box-shadow: 0 0 10px #00ff00;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

.status-text {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #00ff00;
}

.hint-text {
  font-size: 12px;
  color: #666;
  margin: 0;
  font-family: 'Courier New', monospace;
}

.deco-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.deco-line {
  position: absolute;
  background: linear-gradient(90deg, transparent, #00ffff, transparent);
}

.line-1 {
  top: 20px;
  left: -50px;
  width: 100px;
  height: 2px;
  animation: line-move-1 3s infinite;
}

.line-2 {
  bottom: 20px;
  right: -50px;
  width: 100px;
  height: 2px;
  animation: line-move-2 3s infinite;
}

.line-3 {
  top: 50%;
  left: -50px;
  width: 2px;
  height: 100px;
  animation: line-move-3 4s infinite;
}

.line-4 {
  top: 50%;
  right: -50px;
  width: 2px;
  height: 100px;
  animation: line-move-4 4s infinite;
}

@keyframes line-move-1 {
  0%, 100% {
    transform: translateX(0);
    opacity: 0;
  }
  50% {
    transform: translateX(100px);
    opacity: 1;
  }
}

@keyframes line-move-2 {
  0%, 100% {
    transform: translateX(0);
    opacity: 0;
  }
  50% {
    transform: translateX(-100px);
    opacity: 1;
  }
}

@keyframes line-move-3 {
  0%, 100% {
    transform: translateY(0);
    opacity: 0;
  }
  50% {
    transform: translateY(50px);
    opacity: 1;
  }
}

@keyframes line-move-4 {
  0%, 100% {
    transform: translateY(0);
    opacity: 0;
  }
  50% {
    transform: translateY(-50px);
    opacity: 1;
  }
}
</style>
