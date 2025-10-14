// Preload script for Electron
// This script runs in the renderer process before the web page loads
// It has access to Node.js APIs and can expose safe APIs to the renderer

const { contextBridge, ipcRenderer } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');
const { app } = require('@electron/remote');

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
  },
  
  // 文件系统操作
  fs: {
    // 读取文件
    readFile: (filePath, options) => {
      try {
        return fs.readFileSync(filePath, options);
      } catch (error) {
        console.error('读取文件失败:', error);
        throw error;
      }
    },
    
    // 写入文件
    writeFile: (filePath, data, options) => {
      try {
        fs.writeFileSync(filePath, data, options);
        return true;
      } catch (error) {
        console.error('写入文件失败:', error);
        throw error;
      }
    },
    
    // 检查文件/目录是否存在
    exists: (path) => {
      return fs.existsSync(path);
    },
    
    // 创建目录
    mkdir: (path, options) => {
      try {
        fs.mkdirSync(path, options);
        return true;
      } catch (error) {
        console.error('创建目录失败:', error);
        throw error;
      }
    },
    
    // 获取目录内容
    readdir: (path) => {
      try {
        return fs.readdirSync(path);
      } catch (error) {
        console.error('读取目录失败:', error);
        throw error;
      }
    },
    
    // 删除文件
    unlink: (path) => {
      try {
        fs.unlinkSync(path);
        return true;
      } catch (error) {
        console.error('删除文件失败:', error);
        throw error;
      }
    },
    
    // 获取文件信息
    stat: (path) => {
      try {
        return fs.statSync(path);
      } catch (error) {
        console.error('获取文件信息失败:', error);
        throw error;
      }
    }
  },
  
  // 路径操作
  path: {
    join: (...args) => path.join(...args),
    resolve: (...args) => path.resolve(...args),
    dirname: (p) => path.dirname(p),
    basename: (p, ext) => path.basename(p, ext),
    extname: (p) => path.extname(p)
  },
  
  // 获取系统路径
  getPath: (name) => {
    try {
      if (app) {
        return app.getPath(name);
      } else {
        // 备用方案
        const paths = {
          home: os.homedir(),
          appData: path.join(os.homedir(), 'AppData', 'Roaming'),
          userData: path.join(os.homedir(), 'AppData', 'Roaming', 'chat8'),
          temp: os.tmpdir(),
          downloads: path.join(os.homedir(), 'Downloads')
        };
        return paths[name] || '';
      }
    } catch (error) {
      console.error('获取路径失败:', error);
      return '';
    }
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