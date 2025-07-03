<template>
  <div class="steganography-panel">
    <div class="panel-header">
      <h3>图像隐写术</h3>
      <p class="description">在图像中隐藏或提取秘密信息</p>
    </div>

    <div class="tabs">
      <button 
        :class="['tab-button', { active: activeTab === 'embed' }]"
        @click="activeTab = 'embed'"
      >
        嵌入信息
      </button>
      <button 
        :class="['tab-button', { active: activeTab === 'extract' }]"
        @click="activeTab = 'extract'"
      >
        提取信息
      </button>
    </div>

    <!-- 嵌入信息面板 -->
    <div v-if="activeTab === 'embed'" class="tab-content">
      <div class="form-group">
        <label>选择图像文件:</label>
        <input 
          type="file" 
          accept="image/*" 
          @change="handleImageUpload"
          ref="imageInput"
          class="file-input"
        >
      </div>

      <div class="form-group">
        <label>秘密信息:</label>
        <textarea 
          v-model="secretMessage"
          placeholder="输入要隐藏的秘密信息..."
          class="message-input"
          rows="4"
        ></textarea>
      </div>

      <div class="form-group">
        <label>密码:</label>
        <input 
          type="password" 
          v-model="password"
          placeholder="输入用于加密的密码"
          class="password-input"
        >
      </div>

      <button 
        @click="embedMessage"
        :disabled="!selectedImage || !secretMessage || !password || isLoading"
        class="action-button embed-button"
      >
        <span v-if="isLoading">嵌入中...</span>
        <span v-else>嵌入信息</span>
      </button>
    </div>

    <!-- 提取信息面板 -->
    <div v-if="activeTab === 'extract'" class="tab-content">
      <div class="form-group">
        <label>选择包含隐藏信息的图像:</label>
        <input 
          type="file" 
          accept="image/*" 
          @change="handleExtractImageUpload"
          ref="extractImageInput"
          class="file-input"
        >
      </div>

      <div class="form-group">
        <label>密码:</label>
        <input 
          type="password" 
          v-model="extractPassword"
          placeholder="输入用于解密的密码"
          class="password-input"
        >
      </div>

      <button 
        @click="extractMessage"
        :disabled="!extractImage || !extractPassword || isLoading"
        class="action-button extract-button"
      >
        <span v-if="isLoading">提取中...</span>
        <span v-else>提取信息</span>
      </button>

      <div v-if="extractedMessage" class="result-section">
        <label>提取的秘密信息:</label>
        <div class="extracted-message">
          {{ extractedMessage }}
        </div>
        <button @click="copyToClipboard" class="copy-button">
          复制到剪贴板
        </button>
      </div>
    </div>

    <!-- 状态消息 -->
    <div v-if="statusMessage" :class="['status-message', statusType]">
      {{ statusMessage }}
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SteganographyPanel',
  data() {
    return {
      activeTab: 'embed',
      selectedImage: null,
      extractImage: null,
      secretMessage: '',
      password: '',
      extractPassword: '',
      extractedMessage: '',
      isLoading: false,
      statusMessage: '',
      statusType: 'info'
    }
  },
  methods: {
    handleImageUpload(event) {
      const file = event.target.files[0]
      if (file) {
        this.selectedImage = file
        this.showStatus(`已选择图像: ${file.name}`, 'success')
      }
    },
    
    handleExtractImageUpload(event) {
      const file = event.target.files[0]
      if (file) {
        this.extractImage = file
        this.showStatus(`已选择图像: ${file.name}`, 'success')
      }
    },

    async embedMessage() {
      if (!this.selectedImage || !this.secretMessage || !this.password) {
        this.showStatus('请填写所有必需字段', 'error')
        return
      }

      this.isLoading = true
      this.showStatus('正在嵌入信息...', 'info')

      try {
        const formData = new FormData()
        formData.append('image', this.selectedImage)
        formData.append('secret_message', this.secretMessage)
        formData.append('password', this.password)

        const response = await axios.post('/api/steganography/embed', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          responseType: 'blob'
        })

        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `steganography_${this.selectedImage.name}`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)

        this.showStatus('信息嵌入成功！图像已下载', 'success')
        this.resetEmbedForm()
      } catch (error) {
        console.error('嵌入失败:', error)
        this.showStatus('嵌入失败: ' + (error.response?.data?.detail || error.message), 'error')
      } finally {
        this.isLoading = false
      }
    },

    async extractMessage() {
      if (!this.extractImage || !this.extractPassword) {
        this.showStatus('请选择图像并输入密码', 'error')
        return
      }

      this.isLoading = true
      this.showStatus('正在提取信息...', 'info')

      try {
        const formData = new FormData()
        formData.append('image', this.extractImage)
        formData.append('password', this.extractPassword)

        const response = await axios.post('/api/steganography/extract', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        this.extractedMessage = response.data.secret_message
        this.showStatus('信息提取成功！', 'success')
      } catch (error) {
        console.error('提取失败:', error)
        this.showStatus('提取失败: ' + (error.response?.data?.detail || error.message), 'error')
        this.extractedMessage = ''
      } finally {
        this.isLoading = false
      }
    },

    copyToClipboard() {
      if (this.extractedMessage) {
        navigator.clipboard.writeText(this.extractedMessage).then(() => {
          this.showStatus('已复制到剪贴板', 'success')
        }).catch(() => {
          this.showStatus('复制失败', 'error')
        })
      }
    },

    resetEmbedForm() {
      this.selectedImage = null
      this.secretMessage = ''
      this.password = ''
      this.$refs.imageInput.value = ''
    },

    showStatus(message, type = 'info') {
      this.statusMessage = message
      this.statusType = type
      setTimeout(() => {
        this.statusMessage = ''
      }, 5000)
    }
  }
}
</script>

<style scoped>
.steganography-panel {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.panel-header {
  text-align: center;
  margin-bottom: 30px;
}

.panel-header h3 {
  color: #2c3e50;
  margin-bottom: 8px;
  font-size: 24px;
}

.description {
  color: #6c757d;
  margin: 0;
  font-size: 14px;
}

.tabs {
  display: flex;
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tab-button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: #e9ecef;
  color: #495057;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
}

.tab-button:hover {
  background: #dee2e6;
}

.tab-button.active {
  background: #007bff;
  color: white;
}

.tab-content {
  background: white;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2c3e50;
}

.file-input,
.message-input,
.password-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s ease;
}

.file-input:focus,
.message-input:focus,
.password-input:focus {
  outline: none;
  border-color: #007bff;
}

.message-input {
  resize: vertical;
  min-height: 100px;
  font-family: inherit;
}

.action-button {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 10px;
}

.embed-button {
  background: #28a745;
  color: white;
}

.embed-button:hover:not(:disabled) {
  background: #218838;
}

.extract-button {
  background: #17a2b8;
  color: white;
}

.extract-button:hover:not(:disabled) {
  background: #138496;
}

.action-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
}

.result-section {
  margin-top: 25px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #28a745;
}

.extracted-message {
  background: white;
  padding: 15px;
  border-radius: 4px;
  margin: 10px 0;
  border: 1px solid #dee2e6;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
}

.copy-button {
  padding: 8px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.3s ease;
}

.copy-button:hover {
  background: #5a6268;
}

.status-message {
  margin-top: 15px;
  padding: 12px;
  border-radius: 6px;
  font-weight: 500;
  text-align: center;
}

.status-message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.status-message.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}
</style>