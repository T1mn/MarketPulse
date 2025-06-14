#!/bin/bash

# 激活虚拟环境（如果存在）
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 运行 black 格式化
echo "Running black..."
black . --exclude '\.venv|\.git'

# 运行 isort 格式化
echo "Running isort..."
isort . --skip-glob '.*'

echo "Formatting complete!" 