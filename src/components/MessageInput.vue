<template>
  <div class="message-input">
    <div class="input-container">
      <div class="controls">
        <button 
          @click="toggleBurn" 
          :class="['control-btn', { active: burnMode }]"
          title="阅后即焚"
        >
          🔥
        </button>
        <button @click="attachFile" class="control-btn" title="发送文件">
          📎
        </button>
      </div>
      
      <div class="text-input-area">
        <textarea
          v-model="content"
          @keydown.enter.exact.prevent="onSend"
          @keydown.enter.shift.exact="handleShiftEnter"
          placeholder="输入消息..."
          rows="1"
          class="text-input"
          ref="textInput"
        ></textarea>
        
        <div v-if="burnMode" class="burn-timer">
          <select v-model="burnAfter" class="timer-select">
            <option value="10">10秒</option>
            <option value="30">30秒</option>
            <option value="60">1分钟</option>
            <option value="300">5分钟</option>
          </select>
        </div>
      </div>
      
      <button 
        @click="onSend" 
        :disabled="!content.trim()"
        class="send-btn"
      >
        ➤
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';

const props = defineProps({ contact: Object });
const emit = defineEmits(['send']);

const content = ref('');
const burnMode = ref(false);
const burnAfter = ref(30);
const textInput = ref(null);

function onSend() {
  if (!content.value.trim()) return;
  
  const messageData = {
    content: content.value.trim(),
    burnAfter: burnMode.value ? burnAfter.value : null
  };
  
  emit('send', messageData);
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

function toggleBurn() {
  burnMode.value = !burnMode.value;
}

function attachFile() {
  alert('文件发送功能（待实现）');
}

// 自动调整textarea高度
function autoResize() {
  const textarea = textInput.value;
  if (textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  }
}

// 监听输入自动调整高度
function onInput() {
  nextTick(autoResize);
}
</script>

<style scoped>
.message-input {
  border-top: 1px solid #ddd;
  background: white;
  padding: 1rem;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
}

.controls {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.control-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.control-btn:hover {
  background: #f0f0f0;
}

.control-btn.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.text-input-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.text-input {
  width: 100%;
  min-height: 36px;
  max-height: 120px;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.4;
}

.text-input:focus {
  outline: none;
  border-color: #007bff;
}

.burn-timer {
  margin-top: 0.5rem;
}

.timer-select {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.875rem;
  background: white;
}

.send-btn {
  width: 40px;
  height: 40px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #0056b3;
  transform: scale(1.05);
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}
</style> 