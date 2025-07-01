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
  }

  // 初始化混合消息系统
  async initialize(userId, token) {
    this.currentUserId = userId;
    this.token = token;
    
    // 建立WebSocket连接用于信令
    await this.connectSignalingServer();
    
    // 注册用户为支持P2P
    await this.registerP2PCapability();
    
    console.log('混合消息系统初始化完成');
  }

  // 连接信令服务器（C/S）
  async connectSignalingServer() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`ws://localhost:8000/ws/${this.currentUserId}?token=${this.token}`);
      
      this.ws.onopen = () => {
        console.log('信令服务器连接成功');
        this.setupSignalingHandlers();
        resolve();
      };
      
      this.ws.onerror = reject;
      this.ws.onclose = () => {
        console.log('信令服务器连接断开，尝试重连...');
        setTimeout(() => this.connectSignalingServer(), 3000);
      };
    });
  }

  // 设置信令处理
  setupSignalingHandlers() {
    this.ws.onmessage = async (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'p2p_offer':
          await this.handleP2POffer(data);
          break;
          
        case 'p2p_answer':
          await this.handleP2PAnswer(data);
          break;
          
        case 'ice_candidate':
          await this.handleIceCandidate(data);
          break;
          
        case 'message':
          // 实时接收到的消息
          this.handleServerMessage(data.data);
          break;
          
        case 'server_message':
          // 服务器转发的离线消息
          this.handleServerMessage(data);
          break;
          
        case 'user_status':
          // 用户状态变化
          if (this.onUserStatusChanged) {
            this.onUserStatusChanged(data.userId, data.status);
          }
          break;
      }
    };
  }

  // 注册P2P能力
  async registerP2PCapability() {
    try {
      await fetch('/api/users/p2p-capability', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          supportsP2P: true,
          capabilities: ['webrtc', 'datachannel']
        })
      });
    } catch (error) {
      console.error('注册P2P能力失败:', error);
    }
  }

  // 智能发送消息（自动选择P2P或C/S）
  async sendMessage(toUserId, content) {
    try {
      // 1. 检查用户状态
      const userStatus = await this.checkUserStatus(toUserId);
      
      if (userStatus.online && userStatus.supportsP2P) {
        // 尝试P2P直连
        try {
          const p2pResult = await this.sendP2PMessage(toUserId, content);
          if (p2pResult.success) {
            return { success: true, method: 'P2P', ...p2pResult };
          }
        } catch (p2pError) {
          console.warn('P2P发送失败，回退到服务器模式:', p2pError.message);
          // P2P失败时不抛出错误，继续使用服务器转发
        }
      }
      
      // P2P失败或用户离线，使用服务器转发
      return await this.sendServerMessage(toUserId, content);
      
    } catch (error) {
      console.error('发送消息失败:', error);
      return { success: false, error: error.message };
    }
  }

  // 检查用户状态（C/S API）
  async checkUserStatus(userId) {
    try {
      const response = await fetch(`/api/users/${userId}/status`, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      
      if (!response.ok) throw new Error('获取用户状态失败');
      
      return await response.json();
      // 期望返回: { online: true, supportsP2P: true, lastSeen: timestamp }
      
    } catch (error) {
      console.warn('检查用户状态失败，假设离线:', error);
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
      
      return { 
        success: true, 
        method: 'P2P',
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
          this.p2pConnections.set(toUserId, dataChannel);
          resolve(dataChannel);
        };

        dataChannel.onmessage = (event) => {
          const message = JSON.parse(event.data);
          if (message.type === 'direct_message' && this.onMessageReceived) {
            this.onMessageReceived({
              from: message.from,
              content: message.content,
              timestamp: message.timestamp,
              method: 'P2P'
            });
          }
        };

        dataChannel.onerror = reject;

        // ICE候选事件
        peerConnection.onicecandidate = (event) => {
          if (event.candidate) {
            this.ws.send(JSON.stringify({
              type: 'ice_candidate',
              to: toUserId,
              candidate: event.candidate
            }));
          }
        };

        // 创建Offer
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        // 发送Offer给对方
        this.ws.send(JSON.stringify({
          type: 'p2p_offer',
          to: toUserId,
          offer: offer
        }));

        // 保存连接
        this.peerConnections.set(toUserId, peerConnection);

        // 连接超时
        setTimeout(() => {
          if (dataChannel.readyState !== 'open') {
            reject(new Error('P2P连接超时'));
          }
        }, 10000);

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
      await peerConnection.setRemoteDescription(data.offer);

      // 监听数据通道
      peerConnection.ondatachannel = (event) => {
        const dataChannel = event.channel;
        
        dataChannel.onopen = () => {
          console.log(`P2P连接已接受: ${data.from}`);
          this.p2pConnections.set(data.from, dataChannel);
        };

        dataChannel.onmessage = (event) => {
          const message = JSON.parse(event.data);
          if (message.type === 'direct_message' && this.onMessageReceived) {
            this.onMessageReceived({
              from: message.from,
              content: message.content,
              timestamp: message.timestamp,
              method: 'P2P'
            });
          }
        };
      };

      // ICE候选事件
      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          this.ws.send(JSON.stringify({
            type: 'ice_candidate',
            to: data.from,
            candidate: event.candidate
          }));
        }
      };

      // 创建Answer
      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);

      // 发送Answer
      this.ws.send(JSON.stringify({
        type: 'p2p_answer',
        to: data.from,
        answer: answer
      }));

      this.peerConnections.set(data.from, peerConnection);

    } catch (error) {
      console.error('处理P2P Offer失败:', error);
    }
  }

  // 处理P2P Answer
  async handleP2PAnswer(data) {
    try {
      const peerConnection = this.peerConnections.get(data.from);
      if (peerConnection) {
        await peerConnection.setRemoteDescription(data.answer);
      }
    } catch (error) {
      console.error('处理P2P Answer失败:', error);
    }
  }

  // 处理ICE候选
  async handleIceCandidate(data) {
    try {
      const peerConnection = this.peerConnections.get(data.from);
      if (peerConnection) {
        await peerConnection.addIceCandidate(data.candidate);
      }
    } catch (error) {
      console.error('处理ICE候选失败:', error);
    }
  }

  // 服务器转发消息（C/S模式）
  async sendServerMessage(toUserId, content) {
    try {
      console.log('发送服务器消息:', { toUserId, content });
      
      const response = await fetch('/api/messages', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          to: toUserId,
          content: content,
          encrypted: false,
          method: 'Server'
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('服务器响应错误:', response.status, errorText);
        throw new Error(`服务器转发失败: ${response.status}`);
      }

      const result = await response.json();
      console.log('服务器响应结果:', result);
      
      return { 
        success: true, 
        method: 'Server',
        id: result.id,
        timestamp: result.timestamp
      };

    } catch (error) {
      console.error('sendServerMessage错误:', error);
      return { success: false, error: error.message };
    }
  }

  // 处理服务器转发的消息
  handleServerMessage(data) {
    if (this.onMessageReceived) {
      this.onMessageReceived({
        from: data.from,
        content: data.content,
        timestamp: data.timestamp,
        method: 'Server'
      });
    }
  }

  // 获取消息历史（C/S API）
  async getMessageHistory(userId) {
    try {
      const response = await fetch(`/api/messages/history/${userId}`, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });

      if (!response.ok) throw new Error('获取消息历史失败');

      return await response.json();

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
  }

  // 清理资源
  cleanup() {
    // 关闭所有P2P连接
    for (let userId of this.p2pConnections.keys()) {
      this.closeP2PConnection(userId);
    }

    // 关闭WebSocket
    if (this.ws) {
      this.ws.close();
    }
  }
}

export default HybridMessaging;