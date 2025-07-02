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
      
      <!-- 功能按钮 -->
      <div v-if="contact" class="action-buttons">
        <button 
          @click="showHistoryModal" 
          class="history-btn"
          title="查看历史记录"
        >
          📋
        </button>
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
        :class="['message', parseInt(message.from) === parseInt(currentUser.id) ? 'sent' : 'received']"
      >
        <div class="message-content">
          <!-- 文本消息 -->
          <div v-if="!message.messageType || message.messageType === 'text'" class="message-text">{{ message.content }}</div>
          
          <!-- 图片消息 -->
          <div v-else-if="message.messageType === 'image'" class="message-image">
            <div class="image-container" :class="{ 'has-hidden-message': message.hiddenMessage }">
              <img 
                v-if="message.filePath && message.messageType === 'image'" 
                :src="getImageUrl(message.filePath)" 
                :alt="message.fileName || '图片'"
                class="image-content"
                @error="handleImageError"
                @contextmenu="handleImageRightClick(message, $event)"
              />
              <div v-else class="image-placeholder">
                <span class="image-icon">📷</span>
                <span class="image-text">{{ message.content }}</span>
              </div>
              
              <!-- 隐写术提示 -->
              <div v-if="message.hiddenMessage && !message.extractedText" class="steganography-hint">
                <span class="hint-icon">🔐</span>
                <span class="hint-text">此图片包含隐藏信息</span>
              </div>
              
              <!-- 显示提取的隐藏信息 -->
              <div v-if="message.extractedText" class="extracted-message">
                <div class="extracted-header">
                  <span class="extracted-icon">📝</span>
                  <span class="extracted-label">隐藏信息：</span>
                </div>
                <div class="extracted-content">{{ message.extractedText }}</div>
              </div>
            </div>
          </div>
          
          <div class="message-info">
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            <span v-if="message.method" class="message-method">
              {{ message.method === 'P2P' ? 'P2P' : '服务器' }}
            </span>
            <span v-if="message.sending" class="sending-indicator">发送中...</span>
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
        :connectionStatus="getConnectionStatus()"
        @send="(messageData, callback) => handleMessageSent(messageData, callback)"
      />
    </div>

    <!-- 历史记录模态框 -->
    <div v-if="showHistory" class="history-modal-overlay" @click="closeHistoryModal">
      <div class="history-modal" @click.stop>
        <div class="history-header">
          <h3>与 {{ contact?.username }} 的聊天历史</h3>
          <button @click="closeHistoryModal" class="close-btn">×</button>
        </div>
        
        <!-- 搜索框 -->
        <div class="search-container">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索消息内容..." 
            class="search-input"
          />
          <button 
            v-if="searchQuery" 
            @click="clearSearch" 
            class="clear-search-btn"
            title="清除搜索"
          >
            ×
          </button>
        </div>
        
        <div class="history-content">
          <div v-if="loadingHistory" class="loading">
            <div class="loading-spinner"></div>
            <p>正在加载历史记录...</p>
          </div>
          
          <div v-else-if="filteredHistoryMessages.length === 0 && !searchQuery" class="no-history">
            <p>暂无历史记录</p>
          </div>
          
          <div v-else-if="filteredHistoryMessages.length === 0 && searchQuery" class="no-search-results">
            <p>未找到包含 "{{ searchQuery }}" 的消息</p>
          </div>
          
          <div 
            v-else 
            ref="historyContainer"
            @scroll="handleHistoryScroll"
            class="history-messages"
          >
            <div v-if="loadingHistory && historyMessages.length > 0" class="loading-more">
              <p>加载更多消息...</p>
            </div>
            <div
              v-for="message in filteredHistoryMessages"
              :key="message.id"
              :class="['history-message', parseInt(message.from) === parseInt(currentUser.id) ? 'sent' : 'received']"
            >
              <div class="message-content">
                <!-- 文本消息 -->
                <div v-if="!message.messageType || message.messageType === 'text'" class="message-text">{{ message.content }}</div>
                
                <!-- 图片消息 -->
                <div v-else-if="message.messageType === 'image'" class="message-image">
                  <img 
                    v-if="message.filePath && message.messageType === 'image'" 
                    :src="getImageUrl(message.filePath)" 
                    :alt="message.fileName || '图片'"
                    class="image-content"
                    @error="handleImageError"
                  />
                  <div v-else class="image-placeholder">
                    <span class="image-icon">📷</span>
                    <span class="image-text">{{ message.content }}</span>
                  </div>
                </div>
                
                <div class="message-info">
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                  <span v-if="message.method" class="message-method">
                    {{ message.method === 'P2P' ? 'P2P' : '服务器' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="history-status">
            <span class="status-info">
              已显示 {{ filteredHistoryMessages.length }} / {{ historyPagination.totalCount }} 条消息
              <span v-if="historyPagination.hasMore && !searchQuery">
                · 上滑加载更多
              </span>
              <span v-if="searchQuery">
                · 搜索结果
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 解密提示框 -->
    <div 
      v-if="showDecryptTooltip" 
      class="decrypt-tooltip"
      :style="{
        left: tooltipPosition.x + 'px',
        top: (tooltipPosition.y - 60) + 'px'
      }"
      @click.stop
    >
      <div class="tooltip-content">
        <span class="tooltip-text">尝试进行解密</span>
        <div class="tooltip-buttons">
          <button @click="handleDecryptClick" class="decrypt-btn">解密</button>
          <button @click="handleDecryptCancel" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { hybridStore } from '../store/hybrid-store';
import { getMessagesWithFriend, addMessage } from '@/client_db/database';
import { hybridApi } from '@/api/hybrid-api';
import HybridMessageInput from './HybridMessageInput.vue';

const router = useRouter();

const messagesContainer = ref(null);

// 历史记录相关状态
const showHistory = ref(false);
const loadingHistory = ref(false);
const historyMessages = ref([]);
const filteredHistoryMessages = ref([]);
const searchQuery = ref('');
const historyContainer = ref(null);
const historyPagination = ref({
  offset: 0,
  limit: 50,
  totalCount: 0,
  hasMore: true
});

// 解密提示框相关状态
const showDecryptTooltip = ref(false);
const currentLongPressMessage = ref(null);
const tooltipPosition = ref({ x: 0, y: 0 });

const contact = computed(() => hybridStore.currentContact);
const currentUser = computed(() => hybridStore.user);

const messages = computed(() => {
  if (!contact.value) return [];
  const msgs = hybridStore.getMessages(contact.value.id);
  console.log(`HybridChatWindow computed messages for ${contact.value.id}:`, msgs.length);
  return msgs;
});

function getConnectionStatus() {
  if (!contact.value) {
    return {
      preferredMethod: 'Server',
      p2pStatus: 'disconnected',
      isOnline: false,
      supportsP2P: false
    };
  }
  
  const p2pStatus = hybridStore.getP2PStatus(contact.value.id);
  const isOnline = hybridStore.isUserOnline(contact.value.id);
  
  return {
    preferredMethod: p2pStatus === 'connected' ? 'P2P' : 'Server',
    p2pStatus: p2pStatus,
    isOnline: isOnline,
    supportsP2P: isOnline
  };
}

// 监听联系人变化，加载历史消息并滚动到底部
watch(contact, async (newContact) => {
  if (newContact) {
    await loadHistoryMessages(newContact.id);
    await nextTick();
    scrollToBottom();
  }
});

// 监听消息变化，滚动到底部
watch(messages, async () => {
  await nextTick();
  scrollToBottom();
}, { deep: true });

onMounted(async () => {
  if (contact.value) {
    await loadHistoryMessages(contact.value.id);
  }
  scrollToBottom();
});

async function loadHistoryMessages(friendId) {
  if (!currentUser.value) return;
  try {
    const result = await getMessagesWithFriend(friendId, { limit: 50, offset: 0 });
    hybridStore.setMessages(friendId, result.messages);
    console.log(`已从本地数据库加载与 ${friendId} 的 ${result.messages.length} 条历史消息`);
  } catch (error) {
    console.error('加载历史消息失败:', error);
  }
}

function getConnectionMethod() {
  if (!contact.value?.online) return '';
  
  const p2pStatus = hybridStore.getP2PStatus(contact.value.id);
  return p2pStatus === 'connected' ? '(P2P直连)' : '(服务器转发)';
}

function formatTime(timestamp) {
  // 确保时间戳格式正确
  let dateStr = timestamp;
  
  // 处理不同格式的时间戳
  if (typeof timestamp === 'string') {
    if (timestamp.endsWith('Z')) {
      // UTC时间格式，保持原样
      dateStr = timestamp;
    } else if (timestamp.includes('T') && !timestamp.endsWith('Z')) {
      // ISO格式但没有Z后缀，添加Z表示UTC
      dateStr = timestamp + 'Z';
    } else if (!timestamp.includes('T')) {
      // 简单的时间戳，添加UTC标识
      dateStr = timestamp + 'Z';
    }
  }
  
  const date = new Date(dateStr);
  const now = new Date();
  
  // 检查日期是否有效
  if (isNaN(date.getTime())) {
    console.warn('无效的时间戳:', timestamp);
    return '无效时间';
  }
  
  // 获取今天的日期字符串（本地时区）
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  
  const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const todayDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const yesterdayDate = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());
  
  if (messageDate.getTime() === todayDate.getTime()) {
    // 今天的消息只显示时间
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit'
    });
  } else if (messageDate.getTime() === yesterdayDate.getTime()) {
    // 昨天的消息显示"昨天 时间"
    return '昨天 ' + date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit'
    });
  } else {
    // 其他日期显示完整的月日和时间
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

async function handleMessageSent(messageData, callback) {
  // 在函数开始就定义tempMessage，确保在所有块中都能访问
  let tempMessage = null;

  // 根据连接状态决定发送方式
  const connectionStatus = getConnectionStatus();
  console.log('当前连接状态:', connectionStatus);

  // 创建临时消息对象用于立即显示
  tempMessage = {
    id: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    from: currentUser.value.id,
    to: contact.value.id,
    content: messageData.content,
    timestamp: new Date().toISOString(),
    method: 'Server',
    encrypted: false,
    sending: true
  };
  
  try {
    console.log('开始发送消息:', messageData);
    
    // 处理图片消息
    if (messageData.type === 'image') {
      const result = await handleImageSent(messageData);
      if (callback) callback(result);
      return result;
    }
    
    // 处理隐写术消息
    if (messageData.type === 'steganography') {
      const result = await handleSteganographySent(messageData);
      if (callback) callback(result);
      return result;
    }
    
    // 使用HybridMessaging服务发送消息
    const hybridMessaging = hybridStore.getHybridMessaging();
    if (!hybridMessaging) {
      throw new Error('消息服务未初始化');
    }
    
    // 先创建本地消息对象（立即显示）
    tempMessage = {
      id: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      from: currentUser.value.id,
      to: contact.value.id,
      content: messageData.content,
      timestamp: new Date().toISOString(),
      method: 'Server',
      encrypted: false,
      sending: true
    };
    
    // 立即添加到本地显示
    hybridStore.addMessage(contact.value.id, tempMessage);
    console.log('已添加临时消息到store:', tempMessage);
    
    // 滚动到底部
    await nextTick();
    scrollToBottom();
    
    // 发送消息到服务器
    const result = await hybridMessaging.sendMessage(contact.value.id, messageData.content);
    console.log('消息发送结果:', result);
    
    if (result.success) {
      // 更新消息状态
      const finalMessage = {
        ...tempMessage,
        id: result.id || tempMessage.id,
        method: result.method || 'Server',
        timestamp: result.timestamp || tempMessage.timestamp,
        sending: false
      };
      
      // 更新store中的消息
      const messages = hybridStore.getMessages(contact.value.id);
      const messageIndex = messages.findIndex(m => m.id === tempMessage.id);
      if (messageIndex !== -1) {
        messages[messageIndex] = finalMessage;
      }
      
      // 注意：消息存储到数据库由HybridMessaging服务自动处理，这里不需要重复存储
      
      console.log('消息发送成功，已更新状态');
      const successResult = { success: true, method: finalMessage.method };
      if (callback) callback(successResult);
      return successResult;
    } else {
      // 发送失败，移除临时消息
      const messages = hybridStore.getMessages(contact.value.id);
      const messageIndex = messages.findIndex(m => m.id === tempMessage.id);
      if (messageIndex !== -1) {
        messages.splice(messageIndex, 1);
      }
      console.error('发送消息失败:', result.error || '发送失败');
      const errorResult = { success: false, error: result.error || '发送失败' };
      if (callback) callback(errorResult);
      return errorResult;
    }
  } catch (error) {
    console.error('发送消息失败:', error);
    // 发送失败，移除临时消息（如果存在）
    if (tempMessage) {
      const messages = hybridStore.getMessages(contact.value.id);
      const messageIndex = messages.findIndex(m => m.id === tempMessage.id);
      if (messageIndex !== -1) {
        messages.splice(messageIndex, 1);
      }
    }
    const errorResult = { success: false, error: error.message };
    if (callback) callback(errorResult);
    return errorResult;
  }
}

async function handleImageSent(messageData) {
  // 在函数开始就定义tempMessage，确保在所有块中都能访问
  const tempMessage = {
    id: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    from: currentUser.value.id,
    to: contact.value.id,
    content: messageData.hiddenMessage ? 
      `[隐写图片: ${messageData.originalText || '包含隐藏信息'}]` : 
      `[图片: ${messageData.fileName}]`,
    messageType: 'image',
    fileName: messageData.fileName,
    hiddenMessage: messageData.hiddenMessage || false,
    originalText: messageData.originalText || null,
    timestamp: new Date().toISOString(),
    method: 'Server',
    encrypted: false,
    sending: true
  };
  
  try {
    console.log('开始发送图片:', messageData);
    
    // 立即添加到本地显示
    hybridStore.addMessage(contact.value.id, tempMessage);
    console.log('已添加临时图片消息到store:', tempMessage);
    
    // 滚动到底部
    await nextTick();
    scrollToBottom();
    
    // 上传图片到服务器
    const response = await hybridApi.uploadImage(messageData.file);
    const result = response.data;
    console.log('图片上传结果:', result);
    
    // 后端直接返回Message对象，不是包装在success字段中
    if (result && result.id) {
      // 更新消息状态
      const finalMessage = {
        ...tempMessage,
        id: result.id || tempMessage.id,
        content: result.content,
        filePath: result.filePath,
        fileName: result.fileName,
        messageType: result.messageType,
        hiddenMessage: result.hiddenMessage || messageData.hiddenMessage || false,
        originalText: messageData.originalText || null,
        timestamp: result.timestamp || tempMessage.timestamp,
        sending: false
      };
      
      // 更新store中的消息
      const messages = hybridStore.getMessages(contact.value.id);
      const messageIndex = messages.findIndex(m => m.id === tempMessage.id);
      if (messageIndex !== -1) {
        messages[messageIndex] = finalMessage;
      }
      
      // 保存图片消息到本地数据库
      try {
        await addMessage({
          from: finalMessage.from,
          to: finalMessage.to,
          content: finalMessage.content,
          messageType: finalMessage.messageType,
          filePath: finalMessage.filePath,
          fileName: finalMessage.fileName,
          hiddenMessage: finalMessage.hiddenMessage || false,
          originalText: finalMessage.originalText || null,
          method: finalMessage.method,
          encrypted: finalMessage.encrypted || false,
          timestamp: finalMessage.timestamp
        });
        console.log('图片消息已保存到本地数据库');
      } catch (dbError) {
        console.warn('保存图片消息到本地数据库失败:', dbError);
      }
      
      console.log('图片消息发送成功，已更新状态');
      return { success: true, method: finalMessage.method };
    } else {
      // 发送失败，移除临时消息
      const messages = hybridStore.getMessages(contact.value.id);
      const messageIndex = messages.findIndex(m => m.id === tempMessage.id);
      if (messageIndex !== -1) {
        messages.splice(messageIndex, 1);
      }
      console.error('发送图片失败: 响应格式不正确', result);
      return { success: false, error: '发送失败：响应格式不正确' };
    }
  } catch (error) {
    console.error('发送图片失败:', error);
    // 发送失败，移除临时消息
    const messages = hybridStore.getMessages(contact.value.id);
    const messageIndex = messages.findIndex(m => m.id === tempMessage.id);
    if (messageIndex !== -1) {
      messages.splice(messageIndex, 1);
    }
    return { success: false, error: error.message };
  }
}

async function handleSteganographySent(messageData) {
  let tempMessage = null;
  
  // 创建临时消息对象用于立即显示
  tempMessage = {
    id: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    from: currentUser.value.id,
    to: contact.value.id,
    content: messageData.content,
    imageUrl: messageData.imageUrl,
    messageType: 'steganography',
    fileName: messageData.fileName,
    timestamp: new Date().toISOString(),
    method: 'Server',
    encrypted: false,
    sending: true
  };
  
  try {
    console.log('开始发送隐写术消息:', messageData);
    
    // 立即添加到本地显示
    hybridStore.addMessage(contact.value.id, tempMessage);
    console.log('已添加临时隐写术消息到store:', tempMessage);
    
    // 滚动到底部
    await nextTick();
    scrollToBottom();
    
    // 通过HybridMessaging发送隐写术消息给接收方
    const result = await hybridStore.hybridMessaging.sendMessage({
      to: contact.value.id,
      content: messageData.content,
      messageType: 'steganography',
      imageUrl: messageData.imageUrl,
      fileName: messageData.fileName
    });
    
    if (result && result.success) {
      // 发送成功，更新消息状态
      const finalMessage = {
        ...tempMessage,
        sending: false,
        method: result.method || 'Server'
      };
      
      // 更新store中的消息
      const messages = hybridStore.getMessages(contact.value.id);
      const messageIndex = messages.findIndex(m => m.id === tempMessage.id);
      if (messageIndex !== -1) {
        messages[messageIndex] = finalMessage;
      }
    } else {
      // 发送失败，移除临时消息
      const messages = hybridStore.getMessages(contact.value.id);
      const messageIndex = messages.findIndex(m => m.id === tempMessage.id);
      if (messageIndex !== -1) {
        messages.splice(messageIndex, 1);
      }
      console.error('发送隐写术消息失败:', result?.error || '未知错误');
      return { success: false, error: result?.error || '发送失败' };
    }
    
    const finalMessage = {
      ...tempMessage,
      sending: false,
      method: result.method || 'Server'
    };
    
    // 保存隐写术消息到本地数据库
    try {
      await addMessage({
        from: finalMessage.from,
        to: finalMessage.to,
        content: finalMessage.content,
        messageType: finalMessage.messageType,
        imageUrl: finalMessage.imageUrl,
        fileName: finalMessage.fileName,
        method: finalMessage.method,
        encrypted: finalMessage.encrypted || false,
        timestamp: finalMessage.timestamp
      });
      console.log('隐写术消息已保存到本地数据库');
    } catch (dbError) {
      console.warn('保存隐写术消息到本地数据库失败:', dbError);
    }
    
    console.log('隐写术消息发送成功，已更新状态');
    return { success: true, method: finalMessage.method };
  } catch (error) {
    console.error('发送隐写术消息失败:', error);
    // 发送失败，移除临时消息
    const messages = hybridStore.getMessages(contact.value.id);
    const messageIndex = messages.findIndex(m => m.id === tempMessage.id);
    if (messageIndex !== -1) {
      messages.splice(messageIndex, 1);
    }
    return { success: false, error: error.message };
  }
}

function startVoiceCall() {
  if (!contact.value || !contact.value.online) {
    alert('联系人不在线，无法发起语音通话');
    return;
  }
  
  // 跳转到语音通话页面
  router.push(`/voice-call/${contact.value.id}`);
}

// 历史记录相关方法
function showHistoryModal() {
  showHistory.value = true;
  resetHistoryState();
  loadLocalHistory();
}

function closeHistoryModal() {
  showHistory.value = false;
  resetHistoryState();
}

function resetHistoryState() {
  historyMessages.value = [];
  filteredHistoryMessages.value = [];
  searchQuery.value = '';
  historyPagination.value = {
    offset: 0,
    limit: 50,
    totalCount: 0,
    hasMore: true
  };
}

async function loadLocalHistory(append = false) {
  if (!contact.value || !currentUser.value) return;
  
  loadingHistory.value = true;
  try {
    const options = {
      limit: historyPagination.value.limit,
      offset: append ? historyPagination.value.offset : 0,
      search: searchQuery.value || null
    };
    
    const result = await getMessagesWithFriend(contact.value.id, options);
    console.log('本地历史记录响应:', result);
    
    if (append) {
      // 追加到现有消息
      historyMessages.value = [...historyMessages.value, ...result.messages];
    } else {
      // 替换现有消息
      historyMessages.value = result.messages;
    }
    
    // 更新分页信息
    historyPagination.value = {
      offset: result.offset + result.count,
      limit: result.limit,
      totalCount: result.totalCount,
      hasMore: result.hasMore
    };
    
    // 更新过滤后的消息列表
    filterMessages();
    
  } catch (error) {
    console.error('加载本地历史记录失败:', error);
    if (!append) {
      historyMessages.value = [];
      filteredHistoryMessages.value = [];
    }
  } finally {
    loadingHistory.value = false;
  }
}

// 过滤消息函数（用于前端实时过滤）
function filterMessages() {
  if (!searchQuery.value.trim()) {
    // 如果没有搜索词，显示所有消息
    filteredHistoryMessages.value = historyMessages.value;
  } else {
    // 根据搜索词过滤消息，支持中文搜索
    const query = searchQuery.value.toLowerCase().trim();
    filteredHistoryMessages.value = historyMessages.value.filter(message => {
      // 搜索消息内容
      const content = message.content ? message.content.toLowerCase() : '';
      return content.includes(query);
    });
  }
}

// 清除搜索
function clearSearch() {
  searchQuery.value = '';
  // 清除搜索时重新加载所有历史记录
  loadLocalHistory();
}

// 执行搜索（数据库层面搜索）
async function performSearch() {
  if (!contact.value || !currentUser.value) return;
  
  loadingHistory.value = true;
  try {
    const options = {
      limit: 200, // 搜索时加载更多消息
      offset: 0,
      search: searchQuery.value.trim() || null
    };
    
    const result = await getMessagesWithFriend(contact.value.id, options);
    console.log('搜索历史记录响应:', result);
    
    // 替换现有消息
    historyMessages.value = result.messages;
    
    // 更新分页信息
    historyPagination.value = {
      offset: result.offset + result.count,
      limit: result.limit,
      totalCount: result.totalCount,
      hasMore: result.hasMore && !searchQuery.value.trim() // 搜索模式下不支持分页加载
    };
    
    // 直接设置过滤后的消息（数据库已经过滤过了）
    filteredHistoryMessages.value = historyMessages.value;
    
  } catch (error) {
    console.error('搜索历史记录失败:', error);
    historyMessages.value = [];
    filteredHistoryMessages.value = [];
  } finally {
    loadingHistory.value = false;
  }
}

// 监听搜索词变化
watch(searchQuery, async (newQuery, oldQuery) => {
  // 防止重复触发
  if (newQuery === oldQuery) return;
  
  // 使用防抖，避免频繁搜索
  clearTimeout(searchQuery._debounceTimer);
  searchQuery._debounceTimer = setTimeout(async () => {
    if (newQuery.trim()) {
      // 有搜索词时，执行数据库搜索
      await performSearch();
    } else {
      // 没有搜索词时，重新加载所有历史记录
      await loadLocalHistory();
    }
  }, 300); // 300ms防抖
});

// 上滑加载更多
function handleHistoryScroll() {
  // 搜索模式下不支持分页加载
  if (searchQuery.value.trim()) return;
  
  if (!historyContainer.value || loadingHistory.value || !historyPagination.value.hasMore) return;
  
  const { scrollTop, scrollHeight, clientHeight } = historyContainer.value;
  
  // 当滚动到顶部附近时加载更多
  if (scrollTop < 100) {
    loadLocalHistory(true);
  }
}

// 处理图片加载错误
function handleImageError(event) {
  console.error('图片加载失败:', event.target.src);
  event.target.style.display = 'none';
}

// 右键点击事件处理
function handleImageRightClick(message, event) {
  if (!message.hiddenMessage || message.extractedText) return;
  
  event.preventDefault(); // 阻止默认右键菜单
  
  currentLongPressMessage.value = message;
  
  // 设置提示框位置
  tooltipPosition.value = {
    x: event.clientX,
    y: event.clientY
  };
  
  // 直接显示解密提示框
  showDecryptTooltip.value = true;
}

// 这些长按相关的函数已不再需要，因为改为右键点击直接显示

// 点击解密按钮
function handleDecryptClick() {
  if (currentLongPressMessage.value) {
    extractHiddenMessage(currentLongPressMessage.value);
    showDecryptTooltip.value = false;
    currentLongPressMessage.value = null;
  }
}

// 取消解密
function handleDecryptCancel() {
  showDecryptTooltip.value = false;
  currentLongPressMessage.value = null;
}

// 点击其他区域隐藏提示框
function handleDocumentClick(event) {
  if (showDecryptTooltip.value) {
    const tooltip = document.querySelector('.decrypt-tooltip');
    if (tooltip && !tooltip.contains(event.target)) {
      showDecryptTooltip.value = false;
      currentLongPressMessage.value = null;
    }
  }
}

// 监听文档点击事件
watch(showDecryptTooltip, (newValue) => {
  if (newValue) {
    // 延迟添加点击监听，避免立即触发
    setTimeout(() => {
      document.addEventListener('click', handleDocumentClick);
    }, 100);
  } else {
    document.removeEventListener('click', handleDocumentClick);
  }
});

// 组件卸载时清理事件监听
onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick);
});

// 提取隐写术隐藏信息
async function extractHiddenMessage(message) {
  if (message.extractedText) {
    // 如果已经提取过，直接返回
    return;
  }
  
  if (!message.filePath) {
    console.error('无法提取隐藏信息：缺少图片文件路径');
    return;
  }
  
  try {
    // 获取图片文件
    const imageUrl = getImageUrl(message.filePath);
    const response = await fetch(imageUrl);
    
    if (!response.ok) {
      throw new Error('获取图片失败');
    }
    
    const blob = await response.blob();
    
    // 创建FormData用于发送到隐写术提取API
    const formData = new FormData();
    formData.append('image', blob, message.fileName || 'steganography.png');
    formData.append('password', 'default_password'); // 使用默认密码
    
    // 调用隐写术提取API
    const extractResponse = await fetch('/api/steganography/extract', {
      method: 'POST',
      body: formData
    });
    
    if (!extractResponse.ok) {
      throw new Error('提取隐藏信息失败');
    }
    
    const result = await extractResponse.json();
    
    if (result.secret_message) {
      // 更新消息对象，添加提取的文本
      message.extractedText = result.secret_message;
      console.log('成功提取隐藏信息:', result.secret_message);
    } else {
      throw new Error('未找到隐藏信息');
    }
    
  } catch (error) {
     console.error('提取隐藏信息失败:', error);
     // 可以在这里添加用户提示
     alert('提取隐藏信息失败：' + error.message);
   }
 }

// 修复图片路径处理 - 修正API路径
function getImageUrl(filePath) {
  if (!filePath) {
    console.warn('getImageUrl: filePath为空');
    return '';
  }
  
  // 处理新格式：user_id/filename 或旧格式：filename
  let imageParam;
  if (filePath.includes('/')) {
    // 新格式：包含用户ID的路径，直接使用
    imageParam = filePath;
  } else {
    // 旧格式：只有文件名，兼容处理
    imageParam = filePath;
  }
  
  // 使用完整的后端URL：通过upload路由的images端点访问图片
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
  const finalUrl = `${API_BASE_URL}/images/${imageParam}?t=${Date.now()}`;
  
  return finalUrl;
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

.action-buttons {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.history-btn,
.voice-call-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-btn {
  background: #007bff;
}

.history-btn:hover {
  background: #0056b3;
  transform: scale(1.1);
}

.voice-call-btn {
  background: #4caf50;
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

.sending-indicator {
  color: #ffc107;
  font-size: 0.625rem;
  font-weight: 500;
}

.message-image {
  margin-bottom: 0.5rem;
}

.image-content {
  max-width: 200px;
  max-height: 200px;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: transform 0.2s;
}

.image-content:hover {
  transform: scale(1.05);
}

.image-placeholder {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 0.5rem;
  color: #666;
}

.image-icon {
  font-size: 1.5rem;
}

.image-text {
  font-size: 0.875rem;
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

/* 历史记录模态框样式 */
.history-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.history-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
  border-radius: 12px 12px 0 0;
}

.history-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #e9ecef;
  color: #333;
}

.history-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.search-container {
  position: relative;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
  background: #fafafa;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.2s ease;
}

.search-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.clear-search-btn {
  position: absolute;
  right: 2rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #666;
  cursor: pointer;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.clear-search-btn:hover {
  background: #e9ecef;
  color: #333;
}

.no-history,
.no-search-results {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #666;
  font-style: italic;
}

.history-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  max-height: 400px;
}

.history-message {
  margin-bottom: 1rem;
  display: flex;
}

.history-message.sent {
  justify-content: flex-end;
}

.history-message.received {
  justify-content: flex-start;
}

.history-message .message-content {
  max-width: 70%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  background: #f1f3f4;
  position: relative;
}

.history-message.sent .message-content {
  background: #007bff;
  color: white;
}

.history-message .message-text {
  margin-bottom: 0.25rem;
  word-wrap: break-word;
}

.history-message .message-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 0.25rem;
}

.history-status {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 15px;
  padding: 10px;
  border-top: 1px solid #e0e0e0;
}

.status-info {
  font-size: 14px;
  color: #666;
  text-align: center;
}

.loading-more {
  text-align: center;
  padding: 10px;
  color: #666;
  font-size: 14px;
  border-bottom: 1px solid #e0e0e0;
}

.loading-more p {
  margin: 0;
}

/* 解密提示框样式 */
.decrypt-tooltip {
  position: fixed;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.9);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  animation: fadeIn 0.3s ease-out;
  pointer-events: auto;
  min-width: 160px;
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.tooltip-text {
  color: white;
  font-size: 14px;
  white-space: nowrap;
  margin-bottom: 4px;
}

.tooltip-buttons {
  display: flex;
  gap: 8px;
}

.decrypt-btn, .cancel-btn {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 60px;
  user-select: none;
}

.decrypt-btn {
  background: #007bff;
  color: white;
}

.decrypt-btn:hover {
  background: #0056b3;
}

.cancel-btn {
  background: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background: #545b62;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 隐写术消息样式 */
.message-steganography {
  position: relative;
  max-width: 300px;
  border: 2px solid #007bff;
  border-radius: 12px;
  padding: 8px;
  background: linear-gradient(135deg, rgba(0, 123, 255, 0.1), rgba(0, 123, 255, 0.05));
}

.steganography-content {
  width: 100%;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.steganography-content:hover {
  transform: scale(1.02);
}

.steganography-placeholder {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: #f0f0f0;
  border-radius: 8px;
  color: #666;
}

.steganography-icon {
  font-size: 1.5rem;
}

.steganography-text {
  font-style: italic;
}

.steganography-hint {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(0, 123, 255, 0.1);
  border-radius: 6px;
  font-size: 0.85rem;
  color: #007bff;
}

.hint-icon {
  font-size: 1rem;
}

.hint-text {
  font-weight: 500;
}

.extracted-message {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(40, 167, 69, 0.1);
  border: 1px solid rgba(40, 167, 69, 0.3);
  border-radius: 8px;
}

.extracted-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #28a745;
  font-weight: 600;
}

.extracted-icon {
  font-size: 1rem;
}

.extracted-label {
  font-weight: 600;
}

.extracted-content {
  padding: 0.5rem;
  background: white;
  border-radius: 6px;
  border: 1px solid rgba(40, 167, 69, 0.2);
  font-size: 0.9rem;
  line-height: 1.4;
  color: #333;
  word-wrap: break-word;
}
</style>