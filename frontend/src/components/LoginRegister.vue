<template>
  <div class="login-register">
    <div class="form-container">
      <h2>{{ isLogin ? '登录' : '注册' }}</h2>
      
      <form @submit.prevent="handleSubmit" class="form">
        <input 
          v-model="username" 
          placeholder="用户名" 
          required 
          class="input"
        />
        <input 
          v-if="!isLogin"
          v-model="email" 
          type="email"
          placeholder="邮箱" 
          required 
          class="input"
        />
        <input 
          v-model="password" 
          type="password" 
          placeholder="密码" 
          required 
          class="input"
        />
        <button type="submit" class="submit-btn">
          {{ isLogin ? '登录' : '注册' }}
        </button>
      </form>
      
      <!-- 忘记密码链接 -->
      <div v-if="isLogin && !showForgotPassword" class="forgot-password">
        <button @click="showForgotPasswordForm" class="forgot-btn">
          忘记密码？
        </button>
      </div>
      
      <div class="switch">
        <span>{{ isLogin ? '没有账号？' : '已有账号？' }}</span>
        <button @click="toggleMode" class="switch-btn">
          {{ isLogin ? '注册' : '登录' }}
        </button>
      </div>
      
      <!-- 忘记密码表单 -->
      <div v-if="showForgotPassword" class="forgot-password-form">
        <h3>{{ forgotPasswordStep === 'email' ? '重置密码' : forgotPasswordStep === 'verify' ? '验证邮箱' : '设置新密码' }}</h3>
        
        <!-- 步骤1: 输入邮箱 -->
        <form v-if="forgotPasswordStep === 'email'" @submit.prevent="sendResetCode" class="form">
          <input 
            v-model="resetEmail" 
            type="email"
            placeholder="请输入注册邮箱" 
            required 
            class="input"
          />
          <button type="submit" class="submit-btn" :disabled="isLoading">
            {{ isLoading ? '发送中...' : '发送验证码' }}
          </button>
        </form>
        
        <!-- 步骤2: 验证验证码 -->
        <form v-if="forgotPasswordStep === 'verify'" @submit.prevent="verifyResetCode" class="form">
          <input 
            v-model="verificationCode" 
            placeholder="请输入6位验证码" 
            required 
            maxlength="6"
            class="input"
          />
          <button type="submit" class="submit-btn" :disabled="isLoading">
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
          <input 
            v-model="newPassword" 
            type="password"
            placeholder="请输入新密码" 
            required 
            class="input"
          />
          <input 
            v-model="confirmPassword" 
            type="password"
            placeholder="确认新密码" 
            required 
            class="input"
          />
          <button type="submit" class="submit-btn" :disabled="isLoading">
            {{ isLoading ? '重置中...' : '重置密码' }}
          </button>
        </form>
        
        <button @click="backToLogin" class="back-btn">
          返回登录
        </button>
      </div>
      
      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="success" class="success">{{ success }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue';
import { login, register } from '../api';
import api from '../api/hybrid-api';
import { initializeUserEncryption, hasCompleteEncryptionKeys, validateUserKeys } from '../utils/encryption-keys';

const emit = defineEmits(['login']);

const isLogin = ref(true);
const username = ref('');
const email = ref('');
const password = ref('');
const error = ref('');
const success = ref('');

// 忘记密码相关状态
const showForgotPassword = ref(false);
const forgotPasswordStep = ref('email'); // 'email', 'verify', 'reset'
const resetEmail = ref('');
const verificationCode = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const isLoading = ref(false);
const countdown = ref(0);
let countdownTimer = null;

function toggleMode() {
  isLogin.value = !isLogin.value;
  username.value = '';
  email.value = '';
  password.value = '';
  error.value = '';
  success.value = '';
}

async function handleSubmit() {
  error.value = '';
  success.value = '';
  
  try {
    if (isLogin.value) {
      // 登录逻辑
      const res = await login({ username: username.value, password: password.value });
      const { user, token } = res.data.data;
      
      // 保存用户信息和token到localStorage
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('token', token);
      
      // 检查用户是否有完整的加密密钥
      const userId = parseInt(user.id);
      const hasKeys = hasCompleteEncryptionKeys(userId);
      
      if (!hasKeys) {
        console.log('🔐 用户缺少加密密钥，正在从服务器获取...');
        
        try {
          // 从服务器获取用户的加密密钥信息
          const keysResponse = await api.get('/v1/encryption/my-keys', {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          if (keysResponse.data.success && keysResponse.data.data) {
            const serverKeys = keysResponse.data.data;
            
            // 构造加密数据对象
            const encryptionData = {
              public_key: serverKeys.public_key,
              registration_id: serverKeys.registration_id || userId,
              prekey_bundle: serverKeys.prekey_bundle
            };
            
            // 初始化用户加密环境
            const encryptionInitSuccess = await initializeUserEncryption(userId, encryptionData);
            
            if (encryptionInitSuccess) {
              console.log('✅ 用户加密密钥已从服务器同步');
            } else {
              console.warn('⚠️ 加密密钥同步失败，但不影响登录');
            }
          } else {
            console.warn('⚠️ 服务器未返回有效的密钥信息');
          }
        } catch (keyError) {
          console.warn('⚠️ 获取服务器密钥失败:', keyError.message);
          // 不阻止登录，只是警告
        }
      } else {
        // 验证现有密钥
        const validation = validateUserKeys(userId);
        if (validation.valid) {
          console.log('✅ 用户密钥验证通过');
        } else {
          console.warn('⚠️ 本地密钥验证失败:', validation.message);
        }
      }
      
      emit('login', user, token);
      success.value = '登录成功！';
    } else {
      // 注册逻辑
      const registerRes = await register({ username: username.value, email: email.value, password: password.value });
      
      // 处理注册成功后的密钥存储
      if (registerRes.data.success && registerRes.data.data) {
        const { user, token, keys } = registerRes.data.data;
        
        // 保存用户信息和token到localStorage
        localStorage.setItem('user', JSON.stringify(user));
        localStorage.setItem('token', token);
        
        // 如果有密钥信息，初始化用户加密环境
        if (keys) {
          // 构造加密数据对象
          const encryptionData = {
            public_key: keys.public_key,
            registration_id: parseInt(user.id),
            prekey_bundle: {
              identity_key: keys.identity_key,
              signed_prekey: keys.signed_prekey,
              one_time_prekeys_count: keys.one_time_prekeys_count,
              key_version: keys.key_version
            }
          };
          
          // 初始化用户加密环境（包括密钥保存和数据库初始化）
          const encryptionInitSuccess = await initializeUserEncryption(parseInt(user.id), encryptionData);
          
          if (encryptionInitSuccess) {
            console.log('✅ 注册成功，密钥已生成并保存');
          } else {
            console.warn('⚠️ 加密环境初始化失败，但不影响注册');
          }
        }
        
        // 自动登录
        emit('login', user, token);
        success.value = '注册成功！';
      } else {
        console.warn('⚠️ 注册响应格式异常');
        error.value = '注册失败，服务器响应异常';
      }
    }
  } catch (e) {
    console.error('网络请求错误:', e);
    // 检查是否是网络连接问题
    if (e.code === 'ERR_NETWORK' || e.code === 'NETWORK_ERROR' || 
        e.message?.includes('Network Error') || 
        e.message?.includes('connect ECONNREFUSED') ||
        !e.response) {
      error.value = '无法连接到服务器，请检查网络连接';
    } else if (e.response) {
      // 有响应但是状态码错误
      const status = e.response.status;
      if (status === 401) {
        error.value = isLogin.value ? '用户名或密码错误' : '注册失败：用户已存在';
      } else if (status === 422) {
        error.value = isLogin.value ? '请求格式错误' : '注册信息格式错误';
      } else {
        error.value = isLogin.value ? '登录失败' : '注册失败';
      }
    } else {
      error.value = isLogin.value ? '登录失败' : '注册失败';
    }
  }
}

// 忘记密码相关方法
function showForgotPasswordForm() {
  showForgotPassword.value = true;
  forgotPasswordStep.value = 'email';
  resetForm();
}

function backToLogin() {
  showForgotPassword.value = false;
  forgotPasswordStep.value = 'email';
  resetForm();
}

function resetForm() {
  resetEmail.value = '';
  verificationCode.value = '';
  newPassword.value = '';
  confirmPassword.value = '';
  error.value = '';
  success.value = '';
  isLoading.value = false;
  stopCountdown();
}

function startCountdown() {
  countdown.value = 60;
  countdownTimer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      stopCountdown();
    }
  }, 1000);
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
  countdown.value = 0;
}

async function sendResetCode() {
  if (!resetEmail.value) {
    error.value = '请输入邮箱地址';
    return;
  }
  
  isLoading.value = true;
  error.value = '';
  
  try {
    const response = await api.post('/v1/auth/forgot-password', {
      email: resetEmail.value
    });
    
    if (response.data.success) {
      success.value = '验证码已发送到您的邮箱';
      forgotPasswordStep.value = 'verify';
      startCountdown();
    }
  } catch (e) {
    console.error('发送验证码失败:', e);
    if (e.response?.data?.message) {
      error.value = e.response.data.message;
    } else if (e.response?.data?.detail) {
      error.value = e.response.data.detail;
    } else {
      error.value = '发送验证码失败，请稍后重试';
    }
  } finally {
    isLoading.value = false;
  }
}

async function verifyResetCode() {
  if (!verificationCode.value || verificationCode.value.length !== 6) {
    error.value = '请输入6位验证码';
    return;
  }
  
  isLoading.value = true;
  error.value = '';
  
  try {
    const response = await api.post('/v1/auth/verify-reset-code', {
      email: resetEmail.value,
      code: verificationCode.value
    });
    
    if (response.data.success) {
      success.value = '验证码验证成功';
      forgotPasswordStep.value = 'reset';
      stopCountdown();
    }
  } catch (e) {
    console.error('验证码验证失败:', e);
    if (e.response?.data?.message) {
      error.value = e.response.data.message;
    } else if (e.response?.data?.detail) {
      error.value = e.response.data.detail;
    } else {
      error.value = '验证码验证失败，请重试';
    }
  } finally {
    isLoading.value = false;
  }
}

async function resetPassword() {
  if (!newPassword.value || newPassword.value.length < 6) {
    error.value = '密码长度至少6位';
    return;
  }
  
  if (newPassword.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致';
    return;
  }
  
  isLoading.value = true;
  error.value = '';
  
  try {
    const response = await api.post('/v1/auth/reset-password', {
      email: resetEmail.value,
      code: verificationCode.value,
      new_password: newPassword.value
    });
    
    if (response.data.success) {
      success.value = '密码重置成功，请使用新密码登录';
      setTimeout(() => {
        backToLogin();
      }, 2000);
    }
  } catch (e) {
    console.error('密码重置失败:', e);
    if (e.response?.data?.message) {
      error.value = e.response.data.message;
    } else if (e.response?.data?.detail) {
      error.value = e.response.data.detail;
    } else {
      error.value = '密码重置失败，请重试';
    }
  } finally {
    isLoading.value = false;
  }
}

// 组件卸载时清理定时器
onUnmounted(() => {
  stopCountdown();
});
</script>

<style scoped>
.login-register {
  max-width: 400px;
  margin: 0 auto;
}

.form-container {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1rem;
}

.input {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.submit-btn {
  padding: 0.75rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
}

.submit-btn:hover {
  background: #0056b3;
}

.switch {
  text-align: center;
  margin-bottom: 1rem;
}

.switch-btn {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  text-decoration: underline;
  margin-left: 0.5rem;
}

.error {
  color: #dc3545;
  text-align: center;
  margin-top: 1rem;
}

.success {
  color: #28a745;
  text-align: center;
  margin-top: 1rem;
}

/* 忘记密码相关样式 */
.forgot-password {
  text-align: center;
  margin-bottom: 1rem;
}

.forgot-btn {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  text-decoration: underline;
  font-size: 0.9rem;
}

.forgot-btn:hover {
  color: #0056b3;
}

.forgot-password-form {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.forgot-password-form h3 {
  text-align: center;
  margin-bottom: 1rem;
  color: #333;
}

.back-btn {
  width: 100%;
  padding: 0.75rem;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 1rem;
}

.back-btn:hover {
  background: #545b62;
}

.resend-code {
  text-align: center;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

.resend-btn {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  text-decoration: underline;
}

.resend-btn:hover {
  color: #0056b3;
}

.submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.submit-btn:disabled:hover {
  background: #6c757d;
}
</style>