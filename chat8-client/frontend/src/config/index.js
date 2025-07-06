// 安全的环境变量访问函数
const getEnvVar = (key, defaultValue) => {
  try {
    // 在 Vite 环境中，环境变量通过 import.meta.env 访问
    if (typeof import !== 'undefined' && import.meta && import.meta.env) {
      return import.meta.env[key] || defaultValue;
    }
    // 在 webpack 环境中，环境变量通过 process.env 访问
    if (typeof process !== 'undefined' && process.env) {
      return process.env[key] || defaultValue;
    }
    // 浏览器环境回退到默认值
    return defaultValue;
  } catch (error) {
    console.warn(`无法访问环境变量 ${key}，使用默认值:`, defaultValue);
    return defaultValue;
  }
};

// 检查是否为生产环境
const isProduction = () => {
  try {
    if (typeof import !== 'undefined' && import.meta && import.meta.env) {
      return import.meta.env.MODE === 'production';
    }
    if (typeof process !== 'undefined' && process.env) {
      return process.env.NODE_ENV === 'production';
    }
    return false;
  } catch (error) {
    return false;
  }
};

// 统一配置管理
const config = {
  // API配置
  api: {
    baseUrl: getEnvVar('VITE_API_BASE_URL', '/api/v1'),
    baseURL: getEnvVar('VITE_API_BASE_URL', '/api/v1'), // 兼容性
    timeout: 10000,
    retryAttempts: 3,
    retryDelay: 1000
  },

  // WebSocket配置
  websocket: {
    url: getEnvVar('VITE_WS_URL', 'ws://localhost:8000/ws'),
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000
  },

  // P2P配置
  p2p: {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ],
    connectionTimeout: 10000,
    dataChannelOptions: {
      ordered: true,
      maxRetransmits: 3
    },
    capabilities: {
      video: true,
      audio: true,
      file_transfer: true,
      screen_share: false
    }
  },

  // 缓存配置
  cache: {
    userStatusTTL: 30000, // 30秒
    messageHistoryLimit: 100,
    offlineMessageLimit: 50
  },

  // 日志配置
  logging: {
    level: isProduction() ? 'error' : 'debug',
    modules: {
      p2p: true,
      websocket: true,
      api: true,
      messaging: true,
      status: true,
      presence: true
    }
  },

  // 安全配置
  security: {
    tokenRefreshThreshold: 300000, // 5分钟
    maxLoginAttempts: 5,
    lockoutDuration: 900000 // 15分钟
  }
};

export default config;