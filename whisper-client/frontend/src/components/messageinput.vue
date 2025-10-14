<template>
  <div class="message-input">
    <!-- 功能控制面板 -->
    <div class="controls-panel">
      <div class="control-group">
        <label class="control-item">
          <input 
            type="checkbox" 
            v-model="imageHideMode" 
            @change="onImageHideModeChange"
          />
          <span class="control-label">🖼️ 图像隐藏</span>
        </label>
        
        <label class="control-item">
          <input 
            type="checkbox" 
            v-model="burnMode" 
            @change="onBurnModeChange"
          />
          <span class="control-label">🔥 阅后即焚</span>
        </label>
      </div>
      
      <div class="retention-group" v-if="burnMode">
        <label class="retention-label">留存时长：</label>
        <input 
          type="number" 
          v-model.number="retentionTime" 
          min="1" 
          max="3600" 
          class="retention-input"
        />
        <select v-model="retentionUnit" class="retention-unit">
          <option value="seconds">秒</option>
          <option value="minutes">分钟</option>
          <option value="hours">小时</option>
        </select>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="input-container">
      <div class="text-input-area">
        <div v-if="imageHideMode" class="mode-hint">
          🖼️ 图像隐藏模式：输入文本后点击发送按钮选择图片
        </div>
        
        <textarea
          v-model="content"
          @keydown.enter.exact.prevent="onSend"
          @keydown.enter.shift.exact="handleShiftEnter"
          @input="autoResize"
          :placeholder="getPlaceholder()"
          rows="1"
          class="text-input"
          ref="textInput"
        ></textarea>
      </div>
      
      <button 
        @click="onSend" 
        :disabled="!content.trim()"
        :class="getSendButtonClass()"
        :title="getSendButtonTitle()"
      >
        {{ getSendButtonText() }}
      </button>
    </div>
    
    <!-- 隐藏的文件输入 -->
    <input 
      ref="imageInput" 
      type="file" 
      accept="image/*" 
      @change="handleImageSelect" 
      style="display: none;"
    />
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue';

const props = defineProps({ contact: Object });
const emit = defineEmits(['send']);

// 响应式数据
const content = ref('');
const burnMode = ref(false);
const imageHideMode = ref(false);
const retentionTime = ref(30);
const retentionUnit = ref('seconds');
const textInput = ref(null);
const imageInput = ref(null);

// 计算属性：获取留存时间（秒）
const burnAfterSeconds = computed(() => {
  switch (retentionUnit.value) {
    case 'minutes':
      return retentionTime.value * 60;
    case 'hours':
      return retentionTime.value * 3600;
    default:
      return retentionTime.value;
  }
});

// 界面方法
function getPlaceholder() {
  if (imageHideMode.value) {
    return '输入要隐藏在图片中的文本...';
  }
  return '输入消息...';
}

function getSendButtonClass() {
  const classes = ['send-btn'];
  if (imageHideMode.value) {
    classes.push('image-hide-mode');
  }
  return classes;
}

function getSendButtonTitle() {
  return imageHideMode.value ? '选择图片隐藏文本' : '发送消息';
}

function getSendButtonText() {
  return imageHideMode.value ? '🖼️' : '➤';
}

// 事件处理
function onImageHideModeChange() {
  if (imageHideMode.value) {
    console.log('启用图像隐藏模式');
    // 图像隐藏和阅后即焚互斥
    if (burnMode.value) {
      burnMode.value = false;
      console.log('已自动关闭阅后即焚模式');
    }
  }
}

function onBurnModeChange() {
  if (burnMode.value) {
    console.log('启用阅后即焚模式');
    // 图像隐藏和阅后即焚互斥
    if (imageHideMode.value) {
      imageHideMode.value = false;
      console.log('已自动关闭图像隐藏模式');
    }
  }
}

function onSend() {
  if (!content.value.trim()) return;
  
  if (imageHideMode.value) {
    // 图像隐藏模式：选择图片
    selectImageForSteganography();
  } else {
    // 普通消息模式
    sendTextMessage();
  }
}

function sendTextMessage() {
  const messageData = {
    content: content.value.trim(),
    burnAfter: burnMode.value ? burnAfterSeconds.value : null
  };
  
  emit('send', messageData);
  resetInput();
}

function selectImageForSteganography() {
  if (!content.value.trim()) {
    alert('请先输入要隐藏的文本内容');
    return;
  }
  imageInput.value.click();
}

function resetInput() {
  content.value = '';
  
  // 重置textarea高度
  nextTick(() => {
    if (textInput.value) {
      textInput.value.style.height = 'auto';
    }
  });
}

function handleShiftEnter(event) {
  // Shift+Enter 换行，不发送
  return true;
}

async function handleImageSelect(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  try {
    // 创建FormData来发送隐写术请求
    const formData = new FormData();
    formData.append('image', file);
    formData.append('secret_message', content.value.trim());
    formData.append('password', 'default_password'); // 可以后续改为用户设置的密码
    
    // 发送到隐写术API
    const API_BASE_URL = '/api';
        const response = await fetch(`${API_BASE_URL}/steganography/embed`, {
      method: 'POST',
      body: formData
    });
    
    if (response.ok) {
      // 获取处理后的图片blob
      const blob = await response.blob();
      
      // 创建文件对象
      const stegoFile = new File([blob], `stego_${file.name}`, { type: 'image/png' });
      
      // 发送隐写术图片消息
      const messageData = {
        type: 'steganography',
        file: stegoFile,
        originalText: content.value.trim(),
        burnAfter: burnMode.value ? burnAfterSeconds.value : null
      };
      
      emit('send', messageData);
      resetInput();
      imageHideMode.value = false;
      burnMode.value = false;
      
      // 重置文件输入
      event.target.value = '';
    } else {
      alert('隐写术处理失败，请重试');
    }
  } catch (error) {
    console.error('隐写术处理错误:', error);
    alert('隐写术处理出错，请重试');
  }
}

// 自动调整textarea高度
function autoResize() {
  nextTick(() => {
    const textarea = textInput.value;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  });
}
</script>

<style scoped>
.message-input {
  border-top: 1px solid #e1e5e9;
  background: #ffffff;
  padding: 1rem;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
}

/* 控制面板样式 */
.controls-panel {
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.control-group {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 0.5rem;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
}

.control-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #007bff;
}

.control-label {
  user-select: none;
  color: #495057;
}

.retention-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #dee2e6;
}

.retention-label {
  font-size: 0.85rem;
  color: #6c757d;
  font-weight: 500;
}

.retention-input {
  width: 60px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.85rem;
  text-align: center;
}

.retention-unit {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.85rem;
  background: white;
}

/* 输入区域样式 */
.input-container {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
}

.text-input-area {
  flex: 1;
  position: relative;
}

.mode-hint {
  position: absolute;
  top: -28px;
  left: 0;
  font-size: 0.75rem;
  color: #28a745;
  background: rgba(40, 167, 69, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  white-space: nowrap;
  font-weight: 500;
}

.text-input {
  width: 100%;
  min-height: 44px;
  max-height: 120px;
  padding: 0.75rem 1rem;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.5;
  transition: border-color 0.2s ease;
}

.text-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.text-input::placeholder {
  color: #6c757d;
}

/* 发送按钮样式 */
.send-btn {
  width: 44px;
  height: 44px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
}

.send-btn:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}

.send-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
}

.send-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  opacity: 0.6;
}

.send-btn.image-hide-mode {
  background: #28a745;
  box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);
}

.send-btn.image-hide-mode:hover:not(:disabled) {
  background: #1e7e34;
  box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
}

/* 文件输入框样式 */
.file-input {
  display: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .control-group {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .retention-group {
    flex-wrap: wrap;
    gap: 0.25rem;
  }
  
  .input-container {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
  }
  
  .send-btn {
    align-self: flex-end;
    width: 60px;
  }
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.mode-hint {
  animation: fadeIn 0.3s ease;
}

.controls-panel {
  transition: all 0.3s ease;
}

.retention-group {
  transition: all 0.3s ease;
}
</style>