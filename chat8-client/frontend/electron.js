const { app, BrowserWindow, Menu, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');

// 保持对窗口对象的全局引用，如果不这么做的话，当JavaScript对象被
// 垃圾回收的时候，窗口会被自动地关闭
let mainWindow;
let serverProcess = null;
let isQuitting = false;

// 获取应用配置
function getAppConfig() {
  const configPath = path.join(__dirname, '.env');
  const config = {
    apiUrl: 'http://localhost:8000',
    wsUrl: 'ws://localhost:8000'
  };
  
  if (fs.existsSync(configPath)) {
    const envContent = fs.readFileSync(configPath, 'utf8');
    const apiMatch = envContent.match(/VITE_API_BASE_URL=(.+)/);
    const wsMatch = envContent.match(/VITE_WS_BASE_URL=(.+)/);
    
    if (apiMatch) config.apiUrl = apiMatch[1];
    if (wsMatch) config.wsUrl = wsMatch[1];
  }
  
  return config;
}

// 检查服务器是否运行
function checkServerStatus(url) {
  return new Promise((resolve) => {
    const http = require('http');
    const urlObj = new URL(url);
    
    const req = http.request({
      hostname: urlObj.hostname,
      port: urlObj.port || 80,
      path: '/api/ping',
      method: 'GET',
      timeout: 3000
    }, (res) => {
      resolve(res.statusCode === 200);
    });
    
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
    
    req.end();
  });
}

// 启动本地服务器
function startLocalServer() {
  return new Promise((resolve, reject) => {
    const serverPath = path.join(__dirname, '..', '..', 'chat8-server', 'backend');
    
    if (!fs.existsSync(serverPath)) {
      reject(new Error('服务器目录不存在'));
      return;
    }
    
    // 检查Python是否可用
    const pythonCmd = os.platform() === 'win32' ? 'python' : 'python3';
    
    serverProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'], {
      cwd: serverPath,
      stdio: ['ignore', 'pipe', 'pipe']
    });
    
    let serverStarted = false;
    
    serverProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log('Server output:', output);
      
      if (output.includes('Uvicorn running on') && !serverStarted) {
        serverStarted = true;
        setTimeout(() => resolve(), 2000); // 等待2秒确保服务器完全启动
      }
    });
    
    serverProcess.stderr.on('data', (data) => {
      console.error('Server error:', data.toString());
    });
    
    serverProcess.on('error', (error) => {
      console.error('Failed to start server:', error);
      reject(error);
    });
    
    // 如果10秒内没有启动成功，认为失败
    setTimeout(() => {
      if (!serverStarted) {
        reject(new Error('服务器启动超时'));
      }
    }, 10000);
  });
}

// 创建主窗口
function createWindow() {
  // 创建浏览器窗口
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    icon: path.join(__dirname, 'public', 'favicon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: true,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false, // 先不显示，等加载完成后再显示
    titleBarStyle: 'default'
  });

  // 设置应用菜单
  const template = [
    {
      label: '文件',
      submenu: [
        {
          label: '退出',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: '编辑',
      submenu: [
        { label: '撤销', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
        { label: '重做', accelerator: 'Shift+CmdOrCtrl+Z', role: 'redo' },
        { type: 'separator' },
        { label: '剪切', accelerator: 'CmdOrCtrl+X', role: 'cut' },
        { label: '复制', accelerator: 'CmdOrCtrl+C', role: 'copy' },
        { label: '粘贴', accelerator: 'CmdOrCtrl+V', role: 'paste' }
      ]
    },
    {
      label: '视图',
      submenu: [
        { label: '重新加载', accelerator: 'CmdOrCtrl+R', role: 'reload' },
        { label: '强制重新加载', accelerator: 'CmdOrCtrl+Shift+R', role: 'forceReload' },
        { label: '开发者工具', accelerator: 'F12', role: 'toggleDevTools' },
        { type: 'separator' },
        { label: '实际大小', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' },
        { label: '放大', accelerator: 'CmdOrCtrl+Plus', role: 'zoomIn' },
        { label: '缩小', accelerator: 'CmdOrCtrl+-', role: 'zoomOut' },
        { type: 'separator' },
        { label: '全屏', accelerator: 'F11', role: 'togglefullscreen' }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '关于 Chat8',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: '关于 Chat8',
              message: 'Chat8 - 安全的端到端加密聊天应用',
              detail: '版本: 1.0.0\n基于 Electron + Vue.js 构建\n支持端到端加密通信'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);

  // 窗口准备显示时
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // 如果是开发环境，打开开发者工具
    if (process.env.NODE_ENV === 'development') {
      mainWindow.webContents.openDevTools();
    }
  });

  // 当窗口被关闭时
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 处理窗口关闭事件
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      
      dialog.showMessageBox(mainWindow, {
        type: 'question',
        buttons: ['最小化到托盘', '退出应用'],
        defaultId: 0,
        title: '确认',
        message: '您想要最小化到托盘还是退出应用？'
      }).then((result) => {
        if (result.response === 1) {
          isQuitting = true;
          app.quit();
        } else {
          mainWindow.hide();
        }
      });
    }
  });

  // 处理外部链接
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  return mainWindow;
}

// 初始化应用
async function initializeApp() {
  try {
    const config = getAppConfig();
    console.log('应用配置:', config);
    
    // 检查服务器状态
    const serverRunning = await checkServerStatus(config.apiUrl);
    
    if (!serverRunning) {
      console.log('服务器未运行，尝试启动本地服务器...');
      
      try {
        await startLocalServer();
        console.log('本地服务器启动成功');
      } catch (error) {
        console.error('启动本地服务器失败:', error);
        
        const result = await dialog.showMessageBox(null, {
          type: 'warning',
          buttons: ['继续', '退出'],
          defaultId: 0,
          title: 'Chat8 - 服务器连接',
          message: '无法连接到Chat8服务器',
          detail: '本地服务器启动失败。您可以：\n1. 手动启动服务器后重试\n2. 连接到远程服务器\n3. 退出应用'
        });
        
        if (result.response === 1) {
          app.quit();
          return;
        }
      }
    } else {
      console.log('服务器已运行');
    }
    
    // 创建主窗口
    createWindow();
    
    // 加载应用
    if (process.env.NODE_ENV === 'development') {
      // 开发环境：连接到Vite开发服务器
      mainWindow.loadURL('http://localhost:8080');
    } else {
      // 生产环境：加载打包后的文件
      mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
    }
    
  } catch (error) {
    console.error('应用初始化失败:', error);
    
    dialog.showErrorBox('Chat8 - 启动错误', `应用启动失败：${error.message}`);
    app.quit();
  }
}

// 当 Electron 完成初始化并准备创建浏览器窗口时调用此方法
app.whenReady().then(initializeApp);

// 当所有窗口都被关闭时退出应用
app.on('window-all-closed', () => {
  // 在 macOS 上，应用和菜单栏通常会保持活动状态，
  // 直到用户使用 Cmd + Q 显式退出
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // 在 macOS 上，当单击 dock 图标并且没有其他窗口打开时，
  // 通常会在应用中重新创建一个窗口
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// 应用退出前清理
app.on('before-quit', () => {
  isQuitting = true;
  
  // 停止服务器进程
  if (serverProcess) {
    console.log('正在停止服务器...');
    serverProcess.kill();
    serverProcess = null;
  }
});

// 防止多个实例
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    // 当运行第二个实例时，将会聚焦到主窗口
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}