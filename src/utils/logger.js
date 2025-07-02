// 日志工具类 - 用于控制应用的日志输出级别

// 日志级别定义
const LOG_LEVELS = {
  ERROR: 0,   // 只显示错误
  WARN: 1,    // 显示警告和错误
  INFO: 2,    // 显示信息、警告和错误
  DEBUG: 3    // 显示所有日志
};

// 当前日志级别（可通过环境变量控制）
const CURRENT_LOG_LEVEL = import.meta.env.VITE_LOG_LEVEL 
  ? LOG_LEVELS[import.meta.env.VITE_LOG_LEVEL.toUpperCase()] 
  : LOG_LEVELS.WARN; // 默认只显示警告和错误

class Logger {
  static error(message, ...args) {
    if (CURRENT_LOG_LEVEL >= LOG_LEVELS.ERROR) {
      console.error(message, ...args);
    }
  }

  static warn(message, ...args) {
    if (CURRENT_LOG_LEVEL >= LOG_LEVELS.WARN) {
      console.warn(message, ...args);
    }
  }

  static info(message, ...args) {
    if (CURRENT_LOG_LEVEL >= LOG_LEVELS.INFO) {
      console.log(message, ...args);
    }
  }

  static debug(message, ...args) {
    if (CURRENT_LOG_LEVEL >= LOG_LEVELS.DEBUG) {
      console.log('[DEBUG]', message, ...args);
    }
  }

  // 获取当前日志级别
  static getCurrentLevel() {
    return Object.keys(LOG_LEVELS).find(key => LOG_LEVELS[key] === CURRENT_LOG_LEVEL);
  }
}

export default Logger;

// 使用示例：
// import Logger from '@/utils/logger.js';
// 
// Logger.error('这是错误信息');
// Logger.warn('这是警告信息');
// Logger.info('这是普通信息');
// Logger.debug('这是调试信息');
//
// 在 .env 文件中设置日志级别：
// VITE_LOG_LEVEL=ERROR   # 只显示错误
// VITE_LOG_LEVEL=WARN    # 显示警告和错误（默认）
// VITE_LOG_LEVEL=INFO    # 显示信息、警告和错误
// VITE_LOG_LEVEL=DEBUG   # 显示所有日志