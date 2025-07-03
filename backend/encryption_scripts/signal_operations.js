const {
  PrivateKey,
  PublicKey,
  IdentityKeyPair,
  PreKeyBundle,
  PreKeyRecord,
  SignedPreKeyRecord,
  SessionBuilder,
  SessionCipher,
  signalEncrypt,
  signalDecrypt,
  processPreKeyBundle,
  ProtocolAddress
} = require('@signalapp/libsignal-client');

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 密钥存储目录
const KEYS_DIR = path.join(__dirname, 'keys');
if (!fs.existsSync(KEYS_DIR)) {
  fs.mkdirSync(KEYS_DIR, { recursive: true });
}

// 生成身份密钥对
function generateIdentityKeyPair() {
  try {
    const identityKeyPair = IdentityKeyPair.generate();
    const publicKey = identityKeyPair.publicKey().serialize();
    const privateKey = identityKeyPair.privateKey().serialize();
    
    return {
      success: true,
      public_key: Buffer.from(publicKey).toString('base64'),
      private_key: Buffer.from(privateKey).toString('base64'),
      registration_id: Math.floor(Math.random() * 16384) + 1
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// 生成预密钥包
function generatePreKeyBundle(userId, registrationId) {
  try {
    // 生成身份密钥对
    const identityKeyPair = IdentityKeyPair.generate();
    
    // 生成预密钥
    const preKeyId = Math.floor(Math.random() * 0xFFFFFF);
    const preKey = PrivateKey.generate();
    const preKeyRecord = PreKeyRecord.new(preKeyId, preKey);
    
    // 生成签名预密钥
    const signedPreKeyId = Math.floor(Math.random() * 0xFFFFFF);
    const signedPreKey = PrivateKey.generate();
    const signedPreKeyPublic = signedPreKey.getPublicKey();
    const signedPreKeySignature = identityKeyPair.privateKey().sign(signedPreKeyPublic.serialize());
    const signedPreKeyRecord = SignedPreKeyRecord.new(
      signedPreKeyId,
      Date.now(),
      signedPreKey,
      signedPreKeySignature
    );
    
    // 创建预密钥包
    const preKeyBundle = PreKeyBundle.new(
      registrationId,
      1, // deviceId
      preKeyId,
      preKey.getPublicKey(),
      signedPreKeyId,
      signedPreKeyPublic,
      signedPreKeySignature,
      identityKeyPair.publicKey()
    );
    
    return {
      success: true,
      prekey_bundle: {
        registration_id: registrationId,
        device_id: 1,
        prekey_id: preKeyId,
        prekey_public: Buffer.from(preKey.getPublicKey().serialize()).toString('base64'),
        signed_prekey_id: signedPreKeyId,
        signed_prekey_public: Buffer.from(signedPreKeyPublic.serialize()).toString('base64'),
        signed_prekey_signature: Buffer.from(signedPreKeySignature).toString('base64'),
        identity_key: Buffer.from(identityKeyPair.publicKey().serialize()).toString('base64')
      },
      prekey_record: Buffer.from(preKeyRecord.serialize()).toString('base64'),
      signed_prekey_record: Buffer.from(signedPreKeyRecord.serialize()).toString('base64'),
      identity_keypair: {
        public: Buffer.from(identityKeyPair.publicKey().serialize()).toString('base64'),
        private: Buffer.from(identityKeyPair.privateKey().serialize()).toString('base64')
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// 保存用户密钥
function saveUserKeys(userId, keys) {
  try {
    const userKeysPath = path.join(KEYS_DIR, `user_${userId}.json`);
    fs.writeFileSync(userKeysPath, JSON.stringify(keys, null, 2));
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// 加载用户密钥
function loadUserKeys(userId) {
  try {
    const userKeysPath = path.join(KEYS_DIR, `user_${userId}.json`);
    if (!fs.existsSync(userKeysPath)) {
      return {
        success: false,
        error: 'User keys not found'
      };
    }
    const keys = JSON.parse(fs.readFileSync(userKeysPath, 'utf8'));
    return {
      success: true,
      keys: keys
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// 建立会话
function establishSession(fromUserId, toUserId) {
  try {
    // 这里简化处理，实际应该从服务器获取对方的预密钥包
    // 然后使用 processPreKeyBundle 建立会话
    
    const sessionPath = path.join(KEYS_DIR, `session_${fromUserId}_${toUserId}.json`);
    const sessionData = {
      established: true,
      timestamp: Date.now()
    };
    
    fs.writeFileSync(sessionPath, JSON.stringify(sessionData, null, 2));
    
    return {
      success: true,
      message: 'Session established'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// 加密消息
function encryptMessage(fromUserId, toUserId, message) {
  try {
    // 简化的加密实现
    // 实际应该使用 SessionCipher 进行加密
    
    const key = crypto.randomBytes(32);
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipher('aes-256-cbc', key);
    
    let encrypted = cipher.update(message, 'utf8', 'base64');
    encrypted += cipher.final('base64');
    
    const encryptedData = {
      encrypted_message: encrypted,
      key: key.toString('base64'),
      iv: iv.toString('base64'),
      timestamp: Date.now()
    };
    
    return {
      success: true,
      encrypted_message: Buffer.from(JSON.stringify(encryptedData)).toString('base64')
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// 解密消息
function decryptMessage(userId, fromUserId, encryptedMessage) {
  try {
    // 简化的解密实现
    const encryptedData = JSON.parse(Buffer.from(encryptedMessage, 'base64').toString('utf8'));
    
    const key = Buffer.from(encryptedData.key, 'base64');
    const decipher = crypto.createDecipher('aes-256-cbc', key);
    
    let decrypted = decipher.update(encryptedData.encrypted_message, 'base64', 'utf8');
    decrypted += decipher.final('utf8');
    
    return {
      success: true,
      decrypted_message: decrypted
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// 命令行接口
if (require.main === module) {
  const args = process.argv.slice(2);
  const operation = args[0];
  
  let result;
  
  switch (operation) {
    case 'generate_identity':
      result = generateIdentityKeyPair();
      break;
      
    case 'generate_prekey_bundle':
      const userId = parseInt(args[1]);
      const registrationId = parseInt(args[2]);
      result = generatePreKeyBundle(userId, registrationId);
      break;
      
    case 'save_keys':
      const saveUserId = parseInt(args[1]);
      const keys = JSON.parse(args[2]);
      result = saveUserKeys(saveUserId, keys);
      break;
      
    case 'load_keys':
      const loadUserId = parseInt(args[1]);
      result = loadUserKeys(loadUserId);
      break;
      
    case 'establish_session':
      const fromId = parseInt(args[1]);
      const toId = parseInt(args[2]);
      result = establishSession(fromId, toId);
      break;
      
    case 'encrypt':
      const encFromId = parseInt(args[1]);
      const encToId = parseInt(args[2]);
      const message = args[3];
      result = encryptMessage(encFromId, encToId, message);
      break;
      
    case 'decrypt':
      const decUserId = parseInt(args[1]);
      const decFromId = parseInt(args[2]);
      const encMessage = args[3];
      result = decryptMessage(decUserId, decFromId, encMessage);
      break;
      
    default:
      result = {
        success: false,
        error: 'Unknown operation'
      };
  }
  
  console.log(JSON.stringify(result));
}

module.exports = {
  generateIdentityKeyPair,
  generatePreKeyBundle,
  saveUserKeys,
  loadUserKeys,
  establishSession,
  encryptMessage,
  decryptMessage
};