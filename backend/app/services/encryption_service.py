import os
import json
import base64
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import User
import subprocess
import tempfile

class EncryptionService:
    """
    端到端加密服务
    使用libsignal实现Signal协议的端到端加密
    """
    
    def __init__(self):
        self.libsignal_path = "/Users/tsuki/Desktop/大二下/chat8/libsignal"
        self.node_path = os.path.join(self.libsignal_path, "node")
        
    def _run_node_script(self, script_content: str) -> Dict:
        """
        执行Node.js脚本调用libsignal
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                # 添加libsignal导入
                full_script = f"""
const {{ IdentityKeyPair, PrivateKey, PublicKey, PreKeyRecord, SignedPreKeyRecord, 
         KEMKeyPair, KyberPreKeyRecord, processPreKeyBundle, signalEncrypt, signalDecrypt,
         signalDecryptPreKey, UsePQRatchet }} = require('{self.node_path}');
const crypto = require('crypto');

{script_content}
"""
                f.write(full_script)
                f.flush()
                
                # 执行脚本
                result = subprocess.run(
                    ['node', f.name],
                    cwd=self.node_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                os.unlink(f.name)
                
                if result.returncode != 0:
                    raise Exception(f"Node.js script failed: {result.stderr}")
                    
                return json.loads(result.stdout)
                
        except Exception as e:
            raise Exception(f"Failed to run libsignal script: {str(e)}")
    
    def generate_identity_keypair(self) -> Dict[str, str]:
        """
        生成身份密钥对
        返回: {"private_key": "base64", "public_key": "base64"}
        """
        script = """
try {
    const identityKeyPair = IdentityKeyPair.generate();
    const result = {
        private_key: Buffer.from(identityKeyPair.privateKey.serialize()).toString('base64'),
        public_key: Buffer.from(identityKeyPair.publicKey.serialize()).toString('base64')
    };
    console.log(JSON.stringify(result));
} catch (error) {
    console.log(JSON.stringify({error: error.message}));
}
"""
        return self._run_node_script(script)
    
    def generate_prekey_bundle(self, identity_private_key: str, registration_id: int, device_id: int = 1) -> Dict:
        """
        生成预密钥包
        """
        script = f"""
try {{
    const identityPrivateKey = PrivateKey.deserialize(Buffer.from('{identity_private_key}', 'base64'));
    const identityPublicKey = identityPrivateKey.getPublicKey();
    
    // 生成预密钥
    const preKeyId = Math.floor(Math.random() * 16777215); // 24-bit
    const preKeyPrivate = PrivateKey.generate();
    const preKeyPublic = preKeyPrivate.getPublicKey();
    
    // 生成签名预密钥
    const signedPreKeyId = Math.floor(Math.random() * 16777215);
    const signedPreKeyPrivate = PrivateKey.generate();
    const signedPreKeyPublic = signedPreKeyPrivate.getPublicKey();
    const signedPreKeySignature = identityPrivateKey.sign(signedPreKeyPublic.serialize());
    
    // 生成Kyber预密钥
    const kyberPreKeyId = Math.floor(Math.random() * 16777215);
    const kyberKeyPair = KEMKeyPair.generate();
    const kyberPublicKey = kyberKeyPair.getPublicKey();
    const kyberSignature = identityPrivateKey.sign(kyberPublicKey.serialize());
    
    const result = {{
        registration_id: {registration_id},
        device_id: {device_id},
        prekey_id: preKeyId,
        prekey_public: Buffer.from(preKeyPublic.serialize()).toString('base64'),
        prekey_private: Buffer.from(preKeyPrivate.serialize()).toString('base64'),
        signed_prekey_id: signedPreKeyId,
        signed_prekey_public: Buffer.from(signedPreKeyPublic.serialize()).toString('base64'),
        signed_prekey_private: Buffer.from(signedPreKeyPrivate.serialize()).toString('base64'),
        signed_prekey_signature: Buffer.from(signedPreKeySignature).toString('base64'),
        kyber_prekey_id: kyberPreKeyId,
        kyber_public_key: Buffer.from(kyberPublicKey.serialize()).toString('base64'),
        kyber_private_key: Buffer.from(kyberKeyPair.getSecretKey().serialize()).toString('base64'),
        kyber_signature: Buffer.from(kyberSignature).toString('base64'),
        identity_public_key: Buffer.from(identityPublicKey.serialize()).toString('base64')
    }};
    
    console.log(JSON.stringify(result));
}} catch (error) {{
    console.log(JSON.stringify({{error: error.message}}));
}}
"""
        return self._run_node_script(script)
    
    def encrypt_message(self, message: str, sender_identity_private: str, 
                      recipient_prekey_bundle: Dict, sender_address: str, 
                      recipient_address: str) -> Dict[str, str]:
        """
        加密消息
        """
        script = f"""
try {{
    const {{ ProtocolAddress, PreKeyBundle, SessionStore, IdentityKeyStore, 
             PreKeyStore, SignedPreKeyStore, KyberPreKeyStore }} = require('{self.node_path}');
    
    // 简化的内存存储实现
    class SimpleSessionStore {{
        constructor() {{
            this.sessions = new Map();
        }}
        
        async loadSession(address) {{
            const key = `${{address.name()}}:${{address.deviceId()}}`;
            return this.sessions.get(key) || null;
        }}
        
        async storeSession(address, record) {{
            const key = `${{address.name()}}:${{address.deviceId()}}`;
            this.sessions.set(key, record);
        }}
        
        async getExistingSessions(addresses) {{
            return addresses.map(addr => this.loadSession(addr)).filter(s => s !== null);
        }}
    }}
    
    class SimpleIdentityKeyStore {{
        constructor(identityKeyPair) {{
            this.identityKeyPair = identityKeyPair;
            this.trustedKeys = new Map();
        }}
        
        async getIdentityKeyPair() {{
            return this.identityKeyPair;
        }}
        
        async getLocalRegistrationId() {{
            return {recipient_prekey_bundle.get('registration_id', 1)};
        }}
        
        async saveIdentity(address, identityKey) {{
            const key = `${{address.name()}}:${{address.deviceId()}}`;
            this.trustedKeys.set(key, identityKey);
            return true;
        }}
        
        async isTrustedIdentity(address, identityKey, direction) {{
            return true; // 简化实现
        }}
        
        async getIdentity(address) {{
            const key = `${{address.name()}}:${{address.deviceId()}}`;
            return this.trustedKeys.get(key) || null;
        }}
    }}
    
    // 解析密钥
    const senderPrivateKey = PrivateKey.deserialize(Buffer.from('{sender_identity_private}', 'base64'));
    const senderPublicKey = senderPrivateKey.getPublicKey();
    const senderIdentityKeyPair = new IdentityKeyPair(senderPublicKey, senderPrivateKey);
    
    // 创建存储
    const sessionStore = new SimpleSessionStore();
    const identityStore = new SimpleIdentityKeyStore(senderIdentityKeyPair);
    
    // 创建地址
    const senderAddr = ProtocolAddress.new('{sender_address}', 1);
    const recipientAddr = ProtocolAddress.new('{recipient_address}', 1);
    
    // 创建预密钥包
    const bundle = PreKeyBundle.new(
        {recipient_prekey_bundle.get('registration_id', 1)},
        {recipient_prekey_bundle.get('device_id', 1)},
        {recipient_prekey_bundle.get('prekey_id')},
        PublicKey.deserialize(Buffer.from('{recipient_prekey_bundle.get('prekey_public')}', 'base64')),
        {recipient_prekey_bundle.get('signed_prekey_id')},
        PublicKey.deserialize(Buffer.from('{recipient_prekey_bundle.get('signed_prekey_public')}', 'base64')),
        Buffer.from('{recipient_prekey_bundle.get('signed_prekey_signature')}', 'base64'),
        PublicKey.deserialize(Buffer.from('{recipient_prekey_bundle.get('identity_public_key')}', 'base64')),
        {recipient_prekey_bundle.get('kyber_prekey_id')},
        KEMPublicKey.deserialize(Buffer.from('{recipient_prekey_bundle.get('kyber_public_key')}', 'base64')),
        Buffer.from('{recipient_prekey_bundle.get('kyber_signature')}', 'base64')
    );
    
    // 处理预密钥包建立会话
    await processPreKeyBundle(bundle, recipientAddr, sessionStore, identityStore, UsePQRatchet.Yes);
    
    // 加密消息
    const messageBytes = Buffer.from('{message}', 'utf8');
    const ciphertext = await signalEncrypt(messageBytes, recipientAddr, sessionStore, identityStore);
    
    const result = {{
        ciphertext: Buffer.from(ciphertext.serialize()).toString('base64'),
        type: ciphertext.type()
    }};
    
    console.log(JSON.stringify(result));
}} catch (error) {{
    console.log(JSON.stringify({{error: error.message, stack: error.stack}}));
}}
"""
        return self._run_node_script(script)
    
    def decrypt_message(self, ciphertext_data: Dict, recipient_identity_private: str,
                      sender_address: str, recipient_address: str) -> str:
        """
        解密消息
        """
        # 实现消息解密逻辑
        # 这里需要根据消息类型选择合适的解密方法
        pass
    
    def setup_user_encryption(self, user_id: int) -> Dict:
        """
        为用户设置端到端加密
        生成身份密钥对和预密钥包
        """
        try:
            # 生成身份密钥对
            identity_keys = self.generate_identity_keypair()
            if 'error' in identity_keys:
                raise Exception(f"Failed to generate identity keys: {identity_keys['error']}")
            
            # 生成预密钥包
            registration_id = user_id  # 使用用户ID作为注册ID
            prekey_bundle = self.generate_prekey_bundle(
                identity_keys['private_key'], 
                registration_id
            )
            if 'error' in prekey_bundle:
                raise Exception(f"Failed to generate prekey bundle: {prekey_bundle['error']}")
            
            # 保存公钥到数据库
            db: Session = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.public_key = identity_keys['public_key']
                    db.commit()
                    
                # 保存完整的密钥信息到文件（实际应用中应该使用安全存储）
                keys_data = {
                    'identity_private_key': identity_keys['private_key'],
                    'identity_public_key': identity_keys['public_key'],
                    'prekey_bundle': prekey_bundle,
                    'registration_id': registration_id
                }
                
                # 创建用户密钥目录
                keys_dir = f"/Users/tsuki/Desktop/大二下/chat8/backend/user_keys"
                os.makedirs(keys_dir, exist_ok=True)
                
                keys_file = os.path.join(keys_dir, f"user_{user_id}_keys.json")
                with open(keys_file, 'w') as f:
                    json.dump(keys_data, f, indent=2)
                
                return {
                    'success': True,
                    'public_key': identity_keys['public_key'],
                    'registration_id': registration_id,
                    'prekey_bundle': {
                        'registration_id': prekey_bundle['registration_id'],
                        'device_id': prekey_bundle['device_id'],
                        'prekey_id': prekey_bundle['prekey_id'],
                        'prekey_public': prekey_bundle['prekey_public'],
                        'signed_prekey_id': prekey_bundle['signed_prekey_id'],
                        'signed_prekey_public': prekey_bundle['signed_prekey_public'],
                        'signed_prekey_signature': prekey_bundle['signed_prekey_signature'],
                        'kyber_prekey_id': prekey_bundle['kyber_prekey_id'],
                        'kyber_public_key': prekey_bundle['kyber_public_key'],
                        'kyber_signature': prekey_bundle['kyber_signature'],
                        'identity_public_key': prekey_bundle['identity_public_key']
                    }
                }
                
            finally:
                db.close()
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_public_key(self, user_id: int) -> Optional[str]:
        """
        获取用户的公钥
        """
        db: Session = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user.public_key if user else None
        finally:
            db.close()
    
    def get_user_prekey_bundle(self, user_id: int) -> Optional[Dict]:
        """
        获取用户的预密钥包（用于建立会话）
        """
        try:
            keys_file = f"/Users/tsuki/Desktop/大二下/chat8/backend/user_keys/user_{user_id}_keys.json"
            if os.path.exists(keys_file):
                with open(keys_file, 'r') as f:
                    keys_data = json.load(f)
                return keys_data.get('prekey_bundle')
            return None
        except Exception:
            return None
    
    def load_user_private_key(self, user_id: int) -> Optional[str]:
        """
        加载用户的私钥
        """
        try:
            keys_file = f"/Users/tsuki/Desktop/大二下/chat8/backend/user_keys/user_{user_id}_keys.json"
            if os.path.exists(keys_file):
                with open(keys_file, 'r') as f:
                    keys_data = json.load(f)
                return keys_data.get('identity_private_key')
            return None
        except Exception:
            return None

# 全局加密服务实例
encryption_service = EncryptionService()