import axios from 'axios';

const api = axios.create({
  baseURL: '/api', // 你的后端API前缀
});

// 用户注册
export function register(data) {
  // 后端实现：用户注册
  return api.post('/register', data);
}

// 用户登录
export function login(data) {
  // 后端实现：用户登录，返回token
  return api.post('/login', data);
}

// 获取联系人列表
export function getContacts(token) {
  // 后端实现：返回当前用户的联系人
  return api.get('/contacts', { headers: { Authorization: `Bearer ${token}` } });
}

// 添加好友
export function addContact(token, friendId) {
  // 后端实现：添加好友
  return api.post('/contacts/add', { friendId }, { headers: { Authorization: `Bearer ${token}` } });
}

// 获取公钥
export function getPublicKey(token, userId) {
  // 后端实现：获取指定用户的公钥
  return api.get(`/keys/public?userId=${userId}`, { headers: { Authorization: `Bearer ${token}` } });
}

// 上传公钥
export function uploadPublicKey(token, publicKey) {
  // 后端实现：上传当前用户的公钥
  return api.post('/keys/exchange', { publicKey }, { headers: { Authorization: `Bearer ${token}` } });
}

// 获取密钥指纹
export function getFingerprint(token) {
  // 后端实现：返回当前用户的密钥指纹
  return api.get('/keys/fingerprint', { headers: { Authorization: `Bearer ${token}` } });
}