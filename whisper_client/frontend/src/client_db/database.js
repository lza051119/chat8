// import Dexie from 'dexie'; // 不再使用 Dexie
import CryptoJS from 'crypto-js';
import { getChinaTimeISO } from '../utils/timeUtils.js';
import DatabaseAdapter from './database/adapter';
import { isElectronEnvironment } from './database/local-storage';

// 检查运行环境
const isElectron = isElectronEnvironment();
console.log(`数据库初始化 - 运行环境: ${isElectron ? 'Electron' : 'Web浏览器'}`);
console.log(`数据库存储方式: ${isElectron ? '本地文件系统' : 'IndexedDB'}`);

// The database instance for the currently logged-in user.
// This will be null until initDatabase is called.
let db = null;

/**
 * Gets the database instance for the current user.
 * Throws an error if the database is not initialized.
 * @returns {Object} The initialized database instance.
 */
export const getDb = () => {
  if (!db) {
    throw new Error('Database not initialized. Please call initDatabase after user login.');
  }
  return db;
};

// 获取当前用户ID
function getCurrentUserId() {
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  try {
    const user = JSON.parse(userStr);
    return user.id || user.userId;
  } catch (error) {
    console.error('解析用户信息失败:', error);
    return null;
  }
}

// 获取认证token
function getAuthToken() {
  return localStorage.getItem('token');
}

// 加密消息内容
function encryptContent(content, key) {
  if (!key) return content;
  try {
    return CryptoJS.AES.encrypt(content, key).toString();
  } catch (error) {
    console.error('加密失败:', error);
    return content;
  }
}

// 解密消息内容
function decryptContent(encryptedContent, key) {
  if (!key) return encryptedContent;
  try {
    const bytes = CryptoJS.AES.decrypt(encryptedContent, key);
    const decrypted = bytes.toString(CryptoJS.enc.Utf8);
    return decrypted || encryptedContent;
  } catch (error) {
    console.error('解密失败:', error);
    return encryptedContent;
  }
}

/**
 * Initializes a user-specific local database.
 * This must be called after a user logs in.
 * @param {number} userId The ID of the logged-in user.
 * @returns {Promise<boolean>}
 */
export const initDatabase = async (userId) => {
  if (!userId) {
    throw new Error('User ID is required to initialize the database');
  }
  
  try {
    console.log(`🔧 正在为用户 ${userId} 初始化数据库...`);
    console.log(`存储类型: ${isElectron ? '本地文件系统' : 'IndexedDB'}`);
    
    // 创建新的数据库适配器实例
    db = new DatabaseAdapter(userId);
    
    // 打开数据库连接
    await db.open();
    
    console.log(`🎉 数据库初始化成功，用户ID: ${userId}`);
    
    // 检查用户密钥是否存在，不存在则生成
    const userKeys = await db.userKeys.get(userId);
    if (!userKeys) {
      console.log('🔑 正在生成用户密钥对...');
      await generateUserKeyPair(userId);
    }
    
    return true;
  } catch (error) {
    console.error(`❌ 数据库初始化失败:`, error.message);
    throw error;
  }
};

/**
 * Generates and stores a key pair for the user.
 * @param {number} userId - The user's ID.
 */
async function generateUserKeyPair(userId) {
  const localDb = getDb();
  try {
    const keyPair = {
      publicKey: `pub_${userId}_${Date.now()}`,
      privateKey: `priv_${userId}_${Date.now()}`
    };
    
    await localDb.userKeys.add({
      id: userId,
      publicKey: keyPair.publicKey,
      privateKey: keyPair.privateKey,
      keyPair: JSON.stringify(keyPair),
      createdAt: getChinaTimeISO()
    });
    console.log('✅ 用户密钥对生成成功');
  } catch (error) {
    console.error('❌ 密钥对生成失败:', error);
    throw error;
  }
}

/**
 * Adds a message to the local database.
 * @param {object} message - The message object.
 * @returns {Promise<number>} - The ID of the added message.
 */
export const addMessage = async (message) => {
  const localDb = getDb();
  const userId = getCurrentUserId();
  if (!userId) throw new Error('User not logged in');

  try {
    // 无论是发送还是接收，都使用自己的密钥来处理本地存储的加密
    const userKeys = await localDb.userKeys.get(userId);
    const symmetricKey = userKeys?.privateKey; // 使用自己的私钥作为对称加密的密钥

    if (message.encrypted && !symmetricKey) {
      console.error('无法加密/存储消息，因为用户密钥不存在。');
      throw new Error('User key not available for encryption.');
    }

    const messageData = {
      from: message.from,
      to: message.to,
      // 如果消息标记为加密，则使用对称密钥加密内容
      content: message.encrypted ? encryptContent(message.content, symmetricKey) : message.content,
      timestamp: message.timestamp || getChinaTimeISO(),
      method: message.method || 'P2P',
      encrypted: message.encrypted || false,
      messageType: message.messageType || 'text',
      destroyAfter: message.destroyAfter || null,
      isRead: false
    };

    const messageId = await localDb.messages.add(messageData);
    const conversationUserId = message.from === userId ? message.to : message.from;
    await updateConversation(conversationUserId, message.content, messageData.timestamp);
    console.log('✅ 消息已保存到本地数据库，ID:', messageId);
    return messageId;
  } catch (error) {
    console.error('❌ 保存消息失败:', error);
    throw error;
  }
};

/**
 * Retrieves messages with a specific friend using a compound index.
 * @param {number} friendId - The friend's ID.
 * @param {object} options - Query options like limit, offset.
 * @returns {Promise<object>} - A structured object containing messages and total count.
 */
export const getMessagesWithFriend = async (friendId, options = {}) => {
  const localDb = getDb();
  const userId = getCurrentUserId();
  if (!userId) {
    console.warn('用户未登录，无法获取消息。');
    return { messages: [], total: 0 }; // Return a structured object
  }
  
  const { limit = 50, offset = 0 } = options;

  try {
    // 使用复合查询条件获取消息
    const allMessages = await localDb.messages.where('[from+to]')
      .equals([userId, friendId])
      .or('[from+to]')
      .equals([friendId, userId])
      .reverse()
      .sortBy('timestamp');

    const total = allMessages.length;
    // 手动应用分页
    const paginatedMessages = allMessages.slice(offset, offset + limit);

    // 总是使用当前用户的私钥来解密历史记录
    const userKeys = await localDb.userKeys.get(userId);
    const decryptionKey = userKeys?.privateKey;

    if (!decryptionKey) {
      console.warn('无法解密历史消息，因为用户密钥不存在。');
    }

    const decryptedMessages = paginatedMessages.map(msg => ({
      ...msg,
      // 只有标记为加密的消息才尝试解密
      content: (msg.encrypted && decryptionKey) ? decryptContent(msg.content, decryptionKey) : msg.content
    }));
    
    return { messages: decryptedMessages, total: total };

  } catch (error) {
    console.error('❌ 获取消息失败:', error);
    return { messages: [], total: 0 }; // Return a structured object on failure
  }
};

/**
 * Updates conversation details.
 * @param {number} userId - The other user's ID in the conversation.
 * @param {string} lastMessage - The last message content.
 * @param {string} timestamp - The timestamp of the last message.
 */
async function updateConversation(userId, lastMessage, timestamp) {
  const localDb = getDb();
  try {
    const existing = await localDb.conversations.where('userId').equals(userId).first();
    if (existing) {
      await localDb.conversations.update(existing.id, {
        lastMessage: lastMessage,
        lastMessageTime: timestamp,
        unreadCount: (existing.unreadCount || 0) + 1
      });
    } else {
      await localDb.conversations.add({
        userId: userId,
        lastMessage: lastMessage,
        lastMessageTime: timestamp,
        unreadCount: 1
      });
    }
  } catch (error) {
    console.error('❌ 更新会话失败:', error);
  }
}

/**
 * 检查数据库状态
 * @returns {Promise<object>} - 数据库状态信息
 */
export const checkDatabaseStatus = async () => {
  try {
    const localDb = getDb();
    const userId = getCurrentUserId();
    if (!userId) {
      return { success: false, error: '用户未登录' };
    }
    
    const status = await localDb.status();
    return {
      success: true,
      userId: userId,
      initialized: status.initialized,
      tables: status.tables
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

/**
 * 清空所有消息
 * @returns {Promise<boolean>} - 操作是否成功
 */
export const clearAllMessages = async () => {
  try {
    const localDb = getDb();
    await localDb.messages.clear();
    await localDb.conversations.clear();
    console.log('✅ 所有消息和会话记录已清除');
    return true;
  } catch (error) {
    console.error('❌ 清除消息失败:', error);
    return false;
  }
};

/**
 * 存储用户密钥
 * @param {object} keyData - 密钥数据
 * @returns {Promise<boolean>} - 操作是否成功
 */
export const storeUserKeys = async (keyData) => {
  try {
    const localDb = getDb();
    const userId = getCurrentUserId();
    if (!userId) {
      throw new Error('用户未登录，无法存储密钥');
    }
    
    const existingKeys = await localDb.userKeys.get(userId);
    if (existingKeys) {
      await localDb.userKeys.update(existingKeys.id, {
        ...keyData,
        updatedAt: getChinaTimeISO()
      });
    } else {
      await localDb.userKeys.add({
        id: userId,
        ...keyData,
        createdAt: getChinaTimeISO()
      });
    }
    
    console.log('✅ 用户密钥已保存');
    return true;
  } catch (error) {
    console.error('❌ 存储用户密钥失败:', error);
    return false;
  }
};

/**
 * 获取用户密钥
 * @param {number} userId - 用户ID，默认为当前用户
 * @returns {Promise<object|null>} - 用户密钥
 */
export const getUserKeys = async (userId = null) => {
  try {
    const localDb = getDb();
    const targetUserId = userId || getCurrentUserId();
    if (!targetUserId) {
      throw new Error('未指定用户ID');
    }
    
    const keys = await localDb.userKeys.get(targetUserId);
    return keys;
  } catch (error) {
    console.error('❌ 获取用户密钥失败:', error);
    return null;
  }
};

/**
 * 清除用户密钥
 * @param {number} userId - 用户ID，默认为当前用户
 * @returns {Promise<boolean>} - 操作是否成功
 */
export const clearUserKeys = async (userId = null) => {
  try {
    const localDb = getDb();
    const targetUserId = userId || getCurrentUserId();
    if (!targetUserId) {
      throw new Error('未指定用户ID');
    }
    
    const keys = await localDb.userKeys.get(targetUserId);
    if (keys) {
      await localDb.userKeys.delete(keys.id);
      console.log('✅ 用户密钥已清除');
    }
    return true;
  } catch (error) {
    console.error('❌ 清除用户密钥失败:', error);
    return false;
  }
};

/**
 * 验证用户密钥
 * @returns {Promise<object>} - 验证结果
 */
export const validateUserKeys = async () => {
  try {
    const localDb = getDb();
    const userId = getCurrentUserId();
    if (!userId) {
      return { valid: false, error: '用户未登录' };
    }
    
    const keys = await localDb.userKeys.get(userId);
    if (!keys) {
      return { valid: false, error: '未找到用户密钥' };
    }
    
    // 验证密钥是否完整
    const requiredFields = ['publicKey', 'privateKey'];
    const missingFields = requiredFields.filter(field => !keys[field]);
    
    if (missingFields.length > 0) {
      return {
        valid: false,
        error: `密钥不完整，缺少字段: ${missingFields.join(', ')}`,
        keys: {
          id: keys.id,
          hasPublicKey: !!keys.publicKey,
          hasPrivateKey: !!keys.privateKey,
          createdAt: keys.createdAt
        }
      };
    }
    
    return {
      valid: true,
      keys: {
        id: keys.id,
        hasPublicKey: true,
        hasPrivateKey: true,
        createdAt: keys.createdAt,
        updatedAt: keys.updatedAt
      }
    };
  } catch (error) {
    console.error('❌ 验证用户密钥失败:', error);
    return { valid: false, error: error.message };
  }
};

/**
 * 添加联系人
 * @param {object} contact - 联系人信息
 * @returns {Promise<number|string>} - 联系人ID
 */
export const addContact = async (contact) => {
  try {
    const localDb = getDb();
    const contactId = await localDb.contacts.add(contact);
    console.log('✅ 联系人已添加，ID:', contactId);
    return contactId;
  } catch (error) {
    console.error('❌ 添加联系人失败:', error);
    throw error;
  }
};

/**
 * 获取所有联系人
 * @returns {Promise<Array>} - 联系人列表
 */
export const getContacts = async () => {
  try {
    const localDb = getDb();
    return await localDb.contacts.toArray();
  } catch (error) {
    console.error('❌ 获取联系人列表失败:', error);
    return [];
  }
};

/**
 * 标记消息为已读
 * @param {number|string} messageId - 消息ID
 * @returns {Promise<boolean>} - 操作是否成功
 */
export const markMessageAsRead = async (messageId) => {
  try {
    const localDb = getDb();
    await localDb.messages.update(messageId, { isRead: true });
    return true;
  } catch (error) {
    console.error('❌ 标记消息为已读失败:', error);
    return false;
  }
};

/**
 * 删除消息
 * @param {number|string} messageId - 消息ID
 * @returns {Promise<boolean>} - 操作是否成功
 */
export const deleteMessage = async (messageId) => {
  try {
    const localDb = getDb();
    await localDb.messages.delete(messageId);
    console.log('✅ 消息已删除，ID:', messageId);
    return true;
  } catch (error) {
    console.error('❌ 删除消息失败:', error);
    return false;
  }
};

// 在浏览器控制台中暴露调试函数
if (typeof window !== 'undefined') {
  window.checkChat8LocalStorage = checkDatabaseStatus;
  window.clearChat8Messages = clearAllMessages;
  window.getChat8UserKeys = getUserKeys;
  window.clearChat8UserKeys = clearUserKeys;
  window.validateChat8UserKeys = validateUserKeys;
  window.getChat8Contacts = getContacts;
  
  console.log('💡 Chat8 本地数据库调试命令:');
  console.log('  - checkChat8LocalStorage() 查看本地存储状态');
  console.log('  - clearChat8Messages() 清空所有消息');
  console.log('  - getChat8UserKeys() 获取当前用户密钥');
  console.log('  - clearChat8UserKeys() 清除当前用户密钥');
  console.log('  - validateChat8UserKeys() 验证密钥完整性');
  console.log('  - getChat8Contacts() 获取所有联系人');
}

export default {
  name: 'Chat8LocalDatabase',
  type: 'IndexedDB (Browser Local Storage)',
  version: '2.0.0',
  encrypted: true,
  db: db
};