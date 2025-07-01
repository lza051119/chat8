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
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { store } from '../store';
import MessageInput from './MessageInput.vue';
import { getMessageHistory } from '../api';

const props = defineProps({ contact: Object });
const messages = ref([]);
const messagesContainer = ref(null);
const ws = ref(null);

watch(() => props.contact, (newContact) => {
  if (newContact) {
    // 加载与该联系人的历史消息（需要后端API）
    loadMessages(newContact.id);
  }
});

async function loadMessages(contactId) {
  try {
    const response = await getMessageHistory(store.token, contactId);
    const messageData = response.data;
    
    // 转换消息格式
    messages.value = messageData.messages.map(msg => ({
      id: msg.id,
      from: msg.from_id,
      content: msg.content,
      time: new Date(msg.timestamp),
      encrypted: msg.encrypted
    })).reverse(); // 反转顺序，最新消息在底部
    
    nextTick(() => {
      scrollToBottom();
    });
  } catch (error) {
    console.error('加载消息历史失败:', error);
    messages.value = [];
  }
}

function sendMessage(messageData) {
  if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
    console.error('WebSocket连接未建立');
    return;
  }
  
  // 通过WebSocket发送消息
  const message = {
    type: 'private_message',
    to_id: props.contact.id,
    content: messageData.content,
    encrypted: true,
    method: 'Server',
    destroy_after: messageData.burnAfter
  };
  
  ws.value.send(JSON.stringify(message));
  
  // 添加到本地消息列表
  const newMessage = {
    id: Date.now(),
    from: store.user?.id,
    content: messageData.content,
    time: new Date(),
    encrypted: true,
    burnAfter: messageData.burnAfter
  };
  
  messages.value.push(newMessage);
  
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

// WebSocket连接管理
function connectWebSocket() {
  if (!store.user || !store.token) return;
  
  const wsUrl = `ws://localhost:8000/ws/${store.user.id}?token=${store.token}`;
  ws.value = new WebSocket(wsUrl);
  
  ws.value.onopen = () => {
    console.log('WebSocket连接已建立');
  };
  
  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    } catch (error) {
      console.error('解析WebSocket消息失败:', error);
    }
  };
  
  ws.value.onclose = () => {
    console.log('WebSocket连接已关闭');
    // 尝试重连
    setTimeout(() => {
      if (store.user) {
        connectWebSocket();
      }
    }, 3000);
  };
  
  ws.value.onerror = (error) => {
    console.error('WebSocket错误:', error);
  };
}

function handleWebSocketMessage(data) {
  if (data.type === 'message') {
    const messageData = data.data;
    
    // 只处理当前聊天对象的消息
    if (props.contact && (messageData.from === props.contact.id || messageData.to === props.contact.id)) {
      const newMessage = {
        id: messageData.id,
        from: messageData.from,
        content: messageData.content,
        time: new Date(messageData.timestamp),
        encrypted: messageData.encrypted
      };
      
      messages.value.push(newMessage);
      
      nextTick(() => {
        scrollToBottom();
      });
    }
  }
}

// 组件生命周期
onMounted(() => {
  connectWebSocket();
});

onUnmounted(() => {
  if (ws.value) {
    ws.value.close();
  }
});
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
