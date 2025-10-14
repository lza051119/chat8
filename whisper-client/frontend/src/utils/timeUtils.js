// 时间工具函数 - 统一使用中国时间

// 中国时区偏移量（UTC+8）
const CHINA_TIMEZONE_OFFSET = 8 * 60; // 分钟

/**
 * 获取中国时间的ISO字符串
 * @returns {string} 中国时间的ISO格式字符串
 */
export function getChinaTimeISO() {
  const now = new Date();
  // 获取UTC时间戳
  const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
  // 加上中国时区偏移量
  const chinaTime = new Date(utcTime + (CHINA_TIMEZONE_OFFSET * 60000));
  return chinaTime.toISOString();
}

/**
 * 获取中国时间的Date对象
 * @returns {Date} 中国时间的Date对象
 */
export function getChinaTime() {
  const now = new Date();
  const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
  return new Date(utcTime + (CHINA_TIMEZONE_OFFSET * 60000));
}

/**
 * 将任意时间戳转换为中国时间
 * @param {string|Date} timestamp 时间戳
 * @returns {Date} 中国时间的Date对象
 */
export function toChinaTime(timestamp) {
  const date = new Date(timestamp);
  // 如果已经是中国时间，直接返回
  if (date.getTimezoneOffset() === -480) { // UTC+8的偏移量是-480分钟
    return date;
  }
  
  // 转换为中国时间
  const utcTime = date.getTime() + (date.getTimezoneOffset() * 60000);
  return new Date(utcTime + (CHINA_TIMEZONE_OFFSET * 60000));
}

/**
 * 格式化时间戳为中国时间显示
 * @param {string|Date} timestamp 时间戳
 * @returns {string} 格式化后的时间字符串
 */
export function formatTimestamp(timestamp) {
  if (!timestamp) return '';
  
  const messageDate = toChinaTime(timestamp);
  const now = getChinaTime();
  
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
  const messageDay = new Date(messageDate.getFullYear(), messageDate.getMonth(), messageDate.getDate());
  
  // 手动格式化时间，确保显示中国时间
  const hours = messageDate.getHours().toString().padStart(2, '0');
  const minutes = messageDate.getMinutes().toString().padStart(2, '0');
  const timeStr = `${hours}:${minutes}`;
  
  if (messageDay.getTime() === today.getTime()) {
    return timeStr; // 今天只显示时间
  } else if (messageDay.getTime() === yesterday.getTime()) {
    return `昨天 ${timeStr}`;
  } else if (messageDate.getFullYear() === now.getFullYear()) {
    return `${messageDate.getMonth() + 1}月${messageDate.getDate()}日 ${timeStr}`;
  } else {
    return `${messageDate.getFullYear()}年${messageDate.getMonth() + 1}月${messageDate.getDate()}日 ${timeStr}`;
  }
}

/**
 * 生成消息ID（基于中国时间）
 * @returns {string} 消息ID
 */
export function generateMessageId() {
  const chinaTime = getChinaTime();
  return `msg_${chinaTime.getTime()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 生成临时消息ID（基于中国时间）
 * @returns {string} 临时消息ID
 */
export function generateTempMessageId() {
  const chinaTime = getChinaTime();
  return `temp_${chinaTime.getTime()}_${Math.random().toString(36).substr(2, 9)}`;
}