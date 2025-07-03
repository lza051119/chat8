<template>
  <div class="settings-page">
    <div class="settings-container">
      <div class="settings-header">
        <h1>系统设置</h1>
        <button @click="goBack" class="back-btn">← 返回聊天</button>
      </div>

      <div class="settings-content">
        <!-- 用户信息设置 -->
        <div class="settings-section">
          <h2>用户信息</h2>
          <div class="setting-item">
            <label>用户名</label>
            <input v-model="userSettings.username" type="text" class="setting-input" />
          </div>
          <div class="setting-item">
            <label>邮箱</label>
            <input v-model="userSettings.email" type="email" class="setting-input" />
          </div>
        </div>

        <!-- 连接设置 -->
        <div class="settings-section">
          <h2>连接设置</h2>
          <div class="setting-item">
            <label class="checkbox-label">
              <input v-model="connectionSettings.preferP2P" type="checkbox" />
              <span>优先使用P2P连接</span>
            </label>
          </div>
          <div class="setting-item">
            <label class="checkbox-label">
              <input v-model="connectionSettings.autoReconnect" type="checkbox" />
              <span>自动重连</span>
            </label>
          </div>
          <div class="setting-item">
            <label>连接超时时间 (秒)</label>
            <input v-model="connectionSettings.timeout" type="number" min="5" max="60" class="setting-input" />
          </div>
        </div>

        <!-- 通知设置 -->
        <div class="settings-section">
          <h2>通知设置</h2>
          <div class="setting-item">
            <label class="checkbox-label">
              <input v-model="notificationSettings.enableDesktop" type="checkbox" />
              <span>桌面通知</span>
            </label>
          </div>
          <div class="setting-item">
            <label class="checkbox-label">
              <input v-model="notificationSettings.enableSound" type="checkbox" />
              <span>声音提醒</span>
            </label>
          </div>
        </div>

        <!-- 安全设置 -->
        <div class="settings-section">
          <h2>安全设置</h2>
          <div class="setting-item">
            <label class="checkbox-label">
              <input v-model="securitySettings.enableE2E" type="checkbox" />
              <span>端到端加密</span>
            </label>
          </div>
          <div class="setting-item">
            <button @click="regenerateKeys" class="action-btn">重新生成密钥对</button>
          </div>
          <div class="setting-item">
            <button @click="exportKeys" class="action-btn">导出公钥</button>
          </div>
          <div class="setting-item">
            <button @click="openSteganography" class="action-btn steganography-btn">🔒 图像隐写术工具</button>
          </div>
        </div>

        <!-- 保存按钮 -->
        <div class="settings-actions">
          <button @click="saveSettings" class="save-btn">保存设置</button>
          <button @click="resetSettings" class="reset-btn">重置设置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { hybridStore } from '../store/hybrid-store';

const router = useRouter();

const userSettings = reactive({
  username: '',
  email: ''
});

const connectionSettings = reactive({
  preferP2P: true,
  autoReconnect: true,
  timeout: 10
});

const notificationSettings = reactive({
  enableDesktop: true,
  enableSound: true
});

const securitySettings = reactive({
  enableE2E: true
});

onMounted(() => {
  // 检查是否是开发模式
  const isDevMode = window.location.pathname.startsWith('/dev/');
  
  if (isDevMode) {
    // 开发模式：加载模拟数据
    loadMockData();
  } else {
    // 只在非开发模式下检查登录状态
    if (!hybridStore.isLoggedIn) {
      router.push('/login');
      return;
    }
  }
  
  loadSettings();
});

function loadSettings() {
  const user = hybridStore.user;
  if (user) {
    userSettings.username = user.username;
    userSettings.email = user.email;
  }

  // 从本地存储加载设置
  const savedSettings = localStorage.getItem('app-settings');
  if (savedSettings) {
    const settings = JSON.parse(savedSettings);
    Object.assign(connectionSettings, settings.connection || {});
    Object.assign(notificationSettings, settings.notification || {});
    Object.assign(securitySettings, settings.security || {});
  }
}

function openSteganography() {
  router.push('/steganography');
}

function saveSettings() {
  const settings = {
    connection: connectionSettings,
    notification: notificationSettings,
    security: securitySettings
  };

  localStorage.setItem('app-settings', JSON.stringify(settings));
  
  // 这里可以调用API保存到服务器
  console.log('设置已保存');
}

function resetSettings() {
  connectionSettings.preferP2P = true;
  connectionSettings.autoReconnect = true;
  connectionSettings.timeout = 10;
  
  notificationSettings.enableDesktop = true;
  notificationSettings.enableSound = true;
  
  securitySettings.enableE2E = true;
}

function regenerateKeys() {
  // 重新生成密钥对的逻辑
  console.log('重新生成密钥对');
}

function exportKeys() {
  // 导出公钥的逻辑
  console.log('导出公钥');
}

async function loadMockData() {
  // 模拟用户数据
  const mockUser = {
    id: 'dev-user-001',
    username: '开发测试用户',
    email: 'dev@example.com'
  };
  
  // 设置模拟用户到store（异步方法）
  await hybridStore.setUser(mockUser, 'dev-mock-token');
  
  console.log('开发模式：Settings模拟数据加载完成');
}

function goBack() {
  // 在开发模式下返回到开发聊天页面
  const isDevMode = window.location.pathname.startsWith('/dev/');
  if (isDevMode) {
    router.push('/dev/chat');
  } else {
    router.push('/chat');
  }
}
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: #f0f2f5;
  padding: 2rem;
}

.settings-container {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 1rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  overflow: hidden;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.settings-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.back-btn {
  padding: 0.5rem 1rem;
  background: rgba(255,255,255,0.2);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background 0.2s;
}

.back-btn:hover {
  background: rgba(255,255,255,0.3);
}

.settings-content {
  padding: 2rem;
}

.settings-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #eee;
}

.settings-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.settings-section h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.25rem;
  color: #333;
}

.setting-item {
  margin-bottom: 1rem;
}

.setting-item label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.checkbox-label {
  display: flex !important;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.setting-input {
  width: 100%;
  max-width: 300px;
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.setting-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.action-btn {
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background 0.2s;
}

.action-btn:hover {
  background: #e9ecef;
}

.steganography-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  font-weight: 500;
}

.steganography-btn:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.settings-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #eee;
}

.save-btn, .reset-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn {
  background: #28a745;
  color: white;
}

.save-btn:hover {
  background: #218838;
}

.reset-btn {
  background: #6c757d;
  color: white;
}

.reset-btn:hover {
  background: #5a6268;
}

@media (max-width: 768px) {
  .settings-page {
    padding: 1rem;
  }
  
  .settings-header {
    padding: 1.5rem;
  }
  
  .settings-content {
    padding: 1.5rem;
  }
  
  .settings-actions {
    flex-direction: column;
  }
}
</style>