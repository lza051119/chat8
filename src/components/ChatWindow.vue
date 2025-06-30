<template>
  <div class="chat-window">
    <div class="chat-header">
      <div class="contact-info">
        <div class="avatar">{{ contact.username[0].toUpperCase() }}</div>
        <div class="details">
          <h3>{{ contact.username }}</h3>
          <span class="status">{{ contact.online ? '在线' : '离线' }}</span>
        </div>
      </div>
      <div class="actions">
        <button @click="toggleSecurity" class="action-btn">🔒</button>
        <button @click="startCall" class="action-btn">📞</button>
      </div>
    </div>
    
    <div class="messages" ref="messagesContainer">
      <div 
        v-for="msg in messages" 
        :key="msg.id" 
        :class="['message', msg.from === store.user?.id ? 'sent' : 'received']"
      >
        <div class="message-content">
          <div class="text">{{ msg.content }}</div>
          <div class="meta">
            <span class="time">{{ formatTime(msg.time) }}</span>
            <span v-if="msg.encrypted" class="encrypted">🔒</span>
          </div>
        </div>
      </div>
    </div>
    
    <MessageInput :contact="contact" @send="sendMessage" />
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { store } from '../store';
import MessageInput from './MessageInput.vue';

const props = defineProps({ contact: Object });
const messages = ref([]);
const messagesContainer = ref(null);

watch(() => props.contact, (newContact) => {
  if (newContact) {
    // 加载与该联系人的历史消息（需要后端API）
    loadMessages(newContact.id);
  }
});

function loadMessages(contactId) {
  // 临时模拟消息数据
  messages.value = [
    {
      id: 1,
      from: contactId,
      content: '你好！这是一条加密消息。',
      time: new Date(Date.now() - 300000),
      encrypted: true
    },
    {
      id: 2,
      from: store.user?.id,
      content: '收到！我们的对话是安全的。',
      time: new Date(Date.now() - 120000),
      encrypted: true
    }
  ];
  
  nextTick(() => {
    scrollToBottom();
  });
}

function sendMessage(messageData) {
  const newMessage = {
    id: Date.now(),
    from: store.user?.id,
    content: messageData.content,
    time: new Date(),
    encrypted: true,
    burnAfter: messageData.burnAfter
  };
  
  messages.value.push(newMessage);
  
  // 这里应该通过WebSocket发送消息到后端
  // 1. 本地加密（端到端加密，前端实现）
  // 2. 通过WebSocket发送消息（需要后端WebSocket服务）
  // 3. 消息格式：{ to: props.contact.id, content, encrypted: true, burnAfter: 秒 }
  
  nextTick(() => {
    scrollToBottom();
  });
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

function formatTime(time) {
  return new Date(time).toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
}

function toggleSecurity() {
  alert('安全设置面板（待实现）');
}

function startCall() {
  alert('语音通话功能（待实现）');
}
</script>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #ddd;
  background: white;
}

.contact-info {
  display: flex;
  align-items: center;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #007bff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 1rem;
}

.details h3 {
  margin: 0 0 0.25rem 0;
}

.status {
  font-size: 0.875rem;
  color: #666;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.2rem;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: #f8f9fa;
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

.text {
  margin-bottom: 0.5rem;
}

.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  opacity: 0.7;
}

.encrypted {
  color: #28a745;
}
</style>
