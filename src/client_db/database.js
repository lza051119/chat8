import axios from 'axios';

// API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// 获取认证token
function getAuthToken() {
  return localStorage.getItem('token');
}

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 添加请求拦截器，自动添加认证头
api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * 初始化数据库（本地文件存储）
 * @returns {Promise<boolean>}
 */
export const initDatabase = async () => {
  try {
    // 获取当前用户信息
    const userStr = localStorage.getItem('user');
    if (!userStr) {
      throw new Error('用户未登录，无法初始化数据库');
    }
    
    const user = JSON.parse(userStr);
    const userId = user.id;
    
    // 检查本地存储状态
    const response = await api.get(`/v1/local-storage/status?user_id=${userId}`);
    
    if (response.data) {
      const data = response.data;
      
      // 如果数据库不存在，通过发送一条测试消息来触发数据库创建
      if (!data.database.exists) {
        console.log('📦 数据库不存在，正在创建数据库...');
        try {
          // 发送一条系统消息来触发数据库初始化
          await api.post('/v1/local-storage/messages', {
            to: userId, // 发给自己
            content: '数据库初始化完成',
            method: 'System',
            encrypted: false,
            messageType: 'system'
          });
          
          // 立即删除这条测试消息
          const messagesResponse = await api.get(`/v1/local-storage/messages/${userId}?limit=1`);
          if (messagesResponse.data.success && messagesResponse.data.messages.length > 0) {
            const testMessage = messagesResponse.data.messages[0];
            if (testMessage.content === '数据库初始化完成') {
              await api.delete(`/v1/local-storage/messages/${testMessage.id}?user_id=${userId}`);
            }
          }
          
          console.log('✅ 数据库创建成功');
        } catch (initError) {
          console.warn('⚠️ 数据库初始化过程中出现警告:', initError.message);
          // 继续执行，因为数据库可能已经被创建
        }
      }
      
      console.log('🎉 Chat8 本地文件存储已成功初始化!');
      console.log('📍 数据库状态:', data.database);
      console.log('📁 JSON备份文件:', data.has_json_backup ? '存在' : '不存在');
      if (data.json_file_path) {
        console.log('📄 JSON文件路径:', data.json_file_path);
      }
      
      return true;
    } else {
      throw new Error('获取存储状态失败');
    }
  } catch (error) {
    console.error('❌ 本地文件存储初始化失败:', error.message);
    console.log('💡 请确保后端服务正在运行并且用户已登录');
    throw error;
  }
};

/**
 * 添加一条消息到本地文件存储
 * @param {object} message - 消息对象，例如 { from: 1, to: 2, content: '你好', timestamp: '...' }
 * @returns {Promise<number>} - 返回插入的消息的ID
 */
export const addMessage = async (message) => {
  try {
    const messageData = {
      to: parseInt(message.to),  // 使用'to'字段，因为后端schema使用alias
      content: message.content,
      method: message.method || 'Server',
      encrypted: message.encrypted || false,
      messageType: message.messageType || 'text',  // 使用alias名称
      filePath: message.filePath || null,  // 使用alias名称
      fileName: message.fileName || null,  // 使用alias名称
      hiddenMessage: message.hiddenMessage || null,  // 使用alias名称
      destroyAfter: message.destroyAfter || message.destroy_after || null  // 使用alias名称
    };
    
    const response = await api.post('/v1/local-storage/messages', messageData);
    
    if (response.data && response.data.status === 'success') {
      console.log(`💾 消息已保存: ${response.data.message}`);
      return true;
    } else {
      throw new Error('保存消息失败');
    }
  } catch (error) {
    console.error('❌ 存储消息失败:', error.response?.data?.detail || error.message);
    throw error;
  }
};

/**
 * 根据好友ID获取聊天记录，支持分页和搜索
 * @param {number} friendId - 好友的用户ID
 * @param {object} options - 可选参数 { limit, offset, search }
 * @returns {Promise<object>} - 返回包含消息数组和分页信息的对象
 */
export const getMessagesWithFriend = async (friendId, options = {}) => {
  try {
    const { limit = 50, offset = 0, search = null } = options;
    
    // 构建查询参数
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    
    if (search && search.trim()) {
      params.append('search', search.trim());
    }
    
    const response = await api.get(`/v1/local-storage/messages/${parseInt(friendId)}?${params}`);
    
    if (response.data.success) {
      console.log(`📖 已获取与用户 ${friendId} 的 ${response.data.count}/${response.data.total_count} 条聊天记录`);
      console.log(`📁 存储位置: ${response.data.storage_location}`);
      return {
        messages: response.data.messages,
        count: response.data.count,
        totalCount: response.data.total_count,
        offset: response.data.offset,
        limit: response.data.limit,
        hasMore: response.data.has_more
      };
    } else {
      throw new Error('获取消息失败');
    }
  } catch (error) {
    console.error(`❌ 获取与 ${friendId} 的聊天记录失败:`, error.response?.data?.detail || error.message);
    throw error;
  }
};

/**
 * 检查本地存储状态和内容
 * @returns {Promise<object>} - 返回存储状态信息
 */
export const checkDatabaseStatus = async () => {
  try {
    // 获取当前用户信息
    const userStr = localStorage.getItem('user');
    if (!userStr) {
      throw new Error('用户未登录，无法检查数据库状态');
    }
    
    const user = JSON.parse(userStr);
    const userId = user.id;
    
    const response = await api.get(`/v1/local-storage/status?user_id=${userId}`);
    
    if (response.data) {
      const data = response.data;
      
      console.log('📊 本地文件存储状态检查结果:');
      console.log('📍 数据库状态:', data.database);
      console.log('📁 JSON备份文件:', data.has_json_backup ? '存在' : '不存在');
      if (data.json_file_path) {
        console.log('📄 JSON文件路径:', data.json_file_path);
      }
      
      return data;
    } else {
      throw new Error('获取存储状态失败');
    }
  } catch (error) {
    console.error('❌ 检查存储状态失败:', error.response?.data?.detail || error.message);
    return { error: error.message };
  }
};

/**
 * 清空所有消息
 * @returns {Promise<boolean>} - 返回操作结果
 */
export const clearAllMessages = async () => {
  try {
    // 获取当前用户信息
    const userStr = localStorage.getItem('user');
    if (!userStr) {
      throw new Error('用户未登录，无法清空消息');
    }
    
    const user = JSON.parse(userStr);
    const userId = user.id;
    
    const response = await api.delete(`/v1/local-storage/messages?user_id=${userId}`);
    
    if (response.data && response.data.status === 'success') {
      console.log('🗑️ 所有消息已清空:', response.data.message);
      return true;
    } else {
      throw new Error('清空消息失败');
    }
  } catch (error) {
    console.error('❌ 清空消息失败:', error.response?.data?.detail || error.message);
    throw error;
  }
};

/**
 * 存储用户密钥到本地存储
 * @param {object} keyData - 密钥数据对象
 * @returns {Promise<boolean>} - 返回操作结果
 */
export const storeUserKeys = async (keyData) => {
  try {
    // 将密钥数据存储到localStorage
    const keysToStore = {
      publicKey: keyData.public_key,
      privateKey: keyData.private_key,
      identityKey: keyData.identity_key,
      signedPrekey: keyData.signed_prekey,
      oneTimePrekeys: keyData.one_time_prekeys || [],
      keyVersion: keyData.key_version || 1,
      createdAt: keyData.created_at || new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    // 获取当前用户ID
    const userStr = localStorage.getItem('user');
    if (!userStr) {
      throw new Error('用户未登录，无法存储密钥');
    }
    
    const user = JSON.parse(userStr);
    const userId = user.id;
    
    // 存储到localStorage，使用用户ID作为键名后缀
    localStorage.setItem(`user_keys_${userId}`, JSON.stringify(keysToStore));
    
    console.log('🔐 用户密钥已存储到本地');
    return true;
  } catch (error) {
    console.error('❌ 存储用户密钥失败:', error.message);
    throw error;
  }
};

/**
 * 从本地存储获取用户密钥
 * @param {number} userId - 用户ID（可选，默认使用当前登录用户）
 * @returns {Promise<object|null>} - 返回密钥数据或null
 */
export const getUserKeys = async (userId = null) => {
  try {
    // 如果没有提供userId，使用当前登录用户
    if (!userId) {
      const userStr = localStorage.getItem('user');
      if (!userStr) {
        throw new Error('用户未登录，无法获取密钥');
      }
      const user = JSON.parse(userStr);
      userId = user.id;
    }
    
    // 从localStorage获取密钥
    const keysStr = localStorage.getItem(`user_keys_${userId}`);
    if (!keysStr) {
      console.log('ℹ️  本地未找到用户密钥');
      return null;
    }
    
    const keys = JSON.parse(keysStr);
    console.log('🔐 已从本地获取用户密钥');
    return keys;
  } catch (error) {
    console.error('❌ 获取用户密钥失败:', error.message);
    throw error;
  }
};

/**
 * 清除用户密钥
 * @param {number} userId - 用户ID（可选，默认使用当前登录用户）
 * @returns {Promise<boolean>} - 返回操作结果
 */
export const clearUserKeys = async (userId = null) => {
  try {
    // 如果没有提供userId，使用当前登录用户
    if (!userId) {
      const userStr = localStorage.getItem('user');
      if (!userStr) {
        throw new Error('用户未登录，无法清除密钥');
      }
      const user = JSON.parse(userStr);
      userId = user.id;
    }
    
    // 从localStorage删除密钥
    localStorage.removeItem(`user_keys_${userId}`);
    console.log('🗑️ 用户密钥已清除');
    return true;
  } catch (error) {
    console.error('❌ 清除用户密钥失败:', error.message);
    throw error;
  }
};

/**
 * 验证本地密钥的完整性
 * @returns {Promise<boolean>} - 返回验证结果
 */
export const validateUserKeys = async () => {
  try {
    const keys = await getUserKeys();
    if (!keys) {
      return false;
    }
    
    // 检查必要的密钥字段
    const requiredFields = ['publicKey', 'privateKey', 'identityKey', 'signedPrekey'];
    for (const field of requiredFields) {
      if (!keys[field]) {
        console.warn(`⚠️  缺少必要的密钥字段: ${field}`);
        return false;
      }
    }
    
    console.log('✅ 本地密钥验证通过');
    return true;
  } catch (error) {
    console.error('❌ 密钥验证失败:', error.message);
    return false;
  }
};

// 在控制台提供全局访问函数
if (typeof window !== 'undefined') {
  window.checkChat8LocalStorage = checkDatabaseStatus;
  window.clearChat8Messages = clearAllMessages;
  window.getUserKeys = getUserKeys;
  window.clearUserKeys = clearUserKeys;
  window.validateUserKeys = validateUserKeys;
  console.log('💡 提示: 在浏览器控制台输入以下命令:');
  console.log('  - checkChat8LocalStorage() 查看本地存储状态');
  console.log('  - clearChat8Messages() 清空所有消息');
  console.log('  - getUserKeys() 获取当前用户密钥');
  console.log('  - clearUserKeys() 清除当前用户密钥');
  console.log('  - validateUserKeys() 验证密钥完整性');
}

// 导出一个虚拟的数据库对象以保持兼容性
export default {
  name: 'Chat8LocalFileStorage',
  type: 'Local File System',
  isOpen: () => true
};