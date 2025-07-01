<template>
  <div class="security-panel">
    <div class="panel-header">
      <h3>安全设置</h3>
      <button @click="closePanel" class="close-btn">×</button>
    </div>

    <div class="panel-content">
      <!-- 加密设置 -->
      <div class="setting-section">
        <h4>消息加密</h4>
        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="endToEndEncryption" @change="toggleEncryption" />
            <span>启用端到端加密</span>
          </label>
          <p class="setting-description">所有消息都将在发送前加密，只有接收方能够解密</p>
        </div>
      </div>

      <!-- 连接设置 -->
      <div class="setting-section">
        <h4>连接偏好</h4>
        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="preferP2P" @change="toggleP2PPreference" />
            <span>优先P2P连接</span>
          </label>
          <p class="setting-description">在条件允许时优先使用P2P直连，提供更好的隐私保护</p>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="autoRetryConnection" @change="toggleAutoRetry" />
            <span>自动重连</span>
          </label>
          <p class="setting-description">连接断开时自动尝试重新连接</p>
        </div>
      </div>

      <!-- 存储设置 -->
      <div class="setting-section">
        <h4>本地存储</h4>
        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="saveMessageHistory" @change="toggleMessageHistory" />
            <span>保存聊天记录</span>
          </label>
          <p class="setting-description">在本地保存聊天记录以便查看历史消息</p>
        </div>
      </div>

      <!-- 密钥管理 -->
      <div class="setting-section">
        <h4>密钥管理</h4>
        <div class="key-info">
          <div class="key-item">
            <strong>公钥指纹:</strong>
            <code class="key-fingerprint">{{ publicKeyFingerprint }}</code>
          </div>
        </div>
        
        <div class="key-actions">
          <button class="action-btn secondary" @click="exportKeys">
            导出密钥
          </button>
          <button class="action-btn danger" @click="regenerateKeys">
            重新生成密钥
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { hybridStore } from '../store/hybrid-store';

const emit = defineEmits(['close']);

// 安全设置状态
const endToEndEncryption = ref(true);
const preferP2P = ref(true);
const autoRetryConnection = ref(true);
const saveMessageHistory = ref(true);

// 密钥信息
const publicKeyFingerprint = computed(() => {
  // 这里应该显示真实的公钥指纹
  return 'SHA256:2048:AA:BB:CC:DD:EE:FF';
});

onMounted(() => {
  loadSettings();
});

function loadSettings() {
  // 从本地存储加载设置
  const settings = JSON.parse(localStorage.getItem('securitySettings') || '{}');
  
  endToEndEncryption.value = settings.endToEndEncryption !== false;
  preferP2P.value = settings.preferP2P !== false;
  autoRetryConnection.value = settings.autoRetryConnection !== false;
  saveMessageHistory.value = settings.saveMessageHistory !== false;
}

function saveSettings() {
  const settings = {
    endToEndEncryption: endToEndEncryption.value,
    preferP2P: preferP2P.value,
    autoRetryConnection: autoRetryConnection.value,
    saveMessageHistory: saveMessageHistory.value
  };
  
  localStorage.setItem('securitySettings', JSON.stringify(settings));
}

function toggleEncryption() {
  console.log('端到端加密：', endToEndEncryption.value);
  saveSettings();
}

function toggleP2PPreference() {
  console.log('P2P偏好：', preferP2P.value);
  saveSettings();
}

function toggleAutoRetry() {
  console.log('自动重连：', autoRetryConnection.value);
  saveSettings();
}

function toggleMessageHistory() {
  console.log('消息历史：', saveMessageHistory.value);
  saveSettings();
}

function exportKeys() {
  // 实现密钥导出功能
  console.log('导出密钥');
}

function regenerateKeys() {
  if (confirm('重新生成密钥将使现有的加密聊天记录无法解密，确定要继续吗？')) {
    // 实现密钥重新生成功能
    console.log('重新生成密钥');
  }
}

function closePanel() {
  emit('close');
}
</script>

<style scoped>
.security-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 350px;
  height: 100vh;
  background: white;
  border-left: 1px solid #ddd;
  padding: 1rem;
  overflow-y: auto;
  z-index: 1000;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  padding: 0.25rem 0.5rem;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.panel-content {
  padding: 1rem;
}

.setting-section {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

h4 {
  margin: 0 0 1rem 0;
  color: #555;
  font-size: 1rem;
}

.setting-item {
  margin-bottom: 1rem;
}

.setting-label {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
  cursor: pointer;
}

.setting-label input {
  margin-right: 0.5rem;
}

.setting-description {
  font-size: 0.875rem;
  color: #666;
}

.key-info {
  margin-bottom: 1rem;
}

.key-item {
  margin-bottom: 0.5rem;
}

.key-item strong {
  font-size: 0.875rem;
  color: #666;
}

.key-fingerprint {
  display: block;
  background: #f8f9fa;
  padding: 0.5rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  word-break: break-all;
}

.key-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  padding: 0.5rem 1rem;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.action-btn.secondary {
  background: #6c757d;
}

.action-btn.danger {
  background: #dc3545;
}
</style> 