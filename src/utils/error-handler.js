import logger from './logger';
import { getChinaTimeISO, generateTempMessageId } from './timeUtils.js';

/**
 * 错误类型枚举
 */
export const ErrorTypes = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  API_ERROR: 'API_ERROR',
  WEBSOCKET_ERROR: 'WEBSOCKET_ERROR',
  P2P_ERROR: 'P2P_ERROR',
  AUTH_ERROR: 'AUTH_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
};

/**
 * 自定义错误类
 */
export class AppError extends Error {
  constructor(type, message, originalError = null, context = {}) {
    super(message);
    this.name = 'AppError';
    this.type = type;
    this.originalError = originalError;
    this.context = context;
    this.timestamp = getChinaTimeISO();
  }

  /**
   * 获取用户友好的错误消息
   * @returns {string}
   */
  getUserMessage() {
    const userMessages = {
      [ErrorTypes.NETWORK_ERROR]: '网络连接异常，请检查网络设置',
      [ErrorTypes.API_ERROR]: '服务器响应异常，请稍后重试',
      [ErrorTypes.WEBSOCKET_ERROR]: '实时连接中断，正在尝试重连',
      [ErrorTypes.P2P_ERROR]: 'P2P连接失败，将使用服务器转发',
      [ErrorTypes.AUTH_ERROR]: '身份验证失败，请重新登录',
      [ErrorTypes.VALIDATION_ERROR]: '输入数据格式错误，请检查后重试',
      [ErrorTypes.UNKNOWN_ERROR]: '未知错误，请联系技术支持'
    };
    
    return userMessages[this.type] || this.message;
  }

  /**
   * 转换为JSON格式
   * @returns {Object}
   */
  toJSON() {
    return {
      type: this.type,
      message: this.message,
      userMessage: this.getUserMessage(),
      context: this.context,
      timestamp: this.timestamp,
      stack: this.stack
    };
  }
}

/**
 * 错误处理器类
 */
class ErrorHandler {
  constructor() {
    this.errorListeners = [];
    this.setupGlobalErrorHandlers();
  }

  /**
   * 设置全局错误处理器
   */
  setupGlobalErrorHandlers() {
    // 处理未捕获的Promise拒绝
    window.addEventListener('unhandledrejection', (event) => {
      logger.error('global', '未处理的Promise拒绝', event.reason);
      this.handleError(new AppError(
        ErrorTypes.UNKNOWN_ERROR,
        '未处理的异步错误',
        event.reason
      ));
    });

    // 处理全局JavaScript错误
    window.addEventListener('error', (event) => {
      logger.error('global', '全局JavaScript错误', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
      });
      this.handleError(new AppError(
        ErrorTypes.UNKNOWN_ERROR,
        event.message,
        event.error
      ));
    });
  }

  /**
   * 添加错误监听器
   * @param {Function} listener - 错误处理回调
   */
  addErrorListener(listener) {
    this.errorListeners.push(listener);
  }

  /**
   * 移除错误监听器
   * @param {Function} listener - 要移除的监听器
   */
  removeErrorListener(listener) {
    const index = this.errorListeners.indexOf(listener);
    if (index > -1) {
      this.errorListeners.splice(index, 1);
    }
  }

  /**
   * 处理错误
   * @param {Error|AppError} error - 错误对象
   * @param {string} module - 模块名
   * @param {Object} context - 上下文信息
   */
  handleError(error, module = 'unknown', context = {}) {
    let appError;
    
    if (error instanceof AppError) {
      appError = error;
    } else {
      // 根据错误类型自动分类
      const errorType = this.classifyError(error);
      appError = new AppError(errorType, error.message, error, context);
    }

    // 记录错误日志
    logger.error(module, appError.message, {
      type: appError.type,
      context: appError.context,
      originalError: appError.originalError
    });

    // 通知所有错误监听器
    this.errorListeners.forEach(listener => {
      try {
        listener(appError);
      } catch (listenerError) {
        logger.error('error-handler', '错误监听器执行失败', listenerError);
      }
    });

    return appError;
  }

  /**
   * 自动分类错误类型
   * @param {Error} error - 原始错误
   * @returns {string} 错误类型
   */
  classifyError(error) {
    const message = error.message?.toLowerCase() || '';
    
    if (message.includes('network') || message.includes('fetch')) {
      return ErrorTypes.NETWORK_ERROR;
    }
    
    if (message.includes('websocket') || message.includes('connection')) {
      return ErrorTypes.WEBSOCKET_ERROR;
    }
    
    if (message.includes('unauthorized') || message.includes('forbidden')) {
      return ErrorTypes.AUTH_ERROR;
    }
    
    if (message.includes('validation') || message.includes('invalid')) {
      return ErrorTypes.VALIDATION_ERROR;
    }
    
    return ErrorTypes.UNKNOWN_ERROR;
  }

  /**
   * 创建网络错误
   * @param {string} message - 错误消息
   * @param {Error} originalError - 原始错误
   * @param {Object} context - 上下文
   * @returns {AppError}
   */
  createNetworkError(message, originalError = null, context = {}) {
    return new AppError(ErrorTypes.NETWORK_ERROR, message, originalError, context);
  }

  /**
   * 创建API错误
   * @param {string} message - 错误消息
   * @param {Error} originalError - 原始错误
   * @param {Object} context - 上下文
   * @returns {AppError}
   */
  createApiError(message, originalError = null, context = {}) {
    return new AppError(ErrorTypes.API_ERROR, message, originalError, context);
  }

  /**
   * 创建P2P错误
   * @param {string} message - 错误消息
   * @param {Error} originalError - 原始错误
   * @param {Object} context - 上下文
   * @returns {AppError}
   */
  createP2PError(message, originalError = null, context = {}) {
    return new AppError(ErrorTypes.P2P_ERROR, message, originalError, context);
  }
}

// 创建全局错误处理器实例
const errorHandler = new ErrorHandler();

export default errorHandler;