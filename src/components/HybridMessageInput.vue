<template>
  <div class="hybrid-message-input">
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
        <textarea
          ref="messageInput"
          v-model="message"
          @keydown="handleKeyDown"
          @input="adjustHeight"
          placeholder="输入消息..."
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
      
      <button 
        @click="sendMessage" 
        :disabled="!canSend"
        :class="['send-btn', { 'sending': sendStatus.sending }]"
      >
        <span v-if="!sendStatus.sending">发送</span>
        <div v-else class="spinner-small white"></div>
      </button>
    </div>

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

const messageInput = ref(null);
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
async function sendMessage() {
  if (!canSend.value) return;

  const messageContent = message.value.trim();
  sendStatus.value.sending = true;
  sendStatus.value.error = null;

  try {
    const result = await emit('send', { content: messageContent });
    
    if (result && result.success) {
      message.value = '';
      sendStatus.value.lastMethod = result.method;
      adjustHeight();
      
      // 聚焦输入框
      nextTick(() => {
        messageInput.value?.focus();
      });
    } else {
      sendStatus.value.error = result?.error || '发送失败';
    }
  } catch (error) {
    sendStatus.value.error = error.message || '发送失败';
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