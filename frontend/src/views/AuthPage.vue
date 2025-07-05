<template>
  <div class="auth-page">
    <div class="background-shapes">
      <div class="shape shape1"></div>
      <div class="shape shape2"></div>
      <div class="shape shape3"></div>
      <div class="shape shape4"></div>
      <div class="shape shape5"></div>
      <div class="shape shape6"></div>
    </div>
    
    <div class="auth-container">
      <!-- 左侧特性面板 -->
      <div class="features-panel">
        <div class="app-branding">
          <h1 class="app-title">Whisper</h1>
          <p class="app-subtitle">安全 &middot; 混合 &middot; 智能</p>
        </div>
        
        <div class="feature-list">
          <div class="feature-item" v-for="(feature, index) in features" :key="index">
            <span class="feature-icon">{{ feature.icon }}</span>
            <div class="feature-content">
              <strong>{{ feature.title }}</strong>
              <p>{{ feature.description }}</p>
            </div>
          </div>
        </div>
        
        <!-- 幽默提示语 -->
        <div class="humor-tip">
          <p>{{ currentTip }}</p>
        </div>
      </div>
      
      <!-- 右侧表单区域 -->
      <div class="form-panel">
        <div class="form-slider" :class="{ 'show-register': showRegister }">
          <!-- 登录表单 -->
          <div class="form-container login-form">
            <div class="form-header">
              <h2>{{ loginMessages.title }}</h2>
              <p class="form-subtitle">{{ loginMessages.subtitle }}</p>
            </div>
            
            <form @submit.prevent="handleLogin">
              <div class="form-group">
                <input
                  id="login-username"
                  v-model="loginForm.username"
                  type="text"
                  placeholder=" "
                  required
                  class="form-input"
                />
                <label for="login-username">用户名</label>
              </div>

              <div class="form-group">
                <input
                  id="login-password"
                  v-model="loginForm.password"
                  type="password"
                  placeholder=" "
                  required
                  class="form-input"
                />
                <label for="login-password">密码</label>
              </div>

              <div class="form-options">
                <label class="checkbox-label">
                  <input
                    v-model="loginForm.rememberMe"
                    type="checkbox"
                    class="checkbox"
                  />
                  <span>记住我</span>
                </label>
                <button type="button" @click="showForgotPasswordForm" class="forgot-password-link">
                  忘记密码？
                </button>
              </div>

              <button
                type="submit"
                :disabled="isLoading"
                class="auth-btn login-btn"
              >
                <span v-if="!isLoading">{{ loginMessages.button }}</span>
                <div v-else class="loading-spinner"></div>
              </button>

              <div v-if="errorMessage" class="error-message">
                {{ errorMessage }}
              </div>
            </form>

            <div class="form-footer">
              <p>{{ loginMessages.footer }} 
                <button @click="switchToRegister" class="switch-link">
                  {{ loginMessages.switchText }}
                </button>
              </p>
            </div>
          </div>
          
          <!-- 注册表单 -->
          <div class="form-container register-form">
            <div class="form-header">
              <h2>{{ registerMessages.title }}</h2>
              <p class="form-subtitle">{{ registerMessages.subtitle }}</p>
            </div>
            
            <form @submit.prevent="handleRegister">
              <div class="form-group">
                <input
                  id="register-username"
                  v-model="registerForm.username"
                  type="text"
                  placeholder=" "
                  required
                  class="form-input"
                />
                <label for="register-username">用户名</label>
              </div>

              <div class="form-group">
                <input
                  id="register-email"
                  v-model="registerForm.email"
                  type="email"
                  placeholder=" "
                  required
                  class="form-input"
                />
                <label for="register-email">邮箱</label>
              </div>

              <div class="form-group">
                <input
                  id="register-password"
                  v-model="registerForm.password"
                  type="password"
                  placeholder=" "
                  required
                  class="form-input"
                />
                <label for="register-password">密码</label>
              </div>

              <div class="form-group">
                <input
                  id="register-confirm-password"
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder=" "
                  required
                  class="form-input"
                />
                <label for="register-confirm-password">确认密码</label>
              </div>

              <div class="form-options">
                <label class="checkbox-label">
                  <input
                    v-model="registerForm.acceptTerms"
                    type="checkbox"
                    class="checkbox"
                    required
                  />
                  <span>我同意服务条款和隐私政策</span>
                </label>
              </div>

              <button
                type="submit"
                :disabled="isLoading || !canRegister"
                class="auth-btn register-btn"
              >
                <span v-if="!isLoading">{{ registerMessages.button }}</span>
                <div v-else class="loading-spinner"></div>
              </button>

              <div v-if="errorMessage" class="error-message">
                {{ errorMessage }}
              </div>
            </form>

            <div class="form-footer">
              <p>{{ registerMessages.footer }} 
                <button @click="switchToLogin" class="switch-link">
                  {{ registerMessages.switchText }}
                </button>
              </p>
            </div>
          </div>
          
          <!-- 忘记密码表单 -->
          <div v-if="showForgotPassword" class="forgot-password-overlay">
            <div class="forgot-password-form">
              <h3>{{ forgotPasswordStep === 'email' ? '重置密码' : forgotPasswordStep === 'verify' ? '验证邮箱' : '设置新密码' }}</h3>
              
              <!-- 步骤1: 输入邮箱 -->
              <form v-if="forgotPasswordStep === 'email'" @submit.prevent="sendResetCode" class="form">
                <div class="form-group">
                  <input 
                    v-model="resetEmail" 
                    type="email"
                    placeholder="请输入注册邮箱"
                    required 
                    class="form-input"
                    id="resetEmail"
                  />
                  <label for="resetEmail">邮箱地址</label>
                </div>
                <button type="submit" class="auth-btn" :disabled="isLoading">
                  {{ isLoading ? '发送中...' : '发送验证码' }}
                </button>
              </form>
              
              <!-- 步骤2: 验证验证码 -->
              <form v-if="forgotPasswordStep === 'verify'" @submit.prevent="verifyResetCode" class="form">
                <div class="form-group">
                  <input 
                    v-model="verificationCode" 
                    placeholder="请输入6位验证码"
                    required 
                    maxlength="6"
                    class="form-input"
                    id="verificationCode"
                  />
                  <label for="verificationCode">验证码</label>
                </div>
                <button type="submit" class="auth-btn" :disabled="isLoading">
                  {{ isLoading ? '验证中...' : '验证验证码' }}
                </button>
                <div class="resend-code">
                  <span v-if="countdown > 0">{{ countdown }}秒后可重新发送</span>
                  <button v-else @click="sendResetCode" type="button" class="resend-btn">
                    重新发送验证码
                  </button>
                </div>
              </form>
              
              <!-- 步骤3: 设置新密码 -->
              <form v-if="forgotPasswordStep === 'reset'" @submit.prevent="resetPassword" class="form">
                <div class="form-group">
                  <input 
                    v-model="newPassword" 
                    type="password"
                    placeholder="请输入新密码"
                    required 
                    class="form-input"
                    id="newPassword"
                  />
                  <label for="newPassword">新密码</label>
                </div>
                <div class="form-group">
                  <input 
                    v-model="confirmPassword" 
                    type="password"
                    placeholder="确认新密码"
                    required 
                    class="form-input"
                    id="confirmPassword"
                  />
                  <label for="confirmPassword">确认密码</label>
                </div>
                <button type="submit" class="auth-btn" :disabled="isLoading">
                  {{ isLoading ? '重置中...' : '重置密码' }}
                </button>
              </form>
              
              <div v-if="errorMessage" class="error-message">
                {{ errorMessage }}
              </div>
              <div v-if="successMessage" class="success-message">
                {{ successMessage }}
              </div>
              
              <button @click="backToLogin" class="back-btn">
                返回登录
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { hybridStore } from '../store/hybrid-store'
import { authAPI } from '../api/hybrid-api'
import api from '../api/hybrid-api'
import { initializeUserEncryption } from '../utils/encryption-keys'
import { storeUserKeys } from '../client_db/database'

const router = useRouter()
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const showRegister = ref(false)
const currentTip = ref('')

// 忘记密码相关状态
const showForgotPassword = ref(false)
const forgotPasswordStep = ref('email') // 'email', 'verify', 'reset'
const resetEmail = ref('')
const verificationCode = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const countdown = ref(0)
let countdownTimer = null

// 表单数据
const loginForm = reactive({
  username: '',
  password: '',
  rememberMe: false
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false
})

// 特性列表
const features = [
  {
    icon: '🔗',
    title: 'P2P直连',
    description: '在线用户之间直接通信，低延迟高隐私'
  },
  {
    icon: '📡',
    title: '服务器转发',
    description: '离线用户消息存储转发，确保送达'
  },
  {
    icon: '⚡',
    title: '智能切换',
    description: '根据网络状况自动选择最优传输方式'
  },
  {
    icon: '🔒',
    title: '端到端加密',
    description: '消息全程加密保护，保障通信安全'
  }
]

// 幽默提示语
const humorTips = [
  '🤫 在这里，你的秘密比CEO的年终奖还安全',
  '🕵️ 我们的加密技术连FBI都要点赞',
  '🎭 匿名聊天？我们比面具还靠谱',
  '🔐 密码忘了？别担心，我们比你妈还关心你',
  '🚀 传输速度快到让光都嫉妒',
  '🎪 欢迎来到数字马戏团，这里只有安全没有小丑',
  '🌟 你的隐私，我们的使命（听起来很官方对吧？）'
]

// 动态消息
const loginMessages = reactive({
  title: '欢迎回来！',
  subtitle: '准备好继续你的秘密任务了吗？',
  button: '开始潜入',
  footer: '还没有通行证？',
  switchText: '立即申请特工身份'
})

const registerMessages = reactive({
  title: '加入我们！',
  subtitle: '成为数字世界的秘密特工',
  button: '申请特工证',
  footer: '已经是特工了？',
  switchText: '直接潜入基地'
})

// 计算属性
const canRegister = computed(() => {
  return registerForm.username &&
         registerForm.email &&
         registerForm.password &&
         registerForm.confirmPassword &&
         registerForm.password === registerForm.confirmPassword &&
         registerForm.acceptTerms
})

// 方法
function switchToRegister() {
  showRegister.value = true
  errorMessage.value = ''
  updateMessages('register')
  updateTip()
}

function switchToLogin() {
  showRegister.value = false
  errorMessage.value = ''
  updateMessages('login')
  updateTip()
}

function updateMessages(mode) {
  if (mode === 'register') {
    loginMessages.title = '再见了！'
    loginMessages.subtitle = '希望你在新世界找到归属'
  } else {
    registerMessages.title = '回来了！'
    registerMessages.subtitle = '基地一直为你保留位置'
  }
}

function updateTip() {
  const randomIndex = Math.floor(Math.random() * humorTips.length)
  currentTip.value = humorTips[randomIndex]
}

async function handleLogin() {
  if (isLoading.value) return
  
  if (!loginForm.username || !loginForm.password) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await authAPI.login({
      username: loginForm.username,
      password: loginForm.password
    })

    await hybridStore.setUser(response.data.data.user, response.data.data.token)
    
    console.log('登录成功，跳转到过渡页面')
    router.push('/login-transition')

  } catch (error) {
    console.error('登录失败:', error)
    
    if (error.response) {
      const status = error.response.status
      if (status === 401) {
        errorMessage.value = '用户名或密码错误，请重试'
      } else if (status === 500) {
        errorMessage.value = '服务器开小差了，请稍后重试'
      } else {
        errorMessage.value = error.response.data?.message || '登录失败，请重试'
      }
    } else {
      errorMessage.value = '网络连接失败，请检查网络'
    }
  } finally {
    isLoading.value = false
  }
}

async function handleRegister() {
  if (isLoading.value || !canRegister.value) return

  if (registerForm.password !== registerForm.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await authAPI.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password
    })

    await hybridStore.setUser(response.data.user, response.data.token)

    if (response.data.keys) {
      await storeUserKeys(response.data.keys)
    }

    console.log('注册成功，跳转到过渡页面')
    router.push('/login-transition')

  } catch (error) {
    console.error('注册失败:', error)
    
    if (error.response) {
      errorMessage.value = error.response.data?.message || '注册失败，请重试'
    } else {
      errorMessage.value = '网络连接失败，请检查网络'
    }
  } finally {
    isLoading.value = false
  }
}

// 忘记密码相关方法
function showForgotPasswordForm() {
  showForgotPassword.value = true
  forgotPasswordStep.value = 'email'
  resetForm()
}

function backToLogin() {
  showForgotPassword.value = false
  forgotPasswordStep.value = 'email'
  resetForm()
}

function resetForm() {
  resetEmail.value = ''
  verificationCode.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  errorMessage.value = ''
  successMessage.value = ''
  stopCountdown()
}

function startCountdown() {
  countdown.value = 60
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      stopCountdown()
    }
  }, 1000)
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  countdown.value = 0
}

async function sendResetCode() {
  if (!resetEmail.value) {
    errorMessage.value = '请输入邮箱地址'
    return
  }
  
  isLoading.value = true
  errorMessage.value = ''
  
  try {
    const response = await api.post('/v1/auth/forgot-password', {
      email: resetEmail.value
    })
    
    if (response.data.success) {
      errorMessage.value = ''
      forgotPasswordStep.value = 'verify'
      startCountdown()
    }
  } catch (e) {
    console.error('发送验证码失败:', e)
    if (e.response?.data?.message) {
      errorMessage.value = e.response.data.message
    } else if (e.response?.data?.detail) {
      errorMessage.value = e.response.data.detail
    } else {
      errorMessage.value = '发送验证码失败，请稍后重试'
    }
  } finally {
    isLoading.value = false
  }
}

async function verifyResetCode() {
  if (!verificationCode.value || verificationCode.value.length !== 6) {
    errorMessage.value = '请输入6位验证码'
    return
  }
  
  isLoading.value = true
  errorMessage.value = ''
  
  try {
    const response = await api.post('/v1/auth/verify-reset-code', {
      email: resetEmail.value,
      code: verificationCode.value
    })
    
    if (response.data.success) {
      errorMessage.value = ''
      forgotPasswordStep.value = 'reset'
      stopCountdown()
    }
  } catch (e) {
    console.error('验证码验证失败:', e)
    if (e.response?.data?.message) {
      errorMessage.value = e.response.data.message
    } else if (e.response?.data?.detail) {
      errorMessage.value = e.response.data.detail
    } else {
      errorMessage.value = '验证码验证失败，请重试'
    }
  } finally {
    isLoading.value = false
  }
}

async function resetPassword() {
  if (!newPassword.value || newPassword.value.length < 6) {
    errorMessage.value = '密码长度至少6位'
    return
  }
  
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }
  
  isLoading.value = true
  errorMessage.value = ''
  
  try {
    const response = await api.post('/v1/auth/reset-password', {
      email: resetEmail.value,
      code: verificationCode.value,
      new_password: newPassword.value
    })
    
    if (response.data.success) {
      errorMessage.value = ''
      successMessage.value = '密码重置成功！2秒后返回登录页面'
      setTimeout(() => {
        backToLogin()
      }, 2000)
    }
  } catch (e) {
    console.error('密码重置失败:', e)
    if (e.response?.data?.message) {
      errorMessage.value = e.response.data.message
    } else if (e.response?.data?.detail) {
      errorMessage.value = e.response.data.detail
    } else {
      errorMessage.value = '密码重置失败，请重试'
    }
  } finally {
    isLoading.value = false
  }
}

// 生命周期
onMounted(() => {
  updateTip()
  
  // 定期更换提示语
  setInterval(() => {
    updateTip()
  }, 8000)
})

// 组件卸载时清理定时器
onUnmounted(() => {
  stopCountdown()
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.background-shapes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;
}

.shape1 {
  width: 80px;
  height: 80px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape2 {
  width: 120px;
  height: 120px;
  top: 20%;
  right: 10%;
  animation-delay: 1s;
}

.shape3 {
  width: 60px;
  height: 60px;
  bottom: 30%;
  left: 20%;
  animation-delay: 2s;
}

.shape4 {
  width: 100px;
  height: 100px;
  bottom: 10%;
  right: 20%;
  animation-delay: 3s;
}

.shape5 {
  width: 40px;
  height: 40px;
  top: 50%;
  left: 5%;
  animation-delay: 4s;
}

.shape6 {
  width: 90px;
  height: 90px;
  top: 70%;
  right: 5%;
  animation-delay: 5s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

.auth-container {
  display: flex;
  max-width: 1200px;
  width: 100%;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative;
  z-index: 2;
  min-height: 600px;
}

.features-panel {
  flex: 1;
  padding: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.app-branding {
  text-align: center;
  margin-bottom: 40px;
}

.app-title {
  font-size: 3rem;
  font-weight: bold;
  margin: 0;
  background: linear-gradient(45deg, #fff, #f0f8ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.app-subtitle {
  font-size: 1.1rem;
  margin: 10px 0 0 0;
  opacity: 0.9;
}

.feature-list {
  flex: 1;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 30px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  transition: transform 0.3s ease;
}

.feature-item:hover {
  transform: translateX(10px);
}

.feature-icon {
  font-size: 2rem;
  margin-right: 15px;
  flex-shrink: 0;
}

.feature-content strong {
  display: block;
  font-size: 1.1rem;
  margin-bottom: 5px;
}

.feature-content p {
  margin: 0;
  opacity: 0.9;
  font-size: 0.9rem;
  line-height: 1.4;
}

.humor-tip {
  text-align: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  margin-top: 20px;
}

.humor-tip p {
  margin: 0;
  font-size: 1rem;
  font-style: italic;
  opacity: 0.95;
  animation: tipFade 1s ease-in;
}

@keyframes tipFade {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 0.95; transform: translateY(0); }
}

.form-panel {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.form-slider {
  display: flex;
  width: 200%;
  height: 100%;
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.form-slider.show-register {
  transform: translateX(-50%);
}

.form-container {
  width: 50%;
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.form-header {
  text-align: center;
  margin-bottom: 30px;
}

.form-header h2 {
  font-size: 2rem;
  color: #333;
  margin: 0 0 10px 0;
  transition: all 0.3s ease;
}

.form-subtitle {
  color: #666;
  margin: 0;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-group {
  position: relative;
  margin-bottom: 25px;
}

.form-input {
  width: 100%;
  padding: 15px 0;
  border: none;
  border-bottom: 2px solid #ddd;
  background: transparent;
  font-size: 1rem;
  transition: border-color 0.3s ease;
  outline: none;
}

.form-input:focus {
  border-bottom-color: #667eea;
}

.form-input:focus + label,
.form-input:not(:placeholder-shown) + label {
  transform: translateY(-25px) scale(0.8);
  color: #667eea;
}

.form-group label {
  position: absolute;
  top: 15px;
  left: 0;
  color: #999;
  font-size: 1rem;
  transition: all 0.3s ease;
  pointer-events: none;
  transform-origin: left;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  font-size: 0.9rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.checkbox {
  margin-right: 8px;
}

.forgot-password-link {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  text-decoration: underline;
  font-size: 0.9rem;
}

.auth-btn {
  width: 100%;
  padding: 15px;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.login-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.register-btn {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.auth-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.auth-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #e74c3c;
  text-align: center;
  margin-top: 15px;
  padding: 10px;
  background: rgba(231, 76, 60, 0.1);
  border-radius: 5px;
  font-size: 0.9rem;
}

.form-footer {
  text-align: center;
  margin-top: 20px;
  color: #666;
}

.switch-link {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  text-decoration: underline;
  font-weight: bold;
  transition: color 0.3s ease;
}

.switch-link:hover {
  color: #764ba2;
}

/* 忘记密码样式 */
.forgot-password-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.98);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  backdrop-filter: blur(5px);
}

.forgot-password-form {
  background: white;
  padding: 40px;
  border-radius: 15px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.forgot-password-form h3 {
  color: #333;
  margin-bottom: 30px;
  font-size: 1.5rem;
}

.forgot-password-form .form-group {
  margin-bottom: 20px;
  text-align: left;
}

.forgot-password-form .auth-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin-bottom: 20px;
}

.resend-code {
  text-align: center;
  margin-top: 15px;
  font-size: 0.9rem;
  color: #666;
}

.resend-btn {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  text-decoration: underline;
  font-size: 0.9rem;
}

.resend-btn:hover {
  color: #764ba2;
}

.back-btn {
  background: none;
  border: 1px solid #ddd;
  color: #666;
  padding: 10px 20px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.back-btn:hover {
  background: #f8f9fa;
  border-color: #667eea;
  color: #667eea;
}

.success-message {
  color: #27ae60;
  text-align: center;
  margin-top: 15px;
  padding: 10px;
  background: rgba(39, 174, 96, 0.1);
  border-radius: 5px;
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .auth-container {
    flex-direction: column;
    max-width: 400px;
  }
  
  .features-panel {
    padding: 20px;
  }
  
  .app-title {
    font-size: 2rem;
  }
  
  .feature-item {
    margin-bottom: 15px;
    padding: 15px;
  }
  
  .form-container {
    padding: 20px;
  }
  
  .forgot-password-form {
    padding: 30px 20px;
    margin: 20px;
  }
}
</style>