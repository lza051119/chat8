// Chat8 客户端配置文件

// 开发环境配置
const development = {
  API_BASE_URL: '', // 使用相对路径，请求将发送到同源
  WS_BASE_URL: `ws://${window.location.host}`, // 动态获取WebSocket地址
  DEBUG: true,
  LOG_LEVEL: 'debug'
}

// 生产环境配置
const production = {
  API_BASE_URL: '', // 使用相对路径，请求将发送到同源
  WS_BASE_URL: `wss://${window.location.host}`, // 动态获取WebSocket地址 (使用wss)
  DEBUG: false,
  LOG_LEVEL: 'error'
}

// 根据环境变量选择配置
const config = import.meta.env.MODE === 'production' ? production : development

// 如果有环境变量覆盖，使用环境变量
if (import.meta.env.VITE_API_BASE_URL) {
  config.API_BASE_URL = import.meta.env.VITE_API_BASE_URL
}

if (import.meta.env.VITE_WS_BASE_URL) {
  config.WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL
}

export default config

// 导出常用配置
export const {
  API_BASE_URL,
  WS_BASE_URL,
  DEBUG,
  LOG_LEVEL
} = config