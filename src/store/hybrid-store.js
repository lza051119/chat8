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
});

export const hybridStore = {
  ...state,
  
  // 计算属性
  get isLoggedIn() {
    return !!state.token;
  },

  // 设置用户信息
  setUser(user, token) {
    state.user = user;
    state.token = token;
    
    // 保存到本地存储
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('token', token);
  },

  // 从本地存储加载用户信息
  loadUserFromStorage() {
    const user = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    
    if (user && token) {
      state.user = JSON.parse(user);
      state.token = token;
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
    state.contacts = contacts;
    
    // 为每个联系人初始化对话记录
    contacts.forEach(contact => {
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

  // 添加新联系人
  addContact(contact) {
    if (!state.contacts.find(c => c.id === contact.id)) {
      state.contacts.push(contact);
      state.conversations[contact.id] = {
        messages: [],
        lastMessage: {}
      };
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
    conversation.messages.push(message);
    conversation.lastMessage = message;
  },

  // 获取对话消息
  getMessages(userId) {
    return state.conversations[userId]?.messages || [];
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
  updateOnlineStatus(userId, isOnline) {
    if (isOnline) {
      state.onlineUsers.add(userId);
    } else {
      state.onlineUsers.delete(userId);
    }
    
    // 更新联系人在线状态
    const contact = state.contacts.find(c => c.id === userId);
    if (contact) {
      contact.online = isOnline;
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
};

export default hybridStore; 