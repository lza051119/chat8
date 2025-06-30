import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';

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
  
  // 添加联系人
  addContact: (userId) => api.post('/contacts', { userId }),
  
  // 删除联系人
  removeContact: (userId) => api.delete(`/contacts/${userId}`),
  
  // 搜索用户
  searchUsers: (query) => api.get(`/users/search?q=${encodeURIComponent(query)}`)
};

// 消息相关API
export const messageAPI = {
  // 发送消息
  sendMessage: (messageData) => api.post('/messages', messageData),
  
  // 获取消息历史
  getMessageHistory: (userId, page = 1, limit = 50) => 
    api.get(`/messages/history/${userId}?page=${page}&limit=${limit}`)
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
export const presenceAPI = {
  // 设置在线状态
  setOnlineStatus: (status) => api.post('/presence/status', { status }),
  
  // 获取联系人在线状态
  getContactsStatus: () => api.get('/presence/contacts'),
  
  // 心跳保持在线
  heartbeat: () => api.post('/presence/heartbeat')
};

export default api; 