<template>
  <div v-if="isCallActive" class="call-overlay-mini">
    <div class="mini-call-window">
      <div class="mini-call-header">
        <div class="contact-info">
          <div class="mini-avatar">
            <div class="avatar-placeholder">
              {{ contact?.username?.[0]?.toUpperCase() || 'U' }}
            </div>
          </div>
          <div class="call-details">
            <span class="contact-name">{{ contact?.username || '未知联系人' }}</span>
            <span class="call-status">{{ callStatusText }}</span>
            <span v-if="callDuration > 0" class="call-time">{{ formatDuration(callDuration) }}</span>
          </div>
        </div>
        
        <div class="mini-controls">
          <button @click="expandCall" class="expand-btn" title="展开通话窗口">
            ⬆️
          </button>
          <button @click="endCall" class="mini-end-btn" title="结束通话">
            📞
          </button>
        </div>
      </div>
      
      <!-- 迷你音频可视化 -->
      <div class="mini-visualizer" v-if="status === 'active'">
        <div 
          v-for="i in 8" 
          :key="i" 
          class="mini-wave-bar"
          :style="{ height: miniWaveHeights[i] + '%' }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// Props
const props = defineProps({
  contact: {
    type: Object,
    default: null
  },
  status: {
    type: String,
    default: 'inactive' // inactive, connecting, ringing, active, ended
  },
  duration: {
    type: Number,
    default: 0
  }
});

// Emits
const emit = defineEmits(['end-call', 'expand-call']);

// 响应式数据
const callDuration = ref(0);
const miniWaveHeights = ref(Array(8).fill(0).map(() => Math.random() * 100));

// 定时器
let durationTimer = null;
let waveAnimationTimer = null;

// 计算属性
const isCallActive = computed(() => {
  return props.status && props.status !== 'inactive' && props.status !== 'ended';
});

const callStatusText = computed(() => {
  switch (props.status) {
    case 'connecting': return '连接中...';
    case 'ringing': return '呼叫中...';
    case 'active': return '通话中';
    case 'ended': return '已结束';
    default: return '';
  }
});

// 监听器
watch(() => props.status, (newStatus) => {
  if (newStatus === 'active') {
    startTimers();
  } else if (newStatus === 'ended' || newStatus === 'inactive') {
    stopTimers();
  }
});

watch(() => props.duration, (newDuration) => {
  callDuration.value = newDuration;
});

// 生命周期
onMounted(() => {
  if (props.status === 'active') {
    startTimers();
  }
});

onUnmounted(() => {
  stopTimers();
});

// 方法
function startTimers() {
  // 迷你音频波形动画
  waveAnimationTimer = setInterval(() => {
    if (props.status === 'active') {
      miniWaveHeights.value = miniWaveHeights.value.map(() => 
        Math.random() * 80 + 20
      );
    } else {
      miniWaveHeights.value = miniWaveHeights.value.map(() => 5);
    }
  }, 150);
}

function stopTimers() {
  if (waveAnimationTimer) {
    clearInterval(waveAnimationTimer);
    waveAnimationTimer = null;
  }
}

function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function expandCall() {
  if (props.contact) {
    router.push(`/voice-call/${props.contact.id}`);
  }
  emit('expand-call');
}

function endCall() {
  emit('end-call');
}
</script>

<style scoped>
.call-overlay-mini {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 999;
  width: 300px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
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

.mini-call-window {
  padding: 1rem;
}

.mini-call-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.contact-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.mini-avatar {
  width: 40px;
  height: 40px;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1rem;
}

.call-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.contact-name {
  font-weight: 600;
  font-size: 0.9rem;
  color: #333;
}

.call-status {
  font-size: 0.8rem;
  color: #666;
}

.call-time {
  font-size: 0.8rem;
  color: #4caf50;
  font-weight: 500;
}

.mini-controls {
  display: flex;
  gap: 0.5rem;
}

.expand-btn,
.mini-end-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
}

.expand-btn {
  background: #f0f0f0;
  color: #666;
}

.expand-btn:hover {
  background: #e0e0e0;
  transform: scale(1.1);
}

.mini-end-btn {
  background: #f44336;
  color: white;
}

.mini-end-btn:hover {
  background: #d32f2f;
  transform: scale(1.1);
}

.mini-visualizer {
  display: flex;
  justify-content: center;
  align-items: end;
  height: 30px;
  gap: 2px;
  margin-top: 0.5rem;
}

.mini-wave-bar {
  width: 3px;
  background: linear-gradient(to top, #667eea, #764ba2);
  border-radius: 1.5px;
  transition: height 0.1s ease;
  min-height: 3px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .call-overlay-mini {
    width: 280px;
    top: 10px;
    right: 10px;
  }
  
  .mini-call-window {
    padding: 0.75rem;
  }
  
  .contact-name {
    font-size: 0.85rem;
  }
  
  .call-status,
  .call-time {
    font-size: 0.75rem;
  }
}
</style>