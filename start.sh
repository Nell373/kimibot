#!/bin/bash
# 確保環境變數已經設置
echo "正在啟動 Kimibot..."

# 確保Python可以找到模塊
export PYTHONPATH=${PYTHONPATH:-"/app"}
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8080"}

echo "啟動應用於 ${HOST}:${PORT}"

# 打印模塊路徑以便調試
echo "Python路徑："
python -c "import sys; print(sys.path)"

# 啟動應用
exec python webhook.py --host=${HOST} --port=${PORT} 