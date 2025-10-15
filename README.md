## 注意事项：
1. 这个项目的主要功能在master分支里有介绍，所以这里就不提了，这里主要就是实现拆分客户端和服务端
2. 这是一个不完善的客户端服务端分离的版本，之前代码融合在一起，拆开后导致许多功能失效，现在只有注册和登录部分还正常，目前问题卡在了添加好友这一点，搜索好友会显示不存在此用户，不过在日志里却没有任何报错，就很奇怪，慢慢DEBUG吧


## 更新内容：
1. 分离客户端和服务端代码，现在可以独立运行（功能不齐）
2. 正在为一键部署Ubuntu服务器而努力



## 离线镜像导出与导入（推荐在受限网络或服务器部署时使用）
- 在 GitHub 仓库的 `Actions` 里运行工作流：`Export Offline Docker Images`（手动触发，默认 `amd64`）。
- 运行完成后，在该工作流的 `Artifacts` 下载两个文件：
  - `whisper_backend_amd64.tar.gz`
  - `whisper_frontend_amd64.tar.gz`
- 在目标机器导入（Linux/WSL/Windows PowerShell 皆可，路径按实际替换）：
  - `docker load -i /path/to/whisper_backend_amd64.tar.gz`
  - `docker load -i /path/to/whisper_frontend_amd64.tar.gz`
- 使用生产编排启动（如需同域部署）：
  - 在项目根目录：`docker compose -f docker-compose.prod.yml up -d`
  - 必要变量（示例）：`ALLOWED_ORIGINS=http://localhost:8080` 或你的域名
- 验证：
  - 前端 `http://<主机IP或localhost>:8080`
  - 后端 `http://<主机IP或localhost>:8000`

## 其他机器如何完整部署这个服务器（Ubuntu/WSL 详细教程）
**适用对象**：在一台新的 Ubuntu 22.04/24.04 服务器，或在 Windows 上用 WSL2 的 Ubuntu 子系统

**一、准备工作**
- 架构确认（服务器上执行）：
  - `uname -m` 输出 `x86_64` 则为 `amd64`，`aarch64` 则为 `arm64`。
- 安装 Docker 与 Compose：
  - Ubuntu：
    - `sudo apt-get update`
    - `sudo apt-get install -y ca-certificates curl gnupg lsb-release`
    - `sudo install -m 0755 -d /etc/apt/keyrings`
    - `curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg`
    - `echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null`
    - `sudo apt-get update`
    - `sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin`
    - `sudo usermod -aG docker $USER && newgrp docker`
  - WSL2（Windows）：`wsl --install -d Ubuntu` 后按上面 Ubuntu 步骤安装 Docker，或启用 Docker Desktop 的 WSL 集成。
- 网络与端口：确保服务器对外开放 `80/443/8080/8000`（或按你的域名/端口策略调整）。

**二、两种部署方式（任选其一）**
- 方式 A（推荐，因为现在国内的镜像好多都用不了了）：使用离线应用镜像（最稳，不依赖 npm/pip/Docker Hub）
  - 从 GitHub Actions 的 `Artifacts` 下载：
    - `whisper_backend_amd64.tar.gz`
    - `whisper_frontend_amd64.tar.gz`
  - 上传到服务器并导入（示例）：
    - `docker load -i ~/whisper_backend_amd64.tar.gz`
    - `docker load -i ~/whisper_frontend_amd64.tar.gz`
  - 启动（同域反代、免 CORS）：
    - `export ALLOWED_ORIGINS=http://localhost:8080`  # 或你的域名，如 `https://chat.example.com`
    - `docker compose -f docker-compose.prod.yml up -d`
  - 访问与验证：
    - 前端：`http://<服务器IP>:8080`
    - 后端：`http://<服务器IP>:8000`
    - 日志：`docker logs -n 100 whisper_frontend`、`docker logs -n 100 whisper_backend`

- 方式 B：从镜像仓库拉取（需提前用 CI 推送到仓库）
  - 准备镜像仓库（Docker Hub / GHCR / 阿里云 ACR），在 GitHub 仓库设置 Secrets：
    - `REGISTRY_DOMAIN`、`REGISTRY_USERNAME`、`REGISTRY_PASSWORD`、`IMAGE_PREFIX`
  - 触发我们已有的 `build-and-push.yml` 工作流，完成后在服务器执行：
    - `docker login <REGISTRY_DOMAIN>`
    - `export REGISTRY_DOMAIN=<你的域名>`
    - `export IMAGE_PREFIX=<你的命名空间>`
    - `export ALLOWED_ORIGINS=http://<你的前端地址>`
    - `docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d`

**三、目录与配置（生产）**
- 后端容器内持久目录：`/app/data/database`、`/app/data/uploads`、`/app/data/logs`（Compose 已挂载）。
- 关键环境变量：
  - `ALLOWED_ORIGINS`：前端的完整来源（含协议与端口），如 `http://localhost:8080`、`https://chat.example.com`。
  - 如有 `SECRET_KEY`、`DB_URL` 等敏感变量，请在服务器侧通过环境导出或 `.env` 注入。

**四、常见问题排查**
- 端口占用：
  - `sudo lsof -i:8080`、`sudo lsof -i:8000`，确认无其他进程占用。
- 构建失败（仅本地构建时）：
  - 确保基础镜像已可用（离线导入或公网可拉取），网络受限时优先用“方式 A”。
- CORS 报错：
  - 确认 `ALLOWED_ORIGINS` 指向当前前端访问地址；推荐同域部署（前端通过 Nginx 反向代理 `/api`、`/ws`）。
- WebSocket 失败：
  - 检查 Nginx 配置是否包含 `/ws` 反代，确保 80/443 开放；HTTPS 场景需正确证书。

**五、更新与回滚**
- 离线镜像：重新在 Actions 运行 `Export Offline Docker Images`，下载并 `docker load` 覆盖运行。
- 仓库拉取：重新触发 CI 构建，服务器 `docker compose pull && docker compose up -d`。
- 回滚：保留上一个版本的 tar.gz 或镜像标签（如 `:v1.0.0`），通过 `docker tag` 与 `docker compose` 指定版本。

**六、WSL2 本地联调（可选）**
- 导入基础镜像：将 `node:18-alpine`、`python:3.11-slim`、`nginx:alpine` 的 tar.gz 用 `docker load -i` 导入。
- 构建与运行：在项目根目录执行 `docker compose build && docker compose up -d`，在浏览器访问 `http://localhost:8080`。
- 性能建议：将代码复制到 WSL 文件系统（如 `~/work/whisper`）再运行容器。