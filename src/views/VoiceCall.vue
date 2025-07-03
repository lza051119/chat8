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
        <button v-if="callStatus !== 'ended' && callStatus !== 'rejected'" @click="endCall" class="end-call-btn">×</button>
        <button v-else @click="goBack" class="back-btn">返回</button>
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

// 响铃音效相关
const audioContext = ref(null);
const ringtoneOscillator = ref(null);
const ringtoneGain = ref(null);
const isRingtonePlaying = ref(false);

// 定时器
let durationTimer = null;
let waveAnimationTimer = null;
let qualityCheckTimer = null;
let ringtoneTimer = null;

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
  // 初始化音频上下文
  initializeAudioContext();
  
  // 从路由参数获取联系人信息
  const contactId = router.currentRoute.value.params.contactId;
  console.log('[VoiceCall] 路由参数 contactId:', contactId);
  console.log('[VoiceCall] 当前路由:', router.currentRoute.value);
  
  if (contactId) {
    contact.value = hybridStore.getContact(contactId);
    console.log('[VoiceCall] 获取到的联系人信息:', contact.value);
    console.log('[VoiceCall] 所有联系人列表:', hybridStore.getContacts());
  } else {
    console.error('[VoiceCall] 缺少 contactId 参数');
  }
  
  await initializeCall();
});

onUnmounted(() => {
  stopRingtone();
  cleanup();
});

// 监听通话状态变化
watch(callStatus, (newStatus) => {
  if (newStatus === 'active') {
    stopRingtone();
  } else if (newStatus === 'ended') {
    stopRingtone();
    cleanup();
  } else if (newStatus === 'ringing') {
    startRingtone();
  }
});

// 响铃音效方法
function initializeAudioContext() {
  try {
    audioContext.value = new (window.AudioContext || window.webkitAudioContext)();
    console.log('[VoiceCall] 音频上下文初始化成功');
  } catch (error) {
    console.error('[VoiceCall] 音频上下文初始化失败:', error);
  }
}

function startRingtone() {
  if (!audioContext.value || isRingtonePlaying.value) {
    return;
  }
  
  try {
    console.log('[VoiceCall] 开始播放响铃音');
    isRingtonePlaying.value = true;
    
    // 创建响铃音效的循环播放
    const playRingtoneOnce = () => {
      if (!isRingtonePlaying.value || !audioContext.value) {
        return;
      }
      
      // 创建振荡器和增益节点
      const oscillator = audioContext.value.createOscillator();
      const gainNode = audioContext.value.createGain();
      
      // 连接音频节点
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.value.destination);
      
      // 设置响铃音频参数（模拟电话铃声）
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(800, audioContext.value.currentTime);
      oscillator.frequency.setValueAtTime(1000, audioContext.value.currentTime + 0.4);
      
      // 设置音量包络
      gainNode.gain.setValueAtTime(0, audioContext.value.currentTime);
      gainNode.gain.linearRampToValueAtTime(0.3, audioContext.value.currentTime + 0.1);
      gainNode.gain.setValueAtTime(0.3, audioContext.value.currentTime + 0.4);
      gainNode.gain.linearRampToValueAtTime(0, audioContext.value.currentTime + 0.8);
      
      // 播放响铃音
      oscillator.start(audioContext.value.currentTime);
      oscillator.stop(audioContext.value.currentTime + 0.8);
      
      // 清理振荡器
      oscillator.onended = () => {
        oscillator.disconnect();
        gainNode.disconnect();
      };
    };
    
    // 立即播放第一次
    playRingtoneOnce();
    
    // 设置定时器循环播放（每2秒播放一次）
    ringtoneTimer = setInterval(() => {
      if (isRingtonePlaying.value) {
        playRingtoneOnce();
      }
    }, 2000);
    
  } catch (error) {
    console.error('[VoiceCall] 播放响铃音失败:', error);
    isRingtonePlaying.value = false;
  }
}

function stopRingtone() {
  if (!isRingtonePlaying.value) {
    return;
  }
  
  console.log('[VoiceCall] 停止播放响铃音');
  isRingtonePlaying.value = false;
  
  // 清理定时器
  if (ringtoneTimer) {
    clearInterval(ringtoneTimer);
    ringtoneTimer = null;
  }
  
  // 停止当前的振荡器
  if (ringtoneOscillator.value) {
    try {
      ringtoneOscillator.value.stop();
      ringtoneOscillator.value.disconnect();
    } catch (error) {
      // 忽略已经停止的振荡器错误
    }
    ringtoneOscillator.value = null;
  }
  
  if (ringtoneGain.value) {
    try {
      ringtoneGain.value.disconnect();
    } catch (error) {
      // 忽略已经断开连接的增益节点错误
    }
    ringtoneGain.value = null;
  }
}

// 方法
async function initializeCall() {
  try {
    console.log('[VoiceCall] 开始初始化通话');
    
    // 检查联系人信息是否有效
    if (!contact.value || !contact.value.id) {
      console.error('[VoiceCall] 联系人信息无效:', contact.value);
      throw new Error('联系人信息无效或缺失');
    }
    
    console.log('[VoiceCall] 联系人信息有效:', contact.value);
    
    const hybridMessaging = hybridStore.getHybridMessaging();
    if (!hybridMessaging) {
      console.error('[VoiceCall] HybridMessaging服务未初始化');
      throw new Error('消息服务未初始化，请先登录并等待服务启动');
    }
    
    console.log('[VoiceCall] HybridMessaging服务已获取');
    
    // 检查WebSocket连接状态 - 改进的连接检查逻辑
    let wsConnected = false;
    let wsStatus = 'unknown';
    
    if (hybridMessaging.ws) {
      wsStatus = hybridMessaging.ws.readyState;
      wsConnected = hybridMessaging.ws.readyState === WebSocket.OPEN;
    }
    
    console.log('[VoiceCall] WebSocket状态检查:', {
      hasWs: !!hybridMessaging.ws,
      readyState: wsStatus,
      connected: wsConnected
    });
    
    // 如果WebSocket未连接，尝试等待连接建立
    if (!wsConnected) {
      console.log('[VoiceCall] WebSocket未连接，尝试等待连接建立...');
      
      // 等待最多3秒让WebSocket连接建立
      const maxWaitTime = 3000;
      const startTime = Date.now();
      
      while (Date.now() - startTime < maxWaitTime) {
        if (hybridMessaging.ws && hybridMessaging.ws.readyState === WebSocket.OPEN) {
          wsConnected = true;
          console.log('[VoiceCall] WebSocket连接已建立');
          break;
        }
        
        // 等待100ms后再次检查
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      // 如果仍然未连接，抛出错误
      if (!wsConnected) {
        const currentState = hybridMessaging.ws?.readyState;
        const stateText = currentState === WebSocket.CONNECTING ? '正在连接' : 
                         currentState === WebSocket.CLOSING ? '正在关闭' : 
                         currentState === WebSocket.CLOSED ? '已关闭' : '未知状态';
        console.error('[VoiceCall] WebSocket连接超时，当前状态:', stateText);
        throw new Error(`网络连接不可用 (${stateText})，请检查网络连接后重试`);
      }
    }
    
    console.log('[VoiceCall] WebSocket连接状态正常');
    
    // 设置语音通话回调
    hybridMessaging.onVoiceCallStatusChanged = handleVoiceCallStatusChange;
    hybridMessaging.onVoiceCallRejected = handleVoiceCallRejected;
    
    // 检查是否是接听来电还是发起通话
    const callInfo = hybridStore.getCurrentCallInfo;
    console.log('[VoiceCall] 当前通话信息:', callInfo);
    
    // 检查是否已经有活跃的语音连接（在acceptCall中已经处理过）
    const existingConnection = hybridMessaging.voiceConnections.get(contact.value.id);
    const currentVoiceCall = hybridMessaging.currentVoiceCall;
    
    if (existingConnection && currentVoiceCall && currentVoiceCall.userId.toString() === contact.value.id.toString()) {
      // 通话已经在acceptCall中处理过，只需要设置UI状态
      console.log('[VoiceCall] 通话已在acceptCall中处理，设置UI状态');
      callStatus.value = 'connecting';
      
      // 设置本地音频流
      if (hybridMessaging.localStream) {
        if (localAudio.value) {
          localAudio.value.srcObject = hybridMessaging.localStream;
        }
        localStream.value = hybridMessaging.localStream;
      }
      
      // 检查是否已经有远程流
      const remoteStream = hybridMessaging.remoteStreams.get(contact.value.id);
      if (remoteStream && remoteAudio.value) {
        remoteAudio.value.srcObject = remoteStream;
        activateCall();
      }
      
      // 根据当前通话状态设置UI
      if (currentVoiceCall.status === 'active') {
        activateCall();
      } else if (currentVoiceCall.type === 'outgoing') {
        callStatus.value = 'ringing';
      }
      
    } else if (callInfo && callInfo.type === 'incoming' && callInfo.fromUserId.toString() === contact.value.id.toString()) {
      // 这是一个新的来电，需要接听
      console.log('[VoiceCall] 检测到新来电，开始接听');
      callStatus.value = 'connecting';
      try {
        const result = await hybridMessaging.acceptVoiceCall(contact.value.id, callInfo.offer);
        if (localAudio.value && result.localStream) {
          localAudio.value.srcObject = result.localStream;
          localStream.value = result.localStream;
        }
        console.log('[VoiceCall] 来电接听成功，等待连接建立');
      } catch (error) {
        console.error('[VoiceCall] 接听失败:', error);
        throw new Error('接听通话失败');
      }
    } else {
      // 发起新通话
      console.log('[VoiceCall] 发起通话给用户:', contact.value.id);
      callStatus.value = 'connecting';
      const result = await hybridMessaging.initiateVoiceCall(contact.value.id);
      if (localAudio.value && result.localStream) {
        localAudio.value.srcObject = result.localStream;
        localStream.value = result.localStream;
      }
      callStatus.value = 'ringing';
      console.log('[VoiceCall] 通话发起成功');
    }
    
  } catch (error) {
    console.error('[VoiceCall] 初始化通话失败:', error);
    
    // 根据错误类型提供更具体的错误信息
    let errorMessage = '通话初始化失败';
    if (error.message.includes('WebSocket') || error.message.includes('网络')) {
      errorMessage = '网络连接异常，请检查网络后重试';
    } else if (error.message.includes('消息服务')) {
      errorMessage = '服务未就绪，请稍后重试';
    } else if (error.message.includes('联系人')) {
      errorMessage = '联系人信息异常，请返回重新选择';
    } else {
      errorMessage = `通话初始化失败: ${error.message}`;
    }
    
    alert(errorMessage);
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

// 处理语音通话状态变化
function handleVoiceCallStatusChange(event) {
  console.log('[语音通话] 状态变化:', event);
  
  switch (event.type) {
    case 'remote_stream_received':
      if (remoteAudio.value && event.stream) {
        remoteAudio.value.srcObject = event.stream;
        activateCall();
        console.log('[语音通话] 远程音频流已接收，通话已激活');
      }
      break;
      
    case 'call_connected':
      activateCall();
      console.log('[语音通话] 通话已连接');
      break;
      
    case 'call_accepted':
      console.log('[语音通话] 通话已被接受');
      break;
      
    case 'call_rejected':
      alert('对方拒绝了通话');
      // 设置状态但不调用endCall，避免递归
      callStatus.value = 'rejected';
      cleanup();
      // 被拒绝时延迟2秒后自动返回
      setTimeout(() => {
        goBack();
      }, 2000);
      break;
      
    case 'call_ended_local':
      // 本地主动结束通话，直接返回聊天界面
      console.log('[语音通话] 本地主动结束通话');
      callStatus.value = 'ended';
      cleanup();
      router.push('/chat');
      break;
      
    case 'call_ended_remote':
      // 远程结束通话，返回聊天界面但不刷新
      console.log('[语音通话] 远程结束通话');
      callStatus.value = 'ended';
      cleanup();
      router.push('/chat');
      break;
      
    case 'call_ended':
      // 兼容旧的通话结束事件
      console.log('[语音通话] 通话结束');
      callStatus.value = 'ended';
      cleanup();
      router.push('/chat');
      break;
      
    case 'connection_state_changed':
      if (event.state === 'connected') {
        activateCall();
        console.log('[语音通话] 连接状态变为已连接');
      } else if (event.state === 'failed' || event.state === 'disconnected') {
        console.log('[语音通话] 连接失败或断开:', event.state);
        // 设置状态但不调用endCall，避免递归
        callStatus.value = 'ended';
        cleanup();
        // 连接失败时延迟2秒后自动返回
        setTimeout(() => {
          goBack();
        }, 2000);
      }
      break;
  }
}

// 激活通话状态
function activateCall() {
  if (callStatus.value !== 'active') {
    callStatus.value = 'active';
    startTimers(); // 在此处启动UI计时器
    startCallTimer(); // 在此处启动通话时长计时器
    // 通话成功建立后，清理来电信息
    const callInfo = hybridStore.getCurrentCallInfo;
    if (callInfo && callInfo.type === 'incoming') {
      console.log('[VoiceCall] 通话已建立，清理来电信息');
      hybridStore.clearCurrentCallInfo();
    }
  }
}

function toggleMute() {
  const hybridMessaging = hybridStore.getHybridMessaging();
  if (hybridMessaging) {
    const muted = hybridMessaging.toggleMute();
    isMuted.value = muted;
  } else if (localStream.value) {
    isMuted.value = !isMuted.value;
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
  // 防止重复调用导致递归
  if (callStatus.value === 'ended') {
    console.log('[VoiceCall] 通话已结束，跳过重复调用');
    return;
  }
  
  console.log('[VoiceCall] 开始结束通话');
  callStatus.value = 'ended';
  
  const hybridMessaging = hybridStore.getHybridMessaging();
  if (hybridMessaging && contact.value) {
    console.log(`[VoiceCall] 发送通话结束信号给用户 ${contact.value.id}`);
    hybridMessaging.endVoiceCall(contact.value.id);
  }
  
  cleanup();
  // 移除自动跳转，让用户手动返回以避免界面刷新导致通话记录丢失
  // router.push('/chat');
}

function handleVoiceCallRejected({ fromUserId }) {
  if (contact.value && fromUserId.toString() === contact.value.id.toString()) {
    console.log(`[语音通话] ${contact.value.username} 拒绝了通话`);
    callStatus.value = 'rejected';
    
    // 立即清理资源并结束通话
    const hybridMessaging = hybridStore.getHybridMessaging();
    if (hybridMessaging && contact.value) {
      console.log(`[VoiceCall] 对方拒绝通话，立即结束通话`);
      // 不需要再发送结束信号，因为对方已经拒绝了
      // hybridMessaging.endVoiceCall(contact.value.id);
    }
    
    cleanup();
    
    // 显示拒绝提示后自动返回
    setTimeout(() => {
      goBack();
    }, 2000);
  }
}

function cleanup() {
  console.log('[VoiceCall] 开始清理资源');
  
  // 停止响铃音效
  stopRingtone();
  
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
  if (ringtoneTimer) {
    clearInterval(ringtoneTimer);
    ringtoneTimer = null;
  }
  
  // 不要清理全局的语音通话回调，因为其他用户可能还需要接收通话状态变化
  // 只清理本地的回调引用
  const hybridMessaging = hybridStore.getHybridMessaging();
  if (hybridMessaging) {
    console.log('[VoiceCall] 保留全局状态变化回调，仅清理本地引用');
  }
  
  // 清理通话信息
  hybridStore.clearCurrentCallInfo();
  
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
  
  // 关闭音频上下文
  if (audioContext.value) {
    try {
      audioContext.value.close();
      audioContext.value = null;
    } catch (error) {
      console.error('[VoiceCall] 关闭音频上下文失败:', error);
    }
  }
  
  console.log('[VoiceCall] 资源清理完成');
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
.end-call-btn,
.back-btn {
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
.end-call-btn:hover,
.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.back-btn {
  font-size: 0.9rem;
  width: 60px;
  border-radius: 20px;
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