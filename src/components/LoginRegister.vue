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
      
      <div class="switch">
        <span>{{ isLogin ? '没有账号？' : '已有账号？' }}</span>
        <button @click="toggleMode" class="switch-btn">
          {{ isLogin ? '注册' : '登录' }}
        </button>
      </div>
      
      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="success" class="success">{{ success }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { login, register } from '../api';

const emit = defineEmits(['login']);

const isLogin = ref(true);
const username = ref('');
const email = ref('');
const password = ref('');
const error = ref('');
const success = ref('');

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
      emit('login', res.data.data.user, res.data.data.token);
      success.value = '登录成功！';
    } else {
      // 注册逻辑
      await register({ username: username.value, email: email.value, password: password.value });
      success.value = '注册成功，请登录';
      isLogin.value = true;
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
</style>