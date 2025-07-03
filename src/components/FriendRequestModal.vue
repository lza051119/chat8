<template>
  <div v-if="isVisible" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>好友申请</h3>
        <button @click="closeModal" class="close-btn">×</button>
      </div>
      
      <div class="modal-body">
        <!-- 申请列表 -->
        <div v-if="requests.length > 0" class="request-list">
          <div 
            v-for="request in requests" 
            :key="request.id" 
            class="request-item"
          >
            <div class="user-avatar">
              <img v-if="request.from_user_avatar" :src="request.from_user_avatar" :alt="request.from_user_username" />
              <div v-else class="avatar-placeholder">
                {{ request.from_user_username && request.from_user_username.length > 0 ? request.from_user_username[0].toUpperCase() : '?' }}
              </div>
            </div>
            <div class="request-info">
              <div class="username">{{ request.from_user_username }}</div>
              <div class="user-id">ID: {{ request.from_user_id }}</div>
              <div v-if="request.message" class="request-message">{{ request.message }}</div>
              <div class="request-time">{{ formatTime(request.created_at) }}</div>
            </div>
            <div class="request-actions">
              <button 
                @click="handleRequest(request.id, 'accept')"
                class="accept-btn"
                :disabled="processingRequests.includes(request.id)"
              >
                <span v-if="!processingRequests.includes(request.id)">同意</span>
                <span v-else>处理中...</span>
              </button>
              <button 
                @click="handleRequest(request.id, 'reject')"
                class="reject-btn"
                :disabled="processingRequests.includes(request.id)"
              >
                <span v-if="!processingRequests.includes(request.id)">拒绝</span>
                <span v-else>处理中...</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 无申请状态 -->
        <div v-else-if="!loading" class="no-requests">
          <div class="no-requests-icon">📭</div>
          <div class="no-requests-text">暂无好友申请</div>
          <div class="no-requests-hint">当有人向您发送好友申请时，会在这里显示</div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading">
          <div class="loading-spinner"></div>
          <span>加载中...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { hybridApi } from '../api/hybrid-api.js'
import { hybridStore } from '../store/hybrid-store.js'

export default {
  name: 'FriendRequestModal',
  props: {
    isVisible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'request-handled'],
  setup(props, { emit }) {
    const requests = ref([])
    const loading = ref(false)
    const processingRequests = ref([])

    // 监听模态框显示状态，自动加载申请列表
    watch(() => props.isVisible, (newVal) => {
      if (newVal) {
        loadRequests()
      }
    })

    const loadRequests = async () => {
      loading.value = true
      try {
        const response = await hybridApi.getFriendRequests('received')
        if (response.data && response.data.success) {
          requests.value = response.data.data || []
        }
      } catch (error) {
        console.error('加载好友申请失败:', error)
        alert('加载好友申请失败，请重试')
      } finally {
        loading.value = false
      }
    }

    const handleRequest = async (requestId, action) => {
      if (processingRequests.value.includes(requestId)) return

      processingRequests.value.push(requestId)
      try {
        await hybridApi.handleFriendRequest(requestId, action)
        
        // 从列表中移除已处理的申请
        const request = requests.value.find(r => r.id === requestId)
        requests.value = requests.value.filter(r => r.id !== requestId)
        
        if (action === 'accept' && request) {
          // 如果同意申请，添加到联系人列表
          hybridStore.addContact({
            id: request.from_user_id,
            username: request.from_user_username,
            avatar: request.from_user_avatar,
            online: false
          })
        }
        
        emit('request-handled', { requestId, action, request })
        
        const message = action === 'accept' ? '已同意好友申请' : '已拒绝好友申请'
        alert(message)
        
      } catch (error) {
        console.error('处理好友申请失败:', error)
        alert('处理申请失败，请重试')
      } finally {
        processingRequests.value = processingRequests.value.filter(id => id !== requestId)
      }
    }

    const formatTime = (timeString) => {
      const date = new Date(timeString)
      const now = new Date()
      const diff = now - date
      
      if (diff < 60000) { // 1分钟内
        return '刚刚'
      } else if (diff < 3600000) { // 1小时内
        return `${Math.floor(diff / 60000)}分钟前`
      } else if (diff < 86400000) { // 24小时内
        return `${Math.floor(diff / 3600000)}小时前`
      } else {
        return date.toLocaleDateString()
      }
    }

    const closeModal = () => {
      emit('close')
    }

    return {
      requests,
      loading,
      processingRequests,
      handleRequest,
      formatTime,
      closeModal
    }
  }
}
</script>

<style scoped>
.modal-overlay {
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

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.modal-header h3 {
  margin: 0;
  color: #333;
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

.modal-body {
  padding: 1.5rem;
  max-height: 60vh;
  overflow-y: auto;
}

.request-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.request-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #f8f9fa;
}

.user-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 1rem;
  flex-shrink: 0;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background: #007bff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
}

.request-info {
  flex: 1;
  margin-right: 1rem;
}

.username {
  font-weight: 600;
  color: #333;
  margin-bottom: 0.25rem;
}

.user-id {
  color: #666;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.request-message {
  color: #555;
  font-style: italic;
  margin-bottom: 0.25rem;
  padding: 0.5rem;
  background: white;
  border-radius: 4px;
  border-left: 3px solid #007bff;
}

.request-time {
  color: #999;
  font-size: 0.75rem;
}

.request-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.accept-btn, .reject-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.accept-btn {
  background: #28a745;
  color: white;
}

.accept-btn:hover:not(:disabled) {
  background: #218838;
}

.reject-btn {
  background: #dc3545;
  color: white;
}

.reject-btn:hover:not(:disabled) {
  background: #c82333;
}

.accept-btn:disabled, .reject-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.no-requests {
  text-align: center;
  padding: 3rem 1rem;
}

.no-requests-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.no-requests-text {
  font-size: 1.25rem;
  color: #333;
  margin-bottom: 0.5rem;
}

.no-requests-hint {
  color: #666;
  font-size: 0.875rem;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  gap: 0.5rem;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>