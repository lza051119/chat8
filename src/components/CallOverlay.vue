<template>
  <div v-if="show" class="call-overlay">
    <div class="call-container">
      <div class="call-header">
        <div class="contact-info">
          <div class="avatar">{{ contact.username?.[0]?.toUpperCase() }}</div>
          <div class="info">
            <h3>{{ contact.username }}</h3>
            <div class="call-status">{{ callStatus }}</div>
            <div class="call-duration">{{ formattedDuration }}</div>
          </div>
        </div>
      </div>
      
      <div class="call-controls">
        <button 
          @click="toggleMute" 
          :class="['control-btn', { active: isMuted }]"
          title="静音"
        >
          {{ isMuted ? '🔇' : '🎤' }}
        </button>
        
        <button 
          @click="endCall" 
          class="control-btn end-call"
          title="结束通话"
        >
          📞
        </button>
        
        <button 
          @click="toggleSpeaker" 
          :class="['control-btn', { active: isSpeakerOn }]"
          title="扬声器"
        >
          {{ isSpeakerOn ? '🔊' : '🔉' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { store } from '../store';

const show = ref(false);
const contact = ref({});
const callStatus = ref('连接中...');
const callDuration = ref(0);
const isMuted = ref(false);
const isSpeakerOn = ref(false);
let durationTimer = null;

const formattedDuration = computed(() => {
  const minutes = Math.floor(callDuration.value / 60);
  const seconds = callDuration.value % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
});

function startCall(target, type = 'voice') {
  show.value = true;
  contact.value = target;
  callStatus.value = '正在呼叫...';
  callDuration.value = 0;
  
  // 模拟通话连接过程
  setTimeout(() => {
    callStatus.value = type === 'voice' ? '语音通话中' : '视频通话中';
    startDurationTimer();
  }, 2000);
  
  // 1. 通过WebSocket发起通话信令（需要后端支持）
  // 2. 建立WebRTC连接（前端实现）
  console.log(`发起${type}通话:`, target);
}

function endCall() {
  show.value = false;
  callStatus.value = '通话结束';
  stopDurationTimer();
  
  // 通知后端结束通话
  console.log('结束通话');
}

function toggleMute() {
  isMuted.value = !isMuted.value;
  // 实际实现中这里会控制麦克风
  console.log('静音状态:', isMuted.value);
}

function toggleSpeaker() {
  isSpeakerOn.value = !isSpeakerOn.value;
  // 实际实现中这里会控制扬声器
  console.log('扬声器状态:', isSpeakerOn.value);
}

function startDurationTimer() {
  durationTimer = setInterval(() => {
    callDuration.value++;
  }, 1000);
}

function stopDurationTimer() {
  if (durationTimer) {
    clearInterval(durationTimer);
    durationTimer = null;
  }
}

onUnmounted(() => {
  stopDurationTimer();
});

// 暴露给父组件的方法
defineExpose({
  startCall
});
</script>

<style scoped>
.call-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.call-container {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  width: 400px;
  text-align: center;
}

.call-header {
  margin-bottom: 3rem;
}

.contact-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #007bff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 1rem;
}

.info h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
}

.call-status {
  color: #666;
  margin-bottom: 0.5rem;
}

.call-duration {
  font-size: 1.25rem;
  font-weight: bold;
  color: #007bff;
}

.call-controls {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.control-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  background: #f8f9fa;
  cursor: pointer;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.control-btn:hover {
  background: #e9ecef;
  transform: scale(1.05);
}

.control-btn.active {
  background: #007bff;
  color: white;
}

.control-btn.end-call {
  background: #dc3545;
  color: white;
  transform: rotate(135deg);
}

.control-btn.end-call:hover {
  background: #c82333;
}
</style> 