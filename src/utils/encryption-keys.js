/**
 * 加密密钥管理工具
 * 用于管理用户的端到端加密密钥
 */

import { saveLocalKey, getLocalKey, deleteLocalKey } from './key-storage';
import { initDatabase } from '../client_db/database';

/**
 * 保存用户的加密密钥信息
 * @param {number} userId - 用户ID
 * @param {object} encryptionData - 加密数据对象
 * @param {string} encryptionData.public_key - 公钥
 * @param {number} encryptionData.registration_id - 注册ID
 * @param {object} encryptionData.prekey_bundle - 预密钥包（可选）
 * @returns {Promise<boolean>} 是否保存成功
 */
export async function saveUserEncryptionKeys(userId, encryptionData) {
  try {
    const { public_key, registration_id, prekey_bundle } = encryptionData;
    
    // 保存公钥
    const publicKeySuccess = saveLocalKey(`user_${userId}_public_key`, public_key);
    
    // 保存注册ID
    const regIdSuccess = saveLocalKey(`user_${userId}_registration_id`, registration_id.toString());
    
    // 保存预密钥包（如果存在）
    let prekeyBundleSuccess = true;
    if (prekey_bundle) {
      prekeyBundleSuccess = saveLocalKey(`user_${userId}_prekey_bundle`, JSON.stringify(prekey_bundle));
    }
    
    // 保存密钥元数据
    const metadata = {
      userId,
      createdAt: new Date().toISOString(),
      hasPublicKey: !!public_key,
      hasRegistrationId: !!registration_id,
      hasPrekeyBundle: !!prekey_bundle
    };
    const metadataSuccess = saveLocalKey(`user_${userId}_key_metadata`, JSON.stringify(metadata));
    
    const allSuccess = publicKeySuccess && regIdSuccess && prekeyBundleSuccess && metadataSuccess;
    
    if (allSuccess) {
      console.log(`✅ 用户 ${userId} 的加密密钥已成功保存`);
      console.log('📋 保存的密钥信息:', {
        publicKey: !!public_key,
        registrationId: !!registration_id,
        prekeyBundle: !!prekey_bundle
      });
    } else {
      console.error(`❌ 用户 ${userId} 的密钥保存失败`);
    }
    
    return allSuccess;
  } catch (error) {
    console.error('保存用户加密密钥失败:', error);
    return false;
  }
}

/**
 * 获取用户的加密密钥信息
 * @param {number} userId - 用户ID
 * @returns {object|null} 密钥信息对象或null
 */
export function getUserEncryptionKeys(userId) {
  try {
    const publicKey = getLocalKey(`user_${userId}_public_key`);
    const registrationId = getLocalKey(`user_${userId}_registration_id`);
    const prekeyBundleStr = getLocalKey(`user_${userId}_prekey_bundle`);
    const metadataStr = getLocalKey(`user_${userId}_key_metadata`);
    
    if (!publicKey || !registrationId) {
      console.warn(`⚠️ 用户 ${userId} 的密钥信息不完整`);
      return null;
    }
    
    let prekeyBundle = null;
    let metadata = null;
    
    try {
      if (prekeyBundleStr) {
        prekeyBundle = JSON.parse(prekeyBundleStr);
      }
      if (metadataStr) {
        metadata = JSON.parse(metadataStr);
      }
    } catch (parseError) {
      console.warn('解析密钥数据失败:', parseError);
    }
    
    return {
      userId: parseInt(userId),
      publicKey,
      registrationId: parseInt(registrationId),
      prekeyBundle,
      metadata
    };
  } catch (error) {
    console.error('获取用户加密密钥失败:', error);
    return null;
  }
}

/**
 * 删除用户的所有加密密钥
 * @param {number} userId - 用户ID
 * @returns {boolean} 是否删除成功
 */
export function deleteUserEncryptionKeys(userId) {
  try {
    const publicKeySuccess = deleteLocalKey(`user_${userId}_public_key`);
    const regIdSuccess = deleteLocalKey(`user_${userId}_registration_id`);
    const prekeyBundleSuccess = deleteLocalKey(`user_${userId}_prekey_bundle`);
    const metadataSuccess = deleteLocalKey(`user_${userId}_key_metadata`);
    
    const allSuccess = publicKeySuccess && regIdSuccess && prekeyBundleSuccess && metadataSuccess;
    
    if (allSuccess) {
      console.log(`✅ 用户 ${userId} 的所有加密密钥已删除`);
    } else {
      console.warn(`⚠️ 用户 ${userId} 的部分密钥删除失败`);
    }
    
    return allSuccess;
  } catch (error) {
    console.error('删除用户加密密钥失败:', error);
    return false;
  }
}

/**
 * 检查用户是否有完整的加密密钥
 * @param {number} userId - 用户ID
 * @returns {boolean} 是否有完整的密钥
 */
export function hasCompleteEncryptionKeys(userId) {
  const keys = getUserEncryptionKeys(userId);
  return keys && keys.publicKey && keys.registrationId;
}

/**
 * 获取所有已保存密钥的用户列表
 * @returns {number[]} 用户ID数组
 */
export function getAllUsersWithKeys() {
  try {
    const users = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.includes('_key_metadata')) {
        const match = key.match(/user_(\d+)_key_metadata/);
        if (match) {
          users.push(parseInt(match[1]));
        }
      }
    }
    return users;
  } catch (error) {
    console.error('获取用户密钥列表失败:', error);
    return [];
  }
}

/**
 * 验证密钥完整性
 * @param {number} userId - 用户ID
 * @returns {object} 验证结果
 */
export function validateUserKeys(userId) {
  const keys = getUserEncryptionKeys(userId);
  
  if (!keys) {
    return {
      valid: false,
      message: '未找到用户密钥',
      details: {
        hasPublicKey: false,
        hasRegistrationId: false,
        hasPrekeyBundle: false
      }
    };
  }
  
  const hasPublicKey = !!keys.publicKey;
  const hasRegistrationId = !!keys.registrationId;
  const hasPrekeyBundle = !!keys.prekeyBundle;
  
  const isValid = hasPublicKey && hasRegistrationId;
  
  return {
    valid: isValid,
    message: isValid ? '密钥验证通过' : '密钥不完整',
    details: {
      hasPublicKey,
      hasRegistrationId,
      hasPrekeyBundle
    },
    keys
  };
}

/**
 * 初始化用户加密环境
 * @param {number} userId - 用户ID
 * @param {object} encryptionData - 加密数据
 * @returns {Promise<boolean>} 是否初始化成功
 */
export async function initializeUserEncryption(userId, encryptionData) {
  try {
    console.log(`🔐 正在为用户 ${userId} 初始化加密环境...`);
    
    // 保存密钥
    const keysSaved = await saveUserEncryptionKeys(userId, encryptionData);
    
    if (!keysSaved) {
      throw new Error('密钥保存失败');
    }
    
    // 验证密钥
    const validation = validateUserKeys(userId);
    if (!validation.valid) {
      throw new Error(`密钥验证失败: ${validation.message}`);
    }
    
    // 初始化本地数据库
    try {
      await initDatabase();
      console.log('✅ 本地数据库初始化成功');
    } catch (dbError) {
      console.warn('⚠️ 本地数据库初始化失败:', dbError.message);
      // 不抛出错误，因为密钥保存成功更重要
    }
    
    console.log(`✅ 用户 ${userId} 的加密环境初始化完成`);
    return true;
    
  } catch (error) {
    console.error(`❌ 用户 ${userId} 的加密环境初始化失败:`, error);
    return false;
  }
}