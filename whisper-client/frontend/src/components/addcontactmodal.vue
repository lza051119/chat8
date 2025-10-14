<template>
  <div v-if="isVisible" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>添加联系人</h3>
        <button @click="closeModal" class="close-btn">×</button>
      </div>
      
      <div class="modal-body">
        <!-- 搜索用户 -->
        <div class="search-section">
          <div class="search-input-group">
            <input 
              v-model="searchQuery" 
              @keyup.enter="searchUsers"
              type="text" 
              placeholder="输入用户名或ID搜索用户"
              class="search-input"
            />
            <button @click="searchUsers" class="search-btn" :disabled="!searchQuery.trim()">
              🔍
            </button>
          </div>
        </div>

        <!-- 搜索结果 -->
        <div v-if="searchResults.length > 0" class="search-results">
          <h4>搜索结果</h4>
          <div class="user-list">
            <div 
              v-for="user in searchResults" 
              :key="user.id" 
              class="user-item"
              :class="{ 'already-friend': isAlreadyFriend(user.id) }"
            >
              <div class="user-avatar">
                <img v-if="user.avatar" :src="user.avatar" :alt="user.username" />
                <div v-else class="avatar-placeholder">
                  {{ user.username && user.username.length > 0 ? user.username[0].toUpperCase() : '?' }}
                </div>
              </div>
              <div class="user-info">
                <div class="username">{{ user.username || '未知用户' }}</div>
                <div class="user-id">ID: {{ user.id || 'N/A' }}</div>
              </div>
              <button 
                v-if="!isAlreadyFriend(user.id) && !isRequestSent(user.id)"
                @click="sendFriendRequest(user)"
                class="add-btn"
                :class="{ 'adding': addingUsers.includes(user.id) }"
                :disabled="addingUsers.includes(user.id)"
              >
                <span v-if="!addingUsers.includes(user.id)" class="add-btn-content">
                  <svg class="add-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M12 5v14M5 12h14"/>
                  </svg>
                  添加好友
                </span>
                <span v-else class="add-btn-content adding">
                  <div class="adding-spinner"></div>
                  发送中...
                </span>
              </button>
              <span v-else-if="isRequestSent(user.id)" class="request-sent-label">申请已发送</span>
              <span v-else class="already-friend-label">已是好友</span>
            </div>
          </div>
        </div>

        <!-- 搜索状态 -->
        <div v-if="searching" class="search-status">
          <div class="loading">
            <div class="loading-spinner"></div>
            <span>搜索中...</span>
          </div>
        </div>
        
        <div v-if="hasSearched && !searching && searchResults.length === 0" class="search-status">
          <div class="no-results">
            <div class="no-results-icon">😔</div>
            <div class="no-results-text">您查找的用户不存在</div>
            <div class="no-results-hint">请检查用户名是否正确</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { hybridStore } from '../store/hybrid-store.js'
import { hybridApi } from '../api/hybrid-api.js'

export default {
  name: 'AddContactModal',
  props: {
    isVisible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'contact-added'],
  setup(props, { emit }) {
    const searchQuery = ref('')
    const searchResults = ref([])
    const searching = ref(false)
    const addingUsers = ref([])
    const hasSearched = ref(false)
    const sentRequests = ref(new Set()) // 记录已发送申请的用户ID
    
    // 从本地存储加载已发送的好友申请状态
    const loadSentRequestsFromStorage = () => {
      try {
        const currentUser = hybridStore.user
        if (currentUser && currentUser.id) {
          const storageKey = `sentFriendRequests_${currentUser.id}`
          const stored = localStorage.getItem(storageKey)
          if (stored) {
            const requestIds = JSON.parse(stored)
            sentRequests.value = new Set(requestIds)
          }
        }
      } catch (error) {
        console.error('加载已发送好友申请状态失败:', error)
      }
    }
    
    // 保存已发送的好友申请状态到本地存储
    const saveSentRequestsToStorage = () => {
      try {
        const currentUser = hybridStore.user
        if (currentUser && currentUser.id) {
          const storageKey = `sentFriendRequests_${currentUser.id}`
          const requestIds = Array.from(sentRequests.value)
          localStorage.setItem(storageKey, JSON.stringify(requestIds))
        }
      } catch (error) {
        console.error('保存已发送好友申请状态失败:', error)
      }
    }
    
    // 初始化时加载状态
    loadSentRequestsFromStorage()
    
    const contacts = computed(() => hybridStore.contacts)
    
    const isAlreadyFriend = (userId) => {
      return contacts.value.some(contact => contact.id === userId)
    }
    
    const isRequestSent = (userId) => {
      return sentRequests.value.has(userId)
    }
    
    const searchUsers = async () => {
      const query = searchQuery.value.trim()
      if (!query) {
        searchResults.value = []
        hasSearched.value = false
        return
      }
      
      searching.value = true
      hasSearched.value = false
      try {
        const response = await hybridApi.searchUsers(query)
        console.log('搜索响应:', response)
        
        // 检查响应数据结构
        if (response.data && response.data.success && response.data.data) {
          // 后端返回格式: {success: true, data: {items: [...], pagination: {...}}}
          const userData = response.data.data;
          if (userData.items && Array.isArray(userData.items)) {
            searchResults.value = userData.items;
          } else {
            searchResults.value = [];
          }
        } else {
          searchResults.value = [];
        }
        
        console.log('搜索结果:', searchResults.value)
      } catch (error) {
        console.error('搜索用户失败:', error)
        
        // 根据不同错误类型给出不同提示
        if (error.response?.status === 401) {
          alert('登录已过期，请重新登录')
        } else if (error.response?.status === 404) {
          // 404表示没有找到用户，这是正常情况
          searchResults.value = []
        } else if (error.response?.status >= 500) {
          alert('服务器错误，请稍后重试')
        } else {
          alert('搜索失败，请检查网络连接')
        }
        
        searchResults.value = []
      } finally {
        searching.value = false
        hasSearched.value = true
      }
    }
    
    const sendFriendRequest = async (user) => {
      if (addingUsers.value.includes(user.id)) return
      
      addingUsers.value.push(user.id)
      try {
        await hybridApi.sendFriendRequest(parseInt(user.id))
        
        // 标记为已发送申请
        sentRequests.value.add(user.id)
        
        // 保存到本地存储
        saveSentRequestsToStorage()
        
        alert('好友申请已发送，等待对方确认')
        
      } catch (error) {
        console.error('发送好友申请失败:', error)
        
        // 根据后端返回的错误信息显示具体提示
        let errorMessage = '发送好友申请失败，请重试';
        
        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response?.status === 400) {
          errorMessage = '不能向该用户发送好友申请';
        } else if (error.response?.status === 404) {
          errorMessage = '用户不存在';
        } else if (error.response?.status === 401) {
          errorMessage = '登录已过期，请重新登录';
        } else if (error.response?.status >= 500) {
          errorMessage = '服务器错误，请稍后重试';
        }
        
        alert(errorMessage)
      } finally {
        addingUsers.value = addingUsers.value.filter(id => id !== user.id)
      }
    }
    
    const closeModal = () => {
      emit('close')
      // 清空搜索状态
      searchQuery.value = ''
      searchResults.value = []
      searching.value = false
      addingUsers.value = []
      hasSearched.value = false
      // 不清空sentRequests，保持已发送申请的状态
    }
    
    // 监听模态框显示状态，重新加载已发送申请状态
    watch(() => props.isVisible, (newValue) => {
      if (newValue) {
        loadSentRequestsFromStorage()
      }
    })
    
    return {
      searchQuery,
      searchResults,
      searching,
      addingUsers,
      hasSearched,
      isAlreadyFriend,
      isRequestSent,
      searchUsers,
      sendFriendRequest,
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
  max-width: 500px;
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

.search-section {
  margin-bottom: 1.5rem;
}

.search-input-group {
  display: flex;
  gap: 0.5rem;
}

.search-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.search-btn {
  padding: 0.75rem 1rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-btn:hover:not(:disabled) {
  background: #0056b3;
}

.search-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.search-results h4 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1rem;
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border: 1px solid #eee;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.user-item:hover {
  background: #f8f9fa;
}

.user-item.already-friend {
  background: #f0f8f0;
  border-color: #d4edda;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 0.75rem;
  overflow: hidden;
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
  font-size: 1rem;
}

.user-info {
  flex: 1;
}

.username {
  font-weight: 500;
  color: #333;
  margin-bottom: 0.25rem;
}

.user-id {
  font-size: 0.875rem;
  color: #666;
}

.add-btn {
  padding: 0.6rem 1.2rem;
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
  position: relative;
  overflow: hidden;
}

.add-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #218838, #1ea085);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
}

.add-btn:active:not(:disabled) {
  transform: translateY(0);
}

.add-btn:disabled {
  background: #e9ecef;
  color: #6c757d;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.add-btn.adding {
  background: #6c757d;
  cursor: not-allowed;
}

.add-btn-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.add-icon {
  width: 16px;
  height: 16px;
  stroke-width: 2;
}

.adding-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.already-friend-label {
  color: #28a745;
  font-weight: 500;
  padding: 0.5rem 1rem;
  background: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
  font-size: 0.875rem;
}

.request-sent-label {
  color: #856404;
  font-weight: 500;
  padding: 0.5rem 1rem;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 4px;
  font-size: 0.875rem;
}

.search-status {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: #007bff;
  font-weight: 500;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e3f2fd;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.no-results-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.no-results-text {
  font-size: 1.1rem;
  font-weight: 500;
  color: #495057;
  margin-bottom: 0.25rem;
}

.no-results-hint {
  font-size: 0.9rem;
  color: #6c757d;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>