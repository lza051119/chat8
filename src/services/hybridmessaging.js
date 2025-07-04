import { getLocalKey, saveLocalKey, deleteLocalKey } from '@/utils/key-storage';
import { addMessage } from '@/client_db/database';

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
    // 预连接功能已删除
    
    // 初始化语音通话状态
    this.initVoiceCallState();
    
    // 消息处理器映射 - 延迟初始化
    this.messageHandlers = {};
  }

  // 初始化混合消息系统
  async initialize(userId, token) {
    this.currentUserId = userId;
    this.token = token;
    
    console.log(`[初始化] 开始初始化混合消息系统，用户ID: ${userId}`);
    
    // 初始化消息处理器映射
    this.initializeMessageHandlers();
    
    // 建立WebSocket连接用于信令
    await this.connectSignalingServer();
    console.log('[初始化] WebSocket连接已建立');
    
    // P2P能力注册功能已移除
    console.log('[初始化] P2P能力注册功能已移除');
    
    // 设置页面关闭时的清理逻辑
    this.setupBeforeUnloadHandler();
    
    console.log('[初始化] 混合消息系统初始化完成');
  }

  // 初始化消息处理器映射
  initializeMessageHandlers() {
    this.messageHandlers = {
      'p2p_offer': this.handleP2POffer.bind(this),
      'p2p_answer': this.handleP2PAnswer.bind(this),
      'ice_candidate': this.handleIceCandidate.bind(this),
      'user_status_update': this.handleUserStatusUpdate.bind(this),
      'message': this.handleServerMessage.bind(this),
      'voice_call_offer': this.handleVoiceCallOffer.bind(this),
      'voice_call_answer': this.handleVoiceCallAnswer.bind(this),
      'voice_call_ice_candidate': this.handleVoiceCallIceCandidate.bind(this),
      'voice_call_rejected': this.handleVoiceCallRejected.bind(this),
      'voice_call_ended': this.handleVoiceCallEnded.bind(this)
    };
  }

  // 连接信令服务器（C/S）
  async connectSignalingServer() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`ws://localhost:8000/ws/${this.currentUserId}?token=${this.token}`);
      
      this.ws.onopen = async () => {
        console.log('信令服务器连接成功');
        
        // 设置信令处理器
        this.setupSignalingHandlers();
        
        // 重置重连状态
        this.isReconnecting = false;
        this.reconnectAttempts = 0;
        
        // 启动连接健康检查
        this.startConnectionHealthCheck();
        
        // 在线状态同步功能已移除
        console.log('[状态同步] 在线状态同步功能已移除');
        
        resolve();
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket连接错误:', error);
        console.error('WebSocket URL:', `ws://localhost:8000/ws/${this.currentUserId}?token=${this.token}`);
        console.error('Token存在:', !!this.token);
        console.error('Token长度:', this.token ? this.token.length : 0);
        reject(error);
      };
      this.ws.onclose = async (event) => {
        console.log('信令服务器连接断开', { code: event.code, reason: event.reason });
        
        // 详细的错误代码分析
        if (event.code === 1008) {
          console.error('❌ WebSocket认证失败 (错误代码1008)');
          console.error('可能原因: Token无效、过期或用户ID不匹配');
          console.error('当前Token:', this.token ? `${this.token.substring(0, 20)}...` : 'null');
          console.error('当前用户ID:', this.currentUserId);
        } else if (event.code === 1006) {
          console.error('❌ WebSocket异常关闭 (错误代码1006)');
          console.error('可能原因: 网络连接问题或服务器无响应');
        } else {
          console.log(`WebSocket关闭代码: ${event.code}, 原因: ${event.reason || '未知'}`);
        }
        
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
        
        // 离线状态同步功能已移除
        console.log('[状态同步] 离线状态同步功能已移除');
        
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
      const data = JSON.parse(event.data);
      console.log('[WebSocket] 收到消息:', data.type, data);
      
      switch (data.type) {
        case 'webrtc_offer':
          await this.handleP2POffer({
            from: data.from_id,
            offer: data.payload
          });
          break;

        case 'webrtc_answer':
          await this.handleP2PAnswer({
            from: data.from_id,
            answer: data.payload
          });
          break;

        case 'webrtc_ice_candidate':
          await this.handleIceCandidate({
            from: data.from_id,
            candidate: data.payload
          });
          break;

        case 'user_status_update':
          if (this.onUserStatusChanged) {
            this.onUserStatusChanged({
              userId: data.user_id,
              status: data.status,
              lastSeen: data.last_seen
            });
          }
          break;

        case 'message':
          await this.handleServerMessage(data);
          break;
          
        // 语音通话相关消息处理
        case 'voice_call_offer':
        case 'voice_call_answer':
        case 'voice_call_ice_candidate':
        case 'voice_call_rejected':
        case 'voice_call_ended':
          const handler = this.messageHandlers[data.type];
          if (handler) {
            await handler(data);
          }
          break;

        case 'heartbeat_response':
          this.handleHeartbeatResponse();
          break;

        default:
          console.log('未知消息类型:', data.type, data);
          break;
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket连接关闭:', event.code, event.reason);
      
      if (!this.isReconnecting && this.reconnectAttempts < this.maxReconnectAttempts) {
        console.log(`开始重连，尝试次数: ${this.reconnectAttempts + 1}`);
        this.isReconnecting = true;
        
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connectSignalingServer().catch(error => {
            console.error('重连失败:', error);
            this.isReconnecting = false;
          });
        }, 2000 * this.reconnectAttempts); // 递增延迟
      } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('达到最大重连次数，停止重连');
        this.isReconnecting = false;
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };
  }

  // P2P能力注册功能已移除
  async registerP2PCapability() {
    console.log('[P2P] P2P能力注册功能已移除');
  }

  // 预连接功能已删除
  
  // 智能发送消息（自动选择P2P或C/S）
  async sendMessage(toUserId, content, options = {}) {
    try {
      console.log(`[发送消息] 开始发送消息给用户 ${toUserId}`);
      
      // 优先使用已建立的P2P连接
      if (this.p2pConnections.has(toUserId)) {
        console.log(`[发送消息] 使用已建立的P2P连接`);
        try {
          const p2pResult = await this.sendP2PMessage(toUserId, content, options);
          if (p2pResult.success) {
            console.log(`[发送消息] P2P发送成功:`, p2pResult);
            return { success: true, method: 'P2P', ...p2pResult };
          }
        } catch (p2pError) {
          console.warn(`[发送消息] P2P发送失败，移除连接并降级到服务器转发:`, p2pError);
          // 清理失效的连接
          this.p2pConnections.delete(toUserId);
          if (this.peerConnections.has(toUserId)) {
            this.peerConnections.get(toUserId).close();
            this.peerConnections.delete(toUserId);
          }
        }
      }
      
      // 检查用户状态并尝试即时P2P连接
      const userStatus = await this.checkUserStatus(toUserId);
      console.log(`[发送消息] 用户状态:`, userStatus);
      
      if (userStatus.online && userStatus.supportsP2P) {
        console.log(`[发送消息] 用户在线且支持P2P，尝试即时P2P连接`);
        try {
          const p2pResult = await this.sendP2PMessage(toUserId, content, options);
          if (p2pResult.success) {
            console.log(`[发送消息] P2P发送成功:`, p2pResult);
            return { success: true, method: 'P2P', ...p2pResult };
          }
        } catch (p2pError) {
          console.warn('P2P发送失败，回退到服务器模式:', p2pError.message);
          // P2P失败时不抛出错误，继续使用服务器转发
        }
      } else {
        console.log(`[发送消息] 用户离线或不支持P2P，使用服务器转发`);
      }
      
      // P2P失败或用户离线，使用服务器转发
      console.log(`[发送消息] 使用服务器转发模式`);
      const serverResult = await this.sendServerMessage(toUserId, content, options);
      console.log(`[发送消息] 服务器转发结果:`, serverResult);
      return serverResult;
      
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
      
      // 后端返回格式是 {success: true, data: {...}}
      const userStatus = response.data?.data;
      console.log(`[状态检查] API响应:`, response.data);
      console.log(`[状态检查] 用户 ${userId} 状态:`, userStatus);
      
      if (!userStatus) {
        console.warn(`[状态检查] 用户 ${userId} 状态数据为空`);
        return { online: false, supportsP2P: false };
      }
      
      // 根据后端返回的字段判断用户状态
      const isOnline = userStatus.status === 'online' && userStatus.has_connection;
      const supportsP2P = isOnline; // 如果用户在线且有连接，则支持P2P
      
      console.log(`[状态检查] 详细字段检查:`, {
        'userStatus.status': userStatus.status,
        'userStatus.has_connection': userStatus.has_connection,
        'userStatus.last_seen': userStatus.last_seen,
        'userStatus.last_heartbeat': userStatus.last_heartbeat
      });
      
      // 确保返回标准化的状态格式
      const normalizedStatus = {
        online: isOnline,
        supportsP2P: supportsP2P,
        lastSeen: userStatus.last_seen,
        websocketConnected: userStatus.has_connection,
        lastHeartbeat: userStatus.last_heartbeat
      };
      
      console.log(`[状态检查] 标准化后的用户 ${userId} 状态:`, normalizedStatus);
      return normalizedStatus;
      
    } catch (error) {
      console.warn(`[状态检查] 检查用户 ${userId} 状态失败，假设离线:`, error);
      return { online: false, supportsP2P: false };
    }
  }

  // P2P直连发送消息
  async sendP2PMessage(toUserId, content, options = {}) {
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
      
      // 添加阅后即焚支持
      if (options.burnAfter && options.burnAfter > 0) {
        message.destroy_after = options.burnAfter;
      }
      
      dataChannel.send(JSON.stringify(message));
      
      // 存储发送的P2P消息到数据库
      try {
        const dbMessage = {
          from: this.currentUserId,
          to: toUserId,
          content: content,
          timestamp: message.timestamp,
          method: 'P2P',
          encrypted: false,
          messageType: 'text'
        };
        
        // 添加阅后即焚字段
        if (options.burnAfter && options.burnAfter > 0) {
          dbMessage.destroy_after = Math.floor(Date.now() / 1000) + options.burnAfter;
        }
        
        await addMessage(dbMessage);
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
      let timeout;
      let isResolved = false;
      
      const cleanup = () => {
        if (timeout) {
          clearTimeout(timeout);
          timeout = null;
        }
        this.peerConnections.delete(toUserId);
      };
      
      const safeResolve = (result) => {
        if (!isResolved) {
          isResolved = true;
          cleanup();
          resolve(result);
        }
      };
      
      const safeReject = (error) => {
        if (!isResolved) {
          isResolved = true;
          cleanup();
          reject(error);
        }
      };
      
      try {
        // 创建WebRTC连接
        const peerConnection = new RTCPeerConnection({
          iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
          ]
        });

        // 监听连接状态变化
        peerConnection.onconnectionstatechange = () => {
          console.log(`[P2P] 连接状态变化: ${peerConnection.connectionState}`);
          if (peerConnection.connectionState === 'failed' || peerConnection.connectionState === 'closed') {
            safeReject(new Error(`P2P连接失败: 连接状态=${peerConnection.connectionState}`));
          }
        };
        
        peerConnection.oniceconnectionstatechange = () => {
          console.log(`[P2P] ICE连接状态变化: ${peerConnection.iceConnectionState}`);
          if (peerConnection.iceConnectionState === 'failed' || peerConnection.iceConnectionState === 'closed') {
            safeReject(new Error(`P2P连接失败: ICE状态=${peerConnection.iceConnectionState}`));
          }
        };

        // 创建数据通道
        const dataChannel = peerConnection.createDataChannel('messages', {
          ordered: true
        });

        // 数据通道事件处理
        dataChannel.onopen = () => {
          console.log(`P2P连接已建立: ${toUserId}`);
          this.p2pConnections.set(toUserId, dataChannel);
          
          // 通知store更新P2P连接状态
          if (this.onP2PStatusChanged) {
            this.onP2PStatusChanged(toUserId, 'connected');
          }
          
          safeResolve(dataChannel);
        };

        dataChannel.onmessage = async (event) => {
          const message = JSON.parse(event.data);
          if (message.type === 'direct_message' && this.onMessageReceived) {
            const msgData = {
              from: message.from,
              to: this.currentUserId,
              content: message.content,
              timestamp: message.timestamp,
              method: 'P2P',
              messageType: message.messageType || 'text',
              filePath: message.filePath || null,
              fileName: message.fileName || null,
              hiddenMessage: message.hiddenMessage || null
            };
            
            // 添加阅后即焚支持
            if (message.destroy_after && message.destroy_after > 0) {
              // destroy_after已经是发送方设置的绝对时间戳，直接使用
              msgData.destroy_after = message.destroy_after;
            }
            
            try {
              await addMessage(msgData);
            } catch (dbError) {
              console.warn('保存P2P消息到本地数据库失败:', dbError);
            }
            
            this.onMessageReceived(msgData);
          }
        };
        
        dataChannel.onclose = () => {
          this.p2pConnections.delete(toUserId);
          if (this.onP2PStatusChanged) {
            this.onP2PStatusChanged(toUserId, 'disconnected');
          }
        };

        dataChannel.onerror = (error) => {
          console.warn(`[P2P] 数据通道错误 (用户 ${toUserId}):`, error.error?.message || error.type || '连接异常');
          // 清理连接状态
          this.p2pConnections.delete(toUserId);
          if (this.onP2PStatusChanged) {
            this.onP2PStatusChanged(toUserId, 'disconnected');
          }
          safeReject(error);
        };

        // ICE候选事件
        peerConnection.onicecandidate = (event) => {
          if (event.candidate) {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
              this.ws.send(JSON.stringify({
                type: 'webrtc_ice_candidate',
                to_id: toUserId,
                payload: event.candidate
              }));
            } else {
              console.warn(`[P2P] WebSocket连接不可用，无法发送ICE候选到用户 ${toUserId}`);
              safeReject(new Error('WebSocket连接断开，P2P连接失败'));
            }
          }
        };

        // 创建Offer
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        // 发送Offer给对方
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({
            type: 'webrtc_offer',
            to_id: toUserId,
            payload: offer
          }));
        } else {
          console.error(`[P2P] WebSocket连接不可用，无法发送Offer到用户 ${toUserId}`);
          safeReject(new Error('WebSocket连接断开，无法发送Offer'));
          return;
        }

        // 保存连接
        this.peerConnections.set(toUserId, peerConnection);

        // 设置连接超时
        timeout = setTimeout(() => {
          console.warn(`[P2P] 连接超时，当前状态: 连接=${peerConnection.connectionState}, ICE=${peerConnection.iceConnectionState}`);
          try {
            peerConnection.close();
          } catch (error) {
            console.warn(`[P2P] 关闭超时连接失败:`, error);
          }
          safeReject(new Error(`P2P连接超时: 连接状态=${peerConnection.connectionState}, ICE状态=${peerConnection.iceConnectionState}`));
        }, 15000); // 增加到15秒超时

      } catch (error) {
        safeReject(error);
      }
    });
  }

  // 处理P2P Offer
  async handleP2POffer(data) {
    try {
      const peerConnection = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' }
        ]
      });

      // 监听连接状态变化
      peerConnection.onconnectionstatechange = () => {
        console.log(`[P2P] 接收方连接状态变化: ${peerConnection.connectionState}`);
        if (peerConnection.connectionState === 'failed' || peerConnection.connectionState === 'closed') {
          console.warn(`[P2P] 接收方连接失败: ${peerConnection.connectionState}`);
          this.p2pConnections.delete(data.from);
          if (this.peerConnections.has(data.from)) {
            this.peerConnections.delete(data.from);
          }
        }
      };
      
      peerConnection.oniceconnectionstatechange = () => {
        console.log(`[P2P] 接收方ICE连接状态变化: ${peerConnection.iceConnectionState}`);
      };

      // 设置远程描述
      await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));

      // 监听数据通道
      peerConnection.ondatachannel = (event) => {
        const dataChannel = event.channel;
        
        dataChannel.onopen = () => {
          console.log(`P2P连接已接受: ${data.from}`);
          this.p2pConnections.set(data.from, dataChannel);
          
          if (this.onP2PStatusChanged) {
            this.onP2PStatusChanged(data.from, 'connected');
          }
        };

        dataChannel.onmessage = async (event) => {
          const message = JSON.parse(event.data);
          if (message.type === 'direct_message' && this.onMessageReceived) {
            const msgData = {
              from: message.from,
              to: this.currentUserId,
              content: message.content,
              timestamp: message.timestamp,
              method: 'P2P',
              messageType: message.messageType || 'text',
              filePath: message.filePath || null,
              fileName: message.fileName || null,
              hiddenMessage: message.hiddenMessage || null
            };
            
            // 添加阅后即焚支持
            if (message.destroy_after && message.destroy_after > 0) {
              msgData.destroy_after = Math.floor(Date.now() / 1000) + message.destroy_after;
            }
            
            try {
              await addMessage(msgData);
              console.log('P2P消息已保存到本地数据库');
            } catch (dbError) {
              console.warn('保存P2P消息到本地数据库失败:', dbError);
            }
            
            this.onMessageReceived(msgData);
          }
        };
        
        dataChannel.onclose = () => {
          console.log(`[P2P] 数据通道关闭: ${data.from}`);
          this.p2pConnections.delete(data.from);
          if (this.onP2PStatusChanged) {
            this.onP2PStatusChanged(data.from, 'disconnected');
          }
        };
        
        dataChannel.onerror = (error) => {
          console.warn(`[P2P] 接收方数据通道错误 (来自用户 ${data.from}):`, error.error?.message || error.type || '连接异常');
          // 清理连接状态
          this.p2pConnections.delete(data.from);
          if (this.onP2PStatusChanged) {
            this.onP2PStatusChanged(data.from, 'disconnected');
          }
        };
      };

      // ICE候选事件
      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          console.log(`[P2P] 接收方发送ICE候选到 ${data.from}`);
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
      console.log(`[P2P] 发送Answer到 ${data.from}`);
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'webrtc_answer',
          to_id: data.from,
          payload: answer
        }));
      } else {
        console.error(`[P2P] WebSocket连接不可用，无法发送Answer到用户 ${data.from}`);
        peerConnection.close();
        return;
      }

      // 存储连接引用
      this.peerConnections.set(data.from, peerConnection);
      
      // 设置接收方连接超时
      setTimeout(() => {
        if (this.peerConnections.has(data.from) && 
            peerConnection.connectionState !== 'connected' && 
            peerConnection.connectionState !== 'closed') {
          console.warn(`[P2P] 接收方连接超时: ${data.from}`);
          peerConnection.close();
          this.peerConnections.delete(data.from);
          this.p2pConnections.delete(data.from);
        }
      }, 15000);

    } catch (error) {
      console.error('处理P2P Offer失败:', error);
      if (this.peerConnections.has(data.from)) {
        const pc = this.peerConnections.get(data.from);
        pc.close();
        this.peerConnections.delete(data.from);
      }
      this.p2pConnections.delete(data.from);
    }
  }

  // 处理P2P Answer
  async handleP2PAnswer(data) {
    console.log(`[P2P] 收到来自 ${data.from} 的Answer`);
    try {
      const peerConnection = this.peerConnections.get(data.from);
      if (!peerConnection) {
        console.warn(`[P2P] 未找到与 ${data.from} 的连接`);
        return;
      }
      
      if (peerConnection.connectionState === 'closed') {
        console.warn(`[P2P] 与 ${data.from} 的连接已关闭`);
        this.peerConnections.delete(data.from);
        return;
      }
      
      await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
       console.log(`[P2P] 已为 ${data.from} 设置远程描述`);
       
       // 处理暂存的ICE候选
       if (this.pendingIceCandidates && this.pendingIceCandidates.has(data.from)) {
         const candidates = this.pendingIceCandidates.get(data.from);
         console.log(`[P2P] 处理 ${candidates.length} 个暂存的ICE候选`);
         for (const candidate of candidates) {
           try {
             await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
           } catch (err) {
             console.warn(`[P2P] 添加暂存ICE候选失败:`, err);
           }
         }
         this.pendingIceCandidates.delete(data.from);
       }
      
    } catch (error) {
      console.error(`[P2P] 处理来自 ${data.from} 的Answer失败:`, error);
      // 清理失败的连接
      if (this.peerConnections.has(data.from)) {
        const pc = this.peerConnections.get(data.from);
        pc.close();
        this.peerConnections.delete(data.from);
      }
      this.p2pConnections.delete(data.from);
    }
  }

  // 处理ICE候选
  async handleIceCandidate(data) {
    console.log(`[P2P] 收到来自 ${data.from} 的ICE候选`);
    try {
      const peerConnection = this.peerConnections.get(data.from);
      if (!peerConnection) {
        console.warn(`[P2P] 未找到与 ${data.from} 的连接`);
        return;
      }
      
      if (peerConnection.connectionState === 'closed') {
        console.warn(`[P2P] 与 ${data.from} 的连接已关闭，忽略ICE候选`);
        this.peerConnections.delete(data.from);
        return;
      }
      
      if (!data.candidate) {
        console.log(`[P2P] 收到来自 ${data.from} 的空ICE候选（连接完成信号）`);
        return;
      }
      
      // 确保在添加ICE候选之前，远程描述已经设置
      if (peerConnection.remoteDescription) {
        await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
        console.log(`[P2P] 已为 ${data.from} 添加ICE候选`);
      } else {
        console.warn(`[P2P] 收到来自 ${data.from} 的ICE候选，但远程描述尚未设置`);
        // 暂存ICE候选，等待远程描述设置后再添加
        if (!this.pendingIceCandidates) {
          this.pendingIceCandidates = new Map();
        }
        if (!this.pendingIceCandidates.has(data.from)) {
          this.pendingIceCandidates.set(data.from, []);
        }
        this.pendingIceCandidates.get(data.from).push(data.candidate);
      }
      
    } catch (error) {
      console.error(`[P2P] 处理来自 ${data.from} 的ICE候选失败:`, error);
      // ICE候选失败通常不需要关闭整个连接，只记录错误
    }
  }

  // 服务器转发消息（C/S模式）
  async sendServerMessage(toUserId, content, options = {}) {
    try {
      console.log('发送服务器消息:', { toUserId, content, options });
      
      const messageData = {
        to: toUserId,
        content: content,
        encrypted: false,
        method: 'Server'
      };
      
      // 添加阅后即焚支持
      if (options.burnAfter && options.burnAfter > 0) {
        messageData.destroy_after = options.burnAfter;
      }
      
      const { hybridApi } = await import('../api/hybrid-api.js');
      const response = await hybridApi.sendMessage(messageData);

      const result = response.data;
      console.log('服务器响应结果:', result);
      
      // 存储发送的服务器消息到数据库
      try {
        const sentMsgData = {
          from: this.currentUserId,
          to: toUserId,
          content: content,
          timestamp: result.timestamp || new Date().toISOString(),
          method: 'Server',
          messageType: 'text',
          encrypted: false
        };
        
        // 添加阅后即焚字段
        if (options.burnAfter && options.burnAfter > 0) {
          sentMsgData.destroy_after = Math.floor(Date.now() / 1000) + options.burnAfter;
        }
        
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
    // 检查是否为语音通话相关消息
    const voiceCallMessageTypes = [
      'voice_call_offer',
      'voice_call_answer', 
      'voice_call_ice_candidate',
      'voice_call_rejected',
      'voice_call_ended'
    ];
    
    if (voiceCallMessageTypes.includes(data.type)) {
      // 语音通话相关消息由对应的处理器处理
      const handler = this.messageHandlers[data.type];
      if (handler) {
        await handler(data);
      }
      return;
    }
    
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
    
    // 添加阅后即焚支持
    if (data.destroy_after && data.destroy_after > 0) {
      msgData.destroy_after = Math.floor(Date.now() / 1000) + data.destroy_after;
    }
    
    // 存入本地数据库
    try {
      await addMessage(msgData);
      console.log('服务器消息已保存到本地数据库');
    } catch (dbError) {
      console.error('保存服务器消息到数据库失败:', dbError);
    }
    
    // 通知UI层
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
      // 离线状态发送功能已移除
      console.log('[离线] 离线状态发送功能已移除');
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
      console.log('[连接健康检查] 开始检查连接状态');
      
      // 发送WebSocket心跳
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify({
            type: 'heartbeat',
            timestamp: new Date().toISOString()
          }));
          console.log('[心跳] 已发送WebSocket心跳');
        } catch (error) {
          console.error('[心跳] 发送WebSocket心跳失败:', error);
        }
      }
      
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
      
      // 预连接相关的连接尝试记录清理功能已删除
      
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
    
    // 预连接相关状态清理功能已删除
    
    // 清理暂存的ICE候选
    if (this.pendingIceCandidates) {
      this.pendingIceCandidates.clear();
      console.log('已清理暂存的ICE候选');
    }
    
    // 关闭WebSocket连接
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  // 离线状态设置功能已移除
  async setOfflineStatus() {
    console.log('[离线] 离线状态设置功能已移除');
  }

  // ==================== 语音通话功能 ====================
  
  // 语音通话相关状态
  initVoiceCallState() {
    // 保存现有的回调函数引用
    const existingOnVoiceCallReceived = this.onVoiceCallReceived;
    const existingOnVoiceCallStatusChanged = this.onVoiceCallStatusChanged;
    
    // 清理现有的语音通话资源
    if (this.voiceCallState) {
      if (this.voiceCallState.localStream) {
        this.voiceCallState.localStream.getTracks().forEach(track => {
          track.stop();
          console.log('[语音通话] 停止音频轨道:', track.kind);
        });
      }
      if (this.voiceCallState.peerConnection) {
        this.voiceCallState.peerConnection.close();
        console.log('[语音通话] 关闭WebRTC连接');
      }
    }
    
    this.voiceCallState = {
      isInCall: false,
      currentCallId: null,
      localStream: null,
      remoteStream: null,
      peerConnection: null,
      callType: null, // 'outgoing' | 'incoming'
      targetUserId: null,
      callStartTime: null,
      encryptionKey: null, // 音频加密密钥
      audioContext: null,  // 音频上下文
      encryptionEnabled: true // 是否启用加密
    };
    
    // 保持回调函数不被清空，除非是首次初始化
    if (existingOnVoiceCallReceived !== undefined) {
      this.onVoiceCallReceived = existingOnVoiceCallReceived;
    }
    if (existingOnVoiceCallStatusChanged !== undefined) {
      this.onVoiceCallStatusChanged = existingOnVoiceCallStatusChanged;
    }
    
    // 重新初始化VoiceCall.vue中需要的属性
    this.voiceConnections = new Map();
    this.remoteStreams = new Map();
    this.currentVoiceCall = null;
    this.localStream = null;
    
    // 初始化音频加密相关
    this.initAudioEncryption();
  }
  
  // 初始化音频加密
  initAudioEncryption() {
    try {
      // 生成随机加密密钥
      this.generateEncryptionKey();
      console.log('[音频加密] 加密系统初始化完成');
    } catch (error) {
      console.error('[音频加密] 初始化失败:', error);
    }
  }
  
  // 生成加密密钥
  generateEncryptionKey() {
    const key = new Uint8Array(32); // 256位密钥
    crypto.getRandomValues(key);
    this.voiceCallState.encryptionKey = key;
    return key;
  }
  
  // 简单的XOR加密/解密
  encryptAudioData(audioData, key) {
    if (!key || !this.voiceCallState.encryptionEnabled) {
      return audioData;
    }
    
    const encrypted = new Uint8Array(audioData.length);
    for (let i = 0; i < audioData.length; i++) {
      encrypted[i] = audioData[i] ^ key[i % key.length];
    }
    return encrypted;
  }
  
  // 解密音频数据（与加密相同，XOR的特性）
  decryptAudioData(encryptedData, key) {
    return this.encryptAudioData(encryptedData, key);
  }

  // 发起语音通话
  async initiateVoiceCall(toUserId) {
    try {
      console.log(`[语音通话] 开始发起通话给用户 ${toUserId}`);
      
      // 检查是否已在通话中
      if (this.voiceCallState && this.voiceCallState.isInCall) {
        console.log('[语音通话] 当前已在通话中，先结束现有通话');
        await this.forceResetVoiceCallState();
      }
      
      // 强制重置语音通话状态，确保彻底清理之前的资源
      await this.forceResetVoiceCallState();
      
      // 获取用户媒体流
      const localStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000 // 高质量音频
        },
        video: false
      });
      
      console.log('[语音通话] 本地音频流获取成功');
      
      // 创建音频上下文用于加密处理
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      this.voiceCallState.audioContext = audioContext;
      
      // 创建WebRTC连接
      const peerConnection = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' },
          { urls: 'stun:stun2.l.google.com:19302' }
        ],
        iceCandidatePoolSize: 10
      });
      
      // 添加本地流到连接
      localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
      });
      
      // 设置远程流处理
      peerConnection.ontrack = (event) => {
        console.log('[语音通话] 收到远程音频流');
        const remoteStream = event.streams[0];
        
        // 处理音频解密（如果启用）
        if (this.voiceCallState.encryptionEnabled && this.voiceCallState.encryptionKey) {
          console.log('[音频加密] 对远程音频流进行解密处理');
          // 这里可以添加实时音频解密逻辑
        }
        
        this.voiceCallState.remoteStream = remoteStream;
        this.remoteStreams.set(toUserId, remoteStream);
        
        if (this.onVoiceCallStatusChanged) {
          this.onVoiceCallStatusChanged({
            type: 'remote_stream_received',
            stream: remoteStream
          });
        }
      };
      
      // 监听连接状态变化
      peerConnection.onconnectionstatechange = () => {
        console.log(`[语音通话] 连接状态: ${peerConnection.connectionState}`);
        if (this.onVoiceCallStatusChanged) {
          this.onVoiceCallStatusChanged({
            type: 'connection_state_changed',
            state: peerConnection.connectionState
          });
        }
        
        // 连接失败时自动清理
        if (peerConnection.connectionState === 'failed' || peerConnection.connectionState === 'disconnected') {
          console.log('[语音通话] 连接失败，自动清理资源');
          setTimeout(() => {
            this.forceResetVoiceCallState();
          }, 1000);
        }
      };
      
      // ICE候选处理
      peerConnection.onicecandidate = (event) => {
        if (event.candidate && this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({
            type: 'voice_call_ice_candidate',
            to_id: toUserId,
            payload: event.candidate
          }));
        }
      };
      
      // 创建offer
      const offer = await peerConnection.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: false
      });
      await peerConnection.setLocalDescription(offer);
      
      // 发送通话邀请（包含加密密钥）
      const callId = `call_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        const message = {
          type: 'voice_call_offer',
          to_id: toUserId,
          call_id: callId,
          payload: offer,
          encryption_key: this.voiceCallState.encryptionEnabled ? 
            Array.from(this.voiceCallState.encryptionKey) : null // 发送加密密钥
        };
        console.log('[语音通话] 发送通话邀请消息（含加密密钥）');
        this.ws.send(JSON.stringify(message));
        console.log('[语音通话] 通话邀请消息已发送到服务器');
      } else {
        throw new Error('WebSocket连接不可用，无法发起语音通话');
      }
      
      // 更新状态
      this.voiceCallState.isInCall = true;
      this.voiceCallState.currentCallId = callId;
      this.voiceCallState.localStream = localStream;
      this.voiceCallState.peerConnection = peerConnection;
      this.voiceCallState.callType = 'outgoing';
      this.voiceCallState.targetUserId = toUserId;
      this.voiceCallState.callStartTime = new Date().toISOString();
      
      // 为VoiceCall.vue提供访问的属性
      this.localStream = localStream;
      this.currentVoiceCall = {
        userId: toUserId,
        type: 'outgoing',
        status: 'connecting'
      };
      this.voiceConnections.set(toUserId, peerConnection);
      
      console.log('[语音通话] 通话邀请已发送，加密已启用');
      
      return {
        success: true,
        callId: callId,
        localStream: localStream,
        encryptionEnabled: this.voiceCallState.encryptionEnabled
      };
      
    } catch (error) {
      console.error('[语音通话] 发起通话失败:', error);
      
      // 清理资源
      await this.forceResetVoiceCallState();
      
      throw error;
    }
  }
  
  // 接听语音通话
  async acceptVoiceCall(fromUserId, offer, encryptionKey = null) {
    try {
      console.log(`[语音通话] 接听来自用户 ${fromUserId} 的通话`);
      
      // 强制重置语音通话状态，确保彻底清理之前的资源
      await this.forceResetVoiceCallState();
      
      // 如果提供了加密密钥，使用它
      if (encryptionKey && Array.isArray(encryptionKey)) {
        this.voiceCallState.encryptionKey = new Uint8Array(encryptionKey);
        console.log('[音频加密] 接收到加密密钥，启用加密通话');
      }
      
      // 获取用户媒体流
      const localStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000 // 高质量音频
        },
        video: false
      });
      
      console.log('[语音通话] 本地音频流获取成功');
      
      // 创建音频上下文用于加密处理
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      this.voiceCallState.audioContext = audioContext;
      
      // 创建WebRTC连接
      const peerConnection = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' },
          { urls: 'stun:stun2.l.google.com:19302' }
        ],
        iceCandidatePoolSize: 10
      });
      
      // 添加本地流
      localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
      });
      
      // 设置远程流处理
      peerConnection.ontrack = (event) => {
        console.log('[语音通话] 收到远程音频流');
        const remoteStream = event.streams[0];
        
        // 处理音频解密（如果启用）
        if (this.voiceCallState.encryptionEnabled && this.voiceCallState.encryptionKey) {
          console.log('[音频加密] 对远程音频流进行解密处理');
          // 这里可以添加实时音频解密逻辑
        }
        
        this.voiceCallState.remoteStream = remoteStream;
        this.remoteStreams.set(fromUserId, remoteStream);
        
        if (this.onVoiceCallStatusChanged) {
          this.onVoiceCallStatusChanged({
            type: 'remote_stream_received',
            stream: remoteStream
          });
        }
      };
      
      // 监听连接状态变化
      peerConnection.onconnectionstatechange = () => {
        console.log(`[语音通话] 连接状态: ${peerConnection.connectionState}`);
        if (this.onVoiceCallStatusChanged) {
          this.onVoiceCallStatusChanged({
            type: 'connection_state_changed',
            state: peerConnection.connectionState
          });
        }
        
        // 连接失败时自动清理
        if (peerConnection.connectionState === 'failed' || peerConnection.connectionState === 'disconnected') {
          console.log('[语音通话] 连接失败，自动清理资源');
          setTimeout(() => {
            this.forceResetVoiceCallState();
          }, 1000);
        }
      };
      
      // ICE候选处理
      peerConnection.onicecandidate = (event) => {
        if (event.candidate && this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({
            type: 'voice_call_ice_candidate',
            to_id: fromUserId,
            payload: event.candidate
          }));
        }
      };
      
      // 设置远程描述
      await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
      
      // 创建answer
      const answer = await peerConnection.createAnswer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: false
      });
      await peerConnection.setLocalDescription(answer);
      
      // 发送answer（包含确认加密密钥）
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'voice_call_answer',
          to_id: fromUserId,
          payload: answer,
          encryption_confirmed: this.voiceCallState.encryptionEnabled && !!this.voiceCallState.encryptionKey
        }));
        console.log('[语音通话] 发送应答消息（含加密确认）');
      } else {
        throw new Error('WebSocket连接不可用，无法接听语音通话');
      }
      
      // 更新状态
      this.voiceCallState.isInCall = true;
      this.voiceCallState.currentCallId = `call_${Date.now()}`;
      this.voiceCallState.localStream = localStream;
      this.voiceCallState.peerConnection = peerConnection;
      this.voiceCallState.callType = 'incoming';
      this.voiceCallState.targetUserId = fromUserId;
      this.voiceCallState.callStartTime = new Date().toISOString();
      
      // 为VoiceCall.vue提供访问的属性
      this.localStream = localStream;
      this.currentVoiceCall = {
        userId: fromUserId,
        type: 'incoming',
        status: 'active'
      };
      this.voiceConnections.set(fromUserId, peerConnection);
      
      console.log('[语音通话] 通话已接听，加密状态:', this.voiceCallState.encryptionEnabled);
      
      return {
        success: true,
        localStream: localStream,
        encryptionEnabled: this.voiceCallState.encryptionEnabled
      };
      
    } catch (error) {
      console.error('[语音通话] 接听通话失败:', error);
      
      // 清理资源
      await this.forceResetVoiceCallState();
      
      throw error;
    }
  }
  
  // 拒绝语音通话
  async rejectVoiceCall(fromUserId) {
    try {
      console.log(`[语音通话] 拒绝来自用户 ${fromUserId} 的通话`);
      
      // 保存被拒绝的通话记录
      await this.saveVoiceCallRecord(fromUserId, 'rejected');
      
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'voice_call_rejected',
          to_id: fromUserId
        }));
      }
      
      // 保存回调函数引用
      const existingOnVoiceCallReceived = this.onVoiceCallReceived;
      const existingOnVoiceCallStatusChanged = this.onVoiceCallStatusChanged;
      
      // 强制重置状态
      await this.forceResetVoiceCallState();
      
      // 恢复回调函数
      this.onVoiceCallReceived = existingOnVoiceCallReceived;
      this.onVoiceCallStatusChanged = existingOnVoiceCallStatusChanged;
      
      console.log('[语音通话] 拒绝通话处理完成');
      
      return { success: true };
      
    } catch (error) {
      console.error('[语音通话] 拒绝通话失败:', error);
      throw error;
    }
  }
  
  // 结束语音通话
  async endVoiceCall(userId) {
    try {
      console.log(`[语音通话] 结束与用户 ${userId} 的通话`);
      
      // 保存通话记录
      if (this.voiceCallState && this.voiceCallState.callStartTime) {
        await this.saveVoiceCallRecord(userId, 'completed');
      }
      
      // 发送结束通话信号
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'voice_call_ended',
          to_id: userId
        }));
      }
      
      // 保存回调函数引用
      const existingOnVoiceCallReceived = this.onVoiceCallReceived;
      const existingOnVoiceCallStatusChanged = this.onVoiceCallStatusChanged;
      
      // 强制重置状态
      await this.forceResetVoiceCallState();
      
      // 恢复回调函数
      this.onVoiceCallReceived = existingOnVoiceCallReceived;
      this.onVoiceCallStatusChanged = existingOnVoiceCallStatusChanged;
      
      // 通知前端通话已结束，但不触发页面跳转
      if (this.onVoiceCallStatusChanged) {
        this.onVoiceCallStatusChanged({
          type: 'call_ended_local',
          userId: userId
        });
      }
      
      console.log('[语音通话] 通话结束处理完成');
      
      return { success: true };
      
    } catch (error) {
      console.error('[语音通话] 结束通话失败:', error);
      throw error;
    }
  }
  
  // 切换静音状态
  toggleMute() {
    if (this.voiceCallState && this.voiceCallState.localStream) {
      const audioTracks = this.voiceCallState.localStream.getAudioTracks();
      audioTracks.forEach(track => {
        track.enabled = !track.enabled;
      });
      return !audioTracks[0]?.enabled;
    }
    return false;
  }
  
  // 强制重置语音通话状态
  async forceResetVoiceCallState() {
    try {
      console.log('[语音通话] 强制重置语音通话状态');
      
      // 清理本地资源
      if (this.voiceCallState) {
        if (this.voiceCallState.localStream) {
          this.voiceCallState.localStream.getTracks().forEach(track => {
            track.stop();
            console.log('[语音通话] 强制停止音频轨道:', track.kind);
          });
        }
        if (this.voiceCallState.peerConnection) {
          this.voiceCallState.peerConnection.close();
          console.log('[语音通话] 强制关闭WebRTC连接');
        }
        if (this.voiceCallState.audioContext) {
          try {
            await this.voiceCallState.audioContext.close();
            console.log('[语音通话] 强制关闭音频上下文');
          } catch (error) {
            console.warn('[语音通话] 关闭音频上下文失败:', error);
          }
        }
      }
      
      // 清理所有连接
      if (this.voiceConnections) {
        this.voiceConnections.forEach((connection, userId) => {
          try {
            connection.close();
            console.log(`[语音通话] 强制关闭与用户 ${userId} 的连接`);
          } catch (error) {
            console.warn(`[语音通话] 关闭与用户 ${userId} 的连接失败:`, error);
          }
        });
        this.voiceConnections.clear();
      }
      
      // 清理远程流
      if (this.remoteStreams) {
        this.remoteStreams.clear();
      }
      
      // 清理全局属性
      this.localStream = null;
      this.currentVoiceCall = null;
      
      // 重新初始化状态
      this.initVoiceCallState();
      
      console.log('[语音通话] 强制重置完成');
      
      return { success: true };
      
    } catch (error) {
      console.error('[语音通话] 强制重置状态失败:', error);
      return { success: false, error: error.message };
    }
  }
  
  // 保存语音通话记录
   async saveVoiceCallRecord(userId, callStatus) {
     try {
       const callEndTime = new Date().toISOString();
       let callStartTime = callEndTime;
       let duration = 0;
       
       if (this.voiceCallState && this.voiceCallState.callStartTime) {
         callStartTime = this.voiceCallState.callStartTime;
         const startTime = new Date(callStartTime);
         const endTime = new Date(callEndTime);
         duration = Math.floor((endTime - startTime) / 1000); // 通话时长（秒）
       } else {
         // 对于被拒绝的通话，可能没有callStartTime，使用当前时间
         console.warn('[语音通话] 缺少通话开始时间，使用当前时间作为开始时间');
       }
      
      // 构建包含通话信息的内容
      const callInfo = {
        type: 'voice_call',
        status: callStatus,
        duration: duration,
        startTime: callStartTime,
        endTime: callEndTime
      };
      
      const callRecord = {
         to: userId,
         content: JSON.stringify(callInfo),
         messageType: 'voice_call',
         method: 'Server',
         encrypted: false
       };
      
      console.log('[语音通话] 保存通话记录:', callRecord);
      
      // 发送到后端保存
      try {
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
        const response = await fetch(`${API_BASE_URL}/v1/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(callRecord)
        });
        
        if (response.ok) {
          console.log('[语音通话] 通话记录保存成功');
        } else {
          console.error('[语音通话] 保存通话记录失败:', response.statusText);
        }
      } catch (fetchError) {
        console.error('[语音通话] 保存通话记录网络错误:', fetchError);
      }
      
      // 无论后端保存是否成功，都要通知前端更新聊天记录
      if (this.onMessageReceived) {
        const messageForUI = {
          id: `call_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          from: this.currentUserId,
          to: userId,
          content: `语音通话 - ${callStatus === 'completed' ? '已完成' : callStatus === 'rejected' ? '被拒绝' : callStatus}`,
          messageType: 'voice_call',
          callDuration: duration,
          callStatus: callStatus,
          callStartTime: callStartTime,
          callEndTime: callEndTime,
          timestamp: callEndTime,
          method: 'Server'
        };
        
        console.log('[语音通话] 通知前端添加通话记录:', messageForUI);
        this.onMessageReceived(messageForUI);
      }
      
    } catch (error) {
      console.error('[语音通话] 保存通话记录异常:', error);
    }
  }
  
  // 强制重置语音通话状态
  async forceResetVoiceCallState() {
    try {
      console.log('[语音通话] 强制重置通话状态');
      
      // 清理本地媒体流
      if (this.voiceCallState && this.voiceCallState.localStream) {
        this.voiceCallState.localStream.getTracks().forEach(track => {
          track.stop();
          console.log('[语音通话] 停止本地音频轨道:', track.kind);
        });
      }
      
      // 清理WebRTC连接
      if (this.voiceCallState && this.voiceCallState.peerConnection) {
        this.voiceCallState.peerConnection.close();
        console.log('[语音通话] 关闭WebRTC连接');
      }
      
      // 清理音频上下文
      if (this.voiceCallState && this.voiceCallState.audioContext) {
        try {
          await this.voiceCallState.audioContext.close();
          console.log('[语音通话] 关闭音频上下文');
        } catch (audioError) {
          console.warn('[语音通话] 关闭音频上下文失败:', audioError);
        }
      }
      
      // 清理所有语音连接
      if (this.voiceConnections) {
        this.voiceConnections.forEach((connection, userId) => {
          try {
            connection.close();
            console.log(`[语音通话] 关闭与用户 ${userId} 的连接`);
          } catch (connError) {
            console.warn(`[语音通话] 关闭连接失败 ${userId}:`, connError);
          }
        });
        this.voiceConnections.clear();
      }
      
      // 清理远程流
      if (this.remoteStreams) {
        this.remoteStreams.forEach((stream, userId) => {
          try {
            stream.getTracks().forEach(track => track.stop());
            console.log(`[语音通话] 停止用户 ${userId} 的远程流`);
          } catch (streamError) {
            console.warn(`[语音通话] 停止远程流失败 ${userId}:`, streamError);
          }
        });
        this.remoteStreams.clear();
      }
      
      // 清理本地流引用
      if (this.localStream) {
        this.localStream.getTracks().forEach(track => track.stop());
        this.localStream = null;
      }
      
      // 清理当前通话引用
      this.currentVoiceCall = null;
      
      // 重置状态
      this.initVoiceCallState();
      
      console.log('[语音通话] 强制重置完成，所有资源已清理');
      return { success: true };
      
    } catch (error) {
      console.error('[语音通话] 强制重置状态失败:', error);
      return { success: false, error: error.message };
    }
  }
  
  // ==================== 语音通话消息处理器 ====================
  
  // 处理语音通话邀请
  async handleVoiceCallOffer(data) {
    try {
      console.log(`[语音通话] 收到来自用户 ${data.from_id} 的通话邀请`);
      
      // 处理加密密钥
      let encryptionKey = null;
      if (data.encryption_key && Array.isArray(data.encryption_key)) {
        encryptionKey = data.encryption_key;
        console.log('[音频加密] 收到加密密钥，将启用加密通话');
      }
      
      if (this.onVoiceCallReceived) {
        this.onVoiceCallReceived({
          type: 'incoming_call',
          fromUserId: data.from_id,
          callId: data.call_id,
          offer: data.payload,
          encryptionKey: encryptionKey
        });
      }
      
    } catch (error) {
      console.error('[语音通话] 处理通话邀请失败:', error);
    }
  }
  
  // 处理语音通话应答
  async handleVoiceCallAnswer(data) {
    try {
      console.log(`[语音通话] 收到来自用户 ${data.from_id} 的通话应答`);
      
      if (this.voiceCallState && this.voiceCallState.peerConnection) {
        await this.voiceCallState.peerConnection.setRemoteDescription(
          new RTCSessionDescription(data.payload)
        );
        
        if (this.onVoiceCallStatusChanged) {
          this.onVoiceCallStatusChanged({
            type: 'call_answered',
            fromUserId: data.from_id
          });
        }
      }
      
    } catch (error) {
      console.error('[语音通话] 处理通话应答失败:', error);
    }
  }
  
  // 处理语音通话ICE候选
  async handleVoiceCallIceCandidate(data) {
    try {
      console.log(`[语音通话] 收到来自用户 ${data.from_id} 的ICE候选`);
      
      if (this.voiceCallState && this.voiceCallState.peerConnection) {
        await this.voiceCallState.peerConnection.addIceCandidate(
          new RTCIceCandidate(data.payload)
        );
      }
      
    } catch (error) {
      console.error('[语音通话] 处理ICE候选失败:', error);
    }
  }
  
  // 处理语音通话被拒绝
  async handleVoiceCallRejected(data) {
    try {
      console.log(`[语音通话] 用户 ${data.from_id} 拒绝了通话`);
      
      // 保存被拒绝的通话记录
      await this.saveVoiceCallRecord(data.from_id, 'rejected');
      
      // 保存回调函数引用
      const existingOnVoiceCallReceived = this.onVoiceCallReceived;
      const existingOnVoiceCallStatusChanged = this.onVoiceCallStatusChanged;
      
      // 强制重置状态
      await this.forceResetVoiceCallState();
      
      // 恢复回调函数
      this.onVoiceCallReceived = existingOnVoiceCallReceived;
      this.onVoiceCallStatusChanged = existingOnVoiceCallStatusChanged;
      
      if (this.onVoiceCallStatusChanged) {
        this.onVoiceCallStatusChanged({
          type: 'call_rejected',
          fromUserId: data.from_id
        });
      }
      
      console.log('[语音通话] 通话拒绝处理完成');
      
    } catch (error) {
      console.error('[语音通话] 处理通话拒绝失败:', error);
    }
  }
  
  // 处理语音通话结束
  async handleVoiceCallEnded(data) {
    try {
      console.log(`[语音通话] 用户 ${data.from_id} 结束了通话`);
      
      // 保存远程结束的通话记录
      if (this.voiceCallState && this.voiceCallState.callStartTime) {
        await this.saveVoiceCallRecord(data.from_id, 'completed');
      }
      
      // 保存回调函数引用
      const existingOnVoiceCallReceived = this.onVoiceCallReceived;
      const existingOnVoiceCallStatusChanged = this.onVoiceCallStatusChanged;
      
      // 强制重置状态
      await this.forceResetVoiceCallState();
      
      // 恢复回调函数
      this.onVoiceCallReceived = existingOnVoiceCallReceived;
      this.onVoiceCallStatusChanged = existingOnVoiceCallStatusChanged;
      
      if (this.onVoiceCallStatusChanged) {
        this.onVoiceCallStatusChanged({
          type: 'call_ended_remote',
          fromUserId: data.from_id
        });
      }
      
      console.log('[语音通话] 远程通话结束处理完成');
      
    } catch (error) {
      console.error('[语音通话] 处理通话结束失败:', error);
    }
  }
  
  // 处理心跳响应
  handleHeartbeatResponse() {
    console.log('[心跳] 收到服务器心跳响应');
    this.lastHeartbeatTime = Date.now();
    this.connectionHealthy = true;
  }

  // 处理用户状态更新
  handleUserStatusUpdate(data) {
    console.log('[用户状态] 收到用户状态更新:', data);
    if (this.onUserStatusChanged) {
      this.onUserStatusChanged({
        userId: data.user_id,
        status: data.status,
        lastSeen: data.last_seen
      });
    }
  }

  // 切换静音状态
  toggleMute() {
    if (this.localStream || this.voiceCallState?.localStream) {
      const stream = this.localStream || this.voiceCallState.localStream;
      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length > 0) {
        const currentMuted = !audioTracks[0].enabled;
        audioTracks.forEach(track => {
          track.enabled = currentMuted;
        });
        console.log(`[语音通话] 麦克风${currentMuted ? '已开启' : '已静音'}`);
        return !currentMuted; // 返回新的静音状态
      }
    }
    return false;
  }
}

export default HybridMessaging;