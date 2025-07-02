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
    const response = await api.get(`/local-storage/status?user_id=${userId}`);
    
    if (response.data) {
      const data = response.data;
      
      // 如果数据库不存在，通过发送一条测试消息来触发数据库创建
      if (!data.database.exists) {
        console.log('📦 数据库不存在，正在创建数据库...');
        try {
          // 发送一条系统消息来触发数据库初始化
          await api.post('/local-storage/messages', {
            to_id: userId, // 发给自己
            content: '数据库初始化完成',
            method: 'System',
            encrypted: false,
            message_type: 'system'
          });
          
          // 立即删除这条测试消息
          const messagesResponse = await api.get(`/local-storage/messages/${userId}?limit=1`);
          if (messagesResponse.data.success && messagesResponse.data.messages.length > 0) {
            const testMessage = messagesResponse.data.messages[0];
            if (testMessage.content === '数据库初始化完成') {
              await api.delete(`/local-storage/messages/${testMessage.message_id}?user_id=${userId}`);
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
      destroyAfter: message.destroy_after || null  // 使用alias名称
    };
    
    const response = await api.post('/local-storage/messages', messageData);
    
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
    
    const response = await api.get(`/local-storage/messages/${parseInt(friendId)}?${params}`);
    
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
    
    const response = await api.get(`/local-storage/status?user_id=${userId}`);
    
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
    
    const response = await api.delete(`/local-storage/messages?user_id=${userId}`);
    
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

// 在控制台提供全局访问函数
if (typeof window !== 'undefined') {
  window.checkChat8LocalStorage = checkDatabaseStatus;
  window.clearChat8Messages = clearAllMessages;
  console.log('💡 提示: 在浏览器控制台输入以下命令:');
  console.log('  - checkChat8LocalStorage() 查看本地存储状态');
  console.log('  - clearChat8Messages() 清空所有消息');
}

// 导出一个虚拟的数据库对象以保持兼容性
export default {
  name: 'Chat8LocalFileStorage',
  type: 'Local File System',
  isOpen: () => true
};