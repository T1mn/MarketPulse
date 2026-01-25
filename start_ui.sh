#!/bin/bash
# MarketPulse Web UI 启动脚本

cd "$(dirname "$0")"

# 激活虚拟环境
source .venv/bin/activate

# 彻底清除所有代理环境变量
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY
unset all_proxy
unset ALL_PROXY
unset ftp_proxy
unset FTP_PROXY
unset socks_proxy
unset SOCKS_PROXY
unset no_proxy
unset NO_PROXY

# 确保不使用任何代理
export NO_PROXY="*"

echo "🚀 启动 MarketPulse Web UI..."
echo "📍 访问地址: http://127.0.0.1:7860"
echo ""

# 启动 Web UI
python3 main.py ui
