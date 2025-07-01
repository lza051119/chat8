
**已初步完成所有后端API，但完成测试的仅有** *认证相关API (authAPI)、联系人相关API (contactAPI)、消息相关API (messageAPI)*，**剩余部分会继续开展测试，测试结果保存至`Postman_test_result.md`**

---

### 数据库初始化
首次部署或数据库丢失时，请先运行以下命令初始化数据库表结构：
```Bash
cd backend/app
python init_db.py
```
看到“数据库表已创建”即成功。之后即可正常启动后端服务。

---

### 部分功能增强但兼容

##### 1. 联系人和消息接口支持分页
* `/api/contacts` 支持 `page` 和 `limit` 分页参数，方便大数据量场景下的联系人管理。
* `/api/messages/history/{userId}` 也支持分页，便于高效获取历史消息。
##### 2. 密钥指纹校验接口
* 增加了 `/api/keys/verify-fingerprint`，用于校验公钥指纹，提升安全性。
##### 3. WebSocket事件类型更丰富
- 除了标准的 `message|signal|presence`，还实现了：
	- 打字通知（`typing_start/typing_stop`）
	- 截图提醒（`screenshot_alert`）
	- WebRTC信令细分（`webrtc_offer/webrtc_answer/webrtc_ice_candidate`）
- 这些事件类型有助于提升用户体验和安全性。
##### 4. 错误处理更健全
- FastAPI全局异常处理，返回结构与api.md一致，并且能详细返回参数校验错误细节。
##### 5. 参数灵活性增强
- `/api/keys/public` 和 `/api/presence/contacts` 既支持无参数（自动查出所有联系人），也兼容传递 `user_ids` 参数，灵活性更高。
##### 6. 代码结构和接口返回更健壮
- 对部分接口返回结构做了更细致的处理（如好友已存在、消息删除权限等），实际体验更友好。