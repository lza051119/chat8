import axios from 'axios';
import { getChinaTimeISO } from '../utils/timeUtils.js';
import config from '../config/config.js';

const API_BASE_URL = config.API_BASE_URL + '/api';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'ngrok-skip-browser-warning': 'true',// <--- 将 header 添加到这里
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
  login: (credentials) => api.post('/v1/auth/login', credentials),
  
  // 用户注册
  register: (userData) => api.post('/v1/auth/register', userData),
  
  // 退出登录
  logout: () => api.post('/v1/auth/logout'),
  
  // 刷新token
  refreshToken: () => api.post('/v1/auth/refresh'),
  
  // 获取用户信息
  getUserInfo: () => api.get('/v1/auth/me'),
  
  // 获取用户加密密钥
  getUserKeys: (userId) => api.get(`/v1/encryption/my-keys`)
};

// 联系人相关API
export const contactAPI = {
  // 获取联系人列表
  getContacts: () => api.get('/v1/contacts'),
  
  // 发送好友申请
  sendFriendRequest: (userId, message = null) => api.post('/v1/contacts/request', { to_user_id: userId, message }),
  
  // 获取好友申请列表
  getFriendRequests: (type = 'received') => api.get(`/v1/requests?request_type=${type}`),
  
  // 处理好友申请
  handleFriendRequest: (requestId, action) => api.post('/v1/requests/handle', { request_id: requestId, action }),
  
  // 删除联系人
  removeContact: (userId) => api.delete(`/v1/contacts/${userId}`),
  
  // 搜索用户
  searchUsers: (query) => api.get(`/v1/users/search?q=${encodeURIComponent(query)}`)
};

// 消息相关API
export const messageAPI = {
  // 发送消息
  sendMessage: (messageData) => api.post('/v1/messages', messageData),
  
  // 获取消息
  getMessages: (params) => api.get('/v1/messages', { params }),
  
  // 获取消息历史
  getMessageHistory: (userId, params) => api.get(`/v1/messages/history/${userId}`, { params })
};

// 密钥管理API
export const keyAPI = {
  // 上传公钥
  uploadPublicKey: (publicKey) => api.post('/v1/keys/public', { publicKey }),
  
  // 获取用户公钥
  getPublicKey: (userId) => api.get(`/v1/keys/public/${userId}`),
  
  // 获取所有联系人公钥
  getAllPublicKeys: () => api.get('/v1/keys/public')
};

// WebRTC信令API
export const signalingAPI = {
  // 发送WebRTC offer
  sendOffer: (targetUserId, offer) => 
    api.post('/v1/signaling/offer', { targetUserId, offer }),
  
  // 发送WebRTC answer
  sendAnswer: (targetUserId, answer) => 
    api.post('/v1/signaling/answer', { targetUserId, answer }),
  
  // 发送ICE candidate
  sendICECandidate: (targetUserId, candidate) => 
    api.post('/v1/signaling/ice-candidate', { targetUserId, candidate }),
  
  // 获取待处理的信令消息
  getPendingSignals: () => api.get('/v1/signaling/pending')
};

// 在线状态API
const presenceAPI = {
  // 发送心跳
  heartbeat: () => {
    return api.post('/v1/user-status/heartbeat', {
      timestamp: getChinaTimeISO()
    });
  },
  
  // 获取用户状态
  getUserStatus: (userId) => {
    return api.get(`/v1/user-status/${userId}`);
  },
  
  // 获取当前用户状态
  getMyStatus: () => {
    return api.get('/v1/user-status/me');
  },
  
  // 获取服务统计信息
  getStats: () => {
    return api.get('/v1/user-status/stats');
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
    formData.append('file', file);
    return api.post('/v1/avatar/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  deleteAvatar: () => {
    return api.delete('/v1/avatar');
  },
  
  uploadImage: (formData) => {
    return api.post('/v1/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  uploadFile: (formData) => {
    return api.post('/v1/upload/file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

// 用户个人信息API
const profileAPI = {
  // 获取个人信息
  getProfile: () => api.get('/v1/profile'),
  
  // 获取指定用户的个人信息
  getUserProfile: (userId) => api.get(`/v1/profile/${userId}`),
  
  // 创建个人信息
  createProfile: (profileData) => api.post('/v1/profile', profileData),
  
  // 更新个人信息
  updateProfile: (profileData) => api.put('/v1/profile', profileData),
  
  // 删除个人信息
  deleteProfile: () => api.delete('/v1/profile')
};

// 组合所有API模块
export const hybridApi = {
  // 认证相关
  ...authAPI,
  getUserKeys: authAPI.getUserKeys,
  
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
  deleteAvatar: uploadAPI.deleteAvatar,
  uploadImage: uploadAPI.uploadImage,
  uploadFile: uploadAPI.uploadFile,
  
  // 个人信息
  get: profileAPI.getProfile,
  getUserProfile: profileAPI.getUserProfile,
  post: profileAPI.createProfile,
  put: profileAPI.updateProfile,
  delete: profileAPI.deleteProfile
};

export default api;