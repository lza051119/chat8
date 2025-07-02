import { getLocalKey, saveLocalKey, deleteLocalKey } from '@/utils/key-storage';
import { addMessage } from '@/client_db/database';
import { hybridStore } from '@/store/hybrid-store';

// 混合消息传递服务
class HybridMessaging {
  constructor() {
    this.ws = null;                    // WebSocket连接（C/S信令）
    this.p2pConnections = new Map();   // P2P连接池 { userId: WebRTCDataChannel }
    this.peerConnections = new Map();  // WebRTC连接池
    this.currentUserId = null;
    this.token = null;
    this.onMessageReceived = null;     // 消息接收回调
    this.onUserStatusChanged = null;   // 用户状态变化回调
    this.onP2PStatusChanged = null;    // P2P连接状态变化回调
    this.isReconnecting = false;       // 重连状态标志
    this.reconnectAttempts = 0;        // 重连尝试次数
    this.maxReconnectAttempts = 5;     // 最大重连次数
    this.preConnectQueue = new Set();  // 预连接队列
    this.connectionAttempts = new Map(); // 连接尝试记录 { userId: { attempts: number, lastAttempt: timestamp } }
    
    // 语音通话相关
    this.voiceConnections = new Map();  // 语音连接池 { userId: RTCPeerConnection }
    this.localStream = null;            // 本地音频流
    this.remoteStreams = new Map();     // 远程音频流 { userId: MediaStream }
    this.pendingIceCandidates = new Map(); // 缓存待处理的ICE候选 { userId: Array<RTCIceCandidateInit> }
    this.onVoiceCallReceived = null;    // 语音通话接收回调
    this.onVoiceCallRejected = null;    // 语音通话拒绝回调
    this.onVoiceCallStatusChanged = null; // 语音通话状态变化回调
    this.currentVoiceCall = null;       // 当前语音通话信息
  }

  // 初始化混合消息系统
  async initialize(userId, token) {
    this.currentUserId = userId;
    this.token = token;
    
    console.log(`[初始化] 开始初始化混合消息系统，用户ID: ${userId}`);
    
    // 清理可能残留的通话状态
    this.cleanupAllVoiceCalls();
    
    // 建立WebSocket连接用于信令
    await this.connectSignalingServer();
    console.log('[初始化] WebSocket连接已建立');
    
    // 注册用户为支持P2P
    try {
      await this.registerP2PCapability();
      console.log('[初始化] P2P能力注册成功');
    } catch (error) {
      console.warn('[初始化] P2P能力注册失败，但系统将继续运行:', error.message);
    }
    
    // 设置页面关闭时的清理逻辑
    this.setupBeforeUnloadHandler();
    
    console.log('[初始化] 混合消息系统初始化完成');
  }

  // 连接信令服务器（C/S）
  async connectSignalingServer() {
    return new Promise((resolve, reject) => {
      // 使用相对路径，让Vite代理自动路由到正确的后端端口
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${this.currentUserId}?token=${this.token}`;
      console.log(`[WebSocket] 连接到: ${wsUrl}`);
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = async () => {
        console.log('信令服务器连接成功');
        
        // 设置信令处理器
        this.setupSignalingHandlers();
        
        // 重置重连状态
        this.isReconnecting = false;
        this.reconnectAttempts = 0;
        
        // 启动连接健康检查
        this.startConnectionHealthCheck();
        
        // WebSocket连接建立时立即发送在线状态给好友
        try {
          // 动态导入hybridApi以避免循环依赖
          const { hybridApi } = await import('@/api/hybrid-api.js');
          await hybridApi.setOnlineStatus('online');
        } catch (error) {
          console.warn('[状态同步] 发送在线状态失败:', error);
        }
        
        resolve();
      };
      
      this.ws.onerror = reject;
      this.ws.onclose = async (event) => {
        console.log('信令服务器连接断开', { code: event.code, reason: event.reason });
        
        // 清理所有P2P连接
        this.p2pConnections.forEach((connection, userId) => {
          try {
            connection.close();
          } catch (error) {
            console.warn(`[P2P] 关闭与用户 ${userId} 的P2P连接失败:`, error);
          }
        });
        this.p2pConnections.clear();
        
        this.peerConnections.forEach((peerConnection, userId) => {
          try {
            peerConnection.close();
          } catch (error) {
            console.warn(`[P2P] 关闭与用户 ${userId} 的WebRTC连接失败:`, error);
          }
        });
        this.peerConnections.clear();
        
        // 清理语音通话状态
        this.cleanupAllVoiceCalls();
        
        // WebSocket断开时立即发送离线状态给好友
        try {
          // 动态导入hybridApi以避免循环依赖
          const { hybridApi } = await import('@/api/hybrid-api.js');
          await hybridApi.setOnlineStatus('offline');
        } catch (error) {
          console.warn('[状态同步] 发送离线状态失败:', error);
        }
        
        // 智能重连逻辑
        if (!this.isReconnecting && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.isReconnecting = true;
          this.reconnectAttempts++;
          const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 10000); // 指数退避，最大10秒
          
          setTimeout(async () => {
            try {
              await this.connectSignalingServer();
              this.reconnectAttempts = 0; // 重连成功，重置计数器
              console.log('WebSocket重连成功');
            } catch (error) {
              console.error('WebSocket重连失败:', error);
            } finally {
              this.isReconnecting = false;
            }
          }, delay);
        } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          console.error('WebSocket重连次数已达上限，停止重连');
        }
      };
    });
  }

  // 设置信令处理
  setupSignalingHandlers() {
    this.ws.onmessage = async (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch (error) {
        console.error('[WebSocket] 消息解析失败:', error, '原始数据:', event.data);
        return;
      }
      
      // 验证消息基本结构
      if (!data || typeof data !== 'object' || !data.type) {
        console.error('[WebSocket] 收到无效消息格式:', data);
        return;
      }
      
      console.log('[WebSocket] 收到消息:', data.type, '来自:', data.from_id);
      
      switch (data.type) {
        case 'webrtc_offer':
          console.log('[P2P] 收到webrtc_offer，完整数据:', JSON.stringify(data, null, 2));
          // 验证 offer 数据的有效性
          if (data.payload && data.payload.type && data.payload.sdp) {
            await this.handleP2POffer({
              from: data.from_id,
              offer: data.payload
            });
          } else {
            console.error('[P2P] 收到无效的 webrtc_offer，payload 格式错误:', data.payload);
            console.error('[P2P] 完整消息数据:', JSON.stringify(data, null, 2));
            console.error('[P2P] payload类型:', typeof data.payload, '是否存在:', !!data.payload);
          }
          break;

        case 'webrtc_answer':
          // 验证 answer 数据的有效性
          if (data.payload && data.payload.type && data.payload.sdp) {
            await this.handleP2PAnswer({
              from: data.from_id,
              answer: data.payload
            });
          } else {
            console.error('[P2P] 收到无效的 webrtc_answer，payload 格式错误:', data.payload);
          }
          break;

        case 'webrtc_ice_candidate':
          console.log('[P2P] 收到webrtc_ice_candidate，完整数据:', JSON.stringify(data, null, 2));
          // 验证 ICE candidate 数据的有效性
          if (data.payload && (data.payload.candidate || data.payload.candidate === '')) {
            await this.handleIceCandidate({
              from: data.from_id,
              candidate: data.payload
            });
          } else {
            console.error('[P2P] 收到无效的 webrtc_ice_candidate，payload 格式错误:', data.payload);
            console.error('[P2P] 完整消息数据:', JSON.stringify(data, null, 2));
            console.error('[P2P] payload类型:', typeof data.payload, '是否存在:', !!data.payload);
          }
          break;

        case 'voice_call_offer':
          console.log(`[信令] 收到来自 ${data.from_id} 的语音通话offer`);
          console.log('[信令] 完整的offer数据:', data);
          // 检查是否已有活跃通话，避免重复处理
          if (this.currentVoiceCall && this.currentVoiceCall.status === 'active') {
            console.log('[信令] 已有活跃通话，忽略新的来电');
            break;
          }
          
          // 立即设置当前通话信息，确保状态同步
          this.currentVoiceCall = {
            userId: data.from_id,
            status: 'incoming',
            type: 'incoming',
            startTime: Date.now()
          };
          console.log('[信令] 设置currentVoiceCall:', this.currentVoiceCall);
          
          const callInfo = {
            type: 'incoming',
            fromUserId: data.from_id,
            offer: data.payload || data.offer
          };
          console.log('[信令] 构建的callInfo:', callInfo);
          hybridStore.setCurrentCallInfo(callInfo);
          console.log('[信令] callInfo已保存到store');
          if (this.onVoiceCallReceived) {
            console.log('[信令] 调用onVoiceCallReceived回调');
            this.onVoiceCallReceived(callInfo);
            console.log('[信令] onVoiceCallReceived回调调用完成');
          } else {
            console.warn('[信令] onVoiceCallReceived 回调未设置，无法处理来电');
          }
          break;

        case 'voice_call_answer':
          console.log(`[信令] 收到来自 ${data.from_id} 的语音通话answer`);
          await this.handleVoiceAnswer({
            from: data.from_id,
            answer: data.payload || data.answer
          });
          break;

        case 'voice_call_reject':
          console.log(`[信令] 收到来自 ${data.from_id} 的通话拒绝信令`);
          if (this.onVoiceCallRejected) {
            this.onVoiceCallRejected({ fromUserId: data.from_id });
          }
          // Also call the generic status changed for compatibility
          if (this.onVoiceCallStatusChanged) {
            this.onVoiceCallStatusChanged({
              type: 'call_rejected',
              userId: data.from_id
            });
          }
          this.cleanupVoiceCall(data.from_id);
          // 强制清理当前通话状态，确保下次通话能正常进行
          this.currentVoiceCall = null;
          console.log('[语音通话] 收到对方拒绝通话信号，强制清理当前通话状态');
          break;

        case 'voice_call_end':
          if (this.onVoiceCallStatusChanged) {
            this.onVoiceCallStatusChanged({
              type: 'call_ended',
              userId: data.from_id
            });
          }
          this.cleanupVoiceCall(data.from_id);
          // 强制清理当前通话状态，确保下次通话能正常进行
          this.currentVoiceCall = null;
          console.log('[语音通话] 收到对方结束通话信号，强制清理当前通话状态');
          break;

        case 'voice_ice_candidate':
          console.log(`[信令] 收到来自 ${data.from_id} 的ICE Candidate`);
          await this.handleVoiceIceCandidate({
            from: data.from_id,
            candidate: data.payload || data.candidate
          });
          break;

        case 'private_message':
          await this.handleServerMessage(data);
          break;

        case 'typing_start':
        case 'typing_stop':
          if (this.onTypingStatusChanged) {
            this.onTypingStatusChanged({
              userId: data.from_id,
              isTyping: data.type === 'typing_start'
            });
          }
          break;

        case 'presence':
          // 验证presence消息格式
          if (data.userId !== undefined && data.status !== undefined && data.isOnline !== undefined && 
              data.timestamp && data.websocketConnected !== undefined && data.p2pCapability !== undefined) {
            // 兼容性处理：如果userId是字符串，转换为数字
            let userId = data.userId;
            if (typeof userId === 'string') {
              const parsedUserId = parseInt(userId, 10);
              if (!isNaN(parsedUserId)) {
                userId = parsedUserId;
              } else {
                console.warn('presence消息中的userId无法转换为数字:', userId);
              }
            }
            
            if (this.onUserStatusChanged) {
              this.onUserStatusChanged({
                ...data,
                userId: userId // 使用转换后的userId
              });
            }
          } else {
            console.warn('收到无效的presence消息，缺少必要字段:', {
              原始数据: data,
              userId: data.userId,
              userId类型: typeof data.userId,
              status: data.status,
              status类型: typeof data.status,
              isOnline: data.isOnline,
              isOnline类型: typeof data.isOnline,
              timestamp: data.timestamp,
              timestamp类型: typeof data.timestamp,
              websocketConnected: data.websocketConnected,
              websocketConnected类型: typeof data.websocketConnected,
              p2pCapability: data.p2pCapability,
              p2pCapability类型: typeof data.p2pCapability
            });
          }
          break;

        case 'user_status':
          // 兼容旧格式的用户状态消息
          if (data.userId && typeof data.userId === 'number' && data.userId > 0 && 
              data.status && typeof data.status === 'string') {
            if (this.onUserStatusChanged) {
              this.onUserStatusChanged({
                userId: data.userId,
                status: data.status,
                isOnline: data.status === 'online'
              });
            }
          } else {
            console.warn('收到无效的user_status消息:', data);
          }
          break;

        default:
          console.warn('未处理的消息类型:', data.type);
      }
    };
  }

  // 注册P2P能力
  async registerP2PCapability() {
    try {
      // 动态导入hybridApi以避免循环依赖
      const { hybridApi } = await import('@/api/hybrid-api.js');
      const result = await hybridApi.registerP2PCapability({
        supportsP2P: true,
        capabilities: ['webrtc', 'datachannel']
      });
      
      // 验证注册是否成功
      const statusCheck = await this.checkUserStatus(this.currentUserId);
      
    } catch (error) {
      console.error('[P2P] P2P能力注册失败:', error);
      throw error; // 重新抛出错误，让调用者知道注册失败
    }
  }

  // 预连接到指定用户（在打开聊天窗口时调用）
  async preConnectToUser(toUserId) {
    // 检查是否已经有连接
    if (this.p2pConnections.has(toUserId)) {
      return { success: true, method: 'P2P', existing: true };
    }
    
    // 检查连接尝试频率限制
    const attempts = this.connectionAttempts.get(toUserId);
    const now = Date.now();
    if (attempts && attempts.attempts >= 3 && (now - attempts.lastAttempt) < 60000) {
      console.log(`[预连接] 用户 ${toUserId} 连接频率受限，跳过预连接`);
      return { success: false, reason: 'rate_limited' };
    }
    
    // 检查用户状态
    try {
      const userStatus = await this.checkUserStatus(toUserId);
      
      if (!userStatus.online || !userStatus.supportsP2P) {
        console.log(`[预连接] 用户 ${toUserId} 离线或不支持P2P，跳过预连接`);
        return { success: false, reason: 'not_supported' };
      }
      
      // 记录连接尝试
      const currentAttempts = attempts ? attempts.attempts + 1 : 1;
      this.connectionAttempts.set(toUserId, {
        attempts: currentAttempts,
        lastAttempt: now
      });
      
      // 尝试建立P2P连接
      this.preConnectQueue.add(toUserId);
      const connection = await this.establishP2PConnection(toUserId);
      this.preConnectQueue.delete(toUserId);
      
      // 重置连接尝试计数
      this.connectionAttempts.delete(toUserId);
      
      return { success: true, method: 'P2P', connection };
      
    } catch (error) {
      this.preConnectQueue.delete(toUserId);
      // P2P连接失败是正常情况，不应该抛出错误影响其他功能
      console.log(`[预连接] 用户 ${toUserId} P2P连接失败，将使用服务器转发:`, error.message);
      return { success: false, reason: 'connection_failed', error: error.message };
    }
  }
  
  // 智能发送消息（严格遵守：只要两个用户都在线就使用P2P连接）
  async sendMessage(toUserId, content) {
    try {
      console.log(`[发送消息] 开始发送消息给用户 ${toUserId}`);
      
      // 首先检查用户状态
      const userStatus = await this.checkUserStatus(toUserId);
      console.log(`[发送消息] 用户状态:`, userStatus);
      
      // 严格规则：只要两个用户都在线，就必须使用P2P连接
      if (userStatus.online) {
        console.log(`[发送消息] 用户在线，强制使用P2P连接`);
        
        // 优先使用已建立的P2P连接
        if (this.p2pConnections.has(toUserId)) {
          console.log(`[发送消息] 使用已建立的P2P连接`);
          try {
            const p2pResult = await this.sendP2PMessage(toUserId, content);
            if (p2pResult.success) {
              console.log(`[发送消息] P2P发送成功:`, p2pResult);
              return { success: true, method: 'P2P', ...p2pResult };
            }
          } catch (p2pError) {
            console.warn(`[发送消息] 已建立的P2P连接失效，清理并重新建立:`, p2pError);
            // 清理失效的连接
            this.p2pConnections.delete(toUserId);
            if (this.peerConnections.has(toUserId)) {
              this.peerConnections.get(toUserId).close();
              this.peerConnections.delete(toUserId);
            }
          }
        }
        
        // 如果没有连接或连接失效，强制建立新的P2P连接
        console.log(`[发送消息] 用户在线，强制建立P2P连接`);
        try {
          const p2pResult = await this.sendP2PMessage(toUserId, content);
          if (p2pResult.success) {
            console.log(`[发送消息] P2P发送成功:`, p2pResult);
            return { success: true, method: 'P2P', ...p2pResult };
          }
        } catch (p2pError) {
          console.error(`[发送消息] P2P连接建立失败，但用户在线，这违反了严格规则:`, p2pError);
          // 即使P2P失败，也要记录这是一个异常情况
          console.error(`[发送消息] 警告：用户 ${toUserId} 在线但P2P连接失败，可能存在网络问题`);
          
          // 作为最后手段，使用服务器转发，但要明确标记这是异常情况
          console.log(`[发送消息] 异常情况：回退到服务器转发模式`);
          const serverResult = await this.sendServerMessage(toUserId, content);
          console.log(`[发送消息] 服务器转发结果:`, serverResult);
          return { ...serverResult, warning: 'P2P_FAILED_FOR_ONLINE_USER' };
        }
      } else {
        // 用户离线，使用服务器转发
        console.log(`[发送消息] 用户离线，使用服务器转发`);
        const serverResult = await this.sendServerMessage(toUserId, content);
        console.log(`[发送消息] 服务器转发结果:`, serverResult);
        return serverResult;
      }
      
    } catch (error) {
      console.error('发送消息失败:', error);
      return { success: false, error: error.message };
    }
  }

  // 检查用户状态（C/S API）
  async checkUserStatus(userId) {
    try {
      console.log(`[状态检查] 开始检查用户 ${userId} 的状态`);
      const { hybridApi } = await import('../api/hybrid-api.js');
      const response = await hybridApi.getUserStatus(userId);
      
      // 修复：后端返回格式是 {success: true, data: status}，需要获取 response.data.data
      const userStatus = response.data?.data || response.data;
      console.log(`[状态检查] API响应:`, response.data);
      console.log(`[状态检查] 用户 ${userId} 状态:`, userStatus);
      console.log(`[状态检查] 详细字段检查:`, {
        'userStatus.online': userStatus.online,
        'userStatus.isOnline': userStatus.isOnline,
        'userStatus.supportsP2P': userStatus.supportsP2P,
        'userStatus.p2pCapability': userStatus.p2pCapability,
        'userStatus.websocketConnected': userStatus.websocketConnected
      });
      
      // 确保返回标准化的状态格式
      const normalizedStatus = {
        online: userStatus.online || userStatus.isOnline || false,
        supportsP2P: userStatus.supportsP2P || userStatus.p2pCapability || false,
        lastSeen: userStatus.lastSeen,
        websocketConnected: userStatus.websocketConnected || false
      };
      
      console.log(`[状态检查] 标准化后的用户 ${userId} 状态:`, normalizedStatus);
      return normalizedStatus;
      
    } catch (error) {
      console.warn(`[状态检查] 检查用户 ${userId} 状态失败，假设离线:`, error);
      return { online: false, supportsP2P: false };
    }
  }

  // P2P直连发送消息
  async sendP2PMessage(toUserId, content) {
    try {
      let dataChannel = this.p2pConnections.get(toUserId);
      
      if (!dataChannel || dataChannel.readyState !== 'open') {
        // 建立新的P2P连接
        dataChannel = await this.establishP2PConnection(toUserId);
      }
      
      // 发送消息
      const message = {
        type: 'direct_message',
        from: this.currentUserId,
        content: content,
        timestamp: new Date().toISOString()
      };
      
      dataChannel.send(JSON.stringify(message));
      
      // 存储发送的P2P消息到数据库
      try {
        await addMessage({
          from: this.currentUserId,
          to: toUserId,
          content: content,
          timestamp: message.timestamp,
          method: 'P2P',
          encrypted: false
        });
        console.log('发送的P2P消息已存储到数据库');
      } catch (error) {
        console.error('存储P2P消息到数据库失败:', error);
      }
      
      return { 
        success: true, 
        method: 'P2P',
        id: `p2p_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: message.timestamp 
      };
      
    } catch (error) {
      console.warn('P2P发送失败:', error);
      return { success: false, error: error.message };
    }
  }

  // 建立P2P连接
  async establishP2PConnection(toUserId) {
    return new Promise(async (resolve, reject) => {
      let isResolved = false; // 防止重复resolve/reject
      
      const safeResolve = (value) => {
        if (!isResolved) {
          isResolved = true;
          resolve(value);
        }
      };
      
      const safeReject = (error) => {
        if (!isResolved) {
          isResolved = true;
          reject(error);
        }
      };
      
      try {
        // 创建WebRTC连接
        const peerConnection = new RTCPeerConnection({
          iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
        });

        // 创建数据通道
        const dataChannel = peerConnection.createDataChannel('messages', {
          ordered: true
        });

        // 数据通道事件处理
        dataChannel.onopen = () => {
          console.log(`P2P连接已建立: ${toUserId}`);
          clearTimeout(timeout); // 清除超时定时器
          this.p2pConnections.set(toUserId, dataChannel);
          
          // 通知store更新P2P连接状态
          if (this.onP2PStatusChanged) {
            this.onP2PStatusChanged(toUserId, 'connected');
          }
          
          safeResolve(dataChannel);
        };

        dataChannel.onerror = (error) => {
          console.error(`P2P数据通道错误: ${toUserId}`, error);
          clearTimeout(timeout);
          safeReject(error);
        };

        dataChannel.onmessage = async (event) => {
          const message = JSON.parse(event.data);
          if (message.type === 'direct_message' && this.onMessageReceived) {
            const msgData = {
              from: message.from,
              to: this.currentUserId, // P2P消息是发给当前用户的
              content: message.content,
              timestamp: message.timestamp,
              method: 'P2P'
            };
            
            // 存入本地数据库
            try {
              await addMessage(msgData);
              console.log('P2P消息已保存到本地数据库');
            } catch (dbError) {
              console.warn('保存P2P消息到本地数据库失败:', dbError);
            }
            
            this.onMessageReceived(msgData);
          }
        };

        // ICE候选事件
        peerConnection.onicecandidate = (event) => {
          if (event.candidate) {
            console.log(`[P2P] Sending ICE candidate to ${toUserId}`);
            // 检查WebSocket连接状态
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
              this.ws.send(JSON.stringify({
                type: 'webrtc_ice_candidate',
                to_id: toUserId,
                payload: event.candidate
              }));
            } else {
              console.warn(`[P2P] WebSocket连接不可用，无法发送ICE候选到用户 ${toUserId}`);
              // WebSocket断开时，直接拒绝P2P连接
              clearTimeout(timeout);
              safeReject(new Error('WebSocket连接断开，P2P连接失败'));
            }
          }
        };

        // 存储连接以便后续使用
        this.peerConnections.set(toUserId, peerConnection);

        // 创建offer
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        // 发送offer
        this.sendSignalingMessage(toUserId, 'webrtc_offer', offer);
        console.log(`[P2P] Offer sent to ${toUserId}`);

        // 设置20秒超时
        const timeout = setTimeout(() => {
          if (!isResolved) {
            console.log(`[P2P] P2P连接超时，连接状态=${peerConnection.connectionState}, ICE状态=${peerConnection.iceConnectionState}`);
            this.peerConnections.delete(toUserId);
            safeReject(new Error(`P2P连接超时: 连接状态=${peerConnection.connectionState}, ICE状态=${peerConnection.iceConnectionState}`));
          }
        }, 20000);

        // 监听连接状态变化
        peerConnection.onconnectionstatechange = () => {
          console.log(`[P2P] 连接状态变化: ${peerConnection.connectionState}`);
          if (peerConnection.connectionState === 'connected') {
            clearTimeout(timeout);
            console.log(`[P2P] 连接成功，清除超时定时器`);
            safeResolve(dataChannel);
          } else if (peerConnection.connectionState === 'failed') {
            clearTimeout(timeout);
            this.peerConnections.delete(toUserId);
            console.warn(`[P2P] 连接失败: ${peerConnection.connectionState}`);
            safeReject(new Error(`P2P连接失败: ${peerConnection.connectionState}`));
          } else if (peerConnection.connectionState === 'disconnected' ||
                     peerConnection.connectionState === 'closed') {
            clearTimeout(timeout);
            this.peerConnections.delete(toUserId);
            console.log(`[P2P] 连接已断开或关闭: ${peerConnection.connectionState}`);
          }
        };

        // 监听ICE连接状态变化
        peerConnection.oniceconnectionstatechange = () => {
          console.log(`[P2P] ICE连接状态变化: ${peerConnection.iceConnectionState}`);
          if (peerConnection.iceConnectionState === 'connected' || 
              peerConnection.iceConnectionState === 'completed') {
            clearTimeout(timeout);
            console.log(`[P2P] ICE连接成功，清除超时定时器`);
            // 如果还没有通过connectionState resolve，这里也可以resolve
            if (peerConnection.connectionState !== 'connected') {
              safeResolve(dataChannel);
            }
          } else if (peerConnection.iceConnectionState === 'failed') {
            clearTimeout(timeout);
            this.peerConnections.delete(toUserId);
            console.warn(`[P2P] ICE连接失败: ${peerConnection.iceConnectionState}`);
            safeReject(new Error(`P2P ICE连接失败: ${peerConnection.iceConnectionState}`));
          } else if (peerConnection.iceConnectionState === 'disconnected' ||
                     peerConnection.iceConnectionState === 'closed') {
            clearTimeout(timeout);
            this.peerConnections.delete(toUserId);
            console.log(`[P2P] ICE连接已断开或关闭: ${peerConnection.iceConnectionState}`);
          }
        };

      } catch (error) {
        console.error(`[P2P] 建立P2P连接时发生错误:`, error);
        safeReject(error);
      }
    });
  }

  // 处理P2P Offer
  async handleP2POffer(data) {
    try {
      // 再次验证 offer 数据
      if (!data.offer || !data.offer.type || !data.offer.sdp) {
        throw new Error('Invalid offer data: missing type or sdp');
      }
      
      console.log(`[P2P] 处理来自 ${data.from} 的 offer:`, data.offer);
      
      const peerConnection = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });

      // 设置远程描述
      await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));

      // 监听数据通道
      peerConnection.ondatachannel = (event) => {
        const dataChannel = event.channel;
        
        dataChannel.onopen = () => {
          console.log(`P2P连接已接受: ${data.from}`);
          this.p2pConnections.set(data.from, dataChannel);
          
          // 通知store更新P2P连接状态
          if (this.onP2PStatusChanged) {
            this.onP2PStatusChanged(data.from, 'connected');
          }
        };

        dataChannel.onmessage = async (event) => {
          const message = JSON.parse(event.data);
          if (message.type === 'direct_message' && this.onMessageReceived) {
            const msgData = {
              from: message.from,
              to: this.currentUserId, // P2P消息是发给当前用户的
              content: message.content,
              timestamp: message.timestamp,
              method: 'P2P'
            };
            
            // 存入本地数据库
            try {
              await addMessage(msgData);
              console.log('P2P消息已保存到本地数据库');
            } catch (dbError) {
              console.warn('保存P2P消息到本地数据库失败:', dbError);
            }
            
            this.onMessageReceived(msgData);
          }
        };
      };

      // ICE候选事件
      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          console.log(`[P2P] Sending ICE candidate to ${data.from}`);
          // 检查WebSocket连接状态
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
              type: 'webrtc_ice_candidate',
              to_id: data.from,
              payload: event.candidate
            }));
          } else {
            console.warn(`[P2P] WebSocket连接不可用，无法发送ICE候选到用户 ${data.from}`);
          }
        }
      };

      // 创建Answer
      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);

      // 发送Answer
      console.log(`[P2P] Sending answer to ${data.from}`);
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'webrtc_answer',
          to_id: data.from,
          payload: answer
        }));
      } else {
        console.error(`[P2P] WebSocket连接不可用，无法发送Answer到用户 ${data.from}`);
        return;
      }

      this.peerConnections.set(data.from, peerConnection);

    } catch (error) {
      console.error('处理P2P Offer失败:', error);
    }
  }

  // 处理P2P Answer
  async handleP2PAnswer(data) {
    console.log(`[P2P] Received answer from ${data.from}`);
    try {
      // 验证 answer 数据
      if (!data.answer || !data.answer.type || !data.answer.sdp) {
        throw new Error('Invalid answer data: missing type or sdp');
      }
      
      console.log(`[P2P] 处理来自 ${data.from} 的 answer:`, data.answer);
      
      const peerConnection = this.peerConnections.get(data.from);
      if (peerConnection) {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
        console.log(`[P2P] Remote description set for ${data.from}`);
      } else {
        console.warn(`[P2P] 未找到用户 ${data.from} 的 peer connection`);
      }
    } catch (error) {
      console.error('处理P2P Answer失败:', error);
    }
  }

  // 处理ICE候选
  async handleIceCandidate(data) {
    console.log(`[P2P] Received ICE candidate from ${data.from}`);
    try {
      // 验证 candidate 数据
      if (!data.candidate || typeof data.candidate !== 'object') {
        throw new Error('Invalid candidate data: not an object');
      }
      
      console.log(`[P2P] 处理来自 ${data.from} 的 ICE candidate:`, data.candidate);
      
      const peerConnection = this.peerConnections.get(data.from);
      if (!peerConnection) {
        console.warn(`[P2P] 未找到用户 ${data.from} 的 peer connection`);
        return;
      }
      
      // 确保在添加ICE候选之前，远程描述已经设置
      if (peerConnection.remoteDescription) {
        await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
        console.log(`[P2P] Added ICE candidate for ${data.from}`);
      } else {
        console.warn(`[P2P] Received ICE candidate before remote description was set for ${data.from}.`);
        // 可以考虑将候选者暂存起来，等待远程描述设置后再添加
      }
    } catch (error) {
      console.error('处理ICE候选失败:', error);
    }
  }

  // 发送信令消息（用于语音通话）
  sendSignalingMessage(toUserId, messageType, payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: messageType,
        to_id: toUserId,
        payload: payload
      };
      
      console.log(`[信令] 发送${messageType}消息给用户 ${toUserId}:`, payload);
      this.ws.send(JSON.stringify(message));
    } else {
      console.error(`[信令] WebSocket连接不可用，无法发送${messageType}消息`);
      throw new Error('WebSocket连接不可用');
    }
  }

  // 服务器转发消息（C/S模式）
  async sendServerMessage(toUserId, content) {
    try {
      console.log('发送服务器消息:', { toUserId, content });
      
      const { hybridApi } = await import('../api/hybrid-api.js');
      const response = await hybridApi.sendMessage({
        to: toUserId,
        content: content,
        encrypted: false,
        method: 'Server'
      });

      const result = response.data;
      console.log('服务器响应结果:', result);
      
      // 存储发送的服务器消息到数据库
      try {
        const sentMsgData = {
          from: this.currentUserId,
          to: toUserId,
          content: content,
          timestamp: result.timestamp || new Date().toISOString(),
          method: 'Server'
        };
        await addMessage(sentMsgData);
        console.log('发送的服务器消息已保存到本地数据库');
      } catch (dbError) {
        console.warn('保存发送的服务器消息到本地数据库失败:', dbError);
      }
      
      return { 
        success: true, 
        method: 'Server',
        id: result.id || result.message_id,
        timestamp: result.timestamp
      };

    } catch (error) {
      console.error('sendServerMessage错误:', error);
      return { success: false, error: error.message };
    }
  }

  // 处理服务器转发的消息
  async handleServerMessage(data) {
    const msgData = {
      id: data.id || `msg_${data.from}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      from: data.from,
      to: this.currentUserId,
      content: data.content,
      timestamp: data.timestamp,
      method: 'Server',
      // 添加图片消息支持
      messageType: data.messageType || data.message_type || 'text',
      filePath: data.filePath || data.file_path || null,
      fileName: data.fileName || data.file_name || null,
      // 添加隐写术支持
      hiddenMessage: data.hiddenMessage || data.hidden_message || null
    };
    
    // 存入本地数据库
    try {
      await addMessage(msgData);
      console.log('服务器消息已保存到本地数据库');
    } catch (dbError) {
      console.warn('保存服务器消息到本地数据库失败:', dbError);
    }
    
    if (this.onMessageReceived) {
      this.onMessageReceived(msgData);
    }
  }

  // 获取消息历史（C/S API）
  async getMessageHistory(userId) {
    try {
      const { hybridApi } = await import('../api/hybrid-api.js');
      const response = await hybridApi.getMessageHistory(userId);

      return response.data;

    } catch (error) {
      console.error('获取消息历史失败:', error);
      return [];
    }
  }

  // 关闭P2P连接
  closeP2PConnection(userId) {
    const dataChannel = this.p2pConnections.get(userId);
    const peerConnection = this.peerConnections.get(userId);

    if (dataChannel) {
      dataChannel.close();
      this.p2pConnections.delete(userId);
    }

    if (peerConnection) {
      peerConnection.close();
      this.peerConnections.delete(userId);
    }
    
    // 通知store更新P2P连接状态
    if (this.onP2PStatusChanged) {
      this.onP2PStatusChanged(userId, 'disconnected');
    }
  }

  // 设置页面关闭时的处理逻辑
  setupBeforeUnloadHandler() {
    // 页面关闭前发送离线状态
    window.addEventListener('beforeunload', (event) => {
      try {
        // 使用同步的XMLHttpRequest确保在页面关闭时能发送请求
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/presence/status', false); // 同步请求
        xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify({ status: 'offline' }));
        console.log('[离线] 已发送离线状态');
      } catch (error) {
        console.warn('[离线] 发送离线状态失败:', error);
      }
    });
    
    // 注释：移除页面隐藏时发送离线状态的逻辑
    // 现在只要页面打开（无论前台还是后台）都视为在线状态
    // document.addEventListener('visibilitychange', async () => {
    //   if (document.hidden) {
    //     try {
    //       // 页面隐藏时使用同步请求
    //       const xhr = new XMLHttpRequest();
    //       xhr.open('POST', '/api/presence/status', false); // 同步请求
    //       xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
    //       xhr.setRequestHeader('Content-Type', 'application/json');
    //       xhr.send(JSON.stringify({ status: 'offline' }));
    //       console.log('[离线] 页面隐藏，已发送离线状态');
    //     } catch (error) {
    //       console.warn('[离线] 页面隐藏时发送离线状态失败:', error);
    //     }
    //   }
    // });
  }
  
  // 获取P2P连接状态
  getP2PConnectionStatus(userId) {
    const connection = this.p2pConnections.get(userId);
    if (!connection) {
      return { connected: false, status: 'disconnected' };
    }
    
    return {
      connected: connection.readyState === 'open',
      status: connection.readyState,
      bufferedAmount: connection.bufferedAmount || 0
    };
  }
  
  // 获取所有P2P连接状态
  getAllP2PConnectionStatus() {
    const status = {};
    this.p2pConnections.forEach((connection, userId) => {
      status[userId] = this.getP2PConnectionStatus(userId);
    });
    return status;
  }
  
  // 定期清理无效连接
  startConnectionHealthCheck() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
    
    this.healthCheckInterval = setInterval(() => {
      console.log('[连接健康检查] 开始检查P2P连接状态');
      
      // 检查并清理无效的P2P连接
      const toRemove = [];
      this.p2pConnections.forEach((connection, userId) => {
        if (connection.readyState === 'closed' || connection.readyState === 'closing') {
          console.log(`[连接健康检查] 发现无效连接，用户 ${userId}，状态: ${connection.readyState}`);
          toRemove.push(userId);
        }
      });
      
      toRemove.forEach(userId => {
        this.p2pConnections.delete(userId);
        if (this.peerConnections.has(userId)) {
          try {
            this.peerConnections.get(userId).close();
          } catch (error) {
            console.warn(`[连接健康检查] 关闭WebRTC连接失败:`, error);
          }
          this.peerConnections.delete(userId);
        }
        console.log(`[连接健康检查] 已清理用户 ${userId} 的无效连接`);
      });
      
      // 清理过期的连接尝试记录
      const now = Date.now();
      this.connectionAttempts.forEach((attempts, userId) => {
        if (now - attempts.lastAttempt > 300000) { // 5分钟后清理
          this.connectionAttempts.delete(userId);
          console.log(`[连接健康检查] 已清理用户 ${userId} 的过期连接尝试记录`);
        }
      });
      
    }, 60000); // 每分钟检查一次
  }
  
  // 停止连接健康检查
  stopConnectionHealthCheck() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
  }
  
  // 清理资源
  cleanup() {
    console.log('清理HybridMessaging资源');
    
    // 停止健康检查
    this.stopConnectionHealthCheck();
    
    // 关闭所有P2P连接
    this.p2pConnections.forEach((connection, userId) => {
      try {
        connection.close();
        console.log(`已关闭与用户 ${userId} 的P2P连接`);
      } catch (error) {
        console.warn(`关闭与用户 ${userId} 的P2P连接失败:`, error);
      }
    });
    this.p2pConnections.clear();
    
    this.peerConnections.forEach((peerConnection, userId) => {
      try {
        peerConnection.close();
        console.log(`已关闭与用户 ${userId} 的WebRTC连接`);
      } catch (error) {
        console.warn(`关闭与用户 ${userId} 的WebRTC连接失败:`, error);
      }
    });
    this.peerConnections.clear();
    
    // 清理其他状态
    this.preConnectQueue.clear();
    this.connectionAttempts.clear();
    
    // 关闭WebSocket连接
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  // 设置离线状态
  async setOfflineStatus() {
    try {
      const { hybridApi } = await import('../api/hybrid-api.js');
      await hybridApi.setOnlineStatus('offline');
      console.log('[离线] 已发送离线状态');
    } catch (error) {
      console.warn('[离线] 发送离线状态失败:', error);
    }
  }

  // ==================== 语音通话功能 ====================
  
  // 发起语音通话
  async initiateVoiceCall(toUserId) {
    try {
      console.log(`[语音通话] 发起通话给用户 ${toUserId}`);
      
      // 检查参数有效性
      if (!toUserId) {
        throw new Error('目标用户ID无效');
      }
      
      // 检查WebSocket连接状态
      if (!this.ws) {
        throw new Error('WebSocket连接未建立，请检查网络连接');
      }
      
      if (this.ws.readyState !== WebSocket.OPEN) {
        const stateText = this.ws.readyState === WebSocket.CONNECTING ? '正在连接' : 
                         this.ws.readyState === WebSocket.CLOSING ? '正在关闭' : '已关闭';
        throw new Error(`WebSocket连接不可用 (状态: ${stateText})，请检查网络连接`);
      }
      
      // 检查是否已有通话进行中
      if (this.currentVoiceCall) {
        console.warn('[语音通话] 检测到残留的通话状态，正在清理...');
        this.cleanupAllVoiceCalls();
      }
      
      // 获取本地音频流
      console.log('[语音通话] 请求访问麦克风...');
      try {
        this.localStream = await navigator.mediaDevices.getUserMedia({ 
          audio: true, 
          video: false 
        });
        console.log('[语音通话] 麦克风访问成功');
      } catch (mediaError) {
        console.error('[语音通话] 麦克风访问失败:', mediaError);
        if (mediaError.name === 'NotAllowedError') {
          throw new Error('麦克风访问被拒绝，请允许麦克风权限后重试');
        } else if (mediaError.name === 'NotFoundError') {
          throw new Error('未找到可用的麦克风设备');
        } else {
          throw new Error(`麦克风访问失败: ${mediaError.message}`);
        }
      }
      
      // 创建WebRTC连接
      console.log('[语音通话] 创建WebRTC连接...');
      let peerConnection;
      try {
        peerConnection = new RTCPeerConnection({
          iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
        });
        console.log('[语音通话] WebRTC连接创建成功');
      } catch (rtcError) {
        console.error('[语音通话] WebRTC连接创建失败:', rtcError);
        throw new Error(`WebRTC连接创建失败: ${rtcError.message}`);
      }
      
      // 添加本地音频流到连接
      console.log('[语音通话] 添加本地音频流到WebRTC连接...');
      try {
        this.localStream.getTracks().forEach(track => {
          peerConnection.addTrack(track, this.localStream);
        });
        console.log('[语音通话] 本地音频流添加成功');
      } catch (trackError) {
        console.error('[语音通话] 添加音频流失败:', trackError);
        throw new Error(`添加音频流失败: ${trackError.message}`);
      }
      
      // 处理远程音频流
      peerConnection.ontrack = (event) => {
        console.log(`[语音通话] 收到远程音频流`);
        const remoteStream = event.streams[0];
        this.remoteStreams.set(toUserId, remoteStream);
        
        if (this.onVoiceCallStatusChanged) {
          this.onVoiceCallStatusChanged({
            type: 'remote_stream_received',
            userId: toUserId,
            stream: remoteStream
          });
        }
      };
      
      // ICE候选处理
      peerConnection.onicecandidate = (event) => {
        if (event.candidate && this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({
            type: 'voice_ice_candidate',
            to_id: toUserId,
            payload: event.candidate
          }));
        }
      };
      
      // 连接状态监听
      peerConnection.onconnectionstatechange = () => {
        console.log(`[语音通话] 连接状态变化: ${peerConnection.connectionState}`);
        if (this.onVoiceCallStatusChanged) {
          this.onVoiceCallStatusChanged({
            type: 'connection_state_changed',
            userId: toUserId,
            state: peerConnection.connectionState
          });
        }
        
        if (peerConnection.connectionState === 'failed' || 
            peerConnection.connectionState === 'disconnected') {
          this.endVoiceCall(toUserId);
        }
      };
      
      // 创建offer
      console.log('[语音通话] 创建通话offer...');
      let offer;
      try {
        offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        console.log('[语音通话] Offer创建并设置成功');
      } catch (offerError) {
        console.error('[语音通话] 创建offer失败:', offerError);
        throw new Error(`创建通话offer失败: ${offerError.message}`);
      }
      
      // 保存连接
      this.voiceConnections.set(toUserId, peerConnection);
      this.currentVoiceCall = {
        userId: toUserId,
        status: 'calling',
        startTime: Date.now(),
        type: 'outgoing'
      };
      
      // 发送通话邀请
      console.log('[语音通话] 发送通话邀请...');
      try {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({
            type: 'voice_call_offer',
            to_id: toUserId,
            payload: offer
          }));
          console.log('[语音通话] 通话邀请发送成功');
        } else {
          throw new Error('WebSocket连接不可用');
        }
      } catch (sendError) {
        console.error('[语音通话] 发送通话邀请失败:', sendError);
        throw new Error(`发送通话邀请失败: ${sendError.message}`);
      }
      
      // 通知状态变化
      if (this.onVoiceCallStatusChanged) {
        this.onVoiceCallStatusChanged({
          type: 'call_initiated',
          userId: toUserId,
          localStream: this.localStream
        });
      }
      
      return { success: true, localStream: this.localStream };
      
    } catch (error) {
      console.error('[语音通话] 发起通话失败:', error);
      
      // 清理资源
      try {
        this.cleanupVoiceCall(toUserId);
        
        // 如果本地流已创建但通话失败，需要停止流
        if (this.localStream) {
          this.localStream.getTracks().forEach(track => {
            track.stop();
          });
          this.localStream = null;
        }
      } catch (cleanupError) {
        console.warn('[语音通话] 清理资源时出错:', cleanupError);
      }
      
      // 重新抛出原始错误
      throw error;
    }
  }
  
  // 接受语音通话
  async acceptVoiceCall(fromUserId, offer) {
    try {
      console.log(`[语音通话] 接受来自用户 ${fromUserId} 的通话`);
      
      // 设置当前通话信息 - 这是关键修复
      this.currentVoiceCall = {
        userId: fromUserId,
        status: 'connecting',
        type: 'incoming',
        startTime: Date.now()
      };
      
      // 获取本地音频流
      this.localStream = await navigator.mediaDevices.getUserMedia({ 
        audio: true, 
        video: false 
      });
      
      // 创建WebRTC连接
      const peerConnection = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });
      
      // 添加本地音频流
      this.localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, this.localStream);
      });
      
      // 处理远程音频流
      peerConnection.ontrack = (event) => {
        console.log('[语音通话] 接收到远程音频流');
        this.remoteStreams.set(fromUserId, event.streams[0]);
        
        // 触发状态变化事件
        if (this.onVoiceCallStatusChanged) {
          this.onVoiceCallStatusChanged({
            type: 'remote_stream_received',
            userId: fromUserId,
            stream: event.streams[0]
          });
        }
      };
      
      // 处理ICE候选
      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          console.log('[语音通话] 发送ICE候选');
          this.sendSignalingMessage(fromUserId, 'voice_ice_candidate', {
            candidate: event.candidate
          });
        }
      };
      
      // 处理连接状态变化
      peerConnection.onconnectionstatechange = () => {
        console.log(`[语音通话] 连接状态变化: ${peerConnection.connectionState}`);
        if (peerConnection.connectionState === 'connected') {
          // 更新通话状态为活跃
          if (this.currentVoiceCall) {
            this.currentVoiceCall.status = 'active';
          }
        }
      };
      
      // 存储连接
      this.voiceConnections.set(fromUserId, peerConnection);
      
      // 设置远程描述
      await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
      
      // 创建应答
      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);
      
      // 发送应答
       this.sendSignalingMessage(fromUserId, 'voice_call_answer', {
         answer: answer
       });
       
       // 处理缓存的ICE候选
       await this.processPendingIceCandidates(fromUserId);
       
       console.log('[语音通话] 通话接听成功，等待连接建立');
      
      return {
        success: true,
        localStream: this.localStream
      };
      
    } catch (error) {
      console.error('[语音通话] 接听失败:', error);
      this.cleanupVoiceCall(fromUserId);
      throw error;
    }
  }
  
  // 拒绝语音通话
  async rejectVoiceCall(fromUserId) {
    console.log(`[语音通话] 拒绝来自用户 ${fromUserId} 的通话`);
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'voice_call_reject',
        to_id: fromUserId
      }));
    }
    
    this.cleanupVoiceCall(fromUserId);
    
    // 强制清理当前通话状态，确保下次通话能正常进行
    this.currentVoiceCall = null;
    console.log('[语音通话] 强制清理当前通话状态');
  }
  
  // 结束语音通话
  async endVoiceCall(userId) {
    console.log(`[语音通话] 结束与用户 ${userId} 的通话`);
    
    // 检查是否已经结束，防止重复调用导致递归
    if (!this.currentVoiceCall) {
      console.log('[语音通话] 通话已结束，跳过重复调用');
      return;
    }
    
    // 发送结束通话信号
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'voice_call_end',
        to_id: userId
      }));
    }
    
    this.cleanupVoiceCall(userId);
    
    // 强制清理当前通话状态，确保下次通话能正常进行
    this.currentVoiceCall = null;
    console.log('[语音通话] 强制清理当前通话状态');
    
    // 通知状态变化（只在第一次调用时通知）
    if (this.onVoiceCallStatusChanged) {
      this.onVoiceCallStatusChanged({
        type: 'call_ended',
        userId: userId
      });
    }
  }
  
  // 清理语音通话资源
  cleanupVoiceCall(userId) {
    console.log(`[语音通话] 清理用户 ${userId} 的语音通话资源`);
    
    // 关闭WebRTC连接
    const peerConnection = this.voiceConnections.get(userId);
    if (peerConnection) {
      peerConnection.close();
      this.voiceConnections.delete(userId);
    }
    
    // 清理缓存的ICE候选
    this.pendingIceCandidates.delete(userId);
    
    // 停止本地音频流
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }
    
    // 清理远程音频流
    this.remoteStreams.delete(userId);
    
    // 清理当前通话信息
    if (this.currentVoiceCall && this.currentVoiceCall.userId === userId) {
      this.currentVoiceCall = null;
    }
    
    // 清理store中的通话信息
    const currentCallInfo = hybridStore.currentCallInfo;
    if (currentCallInfo && currentCallInfo.fromUserId == userId) {
      console.log(`[语音通话] 清理store中的currentCallInfo`);
      hybridStore.clearCurrentCallInfo();
    }
  }
  


  // 清理所有语音通话资源
  cleanupAllVoiceCalls() {
    console.log('[语音通话] 清理所有语音通话资源');
    
    // 关闭所有语音连接
    this.voiceConnections.forEach((peerConnection, userId) => {
      try {
        peerConnection.close();
      } catch (error) {
        console.warn(`[语音通话] 关闭与用户 ${userId} 的语音连接失败:`, error);
      }
    });
    this.voiceConnections.clear();
    
    // 清理所有缓存的ICE候选
    this.pendingIceCandidates.clear();
    
    // 停止本地音频流
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }
    
    // 清理所有远程音频流
    this.remoteStreams.clear();
    
    // 清理当前通话信息
    this.currentVoiceCall = null;
  }
  
  // 处理语音通话ICE候选
  async handleVoiceIceCandidate(data) {
    console.log(`[语音通话] 收到来自 ${data.from} 的ICE Candidate`);
    console.log(`[语音通话] 当前通话状态:`, {
      currentVoiceCall: this.currentVoiceCall,
      currentCallInfo: hybridStore.currentCallInfo,
      hasConnection: this.voiceConnections.has(data.from)
    });
    
    const peerConnection = this.voiceConnections.get(data.from);
    if (!peerConnection) {
      // 检查是否有来电信息或当前通话信息
      const currentCallInfo = hybridStore.currentCallInfo;
      const hasIncomingCall = currentCallInfo && currentCallInfo.fromUserId == data.from;
      const hasOutgoingCall = currentCallInfo && currentCallInfo.toUserId == data.from;
      const hasCurrentCall = this.currentVoiceCall && this.currentVoiceCall.userId == data.from;
      const hasAnyCallInfo = currentCallInfo !== null;
      
      console.log(`[语音通话] ICE候选检查:`, {
        hasIncomingCall,
        hasOutgoingCall,
        hasCurrentCall,
        hasAnyCallInfo,
        fromUserId: data.from,
        callInfoFromUserId: currentCallInfo?.fromUserId,
        callInfoToUserId: currentCallInfo?.toUserId
      });
      
      // 改进逻辑：只有在确实有相关通话时才缓存ICE候选
      // 更严格的判断条件：必须有明确的通话关系
      if (hasIncomingCall || hasOutgoingCall || hasCurrentCall) {
        console.log(`[语音通话] 连接未建立，缓存ICE候选等待连接建立`);
        // 缓存ICE候选，等待连接建立
        if (!this.pendingIceCandidates.has(data.from)) {
          this.pendingIceCandidates.set(data.from, []);
        }
        this.pendingIceCandidates.get(data.from).push(data.candidate);
        console.log(`[语音通话] 已缓存ICE候选，当前缓存数量: ${this.pendingIceCandidates.get(data.from).length}`);
        return;
      } else {
        console.log(`[语音通话] 忽略来自用户 ${data.from} 的ICE候选（无相关通话）`);
        return;
      }
    }

    try {
      // 确保远程描述已设置
      if (peerConnection.remoteDescription) {
        await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
        console.log(`[语音通话] ICE候选添加成功`);
      } else {
        console.log(`[语音通话] 远程描述未设置，缓存ICE候选`);
        // 缓存ICE候选，等待远程描述设置
        if (!this.pendingIceCandidates.has(data.from)) {
          this.pendingIceCandidates.set(data.from, []);
        }
        this.pendingIceCandidates.get(data.from).push(data.candidate);
        console.log(`[语音通话] 已缓存ICE候选，当前缓存数量: ${this.pendingIceCandidates.get(data.from).length}`);
      }
    } catch (error) {
      console.error('[语音通话] 添加ICE候选失败:', error);
    }
  }
  
  // 处理语音通话Answer
  async handleVoiceAnswer(data) {
    const peerConnection = this.voiceConnections.get(data.from);
    if (!peerConnection) {
      console.warn(`[语音通话] 未找到用户 ${data.from} 的语音连接`);
      return;
    }

    try {
      await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
      console.log(`[语音通话] 设置远程描述成功`);
      
      // 处理缓存的ICE候选
      await this.processPendingIceCandidates(data.from);
      
      if (this.currentVoiceCall) {
        this.currentVoiceCall.status = 'active';
      }
      
      if (this.onVoiceCallStatusChanged) {
        this.onVoiceCallStatusChanged({
          type: 'call_connected',
          userId: data.from
        });
      }
    } catch (error) {
      console.error('[语音通话] 设置远程描述失败:', error);
    }
  }
  
  // 切换麦克风静音状态
  toggleMute() {
    if (this.localStream) {
      const audioTracks = this.localStream.getAudioTracks();
      audioTracks.forEach(track => {
        track.enabled = !track.enabled;
      });
      return !audioTracks[0]?.enabled;
    }
    return false;
  }
  
  // 获取当前通话状态
  getCurrentVoiceCallStatus() {
    return this.currentVoiceCall;
  }
  
  // 获取远程音频流
  getRemoteAudioStream(userId) {
    return this.remoteStreams.get(userId);
  }
  
  // 处理缓存的ICE候选
  async processPendingIceCandidates(userId) {
    const pendingCandidates = this.pendingIceCandidates.get(userId);
    if (!pendingCandidates || pendingCandidates.length === 0) {
      return;
    }

    const peerConnection = this.voiceConnections.get(userId);
    if (!peerConnection) {
      console.warn(`[语音通话] 处理缓存ICE候选时未找到用户 ${userId} 的连接`);
      return;
    }

    console.log(`[语音通话] 处理 ${pendingCandidates.length} 个缓存的ICE候选`);
    
    for (const candidate of pendingCandidates) {
      try {
        await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
        console.log(`[语音通话] 添加缓存的ICE候选成功`);
      } catch (error) {
        console.error('[语音通话] 添加缓存的ICE候选失败:', error);
      }
    }
    
    // 清理已处理的候选
    this.pendingIceCandidates.delete(userId);
  }

  // 强制重置通话状态（用于调试和错误恢复）
  forceResetVoiceCallState() {
    console.log('[语音通话] 强制重置通话状态');
    this.cleanupAllVoiceCalls();
    return { success: true, message: '通话状态已重置' };
  }
}

export default HybridMessaging;