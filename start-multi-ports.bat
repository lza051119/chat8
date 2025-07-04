@echo off
chcp 65001 >nul

REM Chat8 多端口启动脚本 (Windows版本)
REM 同时在8080、8081、8082端口启动前端服务

echo 正在启动Chat8前端服务...
echo 端口: 8080, 8081, 8082
echo 后端API: http://localhost:8000
echo 按 Ctrl+C 停止所有服务
echo ========================

REM 创建日志目录
if not exist logs mkdir logs

REM 启动8080端口服务
echo 启动端口 8080...
start "Chat8-Port-8080" /min cmd /c "set PORT=8080 && npm run dev > logs\port-8080.log 2>&1"
echo 端口 8080 启动完成

REM 等待一秒
timeout /t 1 /nobreak >nul

REM 启动8081端口服务
echo 启动端口 8081...
start "Chat8-Port-8081" /min cmd /c "set PORT=8081 && npm run dev > logs\port-8081.log 2>&1"
echo 端口 8081 启动完成

REM 等待一秒
timeout /t 1 /nobreak >nul

REM 启动8082端口服务
echo 启动端口 8082...
start "Chat8-Port-8082" /min cmd /c "set PORT=8082 && npm run dev > logs\port-8082.log 2>&1"
echo 端口 8082 启动完成

echo ========================
echo 所有服务已启动:
echo - http://localhost:8080
echo - http://localhost:8081
echo - http://localhost:8082
echo ========================
echo 日志文件:
echo - logs\port-8080.log
echo - logs\port-8081.log
echo - logs\port-8082.log
echo ========================
echo 要停止所有服务，请关闭所有Chat8窗口或使用任务管理器
echo 按任意键退出此窗口...
pause >nul