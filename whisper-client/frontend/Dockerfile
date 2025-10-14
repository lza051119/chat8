# 构建阶段
# 允许通过构建参数替换基础镜像以使用国内镜像源
ARG BASE_NODE=node:18-alpine
ARG BASE_NGINX=nginx:alpine
FROM ${BASE_NODE} as build-stage

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖（无 package-lock.json 时使用 install）
RUN npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
# 同样支持替换 Nginx 基础镜像（必须在第一个 FROM 之前声明 ARG 才能在 FROM 中使用）
FROM ${BASE_NGINX} as production-stage

# 复制自定义nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 复制构建结果到nginx目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]