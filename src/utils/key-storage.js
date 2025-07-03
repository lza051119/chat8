/**
 * 本地密钥存储工具
 * 用于管理用户的加密密钥
 */

// 密钥存储的键名前缀
const KEY_PREFIX = 'chat8_key_';

/**
 * 获取本地存储的密钥
 * @param {string} keyId - 密钥ID
 * @returns {string|null} 密钥内容或null
 */
export function getLocalKey(keyId) {
  try {
    const key = localStorage.getItem(KEY_PREFIX + keyId);
    return key;
  } catch (error) {
    console.error('获取本地密钥失败:', error);
    return null;
  }
}

/**
 * 保存密钥到本地存储
 * @param {string} keyId - 密钥ID
 * @param {string} keyData - 密钥内容
 * @returns {boolean} 是否保存成功
 */
export function saveLocalKey(keyId, keyData) {
  try {
    localStorage.setItem(KEY_PREFIX + keyId, keyData);
    return true;
  } catch (error) {
    console.error('保存本地密钥失败:', error);
    return false;
  }
}

/**
 * 删除本地存储的密钥
 * @param {string} keyId - 密钥ID
 * @returns {boolean} 是否删除成功
 */
export function deleteLocalKey(keyId) {
  try {
    localStorage.removeItem(KEY_PREFIX + keyId);
    return true;
  } catch (error) {
    console.error('删除本地密钥失败:', error);
    return false;
  }
}

/**
 * 获取所有本地密钥的ID列表
 * @returns {string[]} 密钥ID列表
 */
export function getAllLocalKeyIds() {
  try {
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(KEY_PREFIX)) {
        keys.push(key.substring(KEY_PREFIX.length));
      }
    }
    return keys;
  } catch (error) {
    console.error('获取本地密钥列表失败:', error);
    return [];
  }
}

/**
 * 清空所有本地密钥
 * @returns {boolean} 是否清空成功
 */
export function clearAllLocalKeys() {
  try {
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(KEY_PREFIX)) {
        keysToRemove.push(key);
      }
    }
    
    keysToRemove.forEach(key => {
      localStorage.removeItem(key);
    });
    
    return true;
  } catch (error) {
    console.error('清空本地密钥失败:', error);
    return false;
  }
}