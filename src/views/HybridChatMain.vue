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
        <button @click="showStatsModal = true" class="stats-btn">📊</button>
        <button @click="logout" class="logout-btn">退出</button>
      </div>
    </div>

    <div class="chat-layout">
      <!-- 左侧联系人列表 -->
      <div class="contacts-sidebar">
        <HybridContactList 
          @contact-selected="handleContactSelected"
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

    <!-- 连接状态悬浮通知 -->
    <div v-if="connectionNotification" class="connection-notification">
      <div :class="['notification', connectionNotification.type]">
        <span class="notification-icon">{{ connectionNotification.icon }}</span>
        <span class="notification-text">{{ connectionNotification.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { hybridStore } from '../store/hybrid-store';
import HybridContactList from '../components/HybridContactList.vue';
import HybridChatWindow from '../components/HybridChatWindow.vue';
import HybridMessaging from '../services/HybridMessaging';

const router = useRouter();

const selectedContact = ref(null);
const showStatsModal = ref(false);
const showMethodSwitchHint = ref(false);
const connectionNotification = ref(null);
const contactList = ref(null);
const messaging = ref(null);

// 计算属性
const user = computed(() => hybridStore.user);
const connectionStats = computed(() => hybridStore.getConnectionStats());
const messageStats = computed(() => hybridStore.messageStats);

const totalOnlineContacts = computed(() => {
  return hybridStore.contacts.filter(contact => 
    hybridStore.onlineUsers.get(contact.id)?.online
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
  // 检查登录状态
  if (!hybridStore.isLoggedIn) {
    router.push('/login');
    return;
  }

  // 初始化混合消息服务
  await initializeMessaging();
  
  // 设置连接状态监听
  setupConnectionNotifications();
});

onUnmounted(() => {
  if (messaging.value) {
    messaging.value.cleanup();
  }
});

// 方法
async function initializeMessaging() {
  try {
    messaging.value = new HybridMessaging();
    
    // 设置回调
    messaging.value.onUserStatusChanged = handleUserStatusChange;
    
    // 初始化
    await messaging.value.initialize(hybridStore.user.id, hybridStore.token);
    
    console.log('混合消息系统初始化完成');
  } catch (error) {
    console.error('初始化消息系统失败:', error);
    showNotification('初始化失败', 'error', '❌');
  }
}

function setupConnectionNotifications() {
  // 监听P2P连接状态变化
  // 这里可以添加更多的连接状态监听逻辑
}

function handleContactSelected(contact) {
  selectedContact.value = contact;
  hybridStore.setCurrentChat(contact);
}

function handleUserStatusChange(userId, status) {
  hybridStore.updateUserStatus(userId, status);
  
  // 显示状态变化通知
  const contact = hybridStore.contacts.find(c => c.id === userId);
  if (contact) {
    const statusText = status.online ? '上线' : '离线';
    showNotification(
      `${contact.username} ${statusText}`,
      status.online ? 'success' : 'info',
      status.online ? '🟢' : '🔴'
    );
  }
}

function showNotification(message, type, icon) {
  connectionNotification.value = {
    message,
    type,
    icon
  };
  
  setTimeout(() => {
    connectionNotification.value = null;
  }, 3000);
}

async function logout() {
  try {
    // 清理连接
    if (messaging.value) {
      messaging.value.cleanup();
    }
    
    // 清空状态
    hybridStore.clear();
    
    // 跳转到登录页
    router.push('/login');
  } catch (error) {
    console.error('退出登录失败:', error);
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

.stats-btn, .logout-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background: white;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.stats-btn:hover, .logout-btn:hover {
  background: #f8f9fa;
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