import Dexie from 'dexie';
import CryptoJS from 'crypto-js';
import { getChinaTimeISO } from '../utils/timeUtils.js';

// 客户端本地数据库类
class Chat8LocalDB extends Dexie {
  constructor() {
    super('Chat8LocalDB');
    
    // 定义数据库结构
    this.version(1).stores({
      messages: '++id, from, to, content, timestamp, method, encrypted, messageType, destroyAfter, isRead',
      contacts: '++id, userId, username, publicKey, lastSeen, status',
      userKeys: '++id, userId, publicKey, privateKey, keyPair, createdAt',
      settings: '++id, key, value',
      conversations: '++id, userId, lastMessage, lastMessageTime, unreadCount'
    });
  }
}

// 创建数据库实例
const db = new Chat8LocalDB();

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
 * 初始化本地数据库
 * @returns {Promise<boolean>}
 */
export const initDatabase = async () => {
  try {
    const userId = getCurrentUserId();
    if (!userId) {
      throw new Error('用户未登录，无法初始化数据库');
    }
    
    // 打开数据库
    await db.open();
    
    console.log('🎉 Chat8 本地数据库已成功初始化!');
    console.log('📍 数据库类型: IndexedDB (浏览器本地存储)');
    console.log('👤 当前用户ID:', userId);
    
    // 检查用户密钥是否存在
    const userKeys = await db.userKeys.where('userId').equals(userId).first();
    if (!userKeys) {
      console.log('🔑 正在生成用户密钥对...');
      await generateUserKeyPair(userId);
    }
    
    return true;
  } catch (error) {
    console.error('❌ 本地数据库初始化失败:', error.message);
    throw error;
  }
};

/**
 * 生成用户密钥对
 * @param {number} userId - 用户ID
 */
async function generateUserKeyPair(userId) {
  try {
    // 生成RSA密钥对（简化版，实际应用中应使用Web Crypto API）
    const keyPair = {
      publicKey: `pub_${userId}_${Date.now()}`,
      privateKey: `priv_${userId}_${Date.now()}`
    };
    
    await db.userKeys.add({
      userId: userId,
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
 * 添加消息到本地数据库
 * @param {object} message - 消息对象
 * @returns {Promise<number>} - 返回消息ID
 */
export const addMessage = async (message) => {
  try {
    const userId = getCurrentUserId();
    if (!userId) {
      throw new Error('用户未登录');
    }
    
    // 获取用户私钥进行加密
    const userKeys = await db.userKeys.where('userId').equals(userId).first();
    const encryptionKey = userKeys?.privateKey || 'default_key';
    
    const messageData = {
      from: message.from,
      to: message.to,
      content: message.encrypted ? encryptContent(message.content, encryptionKey) : message.content,
      timestamp: message.timestamp || getChinaTimeISO(),
      method: message.method || 'P2P',
      encrypted: message.encrypted || false,
      messageType: message.messageType || 'text',
      destroyAfter: message.destroyAfter || null,
      isRead: false
    };
    
    const messageId = await db.messages.add(messageData);
    
    // 更新会话信息
    const conversationUserId = message.from === userId ? message.to : message.from;
    await updateConversation(conversationUserId, message.content, messageData.timestamp);
    
    console.log('✅ 消息已保存到本地数据库, ID:', messageId);
    return messageId;
  } catch (error) {
    console.error('❌ 保存消息失败:', error);
    throw error;
  }
};

/**
 * 获取与好友的消息记录
 * @param {number} friendId - 好友ID
 * @param {object} options - 查询选项
 * @returns {Promise<Array>} - 消息列表
 */
export const getMessagesWithFriend = async (friendId, options = {}) => {
  try {
    const userId = getCurrentUserId();
    if (!userId) {
      throw new Error('用户未登录');
    }
    
    const { limit = 50, offset = 0, search = null } = options;
    
    // 查询与好友的消息
    let query = db.messages
      .where('from').equals(userId).and(msg => msg.to === friendId)
      .or('from').equals(friendId).and(msg => msg.to === userId);
    
    if (search) {
      query = query.filter(msg => msg.content.includes(search));
    }
    
    const messages = await query
      .orderBy('timestamp')
      .reverse()
      .offset(offset)
      .limit(limit)
      .toArray();
    
    // 解密消息内容
    const userKeys = await db.userKeys.where('userId').equals(userId).first();
    const decryptionKey = userKeys?.privateKey || 'default_key';
    
    const decryptedMessages = messages.map(msg => ({
      ...msg,
      content: msg.encrypted ? decryptContent(msg.content, decryptionKey) : msg.content
    }));
    
    return decryptedMessages;
  } catch (error) {
    console.error('❌ 获取消息失败:', error);
    return [];
  }
};

/**
 * 更新会话信息
 * @param {number} userId - 对方用户ID
 * @param {string} lastMessage - 最后一条消息
 * @param {string} timestamp - 时间戳
 */
async function updateConversation(userId, lastMessage, timestamp) {
  try {
    const existing = await db.conversations.where('userId').equals(userId).first();
    
    if (existing) {
      await db.conversations.update(existing.id, {
        lastMessage: lastMessage,
        lastMessageTime: timestamp,
        unreadCount: existing.unreadCount + 1
      });
    } else {
      await db.conversations.add({
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
    const userId = getCurrentUserId();
    if (!userId) {
      return { success: false, error: '用户未登录' };
    }
    
    const messageCount = await db.messages.count();
    const contactCount = await db.contacts.count();
    const conversationCount = await db.conversations.count();
    const userKeys = await db.userKeys.where('userId').equals(userId).first();
    
    return {
      success: true,
      database: {
        exists: true,
        type: 'IndexedDB',
        messageCount: messageCount,
        contactCount: contactCount,
        conversationCount: conversationCount
      },
      user: {
        id: userId,
        hasKeys: !!userKeys
      },
      storage: {
        type: 'Browser Local Storage',
        encrypted: true
      }
    };
  } catch (error) {
    console.error('❌ 检查数据库状态失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 清空所有消息
 * @returns {Promise<boolean>}
 */
export const clearAllMessages = async () => {
  try {
    await db.messages.clear();
    await db.conversations.clear();
    console.log('✅ 所有消息已清空');
    return true;
  } catch (error) {
    console.error('❌ 清空消息失败:', error);
    return false;
  }
};

/**
 * 存储用户密钥
 * @param {object} keyData - 密钥数据
 * @returns {Promise<boolean>}
 */
export const storeUserKeys = async (keyData) => {
  try {
    const userId = getCurrentUserId();
    if (!userId) {
      throw new Error('用户未登录');
    }
    
    const existing = await db.userKeys.where('userId').equals(userId).first();
    
    if (existing) {
      await db.userKeys.update(existing.id, {
        publicKey: keyData.publicKey,
        privateKey: keyData.privateKey,
        keyPair: JSON.stringify(keyData)
      });
    } else {
      await db.userKeys.add({
        userId: userId,
        publicKey: keyData.publicKey,
        privateKey: keyData.privateKey,
        keyPair: JSON.stringify(keyData),
        createdAt: getChinaTimeISO()
      });
    }
    
    console.log('✅ 用户密钥已保存');
    return true;
  } catch (error) {
    console.error('❌ 保存密钥失败:', error);
    return false;
  }
};

/**
 * 获取用户密钥
 * @param {number} userId - 用户ID（可选，默认当前用户）
 * @returns {Promise<object|null>} - 用户密钥
 */
export const getUserKeys = async (userId = null) => {
  try {
    const targetUserId = userId || getCurrentUserId();
    if (!targetUserId) {
      throw new Error('用户ID无效');
    }
    
    const userKeys = await db.userKeys.where('userId').equals(targetUserId).first();
    
    if (userKeys) {
      return {
        userId: userKeys.userId,
        publicKey: userKeys.publicKey,
        privateKey: userKeys.privateKey,
        keyPair: JSON.parse(userKeys.keyPair || '{}'),
        createdAt: userKeys.createdAt
      };
    }
    
    return null;
  } catch (error) {
    console.error('❌ 获取密钥失败:', error);
    return null;
  }
};

/**
 * 清除用户密钥
 * @param {number} userId - 用户ID（可选，默认当前用户）
 * @returns {Promise<boolean>}
 */
export const clearUserKeys = async (userId = null) => {
  try {
    const targetUserId = userId || getCurrentUserId();
    if (!targetUserId) {
      throw new Error('用户ID无效');
    }
    
    await db.userKeys.where('userId').equals(targetUserId).delete();
    console.log('✅ 用户密钥已清除');
    return true;
  } catch (error) {
    console.error('❌ 清除密钥失败:', error);
    return false;
  }
};

/**
 * 验证用户密钥完整性
 * @returns {Promise<object>}
 */
export const validateUserKeys = async () => {
  try {
    const userId = getCurrentUserId();
    if (!userId) {
      return { valid: false, error: '用户未登录' };
    }
    
    const userKeys = await getUserKeys(userId);
    
    if (!userKeys) {
      return { valid: false, error: '密钥不存在' };
    }
    
    const hasPublicKey = !!userKeys.publicKey;
    const hasPrivateKey = !!userKeys.privateKey;
    const hasKeyPair = !!userKeys.keyPair;
    
    return {
      valid: hasPublicKey && hasPrivateKey && hasKeyPair,
      details: {
        hasPublicKey,
        hasPrivateKey,
        hasKeyPair,
        createdAt: userKeys.createdAt
      }
    };
  } catch (error) {
    console.error('❌ 验证密钥失败:', error);
    return { valid: false, error: error.message };
  }
};

// 添加联系人
export const addContact = async (contact) => {
  try {
    const contactId = await db.contacts.add({
      userId: contact.userId,
      username: contact.username,
      publicKey: contact.publicKey,
      lastSeen: contact.lastSeen || getChinaTimeISO(),
      status: contact.status || 'offline'
    });
    
    console.log('✅ 联系人已添加, ID:', contactId);
    return contactId;
  } catch (error) {
    console.error('❌ 添加联系人失败:', error);
    throw error;
  }
};

// 获取所有联系人
export const getContacts = async () => {
  try {
    const contacts = await db.contacts.toArray();
    return contacts;
  } catch (error) {
    console.error('❌ 获取联系人失败:', error);
    return [];
  }
};

// 标记消息为已读
export const markMessageAsRead = async (messageId) => {
  try {
    await db.messages.update(messageId, { isRead: true });
    console.log('✅ 消息已标记为已读');
    return true;
  } catch (error) {
    console.error('❌ 标记消息失败:', error);
    return false;
  }
};

// 删除消息
export const deleteMessage = async (messageId) => {
  try {
    await db.messages.delete(messageId);
    console.log('✅ 消息已删除');
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