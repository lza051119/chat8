import logger from './logger';
import errorHandler, { ErrorTypes } from './error-handler';

/**
 * 标准API响应格式
 * @typedef {Object} StandardResponse
 * @property {boolean} success - 请求是否成功
 * @property {any} data - 响应数据
 * @property {string} message - 响应消息
 * @property {string} code - 错误码（可选）
 * @property {number} timestamp - 时间戳
 */

/**
 * API响应标准化工具
 */
class ApiResponseHandler {
  /**
   * 标准化API响应
   * @param {any} response - 原始响应
   * @param {string} endpoint - API端点（用于日志）
   * @returns {StandardResponse}
   */
  static normalize(response, endpoint = 'unknown') {
    try {
      // 如果响应为空或null
      if (!response) {
        logger.warn('api', `API响应为空: ${endpoint}`);
        return {
          success: false,
          data: null,
          message: '服务器响应为空',
          timestamp: Date.now()
        };
      }

      // 处理不同的响应格式
      let normalizedResponse;

      // 格式1: { success: boolean, data: any, message?: string }
      if (typeof response.success === 'boolean') {
        normalizedResponse = {
          success: response.success,
          data: response.data,
          message: response.message || (response.success ? '操作成功' : '操作失败'),
          code: response.code,
          timestamp: response.timestamp || Date.now()
        };
      }
      // 格式2: { data: any } (默认成功)
      else if (response.data !== undefined) {
        normalizedResponse = {
          success: true,
          data: response.data,
          message: '操作成功',
          timestamp: Date.now()
        };
      }
      // 格式3: 直接返回数据
      else {
        normalizedResponse = {
          success: true,
          data: response,
          message: '操作成功',
          timestamp: Date.now()
        };
      }

      // 记录调试日志
      logger.debug('api', `API响应标准化完成: ${endpoint}`, {
        original: response,
        normalized: normalizedResponse
      });

      return normalizedResponse;
    } catch (error) {
      logger.error('api', `API响应标准化失败: ${endpoint}`, error);
      return {
        success: false,
        data: null,
        message: '响应处理失败',
        timestamp: Date.now()
      };
    }
  }

  /**
   * 处理API错误响应
   * @param {any} error - 错误对象
   * @param {string} endpoint - API端点
   * @returns {StandardResponse}
   */
  static handleError(error, endpoint = 'unknown') {
    logger.error('api', `API请求失败: ${endpoint}`, error);

    let errorMessage = '请求失败';
    let errorCode = 'UNKNOWN_ERROR';
    let statusCode = 0;

    // 处理不同类型的错误
    if (error.response) {
      // 服务器返回了错误状态码
      statusCode = error.response.status;
      errorMessage = error.response.data?.message || error.response.statusText || '服务器错误';
      errorCode = error.response.data?.code || `HTTP_${statusCode}`;
    } else if (error.request) {
      // 请求已发出但没有收到响应
      errorMessage = '网络连接失败';
      errorCode = 'NETWORK_ERROR';
    } else {
      // 其他错误
      errorMessage = error.message || '未知错误';
      errorCode = 'REQUEST_ERROR';
    }

    // 根据状态码提供更友好的错误消息
    const friendlyMessages = {
      400: '请求参数错误',
      401: '身份验证失败，请重新登录',
      403: '权限不足，无法访问',
      404: '请求的资源不存在',
      408: '请求超时，请重试',
      429: '请求过于频繁，请稍后重试',
      500: '服务器内部错误',
      502: '网关错误',
      503: '服务暂时不可用',
      504: '网关超时'
    };

    if (friendlyMessages[statusCode]) {
      errorMessage = friendlyMessages[statusCode];
    }

    return {
      success: false,
      data: null,
      message: errorMessage,
      code: errorCode,
      statusCode: statusCode,
      timestamp: Date.now()
    };
  }

  /**
   * 验证响应数据
   * @param {StandardResponse} response - 标准化响应
   * @param {Function} validator - 验证函数
   * @returns {StandardResponse}
   */
  static validate(response, validator) {
    if (!response.success) {
      return response;
    }

    try {
      const isValid = validator(response.data);
      if (!isValid) {
        logger.warn('api', '响应数据验证失败', response.data);
        return {
          ...response,
          success: false,
          message: '响应数据格式错误'
        };
      }
      return response;
    } catch (error) {
      logger.error('api', '响应数据验证异常', error);
      return {
        ...response,
        success: false,
        message: '数据验证失败'
      };
    }
  }

  /**
   * 提取响应数据
   * @param {StandardResponse} response - 标准化响应
   * @param {any} defaultValue - 默认值
   * @returns {any}
   */
  static extractData(response, defaultValue = null) {
    if (!response || !response.success) {
      return defaultValue;
    }
    return response.data !== undefined ? response.data : defaultValue;
  }

  /**
   * 检查响应是否成功
   * @param {StandardResponse} response - 标准化响应
   * @returns {boolean}
   */
  static isSuccess(response) {
    return response && response.success === true;
  }

  /**
   * 获取错误消息
   * @param {StandardResponse} response - 标准化响应
   * @returns {string}
   */
  static getErrorMessage(response) {
    if (!response) {
      return '未知错误';
    }
    return response.message || '操作失败';
  }

  /**
   * 创建成功响应
   * @param {any} data - 响应数据
   * @param {string} message - 成功消息
   * @returns {StandardResponse}
   */
  static createSuccess(data, message = '操作成功') {
    return {
      success: true,
      data: data,
      message: message,
      timestamp: Date.now()
    };
  }

  /**
   * 创建失败响应
   * @param {string} message - 错误消息
   * @param {string} code - 错误码
   * @returns {StandardResponse}
   */
  static createError(message, code = 'ERROR') {
    return {
      success: false,
      data: null,
      message: message,
      code: code,
      timestamp: Date.now()
    };
  }
}

export default ApiResponseHandler;