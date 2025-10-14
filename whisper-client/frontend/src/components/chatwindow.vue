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
          <!-- 隐写术图片消息 -->
          <div v-if="msg.type === 'steganography'" class="steganography-message">
            <div class="stego-image">
              <img :src="msg.imageUrl" alt="隐写术图片" class="stego-img" @click="openImageModal(msg)" />
              <div class="stego-overlay">
                <span class="stego-icon">🔍</span>
                <span class="stego-text">隐写术图片</span>
              </div>
            </div>
            <div class="stego-hint">包含隐藏信息的图片</div>
          </div>
          <!-- 普通文本消息 -->
          <div v-else class="text">{{ msg.content }}</div>
          
          <div class="meta">
            <span class="time">{{ formatTime(msg.time) }}</span>
            <span v-if="msg.encrypted" class="encrypted">🔒</span>
            <span v-if="msg.type === 'steganography'" class="steganography">🖼️</span>
          </div>
        </div>
      </div>
    </div>
    
    <MessageInput :contact="contact" @send="sendMessage" />
    
    <!-- 图片放大模态框 -->
    <div v-if="showImageModal" class="image-modal-overlay" @click="closeImageModal">
      <div class="image-modal" @click.stop>
        <div class="image-modal-header">
          <h3>隐写术图片</h3>
          <button @click="closeImageModal" class="close-btn">×</button>
        </div>
        <div class="image-modal-content">
          <img 
            v-if="currentImageMessage?.imageUrl" 
            :src="currentImageMessage.imageUrl" 
            alt="隐写术图片"
            class="modal-image"
          />
          <div class="modal-steganography-hint">
            <span class="hint-icon">🔐</span>
            <span class="hint-text">此图片包含隐藏信息</span>
          </div>
        </div>
        <div class="image-modal-footer">
          <span class="image-info">{{ formatTime(currentImageMessage?.time) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { store } from '../store';
import MessageInput from './messageinput.vue';
import { getMessageHistory } from '../api';
import config from '../config/config.js';
import { toChinaTime, getChinaTime } from '../utils/timeUtils.js';

const props = defineProps({ contact: Object });
const messages = ref([]);
const messagesContainer = ref(null);
const ws = ref(null);

// 图片放大模态框相关状态
const showImageModal = ref(false);
const currentImageMessage = ref(null);

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

async function sendMessage(messageData) {
  if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
    console.error('WebSocket连接未建立');
    return;
  }
  
  let message, newMessage;
  
  if (messageData.type === 'steganography') {
    // 处理隐写术消息
    try {
      // 将文件转换为base64
      const base64 = await fileToBase64(messageData.file);
      
      message = {
        type: 'private_message',
        to_id: props.contact.id,
        content: `[隐写术图片] ${messageData.originalText}`,
        encrypted: true,
        method: 'Server',
        destroy_after: messageData.burnAfter,
        steganography: {
          image_data: base64,
          original_text: messageData.originalText,
          filename: messageData.file.name
        }
      };
      
      newMessage = {
        id: Date.now(),
        from: store.user?.id,
        content: `[隐写术图片] ${messageData.originalText}`,
        time: new Date(),
        encrypted: true,
        burnAfter: messageData.burnAfter,
        type: 'steganography',
        imageUrl: URL.createObjectURL(messageData.file)
      };
    } catch (error) {
      console.error('处理隐写术图片失败:', error);
      return;
    }
  } else {
    // 处理普通文本消息
    message = {
      type: 'private_message',
      to_id: props.contact.id,
      content: messageData.content,
      encrypted: true,
      method: 'Server',
      destroy_after: messageData.burnAfter
    };
    
    newMessage = {
      id: Date.now(),
      from: store.user?.id,
      content: messageData.content,
      time: new Date(),
      encrypted: true,
      burnAfter: messageData.burnAfter
    };
  }
  
  ws.value.send(JSON.stringify(message));
  messages.value.push(newMessage);
  
  nextTick(() => {
    scrollToBottom();
  });
}

// 辅助函数：将文件转换为base64
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

function formatTime(timestamp) {
  try {
    let date;
    
    // 统一处理不同格式的时间戳
    if (timestamp instanceof Date) {
      date = timestamp;
    } else if (typeof timestamp === 'string') {
      // 处理UTC时间戳格式
      if (timestamp.endsWith('Z') || timestamp.includes('T')) {
        date = new Date(timestamp);
      } else {
        // 假设是UTC时间戳，添加Z标识
        date = new Date(timestamp + 'Z');
      }
    } else if (typeof timestamp === 'number') {
      date = new Date(timestamp);
    } else {
      console.warn('未知的时间戳格式:', timestamp);
      return '无效时间';
    }
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.warn('无效的时间戳:', timestamp);
      return '无效时间';
    }
    
    // 转换为中国时间
    const chinaDate = toChinaTime(date);
    const now = getChinaTime();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    const messageDate = new Date(chinaDate.getFullYear(), chinaDate.getMonth(), chinaDate.getDate());
    
    // 手动格式化时间，确保显示中国时间
    const hours = chinaDate.getHours().toString().padStart(2, '0');
    const minutes = chinaDate.getMinutes().toString().padStart(2, '0');
    const timeStr = `${hours}:${minutes}`;
    
    if (messageDate.getTime() === today.getTime()) {
      // 今天的消息只显示时间
      return timeStr;
    } else if (messageDate.getTime() === yesterday.getTime()) {
      // 昨天的消息显示"昨天 时:分"
      return `昨天 ${timeStr}`;
    } else {
      // 其他日期显示"月-日 时:分"
      const month = (chinaDate.getMonth() + 1).toString().padStart(2, '0');
      const day = chinaDate.getDate().toString().padStart(2, '0');
      const monthDay = `${month}-${day}`;
      return `${monthDay} ${timeStr}`;
    }
  } catch (error) {
    console.error('formatTime错误:', error, timestamp);
    return '时间错误';
  }
}

function toggleSecurity() {
  alert('安全设置面板（待实现）');
}

function startCall() {
  alert('语音通话功能（待实现）');
}

// 图片放大模态框相关函数
function openImageModal(message) {
  currentImageMessage.value = message;
  showImageModal.value = true;
  console.log('打开图片放大模态框:', message);
}

function closeImageModal() {
  showImageModal.value = false;
  currentImageMessage.value = null;
  console.log('关闭图片放大模态框');
}

// WebSocket连接管理
function connectWebSocket() {
  if (!store.user || !store.token) return;
  
  const wsUrl = `${config.WS_BASE_URL}/ws/${store.user.id}?token=${store.token}`;
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

/* 隐写术消息样式 */
.steganography-message {
  margin-bottom: 0.5rem;
}

.stego-image {
  position: relative;
  display: inline-block;
  border-radius: 8px;
  overflow: hidden;
  max-width: 300px;
}

.stego-img {
  width: 100%;
  height: auto;
  display: block;
}

.stego-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stego-hint {
  font-size: 0.75rem;
  color: #666;
  margin-top: 4px;
  font-style: italic;
}

.message.sent .stego-hint {
  color: rgba(255, 255, 255, 0.8);
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

/* 图片放大模态框样式 */
.image-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
  backdrop-filter: blur(5px);
}

.image-modal {
  background: white;
  border-radius: 12px;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.image-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.image-modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #333;
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: #e9ecef;
}

.image-modal-content {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  max-height: calc(90vh - 120px);
  overflow: auto;
}

.modal-image {
  max-width: 100%;
  max-height: 70vh;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.modal-steganography-hint {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.1), rgba(255, 193, 7, 0.05));
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #856404;
}

.image-modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #eee;
  background: #f8f9fa;
  text-align: center;
}

.image-info {
  font-size: 0.875rem;
  color: #666;
}

.stego-img {
  cursor: pointer;
  transition: transform 0.2s;
}

.stego-img:hover {
  transform: scale(1.02);
}
</style>
