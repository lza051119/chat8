// Preload script for Electron
// This script runs in the renderer process before the web page loads
// It has access to Node.js APIs and can expose safe APIs to the renderer

const { contextBridge, ipcRenderer } = require('electron');
const path = require('path');
const fs = require('fs');

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 获取应用版本
  getVersion: () => {
    return process.env.npm_package_version || '1.0.0';
  },
  
  // 获取平台信息
  getPlatform: () => {
    return process.platform;
  },
  
  // 检查是否在Electron环境中
  isElectron: () => {
    return true;
  },
  
  // 获取应用路径
  getAppPath: () => {
    return process.resourcesPath || process.cwd();
  },
  
  // 读取配置文件
  readConfig: () => {
    try {
      const configPath = path.join(__dirname, '.env');
      if (fs.existsSync(configPath)) {
        const content = fs.readFileSync(configPath, 'utf8');
        const config = {};
        
        content.split('\n').forEach(line => {
          const [key, value] = line.split('=');
          if (key && value) {
            config[key.trim()] = value.trim();
          }
        });
        
        return config;
      }
    } catch (error) {
      console.error('读取配置文件失败:', error);
    }
    return {};
  },
  
  // 显示通知
  showNotification: (title, body) => {
    new Notification(title, { body });
  },
  
  // 打开外部链接
  openExternal: (url) => {
    ipcRenderer.invoke('open-external', url);
  },
  
  // 最小化窗口
  minimizeWindow: () => {
    ipcRenderer.invoke('minimize-window');
  },
  
  // 关闭窗口
  closeWindow: () => {
    ipcRenderer.invoke('close-window');
  },
  
  // 重启应用
  restartApp: () => {
    ipcRenderer.invoke('restart-app');
  }
});

// 监听主进程消息
ipcRenderer.on('server-status', (event, status) => {
  window.dispatchEvent(new CustomEvent('server-status-changed', {
    detail: status
  }));
});

// 在页面加载完成后注入一些全局变量
window.addEventListener('DOMContentLoaded', () => {
  // 标记这是Electron环境
  document.body.classList.add('electron-app');
  
  // 添加平台特定的样式类
  document.body.classList.add(`platform-${process.platform}`);
  
  // 禁用右键菜单（可选）
  if (process.env.NODE_ENV === 'production') {
    document.addEventListener('contextmenu', (e) => {
      e.preventDefault();
    });
  }
});