# 图片上传功能使用指南

## 功能概述

Chat8 现在支持完整的图片消息发送功能，包括图片上传、存储、实时传输和显示。

## 后端改进内容

### 1. 图片上传API优化 (`upload.py`)

**增强的文件验证:**
- 支持的格式：JPEG、PNG、GIF、WebP
- 文件大小限制：10MB
- 文件名安全性检查
- 内容类型验证
- 文件完整性验证

**安全性改进:**
- 防止路径遍历攻击
- UUID文件名生成
- 错误处理和资源清理
- 详细的日志记录

**关键修改:**
```python
# 只保存文件名到数据库，不保存完整路径
file_path=unique_filename,  # 只保存文件名
```

### 2. 图片访问API优化

**安全性增强:**
- 文件名格式验证（正则表达式）
- 路径遍历防护
- MIME类型检测
- 缓存控制头

**功能改进:**
- 自动内容类型检测
- 错误日志记录
- HTTP缓存优化

### 3. WebSocket实时消息传输

**新增图片消息处理:**
- 专门的 `handle_image_message` 函数
- 支持图片消息的实时推送
- 离线消息包含图片信息
- 完整的消息字段传输

**消息格式标准化:**
```json
{
  "type": "message",
  "data": {
    "id": "消息ID",
    "from": "发送者ID",
    "to": "接收者ID",
    "content": "消息内容",
    "messageType": "image",
    "filePath": "文件名.png",
    "fileName": "原始文件名.png",
    "timestamp": "2024-01-01T12:00:00",
    "encrypted": true,
    "method": "Server"
  }
}
```

### 4. 数据库服务优化

**消息服务改进:**
- 图片消息内容自动生成
- 详细的调试日志
- 错误处理增强

## API使用方法

### 上传图片

**端点:** `POST /api/upload/image`

**请求格式:** `multipart/form-data`

**参数:**
- `file`: 图片文件（必需）
- `to_id`: 接收者ID（必需）
- `content`: 消息内容（可选）
- `encrypted`: 是否加密（默认true）
- `method`: 传输方法（默认Server）
- `destroy_after`: 阅后即焚秒数（可选）
- `hidding_message`: 隐藏消息（可选）

**响应示例:**
```json
{
  "id": 123,
  "from": 1,
  "to": 2,
  "content": "发送了图片: photo.jpg",
  "messageType": "image",
  "filePath": "uuid-filename.jpg",
  "fileName": "photo.jpg",
  "timestamp": "2024-01-01T12:00:00",
  "encrypted": true,
  "method": "Server"
}
```

### 获取图片

**端点:** `GET /api/images/{filename}`

**示例:** `GET /api/images/550e8400-e29b-41d4-a716-446655440000.jpg`

**响应:** 图片文件内容，带有适当的Content-Type头

## 前端集成

### 图片URL构建

前端应该使用以下方式构建图片URL：

```javascript
function getImageUrl(filePath) {
  // 从filePath中提取文件名
  const fileName = filePath.split(/[\\/]/).pop();
  return `/api/images/${fileName}`;
}
```

### WebSocket消息处理

```javascript
// 发送图片消息通知（上传完成后）
websocket.send(JSON.stringify({
  type: 'image_message',
  to_id: receiverId,
  file_path: 'filename.jpg',
  file_name: 'original.jpg',
  content: '发送了图片',
  encrypted: true
}));
```

## 测试

使用提供的测试脚本验证功能：

```bash
python test_image_upload.py
```

测试包括：
- 正常图片上传
- 不同格式支持
- 错误处理
- 图片访问
- 大文件处理

## 安全考虑

1. **文件类型限制**: 只允许图片格式
2. **文件大小限制**: 最大10MB
3. **路径安全**: 防止路径遍历攻击
4. **文件名安全**: 使用UUID生成唯一文件名
5. **访问控制**: 文件名格式验证

## 性能优化

1. **缓存控制**: 图片响应包含缓存头
2. **文件验证**: 上传时验证文件完整性
3. **错误处理**: 失败时自动清理资源
4. **日志记录**: 详细的操作日志便于调试

## 故障排除

### 常见问题

1. **图片无法显示**
   - 检查文件路径是否正确
   - 确认图片文件存在于 `static/images/` 目录
   - 验证图片URL格式

2. **上传失败**
   - 检查文件格式是否支持
   - 确认文件大小不超过限制
   - 查看后端日志获取详细错误信息

3. **WebSocket消息不推送**
   - 确认接收者在线状态
   - 检查WebSocket连接
   - 查看消息格式是否正确

### 调试日志

后端会输出详细的调试信息：
- `[UPLOAD]`: 图片上传相关
- `[GET_IMAGE]`: 图片访问相关
- `[WS]`: WebSocket消息相关
- `[MESSAGE_SERVICE]`: 消息服务相关

## 后续优化建议

1. **图片压缩**: 自动压缩大图片
2. **缩略图生成**: 为图片生成缩略图
3. **CDN集成**: 使用CDN加速图片访问
4. **图片预览**: 支持图片预览功能
5. **批量上传**: 支持多图片同时上传