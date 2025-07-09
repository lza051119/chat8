/**
 * 单点登录管理器
 * 确保同一用户不能在多个页面同时登录
 */

// 用于跨页面通信的频道
let loginChannel = null;

// 当前会话ID
const sessionId = Date.now().toString() + Math.random().toString(36).substring(2, 15);

// 初始化单点登录机制
export function initSingleLogin() {
  // 检查浏览器是否支持 BroadcastChannel
  if (typeof BroadcastChannel !== 'undefined') {
    // 创建广播频道
    loginChannel = new BroadcastChannel('chat8_login_channel');
    
    // 监听其他页面的登录消息
    loginChannel.onmessage = (event) => {
      if (event.data.type === 'login_check' && event.data.sessionId !== sessionId) {
        // 响应登录检查，告知该用户已在此页面登录
        const currentUser = JSON.parse(localStorage.getItem('user') || 'null');
        if (currentUser && currentUser.id === event.data.userId) {
          loginChannel.postMessage({
            type: 'login_response',
            sessionId: sessionId,
            requestSessionId: event.data.sessionId,
            userId: currentUser.id,
            username: currentUser.username,
            loggedIn: true
          });
        }
      } else if (event.data.type === 'force_logout' && event.data.sessionId !== sessionId) {
        // 被其他页面强制登出
        const currentUser = JSON.parse(localStorage.getItem('user') || 'null');
        if (currentUser && currentUser.id === event.data.userId) {
          console.log('检测到在其他页面登录，当前会话将被登出');
          // 清除本地存储
          localStorage.removeItem('user');
          localStorage.removeItem('token');
          // 刷新页面，强制重定向到登录页
          window.location.href = '/login?reason=forced_logout';
        }
      }
    };
    
    console.log('单点登录机制已初始化，会话ID:', sessionId);
  } else {
    console.warn('当前浏览器不支持 BroadcastChannel API，单点登录功能将不可用');
  }
}

/**
 * 检查用户是否已在其他页面登录
 * @param {number|string} userId - 用户ID
 * @returns {Promise<boolean>} - 如果用户已在其他页面登录，返回true
 */
export function checkUserLoggedInElsewhere(userId) {
  return new Promise((resolve) => {
    if (!loginChannel) {
      resolve(false);
      return;
    }
    
    // 设置超时，如果没有收到响应，则认为用户未在其他页面登录
    const timeout = setTimeout(() => {
      resolve(false);
    }, 500);
    
    // 监听响应
    const responseHandler = (event) => {
      if (event.data.type === 'login_response' && 
          event.data.requestSessionId === sessionId &&
          event.data.userId === userId &&
          event.data.loggedIn) {
        clearTimeout(timeout);
        loginChannel.removeEventListener('message', responseHandler);
        resolve(true);
      }
    };
    
    loginChannel.addEventListener('message', responseHandler);
    
    // 广播检查消息
    loginChannel.postMessage({
      type: 'login_check',
      sessionId: sessionId,
      userId: userId,
      timestamp: Date.now()
    });
  });
}

/**
 * 强制其他页面登出当前用户
 * @param {number|string} userId - 用户ID
 */
export function forceLogoutOtherSessions(userId) {
  if (!loginChannel) return;
  
  loginChannel.postMessage({
    type: 'force_logout',
    sessionId: sessionId,
    userId: userId,
    timestamp: Date.now()
  });
}

/**
 * 清理单点登录资源
 */
export function cleanupSingleLogin() {
  if (loginChannel) {
    loginChannel.close();
    loginChannel = null;
  }
} 