/**
 * 本地文件系统数据存储模块
 * 用于替代IndexedDB，将数据存储在本地文件系统中
 */

import { getChinaTimeISO } from '../../utils/timeUtils.js';

// 检查是否在 Electron 环境中
const isElectronEnvironment = () => {
  return window.electronAPI !== undefined;
};

// 如果不在 Electron 环境中，提供模拟实现或抛出错误
if (!isElectronEnvironment()) {
  console.warn('非 Electron 环境，本地文件系统存储不可用。将使用 IndexedDB 存储。');
}

// 获取通过 preload.js 暴露的 Electron API（如果可用）
const fs = isElectronEnvironment() ? window.electronAPI.fs : null;
const path = isElectronEnvironment() ? window.electronAPI.path : null;
const crypto = {
  randomBytes: (size) => {
    const array = new Uint8Array(size);
    window.crypto.getRandomValues(array);
    return Array.from(array)
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }
};

// 获取应用数据目录
const USER_DATA_PATH = isElectronEnvironment() 
  ? path.join(window.electronAPI.getPath('userData'), 'chat8-data')
  : null;

// 确保数据目录存在（仅在 Electron 环境中）
if (isElectronEnvironment() && fs && USER_DATA_PATH) {
  if (!fs.exists(USER_DATA_PATH)) {
    fs.mkdir(USER_DATA_PATH, { recursive: true });
  }
}

// 数据表定义
const TABLES = {
  messages: 'messages',
  contacts: 'contacts',
  userKeys: 'userKeys',
  settings: 'settings',
  conversations: 'conversations'
};

/**
 * 获取用户数据目录
 * @param {number|string} userId - 用户ID
 * @returns {string} - 用户数据目录路径
 */
function getUserDataPath(userId) {
  if (!isElectronEnvironment()) {
    throw new Error('本地文件系统存储仅在 Electron 环境中可用');
  }
  
  if (!userId) throw new Error('用户ID不能为空');
  const userDir = path.join(USER_DATA_PATH, `user_${userId}`);
  if (!fs.exists(userDir)) {
    fs.mkdir(userDir, { recursive: true });
  }
  return userDir;
}

/**
 * 获取表文件路径
 * @param {number|string} userId - 用户ID
 * @param {string} table - 表名
 * @returns {string} - 表文件路径
 */
function getTablePath(userId, table) {
  if (!isElectronEnvironment()) {
    throw new Error('本地文件系统存储仅在 Electron 环境中可用');
  }
  
  return path.join(getUserDataPath(userId), `${table}.json`);
}

/**
 * 读取表数据
 * @param {number|string} userId - 用户ID
 * @param {string} table - 表名
 * @returns {Array} - 表数据数组
 */
function readTable(userId, table) {
  if (!isElectronEnvironment()) {
    throw new Error('本地文件系统存储仅在 Electron 环境中可用');
  }
  
  const tablePath = getTablePath(userId, table);
  if (!fs.exists(tablePath)) {
    return [];
  }
  
  try {
    const data = fs.readFile(tablePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error(`读取表 ${table} 失败:`, error);
    return [];
  }
}

/**
 * 写入表数据
 * @param {number|string} userId - 用户ID
 * @param {string} table - 表名
 * @param {Array} data - 表数据数组
 * @returns {boolean} - 是否成功
 */
function writeTable(userId, table, data) {
  if (!isElectronEnvironment()) {
    throw new Error('本地文件系统存储仅在 Electron 环境中可用');
  }
  
  const tablePath = getTablePath(userId, table);
  try {
    fs.writeFile(tablePath, JSON.stringify(data, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error(`写入表 ${table} 失败:`, error);
    return false;
  }
}

/**
 * 生成唯一ID
 * @returns {string} - 唯一ID
 */
function generateId() {
  return crypto.randomBytes(16);
}

/**
 * 本地存储类
 */
class LocalStorage {
  constructor(userId) {
    if (!userId) throw new Error('用户ID不能为空');
    this.userId = userId;
    this.initialized = false;
    
    // 检查环境
    this.isElectron = isElectronEnvironment();
    if (!this.isElectron) {
      console.warn('非 Electron 环境，本地文件系统存储不可用');
    }
  }

  /**
   * 初始化存储
   * @returns {Promise<boolean>}
   */
  async initialize() {
    if (!this.isElectron) {
      console.warn('非 Electron 环境，本地文件系统存储初始化被跳过');
      return false;
    }
    
    try {
      // 确保用户目录存在
      getUserDataPath(this.userId);
      
      // 初始化所有表
      for (const table of Object.values(TABLES)) {
        const tablePath = getTablePath(this.userId, table);
        if (!fs.exists(tablePath)) {
          writeTable(this.userId, table, []);
        }
      }
      
      this.initialized = true;
      return true;
    } catch (error) {
      console.error('初始化本地存储失败:', error);
      return false;
    }
  }

  /**
   * 添加记录
   * @param {string} table - 表名
   * @param {Object} record - 记录对象
   * @returns {Promise<string>} - 记录ID
   */
  async add(table, record) {
    if (!this.isElectron) {
      throw new Error('本地文件系统存储仅在 Electron 环境中可用');
    }
    
    if (!this.initialized) throw new Error('存储尚未初始化');
    
    const records = readTable(this.userId, table);
    const newRecord = {
      ...record,
      id: record.id || generateId()
    };
    
    records.push(newRecord);
    writeTable(this.userId, table, records);
    return newRecord.id;
  }

  /**
   * 获取记录
   * @param {string} table - 表名
   * @param {string|number} id - 记录ID
   * @returns {Promise<Object|null>} - 记录对象
   */
  async get(table, id) {
    if (!this.isElectron) {
      throw new Error('本地文件系统存储仅在 Electron 环境中可用');
    }
    
    if (!this.initialized) throw new Error('存储尚未初始化');
    
    const records = readTable(this.userId, table);
    return records.find(record => record.id == id) || null;
  }

  /**
   * 更新记录
   * @param {string} table - 表名
   * @param {string|number} id - 记录ID
   * @param {Object} updates - 更新内容
   * @returns {Promise<boolean>} - 是否成功
   */
  async update(table, id, updates) {
    if (!this.isElectron) {
      throw new Error('本地文件系统存储仅在 Electron 环境中可用');
    }
    
    if (!this.initialized) throw new Error('存储尚未初始化');
    
    const records = readTable(this.userId, table);
    const index = records.findIndex(record => record.id == id);
    
    if (index === -1) return false;
    
    records[index] = {
      ...records[index],
      ...updates
    };
    
    return writeTable(this.userId, table, records);
  }

  /**
   * 删除记录
   * @param {string} table - 表名
   * @param {string|number} id - 记录ID
   * @returns {Promise<boolean>} - 是否成功
   */
  async delete(table, id) {
    if (!this.isElectron) {
      throw new Error('本地文件系统存储仅在 Electron 环境中可用');
    }
    
    if (!this.initialized) throw new Error('存储尚未初始化');
    
    const records = readTable(this.userId, table);
    const filteredRecords = records.filter(record => record.id != id);
    
    if (filteredRecords.length === records.length) return false;
    
    return writeTable(this.userId, table, filteredRecords);
  }

  /**
   * 获取所有记录
   * @param {string} table - 表名
   * @returns {Promise<Array>} - 记录数组
   */
  async getAll(table) {
    if (!this.isElectron) {
      throw new Error('本地文件系统存储仅在 Electron 环境中可用');
    }
    
    if (!this.initialized) throw new Error('存储尚未初始化');
    return readTable(this.userId, table);
  }

  /**
   * 根据条件查询记录
   * @param {string} table - 表名
   * @param {Function} predicate - 过滤函数
   * @returns {Promise<Array>} - 记录数组
   */
  async query(table, predicate) {
    if (!this.isElectron) {
      throw new Error('本地文件系统存储仅在 Electron 环境中可用');
    }
    
    if (!this.initialized) throw new Error('存储尚未初始化');
    
    const records = readTable(this.userId, table);
    return records.filter(predicate);
  }

  /**
   * 清空表
   * @param {string} table - 表名
   * @returns {Promise<boolean>} - 是否成功
   */
  async clear(table) {
    if (!this.isElectron) {
      throw new Error('本地文件系统存储仅在 Electron 环境中可用');
    }
    
    if (!this.initialized) throw new Error('存储尚未初始化');
    return writeTable(this.userId, table, []);
  }

  /**
   * 检查存储状态
   * @returns {Promise<Object>} - 状态信息
   */
  async checkStatus() {
    if (!this.isElectron) {
      return {
        initialized: false,
        userId: this.userId,
        isElectron: false,
        message: '本地文件系统存储仅在 Electron 环境中可用'
      };
    }
    
    return {
      initialized: this.initialized,
      userId: this.userId,
      isElectron: true,
      tables: Object.values(TABLES).map(table => ({
        name: table,
        count: this.initialized ? readTable(this.userId, table).length : 0
      }))
    };
  }
}

export { LocalStorage, TABLES, isElectronEnvironment }; 