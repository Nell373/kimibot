#!/bin/bash
# 確保環境變數已經設置
echo "正在啟動 Kimibot..."

# 設置簡單明確的 Python 路徑
export PYTHONPATH="/app"
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8080"}
export PYTHONUNBUFFERED=1

echo "啟動應用於 ${HOST}:${PORT}"
echo "Python 路徑: ${PYTHONPATH}"

# 確保資料庫目錄存在
if [ ! -d "/app/database" ]; then
    echo "警告: /app/database 目錄不存在，嘗試創建..."
    mkdir -p /app/database
fi

# 列出目錄內容以便調試
echo "當前目錄內容:"
ls -la /app

# 啟動應用
cd /app && python webhook.py --host=${HOST} --port=${PORT} 