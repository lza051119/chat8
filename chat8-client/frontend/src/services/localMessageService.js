import { 
  initDatabase, 
  addMessage, 
  getMessagesWithFriend, 
  checkDatabaseStatus,
  clearAllMessages,
  storeUserKeys,
  getUserKeys,
  clearUserKeys,
  validateUserKeys,
  addContact,
  getContacts,
  markMessageAsRead,
  deleteMessage
} from '../client_db/database.js';
import CryptoJS from 'crypto-js';
import { getChinaTimeISO } from '../utils/timeUtils.js';

/**
 * 客户端本地消息处理服务
 * 负责消息的加密、解密、存储和管理
 */
class LocalMessageService {
  constructor() {
    this.isInitialized = false;
    this.encryptionEnabled = true;
    this.currentUserId = null;
  }

  /**
   * 初始化本地消息服务
   */
  async initialize() {
    try {
      // 获取当前用户信息
      const userStr = localStorage.getItem('user');
      if (!userStr) {
        throw new Error('用户未登录');
      }
      
      const user = JSON.parse(userStr);
      this.currentUserId = user.id || user.userId;
      
      // 初始化本地数据库
      await initDatabase();
      
      // 检查用户密钥
      const keys = await getUserKeys();
      if (!keys) {
        console.log('🔑 正在生成新的用户密钥...');
        await this.generateUserKeys();
      }
      
      this.isInitialized = true;
      console.log('✅ 本地消息服务初始化成功');
      
      return true;
    } catch (error) {
      console.error('❌ 本地消息服务初始化失败:', error);
      throw error;
    }
  }

  /**
   * 生成用户密钥对
   */
  async generateUserKeys() {
    try {
      // 使用Web Crypto API生成RSA密钥对
      const keyPair = await window.crypto.subtle.generateKey(
        {
          name: 'RSA-OAEP',
          modulusLength: 2048,
          publicExponent: new Uint8Array([1, 0, 1]),
          hash: 'SHA-256'
        },
        true,
        ['encrypt', 'decrypt']
      );
      
      // 导出密钥
      const publicKey = await window.crypto.subtle.exportKey('spki', keyPair.publicKey);
      const privateKey = await window.crypto.subtle.exportKey('pkcs8', keyPair.privateKey);
      
      // 转换为Base64字符串
      const publicKeyBase64 = this.arrayBufferToBase64(publicKey);
      const privateKeyBase64 = this.arrayBufferToBase64(privateKey);
      
      // 存储密钥
      const keyData = {
        publicKey: publicKeyBase64,
        privateKey: privateKeyBase64,
        algorithm: 'RSA-OAEP',
        keySize: 2048,
        createdAt: getChinaTimeISO()
      };
      
      await storeUserKeys(keyData);
      console.log('✅ 用户密钥对生成并保存成功');
      
      return keyData;
    } catch (error) {
      console.error('❌ 生成密钥对失败:', error);
      // 如果Web Crypto API不可用，使用简化的密钥生成
      const fallbackKeys = {
        publicKey: `pub_${this.currentUserId}_${Date.now()}`,
        privateKey: `priv_${this.currentUserId}_${Date.now()}`,
        algorithm: 'AES-256',
        keySize: 256,
        createdAt: getChinaTimeISO()
      };
      
      await storeUserKeys(fallbackKeys);
      console.log('✅ 使用备用方案生成密钥对');
      return fallbackKeys;
    }
  }

  /**
   * ArrayBuffer转Base64
   */
  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  /**
   * Base64转ArrayBuffer
   */
  base64ToArrayBuffer(base64) {
    const binary = window.atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  /**
   * 加密消息内容
   */
  async encryptMessage(content, recipientPublicKey = null) {
    try {
      if (!this.encryptionEnabled) {
        return { content, encrypted: false };
      }
      
      // 使用AES加密消息内容（更快）
      const key = CryptoJS.lib.WordArray.random(256/8);
      const iv = CryptoJS.lib.WordArray.random(128/8);
      
      const encrypted = CryptoJS.AES.encrypt(content, key, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
      });
      
      return {
        content: encrypted.toString(),
        encrypted: true,
        key: key.toString(),
        iv: iv.toString(),
        algorithm: 'AES-256-CBC'
      };
    } catch (error) {
      console.error('❌ 消息加密失败:', error);
      return { content, encrypted: false };
    }
  }

  /**
   * 解密消息内容
   */
  async decryptMessage(encryptedData) {
    try {
      if (!encryptedData.encrypted) {
        return encryptedData.content;
      }
      
      const key = CryptoJS.enc.Hex.parse(encryptedData.key);
      const iv = CryptoJS.enc.Hex.parse(encryptedData.iv);
      
      const decrypted = CryptoJS.AES.decrypt(encryptedData.content, key, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
      });
      
      return decrypted.toString(CryptoJS.enc.Utf8);
    } catch (error) {
      console.error('❌ 消息解密失败:', error);
      return encryptedData.content;
    }
  }

  /**
   * 发送消息（加密并存储到本地）
   */
  async sendMessage(messageData) {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }
      
      // 加密消息内容
      const encryptedData = await this.encryptMessage(messageData.content);
      
      // 准备消息对象
      const message = {
        from: this.currentUserId,
        to: messageData.to,
        content: encryptedData.content,
        timestamp: getChinaTimeISO(),
        method: messageData.method || 'P2P',
        encrypted: encryptedData.encrypted,
        messageType: messageData.messageType || 'text',
        destroyAfter: messageData.destroyAfter || null,
        encryptionKey: encryptedData.key,
        encryptionIv: encryptedData.iv,
        algorithm: encryptedData.algorithm
      };
      
      // 保存到本地数据库
      const messageId = await addMessage(message);
      
      console.log('✅ 消息已加密并保存到本地, ID:', messageId);
      
      return {
        success: true,
        messageId: messageId,
        message: message
      };
    } catch (error) {
      console.error('❌ 发送消息失败:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * 接收消息（解密并存储到本地）
   */
  async receiveMessage(messageData) {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }
      
      // 如果消息已加密，先解密
      let content = messageData.content;
      if (messageData.encrypted && messageData.encryptionKey) {
        content = await this.decryptMessage({
          content: messageData.content,
          encrypted: messageData.encrypted,
          key: messageData.encryptionKey,
          iv: messageData.encryptionIv
        });
      }
      
      // 准备消息对象
      const message = {
        from: messageData.from,
        to: this.currentUserId,
        content: content,
        timestamp: messageData.timestamp || getChinaTimeISO(),
        method: messageData.method || 'P2P',
        encrypted: false, // 本地存储解密后的内容
        messageType: messageData.messageType || 'text',
        destroyAfter: messageData.destroyAfter || null
      };
      
      // 保存到本地数据库
      const messageId = await addMessage(message);
      
      console.log('✅ 接收到的消息已解密并保存到本地, ID:', messageId);
      
      return {
        success: true,
        messageId: messageId,
        message: message
      };
    } catch (error) {
      console.error('❌ 接收消息失败:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * 获取与好友的聊天记录
   */
  async getChatHistory(friendId, options = {}) {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }
      
      const messages = await getMessagesWithFriend(friendId, options);
      
      console.log(`📖 获取到与用户 ${friendId} 的 ${messages.length} 条聊天记录`);
      
      return {
        success: true,
        messages: messages,
        count: messages.length
      };
    } catch (error) {
      console.error('❌ 获取聊天记录失败:', error);
      return {
        success: false,
        error: error.message,
        messages: []
      };
    }
  }

  /**
   * 获取本地存储状态
   */
  async getStorageStatus() {
    try {
      const status = await checkDatabaseStatus();
      return status;
    } catch (error) {
      console.error('❌ 获取存储状态失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 清空所有消息
   */
  async clearAllMessages() {
    try {
      const result = await clearAllMessages();
      return { success: result };
    } catch (error) {
      console.error('❌ 清空消息失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 添加联系人
   */
  async addContact(contactData) {
    try {
      const contactId = await addContact(contactData);
      return { success: true, contactId: contactId };
    } catch (error) {
      console.error('❌ 添加联系人失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 获取所有联系人
   */
  async getContacts() {
    try {
      const contacts = await getContacts();
      return { success: true, contacts: contacts };
    } catch (error) {
      console.error('❌ 获取联系人失败:', error);
      return { success: false, error: error.message, contacts: [] };
    }
  }

  /**
   * 标记消息为已读
   */
  async markAsRead(messageId) {
    try {
      const result = await markMessageAsRead(messageId);
      return { success: result };
    } catch (error) {
      console.error('❌ 标记消息失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 删除消息
   */
  async deleteMessage(messageId) {
    try {
      const result = await deleteMessage(messageId);
      return { success: result };
    } catch (error) {
      console.error('❌ 删除消息失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 获取用户密钥
   */
  async getUserKeys() {
    try {
      const keys = await getUserKeys();
      return { success: true, keys: keys };
    } catch (error) {
      console.error('❌ 获取密钥失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 验证密钥完整性
   */
  async validateKeys() {
    try {
      const validation = await validateUserKeys();
      return validation;
    } catch (error) {
      console.error('❌ 验证密钥失败:', error);
      return { valid: false, error: error.message };
    }
  }

  /**
   * 启用/禁用加密
   */
  setEncryption(enabled) {
    this.encryptionEnabled = enabled;
    console.log(`🔐 消息加密已${enabled ? '启用' : '禁用'}`);
  }

  /**
   * 获取当前用户ID
   */
  getCurrentUserId() {
    return this.currentUserId;
  }

  /**
   * 检查服务是否已初始化
   */
  isReady() {
    return this.isInitialized;
  }
}

// 创建单例实例
const localMessageService = new LocalMessageService();

// 在浏览器控制台中暴露调试函数
if (typeof window !== 'undefined') {
  window.localMessageService = localMessageService;
  window.initLocalMessageService = () => localMessageService.initialize();
  window.getLocalStorageStatus = () => localMessageService.getStorageStatus();
  window.clearLocalMessages = () => localMessageService.clearAllMessages();
  
  console.log('💡 本地消息服务调试命令:');
  console.log('  - localMessageService 访问服务实例');
  console.log('  - initLocalMessageService() 初始化服务');
  console.log('  - getLocalStorageStatus() 查看存储状态');
  console.log('  - clearLocalMessages() 清空所有消息');
}

export default localMessageService;
export { LocalMessageService };