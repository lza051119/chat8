import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器 - 添加认证token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// 响应拦截器 - 处理通用错误
api.interceptors.response.use((response) => {
  return response;
}, (error) => {
  if (error.response?.status === 401) {
    // token过期，清除本地存储并跳转登录
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }
  return Promise.reject(error);
});

// 认证相关API
export const authAPI = {
  // 用户登录
  login: (credentials) => api.post('/auth/login', credentials),
  
  // 用户注册
  register: (userData) => api.post('/auth/register', userData),
  
  // 退出登录
  logout: () => api.post('/auth/logout'),
  
  // 刷新token
  refreshToken: () => api.post('/auth/refresh'),
  
  // 获取用户信息
  getUserInfo: () => api.get('/auth/me')
};

// 联系人相关API
export const contactAPI = {
  // 获取联系人列表
  getContacts: () => api.get('/contacts'),
  
  // 发送好友申请
  sendFriendRequest: (userId, message = null) => api.post('/contacts/request', { to_user_id: userId, message }),
  
  // 获取好友申请列表
  getFriendRequests: (type = 'received') => api.get(`/requests?request_type=${type}`),
  
  // 处理好友申请
  handleFriendRequest: (requestId, action) => api.post('/requests/handle', { request_id: requestId, action }),
  
  // 删除联系人
  removeContact: (userId) => api.delete(`/contacts/${userId}`),
  
  // 搜索用户
  searchUsers: (query) => api.get(`/users/search?q=${encodeURIComponent(query)}`)
};

// 消息相关API
export const messageAPI = {
  // 发送消息
  sendMessage: (messageData) => api.post('/messages', messageData),
  
  // 获取消息
  getMessages: (params) => api.get('/messages', { params }),
  
  // 获取消息历史
  getMessageHistory: (userId, params) => api.get(`/messages/history/${userId}`, { params })
};

// 密钥管理API
export const keyAPI = {
  // 上传公钥
  uploadPublicKey: (publicKey) => api.post('/keys/public', { publicKey }),
  
  // 获取用户公钥
  getPublicKey: (userId) => api.get(`/keys/public/${userId}`),
  
  // 获取所有联系人公钥
  getAllPublicKeys: () => api.get('/keys/public')
};

// WebRTC信令API
export const signalingAPI = {
  // 发送WebRTC offer
  sendOffer: (targetUserId, offer) => 
    api.post('/signaling/offer', { targetUserId, offer }),
  
  // 发送WebRTC answer
  sendAnswer: (targetUserId, answer) => 
    api.post('/signaling/answer', { targetUserId, answer }),
  
  // 发送ICE candidate
  sendICECandidate: (targetUserId, candidate) => 
    api.post('/signaling/ice-candidate', { targetUserId, candidate }),
  
  // 获取待处理的信令消息
  getPendingSignals: () => api.get('/signaling/pending')
};

// 在线状态API
const presenceAPI = {
  // 发送心跳
  heartbeat: () => {
    return api.post('/user-status/heartbeat', {
      timestamp: new Date().toISOString()
    });
  },
  
  // 获取用户状态
  getUserStatus: (userId) => {
    return api.get(`/user-status/${userId}`);
  },
  
  // 获取当前用户状态
  getMyStatus: () => {
    return api.get('/user-status/me');
  },
  
  // 获取服务统计信息
  getStats: () => {
    return api.get('/user-status/stats');
  },
  
  // 已移除的功能（保持兼容性）
  setOnlineStatus: () => Promise.resolve({ data: { success: true, message: '在线状态功能已移除' } }),
  getContactsStatus: () => Promise.resolve({ data: { success: true, data: [], message: '联系人状态功能已移除' } }),
  registerP2PCapability: () => Promise.resolve({ data: { success: true, message: 'P2P注册功能已移除' } })
};

// 上传API
const uploadAPI = {
  uploadAvatar: (file) => {
    const formData = new FormData();
    formData.append('avatar', file);
    return api.post('/upload/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  uploadImage: (formData) => {
    return api.post('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

// 组合所有API模块
export const hybridApi = {
  // 认证相关
  ...authAPI,
  
  // 联系人相关
  getContacts: contactAPI.getContacts,
  sendFriendRequest: contactAPI.sendFriendRequest,
  getFriendRequests: contactAPI.getFriendRequests,
  handleFriendRequest: contactAPI.handleFriendRequest,
  removeContact: contactAPI.removeContact,
  searchUsers: contactAPI.searchUsers,
  
  // 消息相关
  sendMessage: messageAPI.sendMessage,
  getMessageHistory: messageAPI.getMessageHistory,
  
  // 密钥管理
  uploadPublicKey: keyAPI.uploadPublicKey,
  getPublicKey: keyAPI.getPublicKey,
  getAllPublicKeys: keyAPI.getAllPublicKeys,
  
  // WebRTC信令
  sendOffer: signalingAPI.sendOffer,
  sendAnswer: signalingAPI.sendAnswer,
  sendICECandidate: signalingAPI.sendICECandidate,
  getPendingSignals: signalingAPI.getPendingSignals,
  
  // 在线状态
  setOnlineStatus: presenceAPI.setOnlineStatus,
  getContactsStatus: presenceAPI.getContactsStatus,
  heartbeat: presenceAPI.heartbeat,
  registerP2PCapability: presenceAPI.registerP2PCapability,
  getUserStatus: presenceAPI.getUserStatus,
  
  // 上传
  uploadAvatar: uploadAPI.uploadAvatar,
  uploadImage: uploadAPI.uploadImage
};

export default api;