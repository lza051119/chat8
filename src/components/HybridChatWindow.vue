<template>
  <div class="hybrid-chat-window">
    <div class="chat-header">
      <div v-if="contact" class="contact-info">
        <div class="contact-avatar">
          <img v-if="contact.avatar" :src="contact.avatar" :alt="contact.username" />
          <div v-else class="avatar-placeholder">
            {{ contact.username[0].toUpperCase() }}
          </div>
        </div>
        
        <div class="contact-details">
          <h3>{{ contact.username }}</h3>
          <div class="connection-info">
            <span :class="['status-indicator', { online: contact.online }]"></span>
            <span class="status-text">
              {{ contact.online ? '在线' : '离线' }}
            </span>
            <span v-if="contact.online" class="connection-method">
              {{ getConnectionMethod() }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- 通话按钮 -->
      <div v-if="contact" class="call-actions">
        <button 
          @click="startVoiceCall" 
          :disabled="!contact.online"
          class="voice-call-btn"
          title="语音通话"
        >
          📞
        </button>
      </div>
      
      <div v-else class="no-contact">
        <p>请选择一个联系人开始聊天</p>
      </div>
    </div>

    <div v-if="contact" class="messages-container" ref="messagesContainer">
      <div
        v-for="message in messages"
        :key="message.id"
        :class="['message', message.from === currentUser.id ? 'sent' : 'received']"
      >
        <div class="message-content">
          <div class="message-text">{{ message.content }}</div>
          <div class="message-info">
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            <span v-if="message.method" class="message-method">
              {{ message.method === 'P2P' ? 'P2P' : '服务器' }}
            </span>
          </div>
        </div>
      </div>
      
      <div v-if="messages.length === 0" class="empty-messages">
        <div class="empty-icon">💬</div>
        <p>开始你们的第一次对话吧</p>
      </div>
    </div>

    <div v-if="contact" class="message-input-area">
      <HybridMessageInput
        :contact="contact"
        @message-sent="handleMessageSent"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { hybridStore } from '../store/hybrid-store';
import HybridMessageInput from './HybridMessageInput.vue';

const router = useRouter();

const messagesContainer = ref(null);

const contact = computed(() => hybridStore.currentContact);
const currentUser = computed(() => hybridStore.user);

const messages = computed(() => {
  if (!contact.value) return [];
  return hybridStore.getMessages(contact.value.id);
});

// 监听联系人变化，滚动到底部
watch(contact, async () => {
  if (contact.value) {
    await nextTick();
    scrollToBottom();
  }
});

// 监听消息变化，滚动到底部
watch(messages, async () => {
  await nextTick();
  scrollToBottom();
}, { deep: true });

onMounted(() => {
  scrollToBottom();
});

function getConnectionMethod() {
  if (!contact.value?.online) return '';
  
  const p2pStatus = hybridStore.getP2PStatus(contact.value.id);
  return p2pStatus === 'connected' ? '(P2P直连)' : '(服务器转发)';
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  
  if (date.toDateString() === now.toDateString()) {
    // 今天的消息只显示时间
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  } else {
    // 其他日期显示月日和时间
    return date.toLocaleString('zh-CN', { 
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

function handleMessageSent(message) {
  // 消息已经通过HybridMessaging服务添加到store中
  // 这里只需要滚动到底部
  scrollToBottom();
}

function startVoiceCall() {
  if (!contact.value || !contact.value.online) {
    alert('联系人不在线，无法发起语音通话');
    return;
  }
  
  // 跳转到语音通话页面
  router.push(`/voice-call/${contact.value.id}`);
}
</script>

<style scoped>
.hybrid-chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8f9fa;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #ddd;
}

.contact-info {
  display: flex;
  align-items: center;
}

.contact-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 1rem;
}

.avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #007bff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
}

.contact-details h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
}

.connection-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #666;
}

.call-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.voice-call-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: #4caf50;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.voice-call-btn:hover:not(:disabled) {
  background: #45a049;
  transform: scale(1.1);
}

.voice-call-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator.online {
  background: #28a745;
}

.status-text {
  font-weight: 500;
}

.connection-method {
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.625rem;
  font-weight: 500;
  text-transform: uppercase;
}

.no-contact {
  text-align: center;
  padding: 1rem;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.message {
  margin-bottom: 1rem;
  display: flex;
}

.message.sent {
  justify-content: flex-end;
}

.message.received {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  background: white;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.message.sent .message-content {
  background: #007bff;
  color: white;
}

.message-text {
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.message-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  opacity: 0.8;
}

.message-time {
  font-weight: 500;
}

.message-method {
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.625rem;
  font-weight: 500;
  text-transform: uppercase;
}

.empty-messages {
  text-align: center;
  padding: 1rem;
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.message-input-area {
  padding: 1rem;
  background: white;
  border-top: 1px solid #ddd;
}
</style>