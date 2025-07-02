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
    this.preConnectQueue = new Set();  // 预连接队列
    this.connectionAttempts = new Map(); // 连接尝试记录 { userId: { attempts: number, lastAttempt: timestamp } }
  }

  // 初始化混合消息系统
  async initialize(userId, token) {
    this.currentUserId = userId;
    this.token = token;
    
    console.log(`[初始化] 开始初始化混合消息系统，用户ID: ${userId}`);
    
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
      const data = JSON.parse(event.data);
      
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
          // 统一状态管理系统发送的新格式消息
          // 检查消息格式：后端直接发送presence对象，包含userId, status, isOnline等字段
          if (data.userId && typeof data.userId === 'number' && data.userId > 0 && 
              data.status && typeof data.status === 'string') {
            if (this.onUserStatusChanged) {
              this.onUserStatusChanged({
                userId: data.userId,
                status: data.status,
                isOnline: data.isOnline,
                timestamp: data.timestamp,
                websocketConnected: data.websocketConnected,
                p2pCapability: data.p2pCapability
              });
            }
          } else {
            console.warn('收到无效的presence消息，缺少必要字段:', data);
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
      return { success: false, reason: 'rate_limited' };
    }
    
    // 检查用户状态
    try {
      const userStatus = await this.checkUserStatus(toUserId);
      
      if (!userStatus.online || !userStatus.supportsP2P) {
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
      console.warn(`[预连接] 用户 ${toUserId} P2P连接失败:`, error);
      return { success: false, reason: 'connection_failed', error: error.message };
    }
  }
  
  // 智能发送消息（自动选择P2P或C/S）
  async sendMessage(toUserId, content) {
    try {
      console.log(`[发送消息] 开始发送消息给用户 ${toUserId}`);
      
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
          console.warn(`[发送消息] P2P发送失败，移除连接并降级到服务器转发:`, p2pError);
          // 清理失效的连接
          this.p2pConnections.delete(toUserId);
          if (this.peerConnections.has(toUserId)) {
            this.peerConnections.get(toUserId).close();
            this.peerConnections.delete(toUserId);
          }
        }
      }
      
      // 检查用户状态并尝试即时P2P连接（如果没有预连接）
      const userStatus = await this.checkUserStatus(toUserId);
      console.log(`[发送消息] 用户状态:`, userStatus);
      
      if (userStatus.online && userStatus.supportsP2P && !this.preConnectQueue.has(toUserId)) {
        console.log(`[发送消息] 用户在线且支持P2P，尝试即时P2P连接`);
        try {
          const p2pResult = await this.sendP2PMessage(toUserId, content);
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
      const serverResult = await this.sendServerMessage(toUserId, content);
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
          
          resolve(dataChannel);
        };

        dataChannel.onmessage = async (event) => {
          const message = JSON.parse(event.data);
          if (message.type === 'direct_message' && this.onMessageReceived) {
            const msgData = {
              from: message.from,
              to: this.currentUserId, // P2P消息是发给当前用户的
              content: message.content,
              timestamp: message.timestamp,
              method: 'P2P',
              // 添加图片和隐写术消息支持
              messageType: message.messageType || 'text',
              filePath: message.filePath || null,
              fileName: message.fileName || null,
              hiddenMessage: message.hiddenMessage || null
            };
            
            // 存入本地数据库
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
          console.error(`[P2P] 数据通道错误:`, error);
          clearTimeout(timeout); // 清除超时定时器
          reject(error);
        };

        // ICE候选事件
        peerConnection.onicecandidate = (event) => {
          if (event.candidate) {
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
              reject(new Error('WebSocket连接断开，P2P连接失败'));
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
          reject(new Error('WebSocket连接断开，无法发送Offer'));
          return;
        }

        // 保存连接
        this.peerConnections.set(toUserId, peerConnection);

        // 设置连接超时
        const timeout = setTimeout(() => {
          // 清理连接
          try {
            peerConnection.close();
          } catch (error) {
            console.warn(`[P2P] 关闭超时连接失败:`, error);
          }
          
          this.peerConnections.delete(toUserId);
          reject(new Error(`P2P连接超时: 连接状态=${peerConnection.connectionState}, ICE状态=${peerConnection.iceConnectionState}`));
        }, 10000); // 10秒超时

      } catch (error) {
        reject(error);
      }
    });
  }

  // 处理P2P Offer
  async handleP2POffer(data) {
    try {
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
      const peerConnection = this.peerConnections.get(data.from);
      if (peerConnection) {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
        console.log(`[P2P] Remote description set for ${data.from}`);
      }
    } catch (error) {
      console.error('处理P2P Answer失败:', error);
    }
  }

  // 处理ICE候选
  async handleIceCandidate(data) {
    console.log(`[P2P] Received ICE candidate from ${data.from}`);
    try {
      const peerConnection = this.peerConnections.get(data.from);
      if (peerConnection && data.candidate) {
        // 确保在添加ICE候选之前，远程描述已经设置
        if (peerConnection.remoteDescription) {
          await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
          console.log(`[P2P] Added ICE candidate for ${data.from}`);
        } else {
          console.warn(`[P2P] Received ICE candidate before remote description was set for ${data.from}.`);
          // 可以考虑将候选者暂存起来，等待远程描述设置后再添加
        }
      }
    } catch (error) {
      console.error('处理ICE候选失败:', error);
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
}

export default HybridMessaging;