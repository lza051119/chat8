<template>
  <div v-if="show" class="call-type-overlay" @click="handleOverlayClick">
    <div class="call-type-modal" @click.stop>
      <div class="modal-header">
        <h3>选择通话类型</h3>
        <button @click="close" class="close-btn">×</button>
      </div>
      
      <div class="call-options">
        <button @click="selectCallType('voice')" class="call-option voice-option">
          <div class="option-icon">📞</div>
          <div class="option-text">
            <div class="option-title">语音通话</div>
            <div class="option-desc">仅使用麦克风进行通话</div>
          </div>
        </button>
        
        <button @click="selectCallType('video')" class="call-option video-option">
          <div class="option-icon">📹</div>
          <div class="option-text">
            <div class="option-title">视频通话</div>
            <div class="option-desc">使用摄像头和麦克风进行通话</div>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

// Props
const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  contact: {
    type: Object,
    default: null
  }
});

// Emits
const emit = defineEmits(['close', 'call-selected']);

// 方法
function close() {
  emit('close');
}

function handleOverlayClick() {
  close();
}

function selectCallType(type) {
  emit('call-selected', {
    type,
    contact: props.contact
  });
  close();
}
</script>

<style scoped>
.call-type-overlay {
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
  backdrop-filter: blur(4px);
}

.call-type-modal {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  min-width: 400px;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #666;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f8f9fa;
  color: #333;
}

.call-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.call-option {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.call-option:hover {
  border-color: #007bff;
  background: #f8f9ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
}

.voice-option:hover {
  border-color: #28a745;
  background: #f8fff9;
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.15);
}

.video-option:hover {
  border-color: #dc3545;
  background: #fff8f8;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.15);
}

.option-icon {
  font-size: 2.5rem;
  min-width: 60px;
  text-align: center;
}

.option-text {
  flex: 1;
}

.option-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.option-desc {
  font-size: 0.9rem;
  color: #666;
  line-height: 1.4;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .call-type-modal {
    margin: 1rem;
    min-width: auto;
    width: calc(100% - 2rem);
  }
  
  .call-options {
    gap: 0.75rem;
  }
  
  .call-option {
    padding: 1rem;
    gap: 1rem;
  }
  
  .option-icon {
    font-size: 2rem;
    min-width: 50px;
  }
  
  .option-title {
    font-size: 1.1rem;
  }
  
  .option-desc {
    font-size: 0.85rem;
  }
}
</style>