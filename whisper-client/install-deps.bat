@echo off
echo 正在安装 Chat8 客户端依赖项...

cd frontend
echo 安装 NPM 依赖...
call npm install

echo 安装完成！
echo.
echo 现在您可以运行 start.bat 来启动应用。
pause 