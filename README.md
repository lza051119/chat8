## 注意事项：
1. 这个项目的主要功能在master分支里有介绍，所以这里就不提了，这里主要就是实现拆分客户端和服务端
2. 这是一个不完善的客户端服务端分离的版本，之前代码融合在一起，拆开后导致许多功能失效，现在只有注册和登录部分还正常，目前问题卡在了添加好友这一点，搜索好友会显示不存在此用户，不过在日志里却没有任何报错，就很奇怪，慢慢DEBUG吧


## 更新内容：
1. 分离客户端和服务端代码，现在可以独立运行（功能不齐）
2. 在服务端添加内网穿透，可以实现多端访问服务器
3. 修改服务器数据库名称
4. 删除服务端chat8\chat8-server\backend\app\services\friend_service.py内的冗余代码def add_friend(db: Session, user_id: int, friend_id: int):在查代码的时候发现这个功能和双向加好友重复

## 启动服务器的方法：
1. 目前wmt已经弄了一个服务器，然后客户端要连接的地址已经指向了这个服务器，但是因为电脑不是全天开，要测试的时候可以@一下
或者说
2. 可以自己去ngrok的官网注册一个账号，然后在左侧有个栏，点击第二个之后最上方可以看到自己的密钥，然后点击exe之后
3. 打开ngrok.exe,终端里输入ngrok config add-authtoken 2zSSsZZoxrLLU2eqjdv2RzV9a6T_oengdkexpZxJeNWAkSUh
4. 启动隧道：ngrok http 8000
5. 切换到chat8-server/backend目录，在终端输入：uvicorn app.main:app --reload
6. 在chat8-client\frontend这个目录下有个.env文件，把你在第4步输入后返回的Forwarding 填入到开发环境配置当中，比如像这样
7. 自己测试的时候发现一个问题，只要结束隧道之后再次启动，提供的公网地址就不一样了，所以说第四步的这个隧道还是不要乱关

## 开发环境配置
- VITE_API_BASE_URL=https://6db7-183-241-253-253.ngrok-free.app  ←这里
- VITE_WS_BASE_URL=wss://6db7-183-241-253-253.ngrok-free.app     ←这里
- VITE_DEBUG=true
- VITE_LOG_LEVEL=debug