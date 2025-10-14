# Chat8 Client Configuration

## 环境配置

### 开发环境配置

在 `frontend/src/config/config.js` 中配置开发环境：

```javascript
// 开发环境配置
const development = {
  API_BASE_URL: 'http://localhost:8000',
  WS_BASE_URL: 'ws://localhost:8000',
  DEBUG: true,
  LOG_LEVEL: 'debug'
}

// 生产环境配置
const production = {
  API_BASE_URL: 'https://your-server.com',
  WS_BASE_URL: 'wss://your-server.com',
  DEBUG: false,
  LOG_LEVEL: 'error'
}

// 根据环境变量选择配置
const config = process.env.NODE_ENV === 'production' ? production : development

export default config
```

### 环境变量配置

创建 `frontend/.env` 文件：

```env
# 开发环境
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
VITE_DEBUG=true

# 应用配置
VITE_APP_NAME=Chat8
VITE_APP_VERSION=1.0.0

# 加密配置
VITE_ENCRYPTION_ENABLED=true
VITE_KEY_ROTATION_INTERVAL=86400000  # 24小时

# 文件上传配置
VITE_MAX_FILE_SIZE=10485760  # 10MB
VITE_ALLOWED_FILE_TYPES=image/*,video/*,audio/*,application/pdf,text/*

# 本地存储配置
VITE_LOCAL_STORAGE_ENCRYPTION=true
VITE_MESSAGE_RETENTION_DAYS=30
```

创建 `frontend/.env.production` 文件：

```env
# 生产环境
VITE_API_BASE_URL=https://your-server.com
VITE_WS_BASE_URL=wss://your-server.com
VITE_DEBUG=false

# 应用配置
VITE_APP_NAME=Chat8
VITE_APP_VERSION=1.0.0

# 加密配置
VITE_ENCRYPTION_ENABLED=true
VITE_KEY_ROTATION_INTERVAL=86400000

# 文件上传配置
VITE_MAX_FILE_SIZE=10485760
VITE_ALLOWED_FILE_TYPES=image/*,video/*,audio/*,application/pdf,text/*

# 本地存储配置
VITE_LOCAL_STORAGE_ENCRYPTION=true
VITE_MESSAGE_RETENTION_DAYS=30
```

## Vite配置优化

更新 `frontend/vite.config.js`：

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  
  // 路径别名
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@views': resolve(__dirname, 'src/views'),
      '@services': resolve(__dirname, 'src/services'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@store': resolve(__dirname, 'src/store')
    }
  },
  
  // 开发服务器配置
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      }
    }
  },
  
  // 构建配置
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          crypto: ['@/utils/encryption'],
          ui: ['@/components']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  
  // 优化配置
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios']
  }
})
```

## Nginx配置

### 基本配置

```nginx
server {
    listen 80;
    server_name your-client-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-client-domain.com;
    
    # SSL证书配置
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss: https:;";
    
    # 根目录
    root /path/to/chat8-client/frontend/dist;
    index index.html;
    
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
    }
    
    # HTML文件不缓存
    location ~* \.html$ {
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
    }
    
    # Vue Router支持
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass https://your-server.com;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket代理
    location /ws {
        proxy_pass https://your-server.com;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
}
```

## Docker配置

### 多阶段构建Dockerfile

```dockerfile
# 构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app

# 复制package文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY frontend/ .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine as production-stage

# 复制构建结果
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  chat8-client:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    environment:
      - NODE_ENV=production
    restart: unless-stopped
    depends_on:
      - chat8-server

  chat8-server:
    image: chat8-server:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/chat8
    restart: unless-stopped
```

## PWA配置

### Service Worker

创建 `frontend/public/sw.js`：

```javascript
const CACHE_NAME = 'chat8-v1'
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
]

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  )
})

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response
        }
        return fetch(event.request)
      }
    )
  )
})
```

### Manifest文件

创建 `frontend/public/manifest.json`：

```json
{
  "name": "Chat8",
  "short_name": "Chat8",
  "description": "Secure End-to-End Encrypted Chat Application",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#007bff",
  "icons": [
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

## 性能优化

### 代码分割

```javascript
// router/index.js
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/Chat.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

### 图片优化

```javascript
// utils/imageOptimizer.js
export function optimizeImage(file, maxWidth = 800, quality = 0.8) {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()
    
    img.onload = () => {
      const ratio = Math.min(maxWidth / img.width, maxWidth / img.height)
      canvas.width = img.width * ratio
      canvas.height = img.height * ratio
      
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
      
      canvas.toBlob(resolve, 'image/jpeg', quality)
    }
    
    img.src = URL.createObjectURL(file)
  })
}
```

## 安全配置

### 内容安全策略

```html
<!-- index.html -->
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' wss: https:;
  font-src 'self';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
">
```

### 环境变量验证

```javascript
// config/validation.js
export function validateConfig() {
  const required = [
    'VITE_API_BASE_URL',
    'VITE_WS_BASE_URL'
  ]
  
  const missing = required.filter(key => !import.meta.env[key])
  
  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`)
  }
}
```