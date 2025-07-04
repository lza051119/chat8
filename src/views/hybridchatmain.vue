<template>
  <div class="hybrid-chat-main">
    <!-- 顶部导航栏 -->
    <div class="top-navbar">
      <div class="nav-left">
        <h1 class="app-title">安全即时通信</h1>
        <div class="architecture-indicator">
          <span class="arch-badge">混合架构</span>
          <span class="p2p-status">
            P2P: {{ connectionStats.p2pConnections }}/{{ totalOnlineContacts }}
          </span>
        </div>
      </div>
      
      <div class="nav-center">
        <!-- 连接方式切换提示 -->
        <div v-if="showMethodSwitchHint" class="method-switch-hint">
          <span class="hint-icon">🔄</span>
          <span>智能切换连接方式中...</span>
        </div>
      </div>
      
      <div class="nav-right">
        <div class="user-info">
          <span class="username">{{ user?.username }}</span>
          <div class="status-indicator online"></div>
        </div>
        <button @click="showFriendRequestModal = true" class="friend-request-btn" :class="{ 'has-requests': pendingRequestsCount > 0 }">
          📬
          <span v-if="pendingRequestsCount > 0" class="request-badge">{{ pendingRequestsCount }}</span>
        </button>
        <button @click="showUserProfile = true" class="profile-btn" title="个人信息">
          👤
        </button>
        <button @click="showStatsModal = true" class="stats-btn">📊</button>
        <button @click="logout" class="logout-btn">退出</button>
      </div>
    </div>

    <div class="chat-layout">
      <!-- 左侧联系人列表 -->
      <div class="contacts-sidebar">
        <HybridContactList 
          @contact-selected="handleContactSelected"
          @show-friend-profile="showFriendProfileInfo"
          ref="contactList"
        />
      </div>

      <!-- 右侧聊天区域 -->
      <div class="chat-area">
        <div v-if="selectedContact" class="chat-content">
          <HybridChatWindow 
            :contact="selectedContact"
            :key="selectedContact.id"
          />
        </div>
        
        <!-- 未选择联系人时的占位 -->
        <div v-else class="empty-chat">
          <div class="empty-content">
            <div class="empty-icon">💬</div>
            <h3>选择一个联系人开始聊天</h3>
            <p>支持P2P直连和服务器转发两种传输方式</p>
            <div class="feature-list">
              <div class="feature-item">
                <span class="feature-icon">🔗</span>
                <span>在线时自动P2P直连</span>
              </div>
              <div class="feature-item">
                <span class="feature-icon">📡</span>
                <span>离线时服务器转发</span>
              </div>
              <div class="feature-item">
                <span class="feature-icon">⚡</span>
                <span>智能切换传输方式</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计模态框 -->
    <div v-if="showStatsModal" class="modal-overlay" @click="showStatsModal = false">
      <div class="stats-modal" @click.stop>
        <div class="modal-header">
          <h3>连接与消息统计</h3>
          <button @click="showStatsModal = false" class="close-btn">×</button>
        </div>
        
        <div class="modal-content">
          <!-- 连接统计 -->
          <div class="stats-section">
            <h4>连接统计</h4>
            <div class="stats-grid">
              <div class="stat-card p2p">
                <div class="stat-icon">🔗</div>
                <div class="stat-info">
                  <div class="stat-value">{{ connectionStats.p2pConnections }}</div>
                  <div class="stat-label">P2P连接</div>
                </div>
              </div>
              
              <div class="stat-card server">
                <div class="stat-icon">📡</div>
                <div class="stat-info">
                  <div class="stat-value">{{ connectionStats.serverConnections }}</div>
                  <div class="stat-label">服务器转发</div>
                </div>
              </div>
              
              <div class="stat-card ratio">
                <div class="stat-icon">📈</div>
                <div class="stat-info">
                  <div class="stat-value">{{ connectionStats.p2pRatio }}%</div>
                  <div class="stat-label">P2P比例</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 消息统计 -->
          <div class="stats-section">
            <h4>消息统计</h4>
            <div class="message-stats">
              <div class="message-row">
                <span class="message-label">发送消息:</span>
                <div class="message-breakdown">
                  <span class="message-total">总计 {{ messageStats.totalSent }}</span>
                  <span class="message-p2p">P2P {{ messageStats.p2pSent }}</span>
                  <span class="message-server">服务器 {{ messageStats.serverSent }}</span>
                </div>
              </div>
              
              <div class="message-row">
                <span class="message-label">接收消息:</span>
                <div class="message-breakdown">
                  <span class="message-total">总计 {{ messageStats.totalReceived }}</span>
                  <span class="message-p2p">P2P {{ messageStats.p2pReceived }}</span>
                  <span class="message-server">服务器 {{ messageStats.serverReceived }}</span>
                </div>
              </div>
            </div>

            <!-- 效率比较 -->
            <div class="efficiency-chart">
              <h5>传输效率对比</h5>
              <div class="chart-bar">
                <div class="bar-label">P2P传输</div>
                <div class="bar-container">
                  <div 
                    class="bar-fill p2p" 
                    :style="{ width: p2pEfficiency + '%' }"
                  ></div>
                </div>
                <div class="bar-value">{{ p2pEfficiency }}%</div>
              </div>
              
              <div class="chart-bar">
                <div class="bar-label">服务器转发</div>
                <div class="bar-container">
                  <div 
                    class="bar-fill server" 
                    :style="{ width: serverEfficiency + '%' }"
                  ></div>
                </div>
                <div class="bar-value">{{ serverEfficiency }}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 好友申请模态框 -->
    <FriendRequestModal 
      :isVisible="showFriendRequestModal"
      @close="showFriendRequestModal = false"
      @request-handled="handleFriendRequestHandled"
    />

    <!-- 连接状态悬浮通知 -->
    <div v-if="connectionNotification" class="connection-notification">
      <div :class="['notification', connectionNotification.type]">
        <span class="notification-icon">{{ connectionNotification.icon }}</span>
        <span class="notification-text">{{ connectionNotification.message }}</span>
      </div>
    </div>

    <!-- 来电通知模态框 -->
    <div v-if="incomingCall" class="modal-overlay incoming-call-overlay">
      <div class="incoming-call-modal">
        <div class="caller-info">
          <div class="caller-avatar">
            <img v-if="incomingCall.caller.avatar" :src="incomingCall.caller.avatar" :alt="incomingCall.caller.username" />
            <div v-else class="avatar-placeholder">{{ incomingCall.caller.username[0].toUpperCase() }}</div>
          </div>
          <h3 class="caller-name">{{ incomingCall.caller.username }}</h3>
          <p class="call-type">正在呼叫您...</p>
        </div>
        <div class="call-actions">
          <button @click="rejectCall" class="action-btn reject-btn">拒接</button>
          <button @click="acceptCall" class="action-btn accept-btn">接听</button>
        </div>
      </div>
    </div>

    <!-- 用户个人信息面板 -->
    <UserProfile 
      v-if="showUserProfile || showFriendProfile" 
      :userId="friendProfileUserId"
      @close="closeProfile"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { hybridStore } from '../store/hybrid-store';
import HybridContactList from '../components/hybridcontactlist.vue';
import HybridChatWindow from '../components/hybridchatwindow.vue';
import FriendRequestModal from '../components/FriendRequestModal.vue';
import UserProfile from '../components/UserProfile.vue';
import HybridMessaging from '../services/hybridmessaging';
import { hybridApi } from '../api/hybrid-api.js';

const router = useRouter();

const selectedContact = ref(null);
const showStatsModal = ref(false);
const showFriendRequestModal = ref(false);
const showUserProfile = ref(false);
const showFriendProfile = ref(false);
const friendProfileUserId = ref(null);
const showMethodSwitchHint = ref(false);
const connectionNotification = ref(null);
const contactList = ref(null);
const messaging = ref(null);
const pendingRequestsCount = ref(0);
const incomingCall = ref(null);

// 计算属性
const user = computed(() => hybridStore.user);
const connectionStats = computed(() => hybridStore.getConnectionStats());
const messageStats = computed(() => hybridStore.messageStats);

const totalOnlineContacts = computed(() => {
  return hybridStore.contacts.filter(contact => 
    hybridStore.onlineUsers.has(contact.id)
  ).length;
});

const p2pEfficiency = computed(() => {
  const total = messageStats.value.totalSent + messageStats.value.totalReceived;
  const p2pTotal = messageStats.value.p2pSent + messageStats.value.p2pReceived;
  return total > 0 ? Math.round((p2pTotal / total) * 100) : 0;
});

const serverEfficiency = computed(() => {
  return 100 - p2pEfficiency.value;
});

// 生命周期
onMounted(async () => {
  // 首先从本地存储加载用户信息
  hybridStore.loadUserFromStorage();
  
  // 等待下一个 tick 确保响应式状态已更新
  await nextTick();
  
  // 检查是否是开发模式
  const isDevMode = window.location.pathname.startsWith('/dev/');
  
  if (!isDevMode) {
    // 只在非开发模式下检查登录状态
    if (!hybridStore.isLoggedIn) {
      console.warn('用户未登录，跳转到登录页面');
      router.push('/login');
      return;
    }
  }

  // 使用重试机制确保用户信息加载
  const maxRetries = 3;
  let retryCount = 0;
  
  while (retryCount < maxRetries) {
    if (hybridStore.user && hybridStore.user.id) {
      console.log('用户信息加载成功，开始初始化消息系统');
      await initializeMessaging();
      break;
    }
    
    retryCount++;
    console.warn(`用户信息未加载，重试 ${retryCount}/${maxRetries}`);
    
    if (retryCount < maxRetries) {
      // 等待一段时间后重试
      await new Promise(resolve => setTimeout(resolve, 200));
      // 重新加载用户信息
      hybridStore.loadUserFromStorage();
      await nextTick();
    } else {
      // 最后一次重试失败，跳转到登录页面
      console.error('用户信息加载失败，跳转到登录页面');
      router.push('/login');
      return;
    }
  }
  
  // 设置连接状态监听
  setupConnectionNotifications();
  
  // 加载好友申请数量
  loadPendingRequestsCount();
});

onUnmounted(() => {
  try {
    if (messaging.value && typeof messaging.value.cleanup === 'function') {
      messaging.value.cleanup();
    }
    
    // 清理所有引用
    messaging.value = null;
    selectedContact.value = null;
    connectionNotification.value = null;
    
    // 清理定时器
    if (window.hybridChatTimers) {
      window.hybridChatTimers.forEach(timer => clearTimeout(timer));
      window.hybridChatTimers = [];
    }
  } catch (error) {
    console.error('组件卸载时出错:', error);
  }
});

// 方法
function handleIncomingCall(callInfo) {
  console.log('[来电处理] 收到来电信息:', callInfo);
  const caller = hybridStore.getContact(callInfo.fromUserId);
  console.log('[来电处理] 查找到的联系人信息:', caller);
  console.log('[来电处理] 所有联系人列表:', hybridStore.getContacts());
  if (caller) {
    incomingCall.value = {
      ...callInfo,
      caller: caller
    };
    console.log('[来电处理] 来电信息已设置，将显示来电界面:', incomingCall.value);
  } else {
    console.warn(`收到未知联系人 ${callInfo.fromUserId} 的来电`);
    console.warn('[来电处理] 尝试通过用户ID查找联系人失败，fromUserId类型:', typeof callInfo.fromUserId);
  }
}

async function acceptCall() {
  if (incomingCall.value) {
    const contactId = incomingCall.value.fromUserId;
    const callInfo = incomingCall.value;
    
    try {
      console.log('[接听通话] 开始接听来自用户', contactId, '的通话');
      
      // 先设置通话信息到store
      hybridStore.setCurrentCall(callInfo);
      
      // 直接在这里接听通话，避免在VoiceCall页面重复处理
      const result = await messaging.value.acceptVoiceCall(contactId, callInfo.offer);
      console.log('[接听通话] 通话接听成功:', result);
      
      // 跳转到通话页面
      router.push(`/voice-call/${contactId}`);
      
      // 延迟清理来电状态，确保VoiceCall页面能够正确识别通话状态
      setTimeout(() => {
        incomingCall.value = null;
        console.log('[接听通话] 延迟清理来电状态完成');
      }, 1000);
      
    } catch (error) {
      console.error('[接听通话] 接听失败:', error);
      
      // 接听失败时清理状态
      incomingCall.value = null;
      hybridStore.clearCurrentCallInfo();
      
      // 显示错误提示
      showNotification('接听通话失败', 'error', '❌');
    }
  }
}

async function rejectCall() {
  if (incomingCall.value) {
    await messaging.value.rejectVoiceCall(incomingCall.value.fromUserId);
    incomingCall.value = null;
  }
}

// 关闭个人信息面板
function closeProfile() {
  showUserProfile.value = false;
  showFriendProfile.value = false;
  friendProfileUserId.value = null;
}

// 显示好友个人信息
function showFriendProfileInfo(userId) {
      // 确保userId是字符串类型
      userId = String(userId)
  friendProfileUserId.value = userId;
  showFriendProfile.value = true;
}

// 预加载有阅后即焚消息的对话
async function preloadBurnAfterMessages() {
  try {
    console.log('🔍 开始预加载阅后即焚消息...');
    const { getMessagesWithFriend } = await import('../client_db/database.js');
    const contacts = hybridStore.getContacts();
    
    let totalLoadedConversations = 0;
    let totalBurnAfterMessages = 0;
    
    // 遍历所有联系人，检查是否有阅后即焚消息
    for (const contact of contacts) {
      try {
        const result = await getMessagesWithFriend(contact.id, { limit: 50, offset: 0 });
        
        // 检查是否有未过期的阅后即焚消息
        const currentTime = Math.floor(Date.now() / 1000);
        const burnAfterMessages = result.messages.filter(msg => 
          msg.destroy_after && msg.destroy_after > currentTime
        );
        
        if (burnAfterMessages.length > 0) {
          // 如果有阅后即焚消息，加载到store中
          hybridStore.setMessages(contact.id, result.messages);
          totalLoadedConversations++;
          totalBurnAfterMessages += burnAfterMessages.length;
          console.log(`📥 预加载联系人 ${contact.id} 的对话，包含 ${burnAfterMessages.length} 条阅后即焚消息`);
        }
      } catch (error) {
        console.warn(`⚠️ 预加载联系人 ${contact.id} 的消息失败:`, error);
      }
    }
    
    if (totalLoadedConversations > 0) {
      console.log(`✅ 预加载完成：${totalLoadedConversations} 个对话，${totalBurnAfterMessages} 条阅后即焚消息`);
      // 确保清理定时器正在运行
      hybridStore.startBurnAfterCleanupTimer();
    } else {
      console.log('ℹ️ 没有发现需要预加载的阅后即焚消息');
    }
  } catch (error) {
    console.error('❌ 预加载阅后即焚消息失败:', error);
  }
}

async function initializeMessaging() {
  try {
    // 首先重新初始化数据库（用户登录后才有token）
    console.log('🔄 用户登录后重新初始化本地数据库...');
    try {
      const { initDatabase } = await import('../client_db/database.js');
      await initDatabase();
      console.log('✅ 本地数据库重新初始化成功');
    } catch (dbError) {
      console.warn('⚠️ 本地数据库初始化失败，但继续启动消息系统:', dbError);
    }
    
    // 使用hybrid-store的初始化方法
    const success = await hybridStore.initializeHybridMessaging();
    
    if (success) {
      messaging.value = hybridStore.getHybridMessaging();
      
      console.log('[状态同步] 混合消息系统初始化成功，WebSocket已自动发送在线状态');
      
      // 开始定期更新在线状态
      startStatusHeartbeat();
      
      // 加载联系人在线状态
      await updateContactsOnlineStatus();
      
      // 预加载所有有阅后即焚消息的对话，确保刷新后功能正常
      await preloadBurnAfterMessages();

      // 设置来电处理
      messaging.value.onVoiceCallReceived = handleIncomingCall;
      console.log('[来电处理] onVoiceCallReceived 回调已设置');
      
      console.log('混合消息系统初始化完成，在线状态已同步给好友');
    } else {
      throw new Error('HybridMessaging初始化失败');
    }
  } catch (error) {
    console.error('初始化消息系统失败:', error);
    showNotification('初始化失败', 'error', '❌');
  }
}

function setupConnectionNotifications() {
  // 监听P2P连接状态变化
  // 这里可以添加更多的连接状态监听逻辑
}

async function handleContactSelected(contact) {
  selectedContact.value = contact;
  hybridStore.setCurrentContact(contact);
  
  // 预连接功能已移除，直接选择联系人即可
  // P2P连接将在发送消息时自动建立
  console.log(`[聊天窗口] 已选择联系人: ${contact.username}`);
}

function handleUserStatusChange(userId, status) {
  hybridStore.updateOnlineStatus(userId, status === 'online');
  
  // 显示状态变化通知
  const contact = hybridStore.contacts.find(c => c.id === userId);
  if (contact) {
    const statusText = status === 'online' ? '上线' : '离线';
    showNotification(
      `${contact.username} ${statusText}`,
      status === 'online' ? 'success' : 'info',
      status === 'online' ? '🟢' : '🔴'
    );
  }
}

// 开始状态心跳
function startStatusHeartbeat() {
  // 每30秒发送一次心跳
  const heartbeatInterval = setInterval(async () => {
    try {
      await hybridApi.heartbeat();
      // 同时更新联系人在线状态
      await updateContactsOnlineStatus();
    } catch (error) {
      console.error('心跳失败:', error);
    }
  }, 30000);
  
  // 保存定时器引用以便清理
  if (!window.hybridChatTimers) {
    window.hybridChatTimers = [];
  }
  window.hybridChatTimers.push(heartbeatInterval);
}

// 更新联系人在线状态
async function updateContactsOnlineStatus() {
  try {
    const response = await hybridApi.getContactsStatus();
    if (response.data && response.data.success) {
      const statusList = response.data.data || [];
      
      statusList.forEach(statusInfo => {
        const isOnline = statusInfo.status === 'online';
        hybridStore.updateOnlineStatus(parseInt(statusInfo.userId), isOnline);
      });
    }
  } catch (error) {
    console.error('更新联系人在线状态失败:', error);
  }
}



function showNotification(message, type, icon) {
  connectionNotification.value = {
    message,
    type,
    icon
  };
  
  // 管理定时器，避免内存泄漏
  if (!window.hybridChatTimers) {
    window.hybridChatTimers = [];
  }
  
  const timer = setTimeout(() => {
    if (connectionNotification.value) {
      connectionNotification.value = null;
    }
  }, 3000);
  
  window.hybridChatTimers.push(timer);
}

async function loadPendingRequestsCount() {
  try {
    const response = await hybridApi.getFriendRequests('received');
    if (response.data && response.data.success) {
      const requests = response.data.data || [];
      pendingRequestsCount.value = requests.filter(req => req.status === 'pending').length;
    }
  } catch (error) {
    console.error('加载好友申请数量失败:', error);
  }
}

async function handleFriendRequestHandled(data) {
  // 更新好友申请数量
  loadPendingRequestsCount();
  
  // 如果同意了申请，刷新联系人列表
  if (data.action === 'accept') {
    if (contactList.value && contactList.value.refresh) {
      contactList.value.refresh();
    } else {
      // 直接重新加载联系人数据
      try {
        const response = await hybridApi.getContacts();
        const contactsData = response.data.data.items || [];
        hybridStore.setContacts(contactsData);
      } catch (error) {
        console.error('刷新联系人列表失败:', error);
      }
    }
  }
  
  // 显示通知
  const message = data.action === 'accept' ? 
    `已同意 ${data.request.from_user_username} 的好友申请` : 
    `已拒绝 ${data.request.from_user_username} 的好友申请`;
  showNotification(message, 'success', '✅');
}

async function logout() {
  try {
    console.log('开始退出登录...');
    
    console.log('[状态同步] 用户退出，发送离线状态给所有好友');
    
    // 1. 设置用户离线状态（这会通知所有好友）
    try {
      await hybridApi.setOnlineStatus('offline');
      console.log('[状态同步] 离线状态已同步给好友');
    } catch (statusError) {
      console.warn('设置离线状态失败:', statusError);
    }
    
    // 2. 清理HybridMessaging服务
    hybridStore.cleanupHybridMessaging();
    
    // 3. 清理消息系统连接
    if (messaging.value && typeof messaging.value.cleanup === 'function') {
      await messaging.value.cleanup();
      messaging.value = null;
    }
    
    // 4. 清理组件状态
    selectedContact.value = null;
    connectionNotification.value = null;
    showStatsModal.value = false;
    showFriendRequestModal.value = false;
    
    // 5. 清理定时器
    if (window.hybridChatTimers) {
      window.hybridChatTimers.forEach(timer => {
        if (typeof timer === 'number') {
          clearInterval(timer);
          clearTimeout(timer);
        }
      });
      window.hybridChatTimers = [];
    }
    
    // 6. 调用后端退出API（如果需要）
    try {
      await hybridApi.logout();
    } catch (apiError) {
      console.warn('后端退出API调用失败:', apiError);
    }
    
    // 7. 清空store状态
    hybridStore.logout();
    
    console.log('退出登录完成，跳转到登录页');
    
    // 8. 强制跳转到登录页
    await router.replace('/login');
    
    // 9. 刷新页面确保完全清理
    setTimeout(() => {
      window.location.reload();
    }, 100);
    
  } catch (error) {
    console.error('退出登录失败:', error);
    // 即使出错也要清理状态并跳转
    hybridStore.cleanupHybridMessaging();
    hybridStore.logout();
    router.replace('/login');
    setTimeout(() => {
      window.location.reload();
    }, 100);
  }
}
</script>

<style scoped>
.hybrid-chat-main {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.top-navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: white;
  border-bottom: 1px solid #ddd;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.app-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

.architecture-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.arch-badge {
  background: linear-gradient(45deg, #28a745, #007bff);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.p2p-status {
  font-size: 0.875rem;
  color: #666;
  font-weight: 500;
}

.nav-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.method-switch-hint {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #856404;
}

.hint-icon {
  animation: spin 1s linear infinite;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.username {
  font-weight: 500;
  color: #333;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #28a745;
}

.friend-request-btn, .profile-btn, .stats-btn, .logout-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background: white;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.friend-request-btn:hover, .profile-btn:hover, .stats-btn:hover, .logout-btn:hover {
  background: #f8f9fa;
}

.friend-request-btn.has-requests {
  background: #fff3cd;
  border-color: #ffeaa7;
  color: #856404;
}

.friend-request-btn.has-requests:hover {
  background: #ffeaa7;
}

.request-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #dc3545;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  border: 2px solid white;
}

.profile-btn {
  color: #007bff;
  border-color: #007bff;
}

.profile-btn:hover {
  background: #007bff;
  color: white;
}

.logout-btn {
  color: #dc3545;
  border-color: #dc3545;
}

.logout-btn:hover {
  background: #dc3545;
  color: white;
}

.chat-layout {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.contacts-sidebar {
  width: 300px;
  border-right: 1px solid #ddd;
  background: white;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}

.chat-content {
  height: 100%;
}

.empty-chat {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-content {
  text-align: center;
  color: #666;
  max-width: 400px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-content h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  color: #333;
}

.empty-content p {
  margin: 0 0 2rem 0;
  font-size: 1rem;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.feature-icon {
  font-size: 1.5rem;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.stats-modal {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0.25rem;
  line-height: 1;
}

.close-btn:hover {
  color: #333;
}

.modal-content {
  padding: 1.5rem;
}

.stats-section {
  margin-bottom: 2rem;
}

.stats-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #333;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #eee;
}

.stat-card.p2p {
  background: linear-gradient(135deg, #d4edda, #c3e6cb);
}

.stat-card.server {
  background: linear-gradient(135deg, #fff3cd, #ffeaa7);
}

.stat-card.ratio {
  background: linear-gradient(135deg, #e2e3e5, #d1ecf1);
}

.stat-icon {
  font-size: 2rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 0.875rem;
  color: #666;
}

.message-stats {
  margin-bottom: 1.5rem;
}

.message-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 0.25rem;
}

.message-label {
  font-weight: 500;
  color: #333;
}

.message-breakdown {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
}

.message-total {
  font-weight: 500;
  color: #333;
}

.message-p2p {
  color: #28a745;
}

.message-server {
  color: #ffc107;
}

.efficiency-chart h5 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #333;
}

.chart-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.bar-label {
  width: 100px;
  font-size: 0.875rem;
  color: #666;
}

.bar-container {
  flex: 1;
  height: 20px;
  background: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s ease;
}

.bar-fill.p2p {
  background: linear-gradient(90deg, #28a745, #20c997);
}

.bar-fill.server {
  background: linear-gradient(90deg, #ffc107, #fd7e14);
}

.bar-value {
  width: 50px;
  text-align: right;
  font-size: 0.875rem;
  font-weight: 500;
  color: #333;
}

/* 连接通知 */
.connection-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1001;
}

.notification {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  font-size: 0.875rem;
  font-weight: 500;
  animation: slideIn 0.3s ease-out;
}

.notification.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.notification.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.notification.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.modal-overlay.incoming-call-overlay {
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1001;
}

.incoming-call-modal {
  background: linear-gradient(145deg, #2c2c2c, #1a1a1a);
  border-radius: 20px;
  padding: 40px;
  width: 320px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  animation: fadeIn 0.3s ease-out;
}

.caller-info {
  margin-bottom: 30px;
}

.caller-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  margin: 0 auto 20px;
  overflow: hidden;
  border: 3px solid #4a90e2;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #333;
}

.caller-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 48px;
  color: #fff;
  font-weight: bold;
}

.caller-name {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.call-type {
  font-size: 16px;
  color: #aaa;
  margin-top: 5px;
}

.call-actions {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.action-btn {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  color: white;
  font-size: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.3s ease;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.reject-btn {
  background-color: #e74c3c;
}

.reject-btn:hover {
  background-color: #c0392b;
  transform: translateY(-3px);
}

.accept-btn {
  background-color: #2ecc71;
}

.accept-btn:hover {
  background-color: #27ae60;
  transform: translateY(-3px);
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

/* 响应式设计 */
@media (max-width: 768px) {
  .contacts-sidebar {
    width: 250px;
  }
  
  .top-navbar {
    padding: 0.5rem;
  }
  
  .app-title {
    font-size: 1.25rem;
  }
  
  .nav-right {
    gap: 0.5rem;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .message-breakdown {
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .chart-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .bar-container {
    width: 100%;
  }
}
</style>