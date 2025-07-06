<template>
  <div class="login-transition">
    <div class="whisper-container">
      <h1 class="whisper-text" :class="{ 'show': showText, 'hide': fadeOut }">
        Whisper
      </h1>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showText = ref(false)
const fadeOut = ref(false)

onMounted(() => {
  console.log('LoginTransition 组件已挂载')
  
  // 延迟显示文字
  setTimeout(() => {
    console.log('开始显示文字动画')
    showText.value = true
  }, 500)
  
  // 3秒后开始淡出
  setTimeout(() => {
    console.log('开始淡出动画')
    fadeOut.value = true
  }, 3500)
  
  // 4.5秒后跳转到聊天页面
  setTimeout(() => {
    console.log('跳转到聊天页面')
    router.push('/chat')
  }, 4500)
})
</script>

<style scoped>
.login-transition {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, 
    #667eea 0%, 
    #764ba2 25%, 
    #f093fb 50%, 
    #f5576c 75%, 
    #4facfe 100%);
  background-size: 400% 400%;
  animation: gradientShift 8s ease infinite;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

@keyframes gradientShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.whisper-container {
  text-align: center;
}

.whisper-text {
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: 8rem;
  font-weight: bold;
  font-style: italic;
  background: linear-gradient(45deg, 
    #ff6b6b, 
    #4ecdc4, 
    #45b7d1, 
    #96ceb4, 
    #ffeaa7, 
    #dda0dd, 
    #98d8c8);
  background-size: 400% 400%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  animation: textGradient 3s ease-in-out infinite;
  text-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
  opacity: 0;
  transform: scale(0.3) translateY(100px) rotate(-10deg);
  transition: all 2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  letter-spacing: 0.1em;
}

@keyframes textGradient {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.whisper-text.show {
  opacity: 1;
  transform: scale(1) translateY(0) rotate(0deg);
}

.whisper-text.hide {
  opacity: 0;
  transform: scale(1.3) translateY(-50px) rotate(5deg);
  transition: all 1.5s ease-in;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .whisper-text {
    font-size: 4rem;
  }
}

@media (max-width: 480px) {
  .whisper-text {
    font-size: 3rem;
  }
}
</style>