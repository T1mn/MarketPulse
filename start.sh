#!/bin/bash
# MarketPulse 一键启动脚本

cd "$(dirname "$0")"

# 清除代理（访问 Binance 需要）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY

# 激活虚拟环境
source .venv/bin/activate

echo "=========================================="
echo "  MarketPulse 启动中..."
echo "=========================================="

# 启动后端 API（后台运行）
echo "[1/2] 启动后端 API (端口 8000)..."
python3 -m uvicorn api.app:app --host 127.0.0.1 --port 8000 &
API_PID=$!
echo "      后端 PID: $API_PID"

# 等待后端启动
sleep 2

# 启动前端（后台运行）
echo "[2/2] 启动前端 (端口 5173)..."
cd frontend && npm run dev &
FRONTEND_PID=$!
echo "      前端 PID: $FRONTEND_PID"

cd ..

echo ""
echo "=========================================="
echo "  启动完成!"
echo "=========================================="
echo ""
echo "  前端地址: http://127.0.0.1:5173"
echo "  后端地址: http://127.0.0.1:8000"
echo "  API 文档: http://127.0.0.1:8000/docs"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "=========================================="

# 捕获 Ctrl+C 并停止所有服务
trap "echo '正在停止服务...'; kill $API_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# 保持脚本运行
wait
