<template>
  <div class="hybrid-message-input">
    <!-- 功能控制面板 -->
    <div class="controls-panel">
      <div class="control-group">
        <label class="control-item">
          <input 
            type="checkbox" 
            v-model="imageHideMode" 
            @change="onImageHideModeChange"
          />
          <span class="control-label">🖼️ 图像隐藏</span>
        </label>
        
        <label class="control-item">
          <input 
            type="checkbox" 
            v-model="burnMode" 
            @change="onBurnModeChange"
          />
          <span class="control-label">🔥 阅后即焚</span>
        </label>
      </div>
      
      <div class="retention-group" v-if="burnMode">
        <label class="retention-label">留存时长：</label>
        <input 
          type="number" 
          v-model.number="retentionTime" 
          min="1" 
          max="3600" 
          class="retention-input"
        />
        <select v-model="retentionUnit" class="retention-unit">
          <option value="seconds">秒</option>
          <option value="minutes">分钟</option>
          <option value="hours">小时</option>
        </select>
      </div>
    </div>

    <!-- 连接状态指示器 -->
    <div class="connection-indicator">
      <div class="method-display">
        <span :class="['method-icon', connectionStatus.preferredMethod.toLowerCase()]">
          {{ connectionStatus.preferredMethod === 'P2P' ? '🔗' : '📡' }}
        </span>
        <span class="method-text">
          {{ connectionStatus.preferredMethod === 'P2P' ? 'P2P直连' : '服务器转发' }}
        </span>
        <div v-if="connectionStatus.p2pStatus === 'connecting'" class="connecting-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
      
      <!-- 发送状态 -->
      <div v-if="sendStatus.sending" class="send-status">
        <div class="spinner-small"></div>
        <span>发送中...</span>
      </div>
    </div>

    <div class="input-container">
      <div class="input-wrapper">
        <div v-if="imageHideMode" class="mode-hint">
          🖼️ 图像隐藏模式：输入文本后点击发送按钮选择图片
        </div>
        
        <textarea
          ref="messageInput"
          v-model="message"
          @keydown="handleKeyDown"
          @input="adjustHeight"
          :placeholder="getPlaceholder()"
          rows="1"
          class="message-textarea"
          :disabled="sendStatus.sending"
        />
        
        <!-- 字符计数和预估传输方式 -->
        <div class="input-meta">
          <span class="char-count">{{ message.length }}/2000</span>
          <span v-if="message.length > 0" class="estimated-method">
            预估: {{ getEstimatedMethod() }}
          </span>
        </div>
      </div>
      
      <!-- 图片发送按钮 -->
      <button 
        @click="selectImage" 
        class="image-btn"
        :disabled="sendStatus.sending"
        title="发送图片"
      >
        📷
      </button>
      
      <!-- 文件发送按钮 -->
      <button 
        @click="selectFile" 
        class="file-btn"
        :disabled="sendStatus.sending"
        title="发送文件"
      >
        📎
      </button>
      
      <button 
        @click="onSend" 
        :disabled="!canSend"
        :class="getSendButtonClass()"
        :title="getSendButtonTitle()"
      >
        <span v-if="!sendStatus.sending">{{ getSendButtonText() }}</span>
        <div v-else class="spinner-small white"></div>
      </button>
    </div>

    <!-- 隐藏的图片输入 -->
    <input 
      ref="fileInput" 
      type="file" 
      accept="image/*" 
      @change="handleImageSelect" 
      style="display: none;"
    />
    
    <!-- 隐藏的文件输入 -->
    <input 
      ref="genericFileInput" 
      type="file" 
      @change="handleFileSelect" 
      style="display: none;"
    />

    <!-- 快捷操作 -->
    <div v-if="showQuickActions" class="quick-actions">
      <button @click="insertQuickText('👍')" class="quick-btn">👍</button>
      <button @click="insertQuickText('😄')" class="quick-btn">😄</button>
      <button @click="insertQuickText('❤️')" class="quick-btn">❤️</button>
      <button @click="insertQuickText('好的')" class="quick-btn">好的</button>
      <button @click="insertQuickText('收到')" class="quick-btn">收到</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue';

const props = defineProps({
  contact: {
    type: Object,
    required: true
  },
  connectionStatus: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['send']);

// 新增的响应式数据
const imageHideMode = ref(false);
const burnMode = ref(false);
const retentionTime = ref(30);
const retentionUnit = ref('seconds');

// 计算属性：获取留存时间（秒）
const burnAfterSeconds = computed(() => {
  switch (retentionUnit.value) {
    case 'minutes':
      return retentionTime.value * 60;
    case 'hours':
      return retentionTime.value * 3600;
    default:
      return retentionTime.value;
  }
});

const messageInput = ref(null);
const fileInput = ref(null);
const genericFileInput = ref(null);
const message = ref('');
const showQuickActions = ref(false);
const sendStatus = ref({
  sending: false,
  lastMethod: null,
  error: null
});

// 计算属性
const canSend = computed(() => {
  return message.value.trim().length > 0 && 
         !sendStatus.value.sending && 
         message.value.length <= 2000;
});

// 监听连接状态变化
watch(() => props.connectionStatus, (newStatus) => {
  // 如果连接方式改变，显示提示
  if (sendStatus.value.lastMethod && 
      sendStatus.value.lastMethod !== newStatus.preferredMethod) {
    console.log(`连接方式已切换: ${sendStatus.value.lastMethod} -> ${newStatus.preferredMethod}`);
  }
});

// 方法
// 新增的界面方法
function getPlaceholder() {
  if (imageHideMode.value) {
    return '输入要隐藏的文本内容...';
  }
  return '输入消息...';
}

function getSendButtonClass() {
  const classes = ['send-btn'];
  if (sendStatus.value.sending) classes.push('sending');
  if (imageHideMode.value) classes.push('image-hide-mode');
  return classes;
}

function getSendButtonTitle() {
  if (imageHideMode.value) {
    return '点击选择图片并隐藏文本';
  }
  return '发送消息';
}

function getSendButtonText() {
  if (imageHideMode.value) {
    return '选择图片';
  }
  return '发送';
}

function onImageHideModeChange() {
  if (imageHideMode.value) {
    console.log('启用图像隐藏模式');
    // 图像隐藏和阅后即焚互斥
    if (burnMode.value) {
      burnMode.value = false;
      console.log('已自动关闭阅后即焚模式');
    }
  }
}

function onBurnModeChange() {
  if (burnMode.value) {
    console.log('启用阅后即焚模式');
    // 图像隐藏和阅后即焚互斥
    if (imageHideMode.value) {
      imageHideMode.value = false;
      console.log('已自动关闭图像隐藏模式');
    }
  }
}

function onSend() {
  if (imageHideMode.value && message.value.trim()) {
    selectImageForSteganography();
  } else {
    sendMessage();
  }
}

function selectImageForSteganography() {
  fileInput.value?.click();
}

function resetInput() {
  message.value = '';
  adjustHeight();
}

async function handleSteganographyUpload(file) {
  sendStatus.value.sending = true;
  sendStatus.value.error = null;
  
  try {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('secret_message', message.value.trim());
    formData.append('password', 'default_password'); // 临时使用默认密码，后续可以改为用户设置的密码
    
    // 调用隐写术API
    const API_BASE_URL = '/api';
    const response = await fetch(`${API_BASE_URL}/steganography/embed`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error('隐写术处理失败');
    }
    
    // 后端返回的是图片文件，需要创建blob URL
    const blob = await response.blob();
    
    // 创建新的File对象用于上传
    const steganographyFile = new File([blob], `stego_${file.name}`, {
      type: blob.type || 'image/png'
    });
    
    // 创建FormData用于图片上传
    const uploadFormData = new FormData();
    uploadFormData.append('file', steganographyFile);
    uploadFormData.append('to_id', props.contact.id);
    uploadFormData.append('hidding_message', 'true'); // 标记为隐写术图片
    
    // 发送隐写术图片消息
    const messageData = {
      type: 'image',
      file: uploadFormData,
      fileName: steganographyFile.name,
      hiddenMessage: true, // 前端标记
      originalText: message.value.trim(), // 保存原始文本用于显示
      timestamp: Date.now()
    };
    
    if (burnMode.value) {
      messageData.burnAfter = burnAfterSeconds.value;
    }
    
    // 发送消息，等待结果
    const result = await new Promise((resolve) => {
      emit('send', messageData, resolve);
    });
    
    if (!result.success) {
      throw new Error(result.error || '发送失败');
    }
    
    // 重置状态
    resetInput();
    imageHideMode.value = false;
    
    // 清空文件输入
    if (fileInput.value) {
      fileInput.value.value = '';
    }
    
    nextTick(() => {
      messageInput.value?.focus();
    });
    
  } catch (error) {
    sendStatus.value.error = error.message || '隐写术发送失败';
    console.error('隐写术发送失败:', error);
  } finally {
    sendStatus.value.sending = false;
  }
}

async function sendMessage() {
  if (!canSend.value) return;

  const messageContent = message.value.trim();
  sendStatus.value.sending = true;
  sendStatus.value.error = null;

  try {
    const messageData = {
      content: message.value.trim(),
      type: 'text',
      timestamp: Date.now()
    };
    
    // 添加阅后即焚设置
    if (burnMode.value) {
      messageData.burnAfter = burnAfterSeconds.value;
    }
    
    // 发送消息事件，等待结果
    const result = await new Promise((resolve) => {
      emit('send', messageData, resolve);
    });
    
    if (!result.success) {
      throw new Error(result.error || '发送失败');
    }
    
    // 清空输入框
    resetInput();
    sendStatus.value.lastMethod = props.connectionStatus.preferredMethod;
    
    // 聚焦输入框
    nextTick(() => {
      messageInput.value?.focus();
    });
  } catch (error) {
    sendStatus.value.error = error.message || '发送失败';
    console.error('发送消息失败:', error);
  } finally {
    sendStatus.value.sending = false;
  }
}

function handleKeyDown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  } else if (event.key === 'Enter' && event.shiftKey) {
    // 允许换行
    return;
  }
}

function adjustHeight() {
  const textarea = messageInput.value;
  if (textarea) {
    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, 120); // 最大高度120px
    textarea.style.height = newHeight + 'px';
  }
}

function insertQuickText(text) {
  message.value += text;
  nextTick(() => {
    adjustHeight();
    messageInput.value?.focus();
  });
}

function getEstimatedMethod() {
  // 根据用户在线状态和支持情况预估传输方式
  if (!props.connectionStatus.isOnline) {
    return '离线存储';
  }
  
  if (props.connectionStatus.p2pStatus === 'connected') {
    return 'P2P直连';
  } else if (props.connectionStatus.p2pStatus === 'connecting') {
    return '建立连接中...';
  } else if (props.connectionStatus.supportsP2P) {
    return '服务器转发 (尝试P2P)';
  } else {
    return '服务器转发';
  }
}

// 切换快捷操作显示
function selectImage() {
  fileInput.value?.click();
}

function selectFile() {
  genericFileInput.value?.click();
}

async function handleImageSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件');
    return;
  }

  // 验证文件大小 (5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过5MB');
    return;
  }

  // 如果是隐写术模式
  if (imageHideMode.value && message.value.trim()) {
    await handleSteganographyUpload(file);
    return;
  }

  sendStatus.value.sending = true;
  sendStatus.value.error = null;

  try {
    // 创建FormData
    const formData = new FormData();
    formData.append('file', file);
    formData.append('to_id', props.contact.id);
    formData.append('message_type', 'image');

    // 发送图片，等待结果
    const result = await new Promise((resolve) => {
      emit('send', { 
        type: 'image', 
        file: formData,
        fileName: file.name
      }, resolve);
    });
    
    if (!result.success) {
      throw new Error(result.error || '发送失败');
    }
    
    // 清空文件输入
    event.target.value = '';
  } catch (error) {
    sendStatus.value.error = error.message || '发送图片失败';
    console.error('发送图片失败:', error);
  } finally {
    sendStatus.value.sending = false;
  }
}

async function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  // 验证文件大小 (20MB)
  if (file.size > 20 * 1024 * 1024) {
    alert('文件大小不能超过20MB');
    return;
  }

  // 检查是否为禁止的文件类型
  const forbiddenExtensions = ['.exe', '.bat', '.cmd', '.sh', '.php', '.asp', '.aspx', '.js', '.vbs', '.ps1'];
  const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
  if (forbiddenExtensions.includes(fileExtension)) {
    alert('不允许上传可执行文件或脚本文件');
    return;
  }

  sendStatus.value.sending = true;
  sendStatus.value.error = null;

  try {
    // 创建FormData
    const formData = new FormData();
    formData.append('file', file);
    formData.append('to_id', props.contact.id);
    formData.append('message_type', 'file');

    // 发送文件消息，等待结果
    const result = await new Promise((resolve) => {
      emit('send', { 
        type: 'file', 
        file: formData,
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        messageType: 'file'
      }, resolve);
    });
    
    if (!result.success) {
      throw new Error(result.error || '发送失败');
    }
    
    // 清空文件输入
    event.target.value = '';
  } catch (error) {
    sendStatus.value.error = error.message || '发送文件失败';
    console.error('发送文件失败:', error);
  } finally {
    sendStatus.value.sending = false;
  }
}

function toggleQuickActions() {
  showQuickActions.value = !showQuickActions.value;
}

// 暴露方法给父组件
defineExpose({
  focus: () => messageInput.value?.focus(),
  clear: () => {
    message.value = '';
    adjustHeight();
  }
});
</script>

<style scoped>
.hybrid-message-input {
  background: white;
  border-top: 1px solid #ddd;
  padding: 1rem;
}

/* 控制面板样式 */
.controls-panel {
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.control-group {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 0.5rem;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
}

.control-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #007bff;
}

.control-label {
  user-select: none;
  color: #495057;
}

.retention-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #dee2e6;
}

.retention-label {
  font-size: 0.85rem;
  color: #6c757d;
  font-weight: 500;
}

.retention-input {
  width: 60px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.85rem;
  text-align: center;
}

.retention-unit {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.85rem;
  background: white;
}

.mode-hint {
  position: absolute;
  top: -28px;
  left: 0;
  font-size: 0.75rem;
  color: #28a745;
  background: rgba(40, 167, 69, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  white-space: nowrap;
  font-weight: 500;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.connection-indicator {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: #f8f9fa;
  border-radius: 0.5rem;
  font-size: 0.875rem;
}

.method-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.method-icon {
  font-size: 1rem;
}

.method-text {
  font-weight: 500;
}

.method-display.p2p .method-text {
  color: #28a745;
}

.method-display.server .method-text {
  color: #ffc107;
}

.connecting-dots {
  display: flex;
  gap: 0.25rem;
}

.connecting-dots span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #007bff;
  animation: bounce 1.4s infinite ease-in-out both;
}

.connecting-dots span:nth-child(1) { animation-delay: -0.32s; }
.connecting-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.send-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
  font-size: 0.875rem;
}

.input-container {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.message-textarea {
  width: 100%;
  min-height: 40px;
  max-height: 120px;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  line-height: 1.4;
  resize: none;
  outline: none;
  transition: border-color 0.2s;
}

.message-textarea:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 0.125rem rgba(0, 123, 255, 0.25);
}

.message-textarea:disabled {
  background: #f8f9fa;
  color: #666;
}

.input-meta {
  position: absolute;
  bottom: 0.25rem;
  right: 0.5rem;
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #666;
  background: rgba(255, 255, 255, 0.9);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
}

.char-count {
  opacity: 0.7;
}

.estimated-method {
  opacity: 0.8;
  font-weight: 500;
}

.image-btn {
  width: 40px;
  height: 40px;
  background: #f8f9fa;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-btn:hover:not(:disabled) {
  background: #e9ecef;
  transform: translateY(-1px);
}

.image-btn, .file-btn {
  width: 40px;
  height: 40px;
  background: #f8f9fa;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-btn:hover:not(:disabled), .file-btn:hover:not(:disabled) {
  background: #e9ecef;
  transform: translateY(-1px);
}

.image-btn:disabled, .file-btn:disabled {
  background: #f8f9fa;
  color: #ccc;
  cursor: not-allowed;
  transform: none;
}

.send-btn {
  min-width: 80px;
  height: 40px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-1px);
}

.send-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
}

.send-btn.sending {
  background: #28a745;
}

.send-btn.image-hide-mode {
  background: #17a2b8;
  border-color: #17a2b8;
}

.send-btn.image-hide-mode:hover:not(:disabled) {
  background: #138496;
  border-color: #117a8b;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-small.white {
  border: 2px solid rgba(255,255,255,0.3);
  border-top: 2px solid white;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.quick-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #eee;
}

.quick-btn {
  padding: 0.375rem 0.75rem;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 1rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn:hover {
  background: #e9ecef;
  transform: translateY(-1px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hybrid-message-input {
    padding: 0.75rem;
  }
  
  .connection-indicator {
    padding: 0.375rem 0.5rem;
    font-size: 0.8rem;
  }
  
  .input-container {
    gap: 0.5rem;
  }
  
  .send-btn {
    min-width: 60px;
    height: 36px;
    font-size: 0.8rem;
  }
  
  .quick-actions {
    flex-wrap: wrap;
    gap: 0.375rem;
  }
  
  .quick-btn {
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
  }
}
</style>