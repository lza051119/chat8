<template>
  <div class="voice-call-page">
    <!-- 通话状态覆盖层 -->
    <div class="call-overlay">
      <!-- 通话头部信息 -->
      <div class="call-header">
        <button @click="minimizeCall" class="minimize-btn">−</button>
        <div class="call-status">
          <span class="status-text">{{ callStatusText }}</span>
          <div class="call-timer" v-if="callDuration > 0">
            {{ formatDuration(callDuration) }}
          </div>
        </div>
        <button @click="endCall" class="end-call-btn">×</button>
      </div>

      <!-- 联系人信息 -->
      <div class="contact-info">
        <div class="contact-avatar">
          <img v-if="contact?.avatar" :src="contact.avatar" :alt="contact.username" />
          <div v-else class="avatar-placeholder">
            {{ contact?.username?.[0]?.toUpperCase() || 'U' }}
          </div>
        </div>
        <h2 class="contact-name">{{ contact?.username || '未知联系人' }}</h2>
        <div class="connection-method">
          <span class="method-badge" :class="connectionMethod.toLowerCase()">
            {{ connectionMethod }}
          </span>
        </div>
      </div>

      <!-- 音频可视化 -->
      <div class="audio-visualizer" v-if="isCallActive">
        <div class="wave-container">
          <div 
            v-for="i in 20" 
            :key="i" 
            class="wave-bar"
            :style="{ height: waveHeights[i] + '%' }"
          ></div>
        </div>
      </div>

      <!-- 通话控制按钮 -->
      <div class="call-controls">
        <button 
          @click="toggleMute" 
          :class="['control-btn', 'mute-btn', { active: isMuted }]"
          :title="isMuted ? '取消静音' : '静音'"
        >
          <span class="btn-icon">{{ isMuted ? '🔇' : '🎤' }}</span>
          <span class="btn-label">{{ isMuted ? '已静音' : '麦克风' }}</span>
        </button>

        <button 
          @click="toggleSpeaker" 
          :class="['control-btn', 'speaker-btn', { active: isSpeakerOn }]"
          :title="isSpeakerOn ? '关闭扬声器' : '开启扬声器'"
        >
          <span class="btn-icon">{{ isSpeakerOn ? '🔊' : '🔈' }}</span>
          <span class="btn-label">{{ isSpeakerOn ? '扬声器' : '听筒' }}</span>
        </button>

        <button 
          @click="endCall" 
          class="control-btn end-btn"
          title="结束通话"
        >
          <span class="btn-icon">📞</span>
          <span class="btn-label">挂断</span>
        </button>
      </div>

      <!-- 通话质量指示器 -->
      <div class="call-quality" v-if="isCallActive">
        <div class="quality-indicator">
          <span class="quality-label">通话质量:</span>
          <div class="quality-bars">
            <div 
              v-for="i in 4" 
              :key="i" 
              :class="['quality-bar', { active: i <= callQuality }]"
            ></div>
          </div>
          <span class="quality-text">{{ getQualityText() }}</span>
        </div>
        <div class="network-info">
          <span>延迟: {{ networkStats.latency }}ms</span>
          <span>丢包: {{ networkStats.packetLoss }}%</span>
        </div>
      </div>
    </div>

    <!-- 音频元素 -->
    <audio ref="localAudio" muted></audio>
    <audio ref="remoteAudio" autoplay></audio>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { hybridStore } from '../store/hybrid-store';

const router = useRouter();

// 响应式数据
const contact = ref(null);
const callStatus = ref('connecting'); // connecting, ringing, active, ended
const callDuration = ref(0);
const isMuted = ref(false);
const isSpeakerOn = ref(false);
const callQuality = ref(3);
const waveHeights = ref(Array(20).fill(0).map(() => Math.random() * 100));
const networkStats = ref({
  latency: 45,
  packetLoss: 0.2
});

// 音频相关
const localAudio = ref(null);
const remoteAudio = ref(null);
const localStream = ref(null);
const peerConnection = ref(null);

// 定时器
let durationTimer = null;
let waveAnimationTimer = null;
let qualityCheckTimer = null;

// 计算属性
const callStatusText = computed(() => {
  switch (callStatus.value) {
    case 'connecting': return '正在连接...';
    case 'ringing': return '正在呼叫...';
    case 'active': return '通话中';
    case 'ended': return '通话已结束';
    default: return '未知状态';
  }
});

const connectionMethod = computed(() => {
  if (!contact.value) return 'Unknown';
  const p2pStatus = hybridStore.getP2PStatus(contact.value.id);
  return p2pStatus === 'connected' ? 'P2P' : 'Server';
});

const isCallActive = computed(() => callStatus.value === 'active');

// 生命周期
onMounted(async () => {
  // 从路由参数获取联系人信息
  const contactId = router.currentRoute.value.params.contactId;
  if (contactId) {
    contact.value = hybridStore.getContact(contactId);
  }
  
  await initializeCall();
  startTimers();
});

onUnmounted(() => {
  cleanup();
});

// 监听通话状态变化
watch(callStatus, (newStatus) => {
  if (newStatus === 'active') {
    startCallTimer();
  } else if (newStatus === 'ended') {
    cleanup();
  }
});

// 方法
async function initializeCall() {
  try {
    // 获取用户媒体权限
    localStream.value = await navigator.mediaDevices.getUserMedia({ 
      audio: true, 
      video: false 
    });
    
    if (localAudio.value) {
      localAudio.value.srcObject = localStream.value;
    }
    
    // 模拟连接过程
    setTimeout(() => {
      callStatus.value = 'ringing';
    }, 1000);
    
    setTimeout(() => {
      callStatus.value = 'active';
    }, 3000);
    
  } catch (error) {
    console.error('初始化通话失败:', error);
    alert('无法访问麦克风，请检查权限设置');
    endCall();
  }
}

function startTimers() {
  // 音频波形动画
  waveAnimationTimer = setInterval(() => {
    if (isCallActive.value && !isMuted.value) {
      waveHeights.value = waveHeights.value.map(() => 
        Math.random() * 80 + 20
      );
    } else {
      waveHeights.value = waveHeights.value.map(() => 5);
    }
  }, 100);
  
  // 通话质量检测
  qualityCheckTimer = setInterval(() => {
    if (isCallActive.value) {
      // 模拟网络质量变化
      callQuality.value = Math.floor(Math.random() * 4) + 1;
      networkStats.value.latency = Math.floor(Math.random() * 100) + 20;
      networkStats.value.packetLoss = Math.random() * 2;
    }
  }, 2000);
}

function startCallTimer() {
  durationTimer = setInterval(() => {
    callDuration.value++;
  }, 1000);
}

function toggleMute() {
  isMuted.value = !isMuted.value;
  if (localStream.value) {
    localStream.value.getAudioTracks().forEach(track => {
      track.enabled = !isMuted.value;
    });
  }
}

function toggleSpeaker() {
  isSpeakerOn.value = !isSpeakerOn.value;
  // 在实际应用中，这里需要切换音频输出设备
}

function minimizeCall() {
  // 最小化通话窗口，返回聊天界面但保持通话
  router.push('/chat');
}

function endCall() {
  callStatus.value = 'ended';
  cleanup();
  router.push('/chat');
}

function cleanup() {
  // 清理定时器
  if (durationTimer) {
    clearInterval(durationTimer);
    durationTimer = null;
  }
  if (waveAnimationTimer) {
    clearInterval(waveAnimationTimer);
    waveAnimationTimer = null;
  }
  if (qualityCheckTimer) {
    clearInterval(qualityCheckTimer);
    qualityCheckTimer = null;
  }
  
  // 停止媒体流
  if (localStream.value) {
    localStream.value.getTracks().forEach(track => track.stop());
    localStream.value = null;
  }
  
  // 关闭WebRTC连接
  if (peerConnection.value) {
    peerConnection.value.close();
    peerConnection.value = null;
  }
}

function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function getQualityText() {
  switch (callQuality.value) {
    case 1: return '差';
    case 2: return '一般';
    case 3: return '良好';
    case 4: return '优秀';
    default: return '未知';
  }
}

function goBack() {
  router.push('/chat');
}
</script>

<style scoped>
.voice-call-page {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.call-overlay {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
  text-align: center;
  color: white;
}

.call-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.minimize-btn,
.end-call-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.minimize-btn:hover,
.end-call-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.call-status {
  text-align: center;
}

.status-text {
  font-size: 1.1rem;
  opacity: 0.9;
}

.call-timer {
  font-size: 1.3rem;
  font-weight: bold;
  margin-top: 0.5rem;
}

.contact-info {
  margin-bottom: 3rem;
}

.contact-avatar {
  width: 120px;
  height: 120px;
  margin: 0 auto 1rem;
  border-radius: 50%;
  overflow: hidden;
  border: 4px solid rgba(255, 255, 255, 0.3);
}

.contact-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: bold;
}

.contact-name {
  font-size: 1.8rem;
  margin-bottom: 0.5rem;
  font-weight: 300;
}

.method-badge {
  padding: 0.3rem 0.8rem;
  border-radius: 15px;
  font-size: 0.9rem;
  font-weight: 500;
}

.method-badge.p2p {
  background: rgba(76, 175, 80, 0.3);
  border: 1px solid rgba(76, 175, 80, 0.5);
}

.method-badge.server {
  background: rgba(255, 193, 7, 0.3);
  border: 1px solid rgba(255, 193, 7, 0.5);
}

.audio-visualizer {
  margin: 2rem 0;
}

.wave-container {
  display: flex;
  justify-content: center;
  align-items: end;
  height: 60px;
  gap: 3px;
}

.wave-bar {
  width: 4px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 2px;
  transition: height 0.1s ease;
  min-height: 4px;
}

.call-controls {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  margin: 3rem 0;
}

.control-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 80px;
  min-height: 80px;
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.control-btn.active {
  background: rgba(255, 255, 255, 0.4);
}

.end-btn {
  background: rgba(244, 67, 54, 0.8) !important;
}

.end-btn:hover {
  background: rgba(244, 67, 54, 1) !important;
}

.btn-icon {
  font-size: 1.5rem;
}

.btn-label {
  font-size: 0.8rem;
  opacity: 0.9;
}

.call-quality {
  margin-top: 2rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
}

.quality-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.quality-bars {
  display: flex;
  gap: 2px;
}

.quality-bar {
  width: 4px;
  height: 12px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

.quality-bar.active {
  background: #4caf50;
}

.quality-label,
.quality-text {
  font-size: 0.9rem;
  opacity: 0.8;
}

.network-info {
  display: flex;
  justify-content: space-around;
  font-size: 0.8rem;
  opacity: 0.7;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .call-overlay {
    padding: 1rem;
  }
  
  .contact-avatar {
    width: 100px;
    height: 100px;
  }
  
  .contact-name {
    font-size: 1.5rem;
  }
  
  .call-controls {
    gap: 1rem;
  }
  
  .control-btn {
    min-width: 70px;
    min-height: 70px;
    padding: 0.8rem;
  }
}
</style>