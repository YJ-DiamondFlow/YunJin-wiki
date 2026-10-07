@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================
echo   YunJin-wiki 一键启动
echo ============================================

where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 python，请先安装 Python 3 并加入 PATH。
  pause
  exit /b 1
)

if not exist "frontend\dist\index.html" (
  echo [1/2] 未检测到前端构建产物，正在构建前端...
  cd frontend
  if not exist "node_modules" (
    call npm install
  )
  call npm run build
  cd ..
) else (
  echo [1/2] 前端已构建，跳过。
)

echo [2/2] 启动后端服务...
python backend\server.py

pause
