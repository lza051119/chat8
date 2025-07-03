<template>
  <div class="user-profile-container">
    <div class="profile-header">
      <h2>{{ isViewingFriend ? '好友信息' : '个人信息' }}</h2>
      <button @click="closeProfile" class="close-btn">
        <i class="fas fa-times"></i>
      </button>
    </div>
    
    <div class="profile-content">
      <form @submit.prevent="saveProfile" class="profile-form">
        <!-- 头像上传区域 -->
        <div class="form-group avatar-section">
          <label>头像</label>
          <div class="avatar-upload-container">
            <div class="avatar-preview" @click="!isViewingFriend && triggerFileInput()">
              <img v-if="currentUser.avatar" :src="getAvatarUrl(currentUser.avatar)" alt="头像" class="avatar-image" />
              <div v-else class="avatar-placeholder">
                <i class="fas fa-user"></i>
              </div>
              <div v-if="!isViewingFriend" class="avatar-overlay">
                <i class="fas fa-camera"></i>
                <span>点击上传</span>
              </div>
            </div>
            <input 
              ref="fileInput" 
              type="file" 
              accept="image/*" 
              @change="handleAvatarUpload" 
              style="display: none"
              :disabled="isViewingFriend"
            />
            <div v-if="!isViewingFriend && currentUser.avatar" class="avatar-actions">
              <button type="button" @click="deleteAvatar" class="delete-avatar-btn" :disabled="uploading">
                <i class="fas fa-trash"></i>
                删除头像
              </button>
            </div>
          </div>
        </div>
        
        <div class="form-group">
          <label for="displayName">显示名称</label>
          <input 
            type="text" 
            id="displayName" 
            v-model="profileData.display_name" 
            placeholder="请输入显示名称"
            class="form-input"
            :readonly="isViewingFriend"
          />
        </div>
        
        <div class="form-group">
          <label for="birthday">生日</label>
          <input 
            type="date" 
            id="birthday" 
            v-model="profileData.birthday" 
            class="form-input"
            :readonly="isViewingFriend"
          />
        </div>
        
        <div class="form-group">
          <label for="age">年龄</label>
          <input 
            type="number" 
            id="age" 
            v-model.number="profileData.age" 
            placeholder="请输入年龄"
            min="1" 
            max="150"
            class="form-input"
            :readonly="isViewingFriend"
          />
        </div>
        
        <div class="form-group">
          <label for="gender">性别</label>
          <select id="gender" v-model="profileData.gender" class="form-select" :disabled="isViewingFriend">
            <option value="">请选择性别</option>
            <option value="male">男</option>
            <option value="female">女</option>
            <option value="other">其他</option>
          </select>
        </div>
        
        <div class="form-group">
          <label for="hobbies">爱好</label>
          <textarea 
            id="hobbies" 
            v-model="profileData.hobbies" 
            placeholder="请输入您的爱好，用逗号分隔"
            class="form-textarea"
            rows="3"
            :readonly="isViewingFriend"
          ></textarea>
        </div>
        
        <div class="form-group">
          <label for="signature">个性签名</label>
          <textarea 
            id="signature" 
            v-model="profileData.signature" 
            placeholder="请输入您的个性签名"
            class="form-textarea"
            rows="2"
            :readonly="isViewingFriend"
          ></textarea>
        </div>
        
        <div v-if="!isViewingFriend" class="form-actions">
          <button type="submit" class="save-btn" :disabled="saving">
            <i class="fas fa-save"></i>
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <button type="button" @click="resetForm" class="reset-btn">
            <i class="fas fa-undo"></i>
            重置
          </button>
        </div>
      </form>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
        <p>加载中...</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { hybridApi } from '@/api/hybrid-api'

export default {
  name: 'UserProfile',
  props: {
    userId: {
      type: String,
      default: null
    }
  },
  emits: ['close', 'avatar-updated'],
  setup(props, { emit }) {
    const loading = ref(false)
    const saving = ref(false)
    const uploading = ref(false)
    const hasExistingProfile = ref(false)
    const fileInput = ref(null)
    
    // 当前用户信息
    const currentUser = reactive({
      avatar: null
    })
    
    // 判断是否在查看好友信息
    const isViewingFriend = computed(() => {
      return props.userId !== null
    })
    
    const profileData = reactive({
      display_name: '',
      birthday: '',
      age: null,
      gender: '',
      hobbies: '',
      signature: ''
    })
    
    const originalData = reactive({})
    
    // 获取用户个人信息
    const loadProfile = async () => {
      loading.value = true
      try {
        let response
        if (isViewingFriend.value) {
          // 加载好友的个人信息
          response = await hybridApi.getUserProfile(props.userId)
        } else {
          // 加载自己的个人信息
          response = await hybridApi.get()
        }
        
        if (response.data) {
          Object.assign(profileData, response.data)
          Object.assign(originalData, response.data)
          hasExistingProfile.value = true
        }
        
        // 加载用户基本信息（包括头像）
        if (!isViewingFriend.value) {
          const userInfo = await hybridApi.getUserInfo()
          if (userInfo.data?.data?.user) {
            currentUser.avatar = userInfo.data.data.user.avatar
          }
        }
      } catch (error) {
        if (error.response?.status !== 404) {
          console.error('加载个人信息失败:', error)
          const errorMsg = isViewingFriend.value ? '加载好友信息失败，请稍后重试' : '加载个人信息失败，请稍后重试'
          alert(errorMsg)
        }
      } finally {
        loading.value = false
      }
    }
    
    // 保存个人信息
    const saveProfile = async () => {
      saving.value = true
      try {
        let response
        if (hasExistingProfile.value) {
          response = await hybridApi.put(profileData)
        } else {
          response = await hybridApi.post(profileData)
        }
        
        if (response.data?.success) {
          alert('个人信息保存成功！')
          Object.assign(originalData, profileData)
          hasExistingProfile.value = true
        } else {
          throw new Error(response.data?.message || '保存失败')
        }
      } catch (error) {
        console.error('保存个人信息失败:', error)
        alert(error.response?.data?.detail || '保存失败，请稍后重试')
      } finally {
        saving.value = false
      }
    }
    
    // 重置表单
    const resetForm = () => {
      Object.assign(profileData, originalData)
    }
    
    // 触发文件选择
    const triggerFileInput = () => {
      if (fileInput.value) {
        fileInput.value.click()
      }
    }
    
    // 处理头像上传
    const handleAvatarUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return
      
      // 验证文件类型
      if (!file.type.startsWith('image/')) {
        alert('请选择图片文件')
        return
      }
      
      // 验证文件大小（5MB）
      if (file.size > 5 * 1024 * 1024) {
        alert('图片大小不能超过5MB')
        return
      }
      
      uploading.value = true
      try {
        const response = await hybridApi.uploadAvatar(file)
        if (response.data?.data?.avatarUrl) {
          currentUser.avatar = response.data.data.avatarUrl
          emit('avatar-updated', currentUser.avatar)
          alert('头像上传成功')
        }
      } catch (error) {
        console.error('头像上传失败:', error)
        alert('头像上传失败，请稍后重试')
      } finally {
        uploading.value = false
        // 清空文件输入
        if (fileInput.value) {
          fileInput.value.value = ''
        }
      }
    }
    
    // 删除头像
    const deleteAvatar = async () => {
      if (!confirm('确定要删除头像吗？')) return
      
      uploading.value = true
      try {
        await hybridApi.deleteAvatar()
        currentUser.avatar = null
        emit('avatar-updated', null)
        alert('头像删除成功')
      } catch (error) {
        console.error('头像删除失败:', error)
        alert('头像删除失败，请稍后重试')
      } finally {
        uploading.value = false
      }
    }
    
    // 获取头像URL
    const getAvatarUrl = (avatarPath) => {
      if (!avatarPath) return ''
      
      // 如果是绝对路径（以http开头），直接返回
      if (avatarPath.startsWith('http')) {
        return avatarPath
      }
      
      // 如果是API相对路径（以/api开头），拼接基础URL
      if (avatarPath.startsWith('/api/')) {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        return `${baseUrl}${avatarPath}`
      }
      
      // 其他相对路径，拼接API基础URL
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      return `${baseUrl}${avatarPath.startsWith('/') ? '' : '/'}${avatarPath}`
    }

    // 关闭个人信息面板
    const closeProfile = () => {
      emit('close')
    }
    
    onMounted(() => {
      loadProfile()
    })
    
    return {
      loading,
      saving,
      uploading,
      profileData,
      currentUser,
      fileInput,
      isViewingFriend,
      saveProfile,
      resetForm,
      closeProfile,
      triggerFileInput,
      handleAvatarUpload,
      deleteAvatar,
      getAvatarUrl
    }
  }
}
</script>

<style scoped>
.user-profile-container {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  height: 100vh;
  background: white;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  background: #f8f9fa;
}

.profile-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #666;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e9ecef;
  color: #333;
}

.profile-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
}

/* 头像相关样式 */
.avatar-section {
  align-items: center;
}

.avatar-upload-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.avatar-preview {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  border: 3px solid #e1e5e9;
  transition: border-color 0.2s;
}

.avatar-preview:hover {
  border-color: #007bff;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background-color: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6c757d;
  font-size: 3rem;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
  font-size: 0.9rem;
}

.avatar-preview:hover .avatar-overlay {
  opacity: 1;
}

.avatar-overlay i {
  font-size: 1.5rem;
  margin-bottom: 5px;
}

.avatar-actions {
  display: flex;
  gap: 10px;
}

.delete-avatar-btn {
  padding: 8px 16px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.delete-avatar-btn:hover:not(:disabled) {
  background-color: #c82333;
}

.delete-avatar-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-input,
.form-select,
.form-textarea {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.form-input:read-only,
.form-textarea:read-only {
  background-color: #f8f9fa;
  color: #6c757d;
  cursor: default;
}

.form-select:disabled {
  background-color: #f8f9fa;
  color: #6c757d;
  cursor: not-allowed;
}

.form-textarea {
  resize: vertical;
  min-height: 60px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.save-btn,
.reset-btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.save-btn {
  background: #007bff;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #0056b3;
}

.save-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.reset-btn {
  background: #6c757d;
  color: white;
}

.reset-btn:hover {
  background: #545b62;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.loading-spinner {
  text-align: center;
  color: #666;
}

.loading-spinner i {
  font-size: 2rem;
  margin-bottom: 10px;
}

.loading-spinner p {
  margin: 0;
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-profile-container {
    width: 100vw;
    right: 0;
  }
  
  .avatar-preview {
    width: 100px;
    height: 100px;
  }
}
</style>