/**
 * 数据库适配器
 * 提供统一的数据库接口，根据环境自动选择存储方式：
 * - Electron 环境：使用本地文件系统存储
 * - Web 环境：使用 IndexedDB (Dexie)
 */

import { LocalStorage, TABLES, isElectronEnvironment } from './local-storage';
import Dexie from 'dexie';

class DatabaseAdapter {
  constructor(userId) {
    this.userId = userId;
    this.isElectron = isElectronEnvironment();
    
    if (this.isElectron) {
      // Electron 环境：使用本地文件系统存储
      this.storage = new LocalStorage(userId);
      console.log('使用本地文件系统存储模式');
    } else {
      // Web 环境：使用 IndexedDB
      this.db = new Dexie(`Chat8LocalDB_${userId}`);
      this.db.version(1).stores({
        messages: '++id, from, to, timestamp, [from+to]',
        contacts: '++id, username, publicKey, lastSeen, status',
        userKeys: 'id, publicKey, privateKey, keyPair, createdAt',
        settings: 'key',
        conversations: '++id, userId, lastMessageTime'
      });
      console.log('使用 IndexedDB 存储模式');
    }
    
    // 创建表接口
    this.messages = this._createTableInterface(TABLES.messages);
    this.contacts = this._createTableInterface(TABLES.contacts);
    this.userKeys = this._createTableInterface(TABLES.userKeys);
    this.settings = this._createTableInterface(TABLES.settings);
    this.conversations = this._createTableInterface(TABLES.conversations);
  }

  /**
   * 初始化数据库
   * @returns {Promise<boolean>}
   */
  async open() {
    if (this.isElectron) {
      // 本地文件系统存储初始化
      return this.storage.initialize();
    } else {
      // IndexedDB 初始化
      try {
        await this.db.open();
        return true;
      } catch (error) {
        console.error('IndexedDB 初始化失败:', error);
        return false;
      }
    }
  }

  /**
   * 关闭数据库连接
   * @returns {Promise<void>}
   */
  async close() {
    if (!this.isElectron && this.db) {
      return this.db.close();
    }
    return Promise.resolve();
  }

  /**
   * 创建表接口
   * @param {string} tableName - 表名
   * @returns {Object} - 表接口
   */
  _createTableInterface(tableName) {
    if (this.isElectron) {
      // 本地文件系统存储接口
      return {
        // 添加记录
        add: async (record) => {
          return this.storage.add(tableName, record);
        },
        
        // 获取记录
        get: async (id) => {
          return this.storage.get(tableName, id);
        },
        
        // 更新记录
        update: async (id, changes) => {
          return this.storage.update(tableName, id, changes);
        },
        
        // 删除记录
        delete: async (id) => {
          return this.storage.delete(tableName, id);
        },
        
        // 获取所有记录
        toArray: async () => {
          return this.storage.getAll(tableName);
        },
        
        // 清空表
        clear: async () => {
          return this.storage.clear(tableName);
        },
        
        // 按条件查询
        where: (field) => {
          return {
            equals: (value) => {
              return {
                // 获取第一条匹配记录
                first: async () => {
                  const results = await this.storage.query(tableName, record => record[field] == value);
                  return results[0] || null;
                },
                
                // 获取所有匹配记录
                toArray: async () => {
                  return this.storage.query(tableName, record => record[field] == value);
                },
                
                // 或条件
                or: (otherField) => {
                  return {
                    equals: (otherValue) => {
                      return {
                        // 按时间戳倒序排序
                        reverse: () => {
                          return {
                            // 排序后返回结果
                            sortBy: async (sortField) => {
                              const results = await this.storage.query(
                                tableName, 
                                record => record[field] == value || record[otherField] == otherValue
                              );
                              
                              return results.sort((a, b) => {
                                if (a[sortField] < b[sortField]) return -1;
                                if (a[sortField] > b[sortField]) return 1;
                                return 0;
                              });
                            }
                          };
                        }
                      };
                    }
                  };
                }
              };
            }
          };
        },
        
        // 按ID查询
        bulkGet: async (ids) => {
          const results = [];
          for (const id of ids) {
            const record = await this.storage.get(tableName, id);
            if (record) results.push(record);
          }
          return results;
        },
        
        // 批量添加
        bulkAdd: async (records) => {
          const ids = [];
          for (const record of records) {
            const id = await this.storage.add(tableName, record);
            ids.push(id);
          }
          return ids;
        },
        
        // 批量删除
        bulkDelete: async (ids) => {
          let count = 0;
          for (const id of ids) {
            const success = await this.storage.delete(tableName, id);
            if (success) count++;
          }
          return count;
        }
      };
    } else {
      // IndexedDB 接口（直接返回 Dexie 表对象）
      return this.db[tableName];
    }
  }

  /**
   * 获取数据库状态
   * @returns {Promise<Object>} - 状态信息
   */
  async status() {
    if (this.isElectron) {
      return this.storage.checkStatus();
    } else {
      try {
        const messageCount = await this.db.messages.count();
        const contactCount = await this.db.contacts.count();
        const conversationCount = await this.db.conversations.count();
        const userKeys = await this.db.userKeys.get(this.userId);
        
        return {
          initialized: true,
          userId: this.userId,
          isElectron: false,
          storageType: 'IndexedDB',
          tables: [
            { name: 'messages', count: messageCount },
            { name: 'contacts', count: contactCount },
            { name: 'userKeys', count: userKeys ? 1 : 0 },
            { name: 'conversations', count: conversationCount }
          ]
        };
      } catch (error) {
        return {
          initialized: false,
          userId: this.userId,
          isElectron: false,
          error: error.message
        };
      }
    }
  }

  /**
   * 版本控制（兼容Dexie接口）
   * @returns {Object} - 版本控制接口
   */
  version() {
    return {
      stores: () => this
    };
  }
}

export default DatabaseAdapter; 