<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1 class="app-title">安全即时通信</h1>
        <p class="app-subtitle">混合架构 P2P + 服务器转发</p>
      </div>

      <!-- 开发模式提示 -->
      <div class="dev-mode-notice">
        <h3>🔧 开发模式</h3>
        <p>无需后端，直接访问页面进行开发测试：</p>
        <div class="dev-links">
          <a href="/dev/chat" class="dev-link">📱 聊天页面</a>
          <a href="/dev/settings" class="dev-link">⚙️ 设置页面</a>
        </div>
      </div>

      <div class="login-form">
        <h2>用户登录</h2>
        
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="username">用户名</label>
            <input
              id="username"
              v-model="loginForm.username"
              type="text"
              placeholder="请输入用户名"
              required
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="password">密码</label>
            <input
              id="password"
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              required
              class="form-input"
            />
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
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="login-btn"
          >
            <span v-if="!isLoading">登录</span>
            <div v-else class="loading-spinner"></div>
          </button>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
        </form>

        <div class="login-footer">
          <p>还没有账号？ 
            <router-link to="/register" class="register-link">立即注册</router-link>
          </p>
        </div>
      </div>

      <!-- 架构特性说明 -->
      <div class="features-panel">
        <h3>系统特性</h3>
        <div class="feature-list">
          <div class="feature-item">
            <span class="feature-icon">🔗</span>
            <div class="feature-content">
              <strong>P2P直连</strong>
              <p>在线用户之间直接通信，低延迟高隐私</p>
            </div>
          </div>
          
          <div class="feature-item">
            <span class="feature-icon">📡</span>
            <div class="feature-content">
              <strong>服务器转发</strong>
              <p>离线用户消息存储转发，确保送达</p>
            </div>
          </div>
          
          <div class="feature-item">
            <span class="feature-icon">⚡</span>
            <div class="feature-content">
              <strong>智能切换</strong>
              <p>根据网络状况自动选择最优传输方式</p>
            </div>
          </div>
          
          <div class="feature-item">
            <span class="feature-icon">🔒</span>
            <div class="feature-content">
              <strong>端到端加密</strong>
              <p>消息全程加密保护，保障通信安全</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { hybridStore } from '../store/hybrid-store';
import { authAPI } from '../api/hybrid-api';

const router = useRouter();

const isLoading = ref(false);
const errorMessage = ref('');

const loginForm = reactive({
  username: '',
  password: '',
  rememberMe: false
});

async function handleLogin() {
  if (isLoading.value) return;

  if (!loginForm.username || !loginForm.password) {
    errorMessage.value = '请输入用户名和密码';
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';

  try {
    const response = await authAPI.login({
      username: loginForm.username,
      password: loginForm.password
    });

    // 设置用户信息到store（现在是异步方法）
    const setUserSuccess = await hybridStore.setUser(response.data.data.user, response.data.data.token);
    
    if (!setUserSuccess) {
      errorMessage.value = '用户信息设置失败，请重试';
      return;
    }
    
    // 验证用户信息是否正确设置
    if (!hybridStore.user || !hybridStore.user.id) {
      errorMessage.value = '用户信息验证失败，请重试';
      return;
    }
    
    console.log('登录成功，跳转到聊天页面');
    // 跳转到聊天页面
    router.push('/chat');

  } catch (error) {
    console.error('登录失败:', error);
    
    if (error.response) {
      // 服务器返回了错误响应
      const status = error.response.status;
      if (status === 401) {
        errorMessage.value = '用户名或密码错误';
      } else if (status === 500) {
        errorMessage.value = '服务器内部错误，请稍后重试';
      } else {
        errorMessage.value = error.response.data?.message || '登录失败，请重试';
      }
    } else if (error.request) {
      // 网络错误
      errorMessage.value = '无法连接到服务器，请检查网络连接';
    } else {
      // 其他错误
      errorMessage.value = '登录失败，请重试';
    }
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.login-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  max-width: 1000px;
  width: 100%;
  background: white;
  border-radius: 1rem;
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
  overflow: hidden;
}

.login-header {
  grid-column: span 2;
  text-align: center;
  padding: 2rem 2rem 0;
}

.app-title {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  font-weight: 700;
  color: #333;
}

.app-subtitle {
  margin: 0;
  color: #666;
  font-size: 1rem;
}

.dev-mode-notice {
  grid-column: span 2;
  padding: 1.5rem 2rem;
  background: linear-gradient(135deg, #fff3cd, #ffeaa7);
  border: 1px solid #ffeaa7;
  border-radius: 0.5rem;
  margin: 0 2rem 1rem;
  text-align: center;
}

.dev-mode-notice h3 {
  margin: 0 0 0.5rem 0;
  color: #856404;
  font-size: 1.1rem;
}

.dev-mode-notice p {
  margin: 0 0 1rem 0;
  color: #856404;
  font-size: 0.9rem;
}

.dev-links {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.dev-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #856404;
  color: white;
  text-decoration: none;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 0.2s;
}

.dev-link:hover {
  background: #6c5ce7;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.login-form {
  padding: 0 2rem 2rem;
}

.login-form h2 {
  margin: 0 0 2rem 0;
  font-size: 1.5rem;
  color: #333;
  text-align: center;
}

.demo-notice {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: #e8f4fd;
  border: 1px solid #bee5eb;
  border-radius: 0.5rem;
  margin-bottom: 2rem;
}

.notice-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.notice-content strong {
  display: block;
  color: #0c5460;
  margin-bottom: 0.25rem;
}

.notice-content p {
  margin: 0;
  color: #0c5460;
  font-size: 0.875rem;
  line-height: 1.4;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e1e5e9;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-options {
  margin-bottom: 2rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: #666;
}

.checkbox {
  width: 1rem;
  height: 1rem;
}

.login-btn {
  width: 100%;
  padding: 0.875rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 50px;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #fee;
  color: #c33;
  border: 1px solid #fcc;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  text-align: center;
}

.login-footer {
  text-align: center;
  margin-top: 2rem;
  color: #666;
}

.register-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.register-link:hover {
  text-decoration: underline;
}

.features-panel {
  padding: 2rem;
  background: #f8f9fa;
}

.features-panel h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1.25rem;
  color: #333;
  text-align: center;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.feature-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.feature-content strong {
  display: block;
  margin-bottom: 0.25rem;
  color: #333;
  font-size: 1rem;
}

.feature-content p {
  margin: 0;
  color: #666;
  font-size: 0.875rem;
  line-height: 1.4;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-page {
    padding: 1rem;
  }
  
  .login-container {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .login-header {
    grid-column: span 1;
    padding: 1.5rem 1.5rem 0;
  }
  
  .app-title {
    font-size: 1.5rem;
  }
  
  .login-form, .features-panel {
    padding: 0 1.5rem 1.5rem;
  }
  
  .feature-list {
    gap: 1rem;
  }
  
  .feature-item {
    gap: 0.75rem;
  }
  
  .feature-icon {
    font-size: 1.5rem;
  }
}
</style>