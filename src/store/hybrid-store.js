import { reactive, computed } from 'vue';
import CryptoJS from 'crypto-js';

// 创建reactive状态
const state = reactive({
  // 用户信息
  user: null,
  token: null,

  // 联系人列表
  contacts: [],

  // 对话记录 - 简化结构，只保留消息列表和最后一条消息
  conversations: {}, // { userId: { messages: [], lastMessage: {} } }

  // 当前聊天对象
  currentContact: null,

  // P2P连接状态
  p2pConnections: {},

  // 在线状态
  onlineUsers: new Set(),

  // 消息统计
  messageStats: {
    totalSent: 0,
    totalReceived: 0,
    p2pSent: 0,
    p2pReceived: 0,
    serverSent: 0,
    serverReceived: 0
  },

  // HybridMessaging服务实例
  hybridMessaging: null,
});

export const hybridStore = {
  // 直接暴露响应式状态
  get user() {
    return state.user;
  },
  get token() {
    return state.token;
  },
  get contacts() {
    return state.contacts;
  },
  get conversations() {
    return state.conversations;
  },
  get currentContact() {
    return state.currentContact;
  },
  get p2pConnections() {
    return state.p2pConnections;
  },
  get onlineUsers() {
    return state.onlineUsers;
  },
  get messageStats() {
    return state.messageStats;
  },
  
  // 计算属性
  get isLoggedIn() {
    return !!state.token;
  },

  // 设置用户信息
  async setUser(user, token) {
    // 验证输入参数 - 后端返回的用户对象使用 userId 字段
    const userId = user?.id || user?.userId;
    if (!user || !userId || !token) {
      console.error('setUser: 无效的用户信息或token', { user, token });
      return false;
    }
    
    // 标准化用户对象，确保有 id 字段
    const normalizedUser = {
      ...user,
      id: userId
    };
    
    try {
      // 设置状态
      state.user = normalizedUser;
      state.token = token;
      
      // 保存到本地存储
      localStorage.setItem('user', JSON.stringify(normalizedUser));
      localStorage.setItem('token', token);
      
      console.log('用户信息设置成功:', { userId: normalizedUser.id, username: normalizedUser.username });
      
      // 登录成功后初始化本地数据库
      try {
        console.log('📦 正在初始化本地数据库...');
        const { initDatabase } = await import('../client_db/database.js');
        await initDatabase();
        console.log('✅ 本地数据库初始化完成');
      } catch (dbError) {
        console.error('❌ 本地数据库初始化失败:', dbError);
        console.log('⚠️ 应用将在没有本地数据库的情况下运行');
      }
      
      return true;
    } catch (error) {
      console.error('设置用户信息失败:', error);
      return false;
    }
  },

  // 从本地存储加载用户信息
  loadUserFromStorage() {
    const user = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    
    if (user && token) {
      try {
        const parsedUser = JSON.parse(user);
        // 标准化用户对象，确保有 id 字段
        const userId = parsedUser?.id || parsedUser?.userId;
        if (userId) {
          state.user = {
            ...parsedUser,
            id: userId
          };
        } else {
          state.user = parsedUser;
        }
        state.token = token;
      } catch (error) {
        console.error('解析用户信息失败:', error);
        state.user = null;
        state.token = null;
      }
    } else {
      state.user = null;
      state.token = null;
    }
  },

  // 退出登录
  logout() {
    state.user = null;
    state.token = null;
    state.contacts = [];
    state.conversations = {};
    state.currentContact = null;
    state.p2pConnections = {};
    state.onlineUsers.clear();
    
    // 清除本地存储
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  },

  // 设置联系人列表
  setContacts(contacts) {
    // 确保contacts是数组
    if (!Array.isArray(contacts)) {
      console.error('setContacts: contacts must be an array, received:', typeof contacts);
      state.contacts = [];
      return;
    }
    
    // 标准化联系人数据，确保必要字段存在
    const normalizedContacts = contacts.map(contact => ({
      ...contact,
      username: contact.username || '',
      email: contact.email || '',
      online: contact.online || false,
      connectionStatus: contact.connectionStatus || {
        canUseP2P: false,
        preferredMethod: 'Server',
        p2pStatus: 'disconnected'
      },
      lastMessage: contact.lastMessage || null
    }));
    
    state.contacts = normalizedContacts;
    
    // 为每个联系人初始化对话记录
    normalizedContacts.forEach(contact => {
      if (!state.conversations[contact.id]) {
        state.conversations[contact.id] = {
          messages: [],
          lastMessage: {}
        };
      }
    });
  },

  // 设置当前聊天对象
  setCurrentContact(contact) {
    state.currentContact = contact;
  },

  // 设置当前聊天（兼容性方法）
  setCurrentChat(contact) {
    state.currentContact = contact;
  },

  // 添加新联系人
  addContact(contact) {
    if (!state.contacts.find(c => c.id === contact.id)) {
      // 标准化联系人数据
      const normalizedContact = {
        ...contact,
        username: contact.username || '',
        email: contact.email || '',
        online: contact.online || false,
        connectionStatus: contact.connectionStatus || {
          canUseP2P: false,
          preferredMethod: 'Server',
          p2pStatus: 'disconnected'
        },
        lastMessage: contact.lastMessage || null
      };
      
      state.contacts.push(normalizedContact);
      state.conversations[contact.id] = {
        messages: [],
        lastMessage: {}
      };
    }
  },

  removeContact(userId) {
    // 从联系人列表中移除
    const index = state.contacts.findIndex(c => c.id === userId);
    if (index !== -1) {
      state.contacts.splice(index, 1);
    }
    
    // 删除对话记录
    if (state.conversations[userId]) {
      delete state.conversations[userId];
    }
    
    // 清除P2P连接状态
    if (state.p2pConnections[userId]) {
      delete state.p2pConnections[userId];
    }
    
    // 从在线用户列表中移除
    state.onlineUsers.delete(userId);
    
    // 如果当前聊天对象是被删除的联系人，清除当前聊天
    if (state.currentContact?.id === userId) {
      state.currentContact = null;
    }
  },

  // 添加消息到对话
  addMessage(userId, message) {
    if (!state.conversations[userId]) {
      state.conversations[userId] = {
        messages: [],
        lastMessage: {}
      };
    }

    const conversation = state.conversations[userId];
    
    // 检查是否已存在相同ID的消息，避免重复添加
    const existingIndex = conversation.messages.findIndex(m => m.id === message.id);
    if (existingIndex !== -1) {
      // 更新现有消息 - 使用splice确保触发响应式更新
      conversation.messages.splice(existingIndex, 1, { ...message });
    } else {
      // 添加新消息 - 创建新数组确保触发响应式更新
      conversation.messages = [...conversation.messages, { ...message }];
    }
    
    conversation.lastMessage = { ...message };
    
    // 更新联系人的最后一条消息
    const contact = state.contacts.find(c => c.id === userId);
    if (contact) {
      contact.lastMessage = { ...message };
    }
    
    console.log(`已添加消息到用户${userId}的对话:`, message);
    console.log(`当前对话消息数量:`, conversation.messages.length);
  },

  // 设置对话消息（用于加载历史消息）
  setMessages(userId, messages) {
    if (!state.conversations[userId]) {
      state.conversations[userId] = {
        messages: [],
        lastMessage: {}
      };
    }
    
    // 确保messages是数组
    if (!Array.isArray(messages)) {
      console.error('setMessages: messages must be an array');
      return;
    }
    
    // 按时间戳排序消息
    const sortedMessages = messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    state.conversations[userId].messages = sortedMessages;
    
    // 更新最后一条消息
    if (sortedMessages.length > 0) {
      state.conversations[userId].lastMessage = sortedMessages[sortedMessages.length - 1];
      
      // 更新联系人的最后一条消息
      const contact = state.contacts.find(c => c.id === userId);
      if (contact) {
        contact.lastMessage = sortedMessages[sortedMessages.length - 1];
      }
    }
    
    console.log(`已设置用户${userId}的消息历史，共${sortedMessages.length}条消息`);
  },

  // 获取对话消息
  getMessages(userId) {
    if (!state.conversations[userId]) {
      state.conversations[userId] = {
        messages: [],
        lastMessage: {}
      };
    }
    return state.conversations[userId].messages;
  },

  // 获取联系人信息
  getContact(userId) {
    return state.contacts.find(c => c.id === userId);
  },

  // 更新P2P连接状态
  updateP2PConnection(userId, status) {
    state.p2pConnections[userId] = status;
  },

  // 获取P2P连接状态
  getP2PStatus(userId) {
    return state.p2pConnections[userId] || 'disconnected';
  },

  // 更新在线状态
  updateOnlineStatus(userId, isOnline, timestamp = null) {
    // 确保userId是数字类型
    const numericUserId = parseInt(userId);
    
    if (isOnline) {
      state.onlineUsers.add(numericUserId);
    } else {
      state.onlineUsers.delete(numericUserId);
    }
    
    // 更新联系人在线状态
    const contact = state.contacts.find(c => parseInt(c.id) === numericUserId);
    if (contact) {
      contact.online = isOnline;
      if (timestamp) {
        contact.lastSeen = timestamp;
      }
      console.log(`已更新用户 ${numericUserId} 的在线状态: ${isOnline ? '在线' : '离线'}`);
    }
  },

  // 检查用户是否在线
  isUserOnline(userId) {
    return state.onlineUsers.has(userId);
  },

  // 加密消息
  encryptMessage(message, publicKey) {
    try {
      // 这里应该使用RSA加密，暂时用AES模拟
      const encrypted = CryptoJS.AES.encrypt(message, publicKey).toString();
      return encrypted;
    } catch (error) {
      console.error('加密失败:', error);
      return message; // 如果加密失败，返回原消息
    }
  },

  // 解密消息
  decryptMessage(encryptedMessage, privateKey) {
    try {
      // 这里应该使用RSA解密，暂时用AES模拟
      const decrypted = CryptoJS.AES.decrypt(encryptedMessage, privateKey).toString(CryptoJS.enc.Utf8);
      return decrypted || encryptedMessage; // 如果解密失败，返回原消息
    } catch (error) {
      console.error('解密失败:', error);
      return encryptedMessage; // 如果解密失败，返回原消息
    }
  },

  // 清空所有对话
  clearAllConversations() {
    Object.keys(state.conversations).forEach(userId => {
      state.conversations[userId] = {
        messages: [],
        lastMessage: {}
      };
    });
  },

  getConnectionStats() {
    // 返回一个模拟的连接统计对象
    return {
      p2pConnections: 1,
      serverConnections: 1,
      p2pRatio: 50
    };
  },

  // HybridMessaging服务管理
  setHybridMessaging(hybridMessaging) {
    state.hybridMessaging = hybridMessaging;
    
    // 设置消息接收回调
    if (hybridMessaging) {
      hybridMessaging.onMessageReceived = async (message) => {
        await this.handleReceivedMessage(message);
      };
      
      hybridMessaging.onUserStatusChanged = (data) => {
        console.log('Store收到用户状态变化:', data);
        
        // 验证数据有效性
        if (!data || typeof data !== 'object') {
          console.warn('收到无效的用户状态变化数据:', data);
          return;
        }
        
        // 验证userId
        const userId = parseInt(data.userId);
        if (!userId || userId <= 0) {
          console.warn('收到无效的用户ID:', data.userId);
          return;
        }
        
        // 验证status
        if (!data.status || typeof data.status !== 'string') {
          console.warn('收到无效的用户状态:', data.status);
          return;
        }
        
        // 处理新格式的presence消息
        const isOnline = data.isOnline !== undefined ? data.isOnline : (data.status === 'online');
        const timestamp = data.timestamp;
        const websocketConnected = data.websocketConnected;
        const p2pCapability = data.p2pCapability;
        
        // 更新在线状态
        this.updateOnlineStatus(userId, isOnline, timestamp);
        
        // 如果有P2P能力信息，更新P2P状态
        if (p2pCapability !== undefined) {
          this.updateP2PConnection(userId, p2pCapability ? 'available' : 'unavailable');
        }
        
        // 状态变化已处理
      };
      
      // 设置P2P连接状态变化回调
      hybridMessaging.onP2PStatusChanged = (userId, status) => {
        this.updateP2PConnection(userId, status);
        
        // 更新联系人的连接状态
        const contact = state.contacts.find(c => c.id === userId);
        if (contact) {
          contact.connectionStatus = {
            ...contact.connectionStatus,
            canUseP2P: status === 'connected',
            preferredMethod: status === 'connected' ? 'P2P' : 'Server',
            p2pStatus: status
          };
        }
      };
    }
  },

  getHybridMessaging() {
    return state.hybridMessaging;
  },

  // 处理接收到的消息
  async handleReceivedMessage(message) {
    // 生成唯一的消息ID，避免重复
    const messageId = message.id || `msg_${message.from}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const messageObj = {
      id: messageId,
      from: message.from,
      to: state.user?.id,
      content: message.content,
      timestamp: message.timestamp || new Date().toISOString(),
      method: message.method || 'Server',
      encrypted: false,
      // 添加图片消息支持
      messageType: message.messageType || message.message_type || 'text',
      filePath: message.filePath || message.file_path || null,
      fileName: message.fileName || message.file_name || null,
      imageUrl: message.imageUrl || null
    };
    
    console.log('Store处理接收到的消息:', messageObj);
    
    // 立即添加到对话记录（UI显示）
    this.addMessage(message.from, messageObj);
    
    // 异步保存到本地数据库
    try {
      // 动态导入数据库函数
      const { addMessage } = await import('../client_db/database.js');
      
      // 构造数据库消息对象
      const dbMessage = {
        from: message.from,
        to: state.user?.id,
        content: message.content,
        timestamp: message.timestamp || new Date().toISOString(),
        method: message.method || 'Server',
        messageType: message.messageType || message.message_type || 'text',
        filePath: message.filePath || message.file_path || null,
        fileName: message.fileName || message.file_name || null,
        imageUrl: message.imageUrl || null
      };
      
      await addMessage(dbMessage);
      console.log('接收到的消息已保存到本地数据库');
    } catch (dbError) {
      console.warn('保存接收消息到本地数据库失败:', dbError);
    }
    
    // 更新消息统计
    state.messageStats.totalReceived++;
    if (message.method === 'P2P') {
      state.messageStats.p2pReceived++;
    } else {
      state.messageStats.serverReceived++;
    }
    
    console.log(`消息已添加到用户${message.from}的对话，当前消息总数:`, this.getMessages(message.from).length);
  },

  // 初始化HybridMessaging服务
  async initializeHybridMessaging() {
    if (!state.user || !state.token) {
      console.error('用户未登录，无法初始化消息服务');
      return false;
    }
    
    try {
      // 动态导入HybridMessaging
      const { default: HybridMessaging } = await import('../services/HybridMessaging.js');
      
      const hybridMessaging = new HybridMessaging();
      
      // 先设置回调函数，再初始化
      this.setHybridMessaging(hybridMessaging);
      
      // 然后初始化连接
      await hybridMessaging.initialize(state.user.id, state.token);
      
      console.log('HybridMessaging服务初始化成功，回调函数已设置');
      return true;
    } catch (error) {
      console.error('初始化HybridMessaging服务失败:', error);
      return false;
    }
  },

  // 清理HybridMessaging服务
  cleanupHybridMessaging() {
    if (state.hybridMessaging) {
      state.hybridMessaging.cleanup();
      state.hybridMessaging = null;
    }
  },
};

export default hybridStore;